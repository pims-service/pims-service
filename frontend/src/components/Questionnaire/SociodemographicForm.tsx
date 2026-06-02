import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { questionnairesApi } from '../../services/api';
import { CheckCircle2, Loader2, Save } from 'lucide-react';

interface Question {
  id: string;
  content: string;
  type: string;
  required: boolean;
  options: { id: string; label: string; numeric_value: number }[];
}

interface SociodemographicFormProps {
  questions: Question[];
  responseSetId: string;
  initialResponses: Record<string, any>;
  onComplete: (responses: Record<string, any>) => void;
}

const SociodemographicForm: React.FC<SociodemographicFormProps> = ({
  questions,
  responseSetId,
  initialResponses,
  onComplete
}) => {
  const [responses, setResponses] = useState<Record<string, any>>(initialResponses);
  const [isSaving, setIsSaving] = useState(false);
  const [lastSaved, setLastSaved] = useState<Date | null>(null);

  // Split question content into English and Urdu
  const getBilingualText = (content: string) => {
    const parts = content.split('|').map(s => s.trim());
    return {
      en: parts[0] || content,
      ur: parts[1] || ''
    };
  };

  const handleResponseChange = async (questionId: string, optionId: string) => {
    const newResponses = { ...responses, [questionId]: optionId };
    setResponses(newResponses);
    
    // Trigger Auto-Save
    setIsSaving(true);
    try {
      const payload = Object.entries(newResponses).map(([qId, optId]) => ({
        question_id: qId,
        selected_option_id: optId
      }));
      
      await questionnairesApi.saveDraftResponseSet(responseSetId, payload);
      setLastSaved(new Date());
    } catch (error) {
      console.error("Failed to auto-save", error);
    } finally {
      setIsSaving(false);
    }
  };

  const isAllCompleted = questions.every(q => responses[q.id]);

  const handleSubmit = () => {
    if (isAllCompleted) {
      onComplete(responses);
    }
  };

  return (
    <div className="space-y-12 pb-24">
      {/* Sticky Header for Save Status */}
      <div className="sticky top-0 z-10 bg-zinc-50/90 backdrop-blur-md border-b border-zinc-200 py-4 px-6 flex justify-between items-center -mx-4 mb-8">
        <h2 className="text-lg font-bold text-zinc-900">Sociodemographic Information</h2>
        <div className="flex items-center gap-2 text-sm text-zinc-500 font-medium">
          {isSaving ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Saving...</span>
            </>
          ) : lastSaved ? (
            <>
              <Save className="w-4 h-4" />
              <span>Draft Saved</span>
            </>
          ) : (
            <span>Ready</span>
          )}
        </div>
      </div>

      <div className="space-y-16">
        {questions.map((question, index) => {
          const { en, ur } = getBilingualText(question.content);
          const hasResponded = !!responses[question.id];

          return (
            <motion.div 
              key={question.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
              className={`p-6 md:p-8 rounded-2xl border transition-all duration-300 ${
                hasResponded 
                  ? 'bg-white border-zinc-200 shadow-sm' 
                  : 'bg-zinc-50/50 border-zinc-300/80 shadow-inner'
              }`}
            >
              {/* Question Text (Bilingual) */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 md:gap-12 mb-8">
                <div className="space-y-2">
                  <span className="text-xs font-black uppercase tracking-wider text-zinc-400">English</span>
                  <p className="text-lg md:text-xl font-medium text-zinc-900 leading-snug">
                    {en}
                    {question.required && <span className="text-red-500 ml-1">*</span>}
                  </p>
                </div>
                {ur && (
                  <div className="space-y-2 text-right" dir="rtl">
                    <span className="text-xs font-black uppercase tracking-wider text-zinc-400 block text-left md:text-right" dir="ltr">Urdu</span>
                    <p className="text-xl md:text-2xl font-medium text-zinc-900 leading-relaxed font-urdu">
                      {ur}
                      {question.required && <span className="text-red-500 mr-1">*</span>}
                    </p>
                  </div>
                )}
              </div>

              {/* Response Options */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {question.options.map(option => (
                  <button
                    key={option.id}
                    onClick={() => handleResponseChange(question.id, option.id)}
                    className={`group p-4 border rounded-xl text-left transition-all duration-200 flex items-center justify-between ${
                      responses[question.id] === option.id
                        ? 'border-zinc-800 bg-zinc-900 text-white shadow-md ring-2 ring-zinc-900/20 ring-offset-2'
                        : 'border-zinc-200 bg-white hover:border-zinc-300 hover:shadow-sm text-zinc-700 hover:bg-zinc-50'
                    }`}
                  >
                    <span className="font-medium text-sm">{option.label}</span>
                    <CheckCircle2 className={`w-5 h-5 transition-transform duration-300 ${
                      responses[question.id] === option.id ? 'opacity-100 scale-100' : 'opacity-0 scale-50'
                    }`} />
                  </button>
                ))}
              </div>
            </motion.div>
          );
        })}
      </div>

      {/* Submission Button */}
      <div className="mt-16 pt-8 border-t border-zinc-200 flex justify-end">
        <button
          onClick={handleSubmit}
          disabled={!isAllCompleted || isSaving}
          className={`px-8 py-4 rounded-xl font-bold text-sm tracking-wide transition-all duration-300 ${
            isAllCompleted && !isSaving
              ? 'bg-zinc-900 text-white hover:bg-zinc-800 hover:shadow-lg hover:-translate-y-0.5'
              : 'bg-zinc-200 text-zinc-400 cursor-not-allowed'
          }`}
        >
          {isSaving ? 'Saving...' : isAllCompleted ? 'Submit Sociodemographic Data' : 'Complete all questions to submit'}
        </button>
      </div>
    </div>
  );
};

export default SociodemographicForm;
