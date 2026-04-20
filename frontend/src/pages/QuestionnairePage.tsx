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
  const [completed, setCompleted] = useState(false);
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

      // Update Onboarding State
      localStorage.setItem('has_completed_baseline', 'true');

      setCompleted(true);

      // Short delay for success experience before redirect
      setTimeout(() => {
        navigate('/dashboard', {
          state: { message: 'Baseline assessment finalized and group assigned.' },
          replace: true
        });
      }, 3000);
    } catch (err: any) {
      setError('Failed to submit questionnaire. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  if (completed) {
    return (
      <div className="max-w-md mx-auto py-24 px-4 text-center space-y-8">
        <motion.div
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ type: 'spring', damping: 12 }}
          className="w-20 h-20 bg-zinc-800 rounded-xl flex items-center justify-center mx-auto shadow-lg"
        >
          <CheckCircle2 className="w-12 h-12 text-white" />
        </motion.div>

        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.2 }}
          className="space-y-4"
        >
          <h2 className="text-3xl font-bold text-zinc-900">Data Finalized</h2>
          <p className="text-zinc-500 text-sm max-w-xs mx-auto">
            Profile entry complete. Synchronizing results with research matrix.
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="flex items-center justify-center gap-2 text-zinc-500 text-xs font-medium"
        >
          <Loader2 className="w-4 h-4 animate-spin" />
          Synchronizing Environment
        </motion.div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4">
        <Loader2 className="w-10 h-10 animate-spin text-zinc-400" />
        <p className="text-zinc-500 font-medium text-sm">Loading questionnaire...</p>
      </div>
    );
  }

  if (error || !currentQuestion) {
    return (
      <div className="max-w-md mx-auto border border-zinc-200 rounded-xl p-10 text-center mt-12 space-y-6 bg-white shadow-sm">
        <AlertCircle className="w-12 h-12 text-zinc-400 mx-auto" />
        <h2 className="text-xl font-semibold text-zinc-800">Error</h2>
        <p className="text-zinc-500 text-sm">{error || 'Unable to load questionnaire data.'}</p>
        <button onClick={() => navigate('/dashboard')} className="w-full py-3 bg-zinc-800 text-white rounded-lg font-medium text-sm hover:bg-zinc-700 transition-colors">Back to Dashboard</button>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto py-12 px-4">
      {/* Header & Progress */}
      <div className="mb-16 space-y-6">
        <div className="flex justify-between items-end text-[10px] font-black uppercase tracking-[0.3em]">
          <span className="text-zinc-400 text-xs font-medium">Step {currentIndex + 1} / {questions.length}</span>
          <span className="text-zinc-700 text-xs font-medium">{questionnaire?.title}</span>
        </div>
        <div className="h-2 w-full bg-zinc-100 rounded-full overflow-hidden">
          <motion.div
            className="h-full bg-zinc-700 rounded-full"
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
          className="border border-zinc-200 rounded-xl p-8 md:p-12 min-h-[500px] flex flex-col bg-white shadow-sm"
        >
          <div className="flex-grow">
            <h2 className="text-2xl md:text-3xl font-bold text-zinc-900 leading-tight mb-12">
              {currentQuestion.content}
              {currentQuestion.required && <span className="text-zinc-300 ml-2">*</span>}
            </h2>

            {/* Dynamic Rendering */}
            <div className="mt-8">
              {currentQuestion.type === 'CHOICE' && (
                <div className="grid grid-cols-1 gap-4">
                  {currentQuestion.options.map((option: any) => (
                    <button
                      key={option.id}
                      onClick={() => handleResponseChange(currentQuestion.id, option.id)}
                      className={`group p-5 border rounded-lg text-left transition-all duration-200 flex items-center justify-between ${responses[currentQuestion.id] === option.id
                          ? 'border-zinc-700 bg-zinc-800 text-white shadow-md'
                          : 'border-zinc-200 bg-white hover:border-zinc-300 hover:shadow-sm'
                        }`}
                    >
                      <span className="font-medium text-sm">{option.label}</span>
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
                  className="w-full min-h-[300px] bg-white border border-zinc-200 rounded-lg p-6 text-base outline-none focus:ring-2 focus:ring-zinc-200 transition-all resize-none"
                  placeholder="Type your response..."
                  value={responses[currentQuestion.id] || ''}
                  onChange={(e) => handleResponseChange(currentQuestion.id, e.target.value)}
                />
              )}
            </div>
          </div>

          <div className="mt-8 pt-8 border-t border-zinc-200 flex justify-between items-center">
            <button
              onClick={handleBack}
              disabled={currentIndex === 0}
              className="flex items-center gap-2 text-zinc-400 hover:text-zinc-700 disabled:opacity-0 transition-all font-medium text-sm"
            >
              <ArrowLeft className="w-4 h-4" /> Previous
            </button>

            <button
              onClick={handleNext}
              disabled={submitting || (currentQuestion.required && responses[currentQuestion.id] === undefined)}
              className="px-8 py-3 bg-zinc-800 text-white font-medium rounded-lg text-sm hover:bg-zinc-700 transition-colors min-w-[140px] flex items-center justify-center gap-2"
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
