import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { questionnairesApi } from '../services/api';
import LikertSlider from '../components/Questionnaire/LikertSlider';
import { 
  Loader2, 
  ArrowLeft, 
  ArrowRight, 
  CheckCircle2, 
  AlertCircle
} from 'lucide-react';

const QuestionnairePage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [questionnaire, setQuestionnaire] = useState<any>(null);
  const [responseSetId, setResponseSetId] = useState<string | null>(null);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [responses, setResponses] = useState<Record<string, any>>({});
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const initSession = async () => {
      if (!id) return;
      try {
        const [qRes, rsRes] = await Promise.all([
          questionnairesApi.getDetail(id),
          questionnairesApi.createResponseSet(id)
        ]);
        setQuestionnaire(qRes.data);
        setResponseSetId(rsRes.data.id);
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to initialize questionnaire session.');
      } finally {
        setLoading(false);
      }
    };
    initSession();
  }, [id]);

  const questions = questionnaire?.questions || [];
  const currentQuestion = questions[currentIndex];
  const progress = questions.length > 0 ? ((currentIndex + 1) / questions.length) * 100 : 0;

  const handleResponseChange = (questionId: string, value: any) => {
    setResponses(prev => ({
      ...prev,
      [questionId]: value
    }));
  };

  const handleNext = () => {
    if (currentIndex < questions.length - 1) {
      setCurrentIndex(prev => prev + 1);
    } else {
      submitAll();
    }
  };

  const handleBack = () => {
    if (currentIndex > 0) {
      setCurrentIndex(prev => prev - 1);
    }
  };

  const submitAll = async () => {
    if (!responseSetId) return;
    setSubmitting(true);
    try {
      const payload = questions.map((q: any) => {
        const response = responses[q.id];
        const base = { question_id: q.id };
        
        if (q.type === 'TEXT') {
          return { ...base, text_value: response || "" };
        } else if (q.type === 'SCALE' || q.type === 'CHOICE') {
          if (q.type === 'SCALE') {
            const selectedOpt = q.options.find((o: any) => o.numeric_value === response);
            return { ...base, selected_option_id: selectedOpt?.id || null };
          } else {
            return { ...base, selected_option_id: response || null };
          }
        }
        return base;
      });

      await questionnairesApi.submitResponseSet(responseSetId, payload);
      navigate('/dashboard', { state: { message: 'Questionnaire completed successfully!' } });
    } catch (err: any) {
      setError('Failed to submit questionnaire. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4">
        <Loader2 className="w-12 h-12 animate-spin text-zinc-900" />
        <p className="text-zinc-500 font-medium font-serif">Initializing assessment environment...</p>
      </div>
    );
  }

  if (error || !currentQuestion) {
    return (
      <div className="max-w-md mx-auto card-minimal p-12 text-center mt-12 space-y-6">
        <AlertCircle className="w-16 h-16 text-red-500 mx-auto" />
        <h2 className="text-2xl font-bold">Something went wrong</h2>
        <p className="text-zinc-500">{error || 'Unable to load questionnaire.'}</p>
        <button onClick={() => navigate('/dashboard')} className="btn-minimal w-full">Back to Dashboard</button>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto py-12 px-4">
      {/* Header & Progress */}
      <div className="mb-12 space-y-4">
        <div className="flex justify-between items-center text-sm mb-2">
          <span className="font-bold uppercase tracking-widest text-zinc-400">Step {currentIndex + 1} <span className="text-zinc-200">/</span> {questions.length}</span>
          <span className="font-serif italic text-zinc-900">{questionnaire?.title}</span>
        </div>
        <div className="h-1 w-full bg-zinc-100 rounded-full overflow-hidden">
          <motion.div 
            className="h-full bg-zinc-900"
            initial={{ width: 0 }}
            animate={{ width: `${progress}%` }}
            transition={{ type: 'spring', damping: 20 }}
          />
        </div>
      </div>

      <AnimatePresence mode="wait">
        <motion.div
          key={currentQuestion.id}
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -20 }}
          transition={{ duration: 0.3 }}
          className="card-minimal p-8 md:p-12 min-h-[400px] flex flex-col"
        >
          <div className="flex-grow">
            <h2 className="text-2xl md:text-3xl font-serif leading-tight mb-12">
              {currentQuestion.content}
              {currentQuestion.required && <span className="text-zinc-300 ml-2" title="Required">*</span>}
            </h2>

            {/* Dynamic Rendering */}
            <div className="mt-8">
              {currentQuestion.type === 'CHOICE' && (
                <div className="grid grid-cols-1 gap-4">
                  {currentQuestion.options.map((option: any) => (
                    <button
                      key={option.id}
                      onClick={() => handleResponseChange(currentQuestion.id, option.id)}
                      className={`group p-6 rounded-xl border-2 text-left transition-all duration-200 flex items-center justify-between ${
                        responses[currentQuestion.id] === option.id 
                          ? 'border-zinc-900 bg-zinc-900 text-white shadow-lg' 
                          : 'border-zinc-100 hover:border-zinc-300 bg-zinc-50/50'
                      }`}
                    >
                      <span className="font-medium">{option.label}</span>
                      <CheckCircle2 className={`w-6 h-6 transition-opacity ${responses[currentQuestion.id] === option.id ? 'opacity-100' : 'opacity-0'}`} />
                    </button>
                  ))}
                </div>
              )}

              {currentQuestion.type === 'SCALE' && (
                <LikertSlider 
                  options={currentQuestion.options}
                  value={responses[currentQuestion.id]}
                  onChange={(val) => handleResponseChange(currentQuestion.id, val)}
                />
              )}

              {currentQuestion.type === 'TEXT' && (
                <textarea
                  className="input-minimal min-h-[200px] text-lg resize-none p-6"
                  placeholder="Type your response here..."
                  value={responses[currentQuestion.id] || ''}
                  onChange={(e) => handleResponseChange(currentQuestion.id, e.target.value)}
                />
              )}
            </div>
          </div>

          <div className="mt-12 pt-8 border-t border-zinc-100 flex justify-between items-center">
            <button
              onClick={handleBack}
              disabled={currentIndex === 0}
              className="flex items-center gap-2 text-zinc-400 hover:text-zinc-900 disabled:opacity-0 transition-all font-medium"
            >
              <ArrowLeft className="w-4 h-4" /> Previous
            </button>

            <button
              onClick={handleNext}
              disabled={submitting || (currentQuestion.required && responses[currentQuestion.id] === undefined)}
              className="btn-minimal min-w-[140px] flex items-center justify-center gap-2"
            >
              {submitting ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <>
                  {currentIndex === questions.length - 1 ? 'Complete' : 'Continue'}
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </div>
        </motion.div>
      </AnimatePresence>
    </div>
  );
};

export default QuestionnairePage;
