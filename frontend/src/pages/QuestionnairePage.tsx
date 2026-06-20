import React, { useState, useEffect, useMemo, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import api, { questionnairesApi } from '../services/api';
import LikertSlider from '../components/Questionnaire/LikertSlider';
import SociodemographicForm from '../components/Questionnaire/SociodemographicForm';
import SafetyPanelModal from '../components/Questionnaire/SafetyPanelModal';
import {
  Loader2,
  ArrowLeft,
  ArrowRight,
  CheckCircle2,
  AlertCircle,
  Save
} from 'lucide-react';


const getNumericValueForResponse = (question: any, responseValue: any): number | undefined => {
  if (responseValue === undefined || responseValue === null) return undefined;
  if (typeof responseValue === 'number') return responseValue;
  if (typeof responseValue === 'string') {
    const opt = question.options?.find((o: any) => o.id === responseValue);
    if (opt) return opt.numeric_value;
    const parsed = parseInt(responseValue, 10);
    if (!isNaN(parsed)) return parsed;
  }
  return undefined;
};

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

  const [transitioning, setTransitioning] = useState(false);
  const submittingRef = useRef(false);
  const transitioningRef = useRef(false);

  const [isSaving, setIsSaving] = useState(false);
  const [lastSaved, setLastSaved] = useState<Date | null>(null);
  const saveTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const [showSafetyPanel, setShowSafetyPanel] = useState(false);
  const [submittingOptIn, setSubmittingOptIn] = useState(false);
  const [hasShownSafetyPanel, setHasShownSafetyPanel] = useState(false);
  const [safetyPanelPendingAction, setSafetyPanelPendingAction] = useState<'next' | 'submit' | null>(null);

  useEffect(() => {
    return () => {
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current);
      }
    };
  }, []);

  useEffect(() => {
    const initSession = async () => {
      if (!id) return;
      
      // Reset questionnaire states to prevent UI flickering or carrying over responses
      setCompleted(false);
      setError(null);
      setResponses({});
      setCurrentIndex(0);
      setQuestionnaire(null);
      setResponseSetId(null);
      setLoading(true);

      try {
        const queryParams = new URLSearchParams(window.location.search);
        const milestone = queryParams.get('milestone') || undefined;

        const [qRes, rsRes] = await Promise.all([
          questionnairesApi.getDetail(id),
          questionnairesApi.createResponseSet(id, milestone)
        ]);
        setQuestionnaire(qRes.data);
        setResponseSetId(rsRes.data.id);
        
        // Restore previous draft responses if they exist
        if (rsRes.data.responses && Array.isArray(rsRes.data.responses)) {
          const restored: Record<string, any> = {};
          const qs = qRes.data.questions || [];
          rsRes.data.responses.forEach((r: any) => {
            const questionObj = qs.find((q: any) => q.id === r.question);
            if (questionObj && questionObj.type === 'SCALE') {
              const selectedOpt = questionObj.options?.find((o: any) => o.id === r.selected_option);
              if (selectedOpt) {
                restored[r.question] = selectedOpt.numeric_value;
              } else {
                restored[r.question] = r.selected_option;
              }
            } else {
              restored[r.question] = r.selected_option || r.text_value;
            }
          });
          setResponses(restored);

          // Auto-advance to the last scale group that has at least one saved answer,
          // so the user is dropped back at the right place without having to click Next.
          const groups: { name: string; questions: any[] }[] = [];
          const groupMap: Record<string, any[]> = {};
          qs.forEach((q: any) => {
            const match = q.content.match(/^\[(.*?)\]/);
            const scale = match ? match[1] : 'General';
            if (!groupMap[scale]) {
              groupMap[scale] = [];
              groups.push({ name: scale, questions: groupMap[scale] });
            }
            groupMap[scale].push(q);
          });
          let resumeIndex = 0;
          for (let i = 0; i < groups.length; i++) {
            const groupHasAnswer = groups[i].questions.some(
              (q: any) => restored[q.id] !== undefined && restored[q.id] !== null && restored[q.id] !== ''
            );
            if (groupHasAnswer) resumeIndex = i;
          }
          setCurrentIndex(resumeIndex);
        }
      } catch (err: any) {
        const detail = err.response?.data?.detail;
        if (detail && (detail.includes('already completed') || detail.includes('not available yet'))) {
          if (detail.includes('sociodemographic')) {
            localStorage.setItem('has_completed_sociodemographic', 'true');
          }
          navigate('/dashboard', { replace: true });
        } else {
          setError(detail || 'Failed to initialize questionnaire session.');
        }
      } finally {
        setLoading(false);
      }
    };
    initSession();
  }, [id, navigate]);

  const questions = questionnaire?.questions || [];

  // Helper to extract prefix from question content
  const getScaleGroup = (q: any) => {
    const match = q.content.match(/^\[(.*?)\]/);
    return match ? match[1] : 'General';
  };

  // Group questions by scale prefix
  const scaleGroups = useMemo(() => {
    const groups: { name: string; questions: any[] }[] = [];
    const map: Record<string, any[]> = {};
    
    questions.forEach((q: any) => {
      const scale = getScaleGroup(q);
      if (!map[scale]) {
        map[scale] = [];
        groups.push({ name: scale, questions: map[scale] });
      }
      map[scale].push(q);
    });
    
    return groups;
  }, [questions]);

  const currentScaleGroup = scaleGroups[currentIndex];
  
  // Progress is computed based on scale groups rather than individual questions
  const progress = scaleGroups.length > 0 ? ((currentIndex + 1) / scaleGroups.length) * 100 : 0;

  const isScaleGroupCompleted = useMemo(() => {
    if (!currentScaleGroup) return false;

    if (currentScaleGroup.name === 'SIDAS') {
      const firstSidasQ = currentScaleGroup.questions[0];
      if (firstSidasQ) {
        const val1 = responses[firstSidasQ.id];
        if (val1 === 0) {
          return true;
        }
      }
    }

    return currentScaleGroup.questions.every((q: any) => {
      if (!q.required) return true;
      const val = responses[q.id];
      return val !== undefined && val !== null && val !== '';
    });
  }, [currentScaleGroup, responses]);

  /**
   * Build a save payload that only includes questions that have been answered.
   * This is critical: the backend does delete+bulk_create on every save, so sending
   * null for unanswered questions would wipe out previously-saved answers.
   */
  const buildAnsweredPayload = (currentResponses: Record<string, any>) => {
    return questions
      .filter((q: any) => {
        const val = currentResponses[q.id];
        return val !== undefined && val !== null && val !== '';
      })
      .map((q: any) => {
        const response = currentResponses[q.id];
        const base = { question_id: q.id };
        if (q.type === 'TEXT') {
          return { ...base, text_value: String(response) };
        } else if (q.type === 'SCALE') {
          const selectedOpt = q.options.find((o: any) => o.numeric_value === response);
          return { ...base, selected_option_id: selectedOpt?.id || null };
        } else if (q.type === 'CHOICE') {
          return { ...base, selected_option_id: response || null };
        }
        return base;
      });
  };

  /**
   * Immediately flush all answered responses to the server (no debounce).
   * Called explicitly on Next click to guarantee current-scale answers are
   * persisted before the user advances, even if no answer was changed.
   */
  const saveDraftNow = async (currentResponses: Record<string, any>) => {
    if (!responseSetId) return;
    // Cancel any pending debounced save — this one supersedes it.
    if (saveTimeoutRef.current) {
      clearTimeout(saveTimeoutRef.current);
      saveTimeoutRef.current = null;
    }
    const payload = buildAnsweredPayload(currentResponses);
    if (payload.length === 0) return;
    setIsSaving(true);
    try {
      await questionnairesApi.saveDraftResponseSet(responseSetId, payload);
      setLastSaved(new Date());
    } catch (err) {
      console.error('Failed to flush draft:', err);
    } finally {
      setIsSaving(false);
    }
  };

  const handleResponseChange = (questionId: string, value: any) => {
    let newResponses = {
      ...responses,
      [questionId]: value
    };

    // If this is SIDAS Item 1 and the value is 0, auto-populate Items 2-5 with 0.
    // If the value is > 0 and was previously 0, clear Items 2-5 to force manual input.
    if (currentScaleGroup?.name === 'SIDAS') {
      const firstSidasQ = currentScaleGroup.questions[0];
      if (firstSidasQ && questionId === firstSidasQ.id) {
        if (value === 0) {
          currentScaleGroup.questions.slice(1).forEach((q: any) => {
            newResponses[q.id] = 0;
          });
        } else if (responses[firstSidasQ.id] === 0) {
          currentScaleGroup.questions.slice(1).forEach((q: any) => {
            delete newResponses[q.id];
          });
        }
      }
    }

    setResponses(newResponses);

    // Debounced autosave — only sends answered questions.
    if (saveTimeoutRef.current) {
      clearTimeout(saveTimeoutRef.current);
    }
    setIsSaving(true);
    saveTimeoutRef.current = setTimeout(async () => {
      if (!responseSetId) return;
      try {
        const payload = buildAnsweredPayload(newResponses);
        if (payload.length > 0) {
          await questionnairesApi.saveDraftResponseSet(responseSetId, payload);
          setLastSaved(new Date());
        }
      } catch (err) {
        console.error('Failed to auto-save:', err);
      } finally {
        setIsSaving(false);
      }
    }, 500);
  };

  const checkSuicideRiskLocal = (): boolean => {
    // 1. PHQ-9 Item 9 >= 1  (order 33 after header insertion)
    const phq9Item9Q = questions.find((q: any) =>
      q.order === 33 ||
      (q.content.includes('[PHQ-9]') && q.content.toLowerCase().includes('dead'))
    );
    if (phq9Item9Q) {
      const val = getNumericValueForResponse(phq9Item9Q, responses[phq9Item9Q.id]);
      if (val !== undefined && val >= 1) {
        return true;
      }
    }

    // 2. SIDAS Item 3 > 0  (order 80 after header insertion)
    const sidasItem3Q = questions.find((q: any) => q.order === 80);
    if (sidasItem3Q) {
      const val = getNumericValueForResponse(sidasItem3Q, responses[sidasItem3Q.id]);
      if (val !== undefined && val > 0) {
        return true;
      }
    }

    // 3. SIDAS Total >= 21  (orders 78-82 after header insertion)
    const sidasQ1 = questions.find((q: any) => q.order === 78);
    const sidasQ2 = questions.find((q: any) => q.order === 79);
    const sidasQ3 = questions.find((q: any) => q.order === 80);
    const sidasQ4 = questions.find((q: any) => q.order === 81);
    const sidasQ5 = questions.find((q: any) => q.order === 82);

    if (sidasQ1) {
      const val1 = getNumericValueForResponse(sidasQ1, responses[sidasQ1.id]);
      if (val1 === 0) {
        return false;
      }
      if (val1 !== undefined) {
        const val2 = sidasQ2 ? getNumericValueForResponse(sidasQ2, responses[sidasQ2.id]) : undefined;
        const val3 = sidasQ3 ? getNumericValueForResponse(sidasQ3, responses[sidasQ3.id]) : undefined;
        const val4 = sidasQ4 ? getNumericValueForResponse(sidasQ4, responses[sidasQ4.id]) : undefined;
        const val5 = sidasQ5 ? getNumericValueForResponse(sidasQ5, responses[sidasQ5.id]) : undefined;

        if (
          val2 !== undefined &&
          val3 !== undefined &&
          val4 !== undefined &&
          val5 !== undefined
        ) {
          const total = val1 + (10 - val2) + val3 + val4 + val5;
          if (total >= 21) {
            return true;
          }
        }
      }
    }

    return false;
  };

  const handleNext = () => {
    if (transitioningRef.current || submittingRef.current) return;
    if (checkSuicideRiskLocal() && !hasShownSafetyPanel) {
      setHasShownSafetyPanel(true);
      setSafetyPanelPendingAction('next');
      setShowSafetyPanel(true);
      return;
    }
    proceedNext();
  };

  const proceedNext = async () => {
    if (transitioningRef.current || submittingRef.current) return;
    if (currentIndex < scaleGroups.length - 1) {
      transitioningRef.current = true;
      setTransitioning(true);
      try {
        // Flush all answered responses to the server before advancing.
        // This guarantees the current scale's answers are persisted even
        // if no answer was changed (so the debounced autosave didn't fire).
        await saveDraftNow(responses);
        setCurrentIndex(prev => prev + 1);
        window.scrollTo({ top: 0, behavior: 'smooth' });
      } catch (err) {
        console.error('Failed to save draft and transition:', err);
      } finally {
        transitioningRef.current = false;
        setTransitioning(false);
      }
    } else {
      submitAll();
    }
  };

  const handleBack = () => {
    if (transitioningRef.current || submittingRef.current) return;
    if (currentIndex > 0) {
      setCurrentIndex(prev => prev - 1);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };
  const completeSubmissionWorkflow = () => {
    if (questionnaire?.assessment_type === 'SOCIODEMOGRAPHIC') {
      const fetchProfileWithRetry = (retries: number, delay: number) => {
        api.get('/users/profile/')
          .then(profileRes => {
            const profile = profileRes.data;
            if (profile) {
              localStorage.setItem('is_disqualified', String(profile.is_disqualified || false));
              localStorage.setItem('has_completed_sociodemographic', String(profile.has_completed_sociodemographic));
              localStorage.setItem('due_milestone', profile.due_milestone || '');

              if (profile.is_disqualified) {
                setCompleted(true);
                setTimeout(() => {
                  setCompleted(false);
                  navigate('/dashboard', { replace: true });
                }, 1000);
                return;
              }
            }

            // If not disqualified, fetch next battery
            localStorage.setItem('has_completed_sociodemographic', 'true');
            questionnairesApi.list().then(qRes => {
              const qList = Array.isArray(qRes.data) ? qRes.data : qRes.data?.results || [];
              const battery = qList.find((q: any) => q.is_active && q.assessment_type === 'PSYCHOMETRIC');
              if (battery) {
                setCompleted(true);
                setTimeout(() => {
                  setCompleted(false);
                  navigate(`/questionnaire/${battery.id}?milestone=SIGNUP`, { replace: true });
                }, 1000);
              }
            }).catch(e => {
              console.error("Failed to find psychometric battery questionnaire", e);
            });
          })
          .catch(err => {
            if (retries > 0) {
              console.warn(`Failed to fetch user profile, retrying in ${delay}ms... (Retries left: ${retries})`, err);
              setTimeout(() => {
                fetchProfileWithRetry(retries - 1, delay * 2);
              }, delay);
            } else {
              console.error("Failed to fetch user profile after all retries", err);
              // Fallback
              localStorage.setItem('has_completed_sociodemographic', 'true');
              navigate('/dashboard', { replace: true });
            }
          });
      };

      fetchProfileWithRetry(3, 500);
      return;
    }

    const queryParams = new URLSearchParams(window.location.search);
    const completedMilestone = queryParams.get('milestone');
    if (completedMilestone === 'SIGNUP' && questionnaire?.assessment_type === 'PSYCHOMETRIC') {
      localStorage.removeItem('due_milestone');
    }

    setCompleted(true);

    setTimeout(() => {
      navigate('/dashboard', {
        state: { message: 'Assessment finalized.' },
        replace: true
      });
    }, 1000);
  };

  const handleSafetyPanelConfirm = async (optIn: boolean) => {
    if (!responseSetId) return;
    setSubmittingOptIn(true);
    try {
      await questionnairesApi.submitOptIn(responseSetId, optIn);
      setShowSafetyPanel(false);
      if (safetyPanelPendingAction === 'next') {
        proceedNext();
      } else {
        completeSubmissionWorkflow();
      }
    } catch (err) {
      console.error('Failed to save opt-in choice:', err);
      setShowSafetyPanel(false);
      if (safetyPanelPendingAction === 'next') {
        proceedNext();
      } else {
        completeSubmissionWorkflow();
      }
    } finally {
      setSubmittingOptIn(false);
      setSafetyPanelPendingAction(null);
    }
  };

  const submitAll = async (overrideResponses?: Record<string, any>) => {
    if (!responseSetId || submittingRef.current || transitioningRef.current) return;
    submittingRef.current = true;
    setSubmitting(true);
    const finalState = overrideResponses || responses;
    
    try {
      const payload = questions.map((q: any) => {
        const response = finalState[q.id];
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

      // Introduce a minimum delay of 1.5 seconds to let the server transaction settle and show a premium loading experience
      const isTest = typeof process !== 'undefined' && process.env?.NODE_ENV === 'test';
      const [res] = await Promise.all([
        questionnairesApi.submitResponseSet(responseSetId, payload),
        new Promise(resolve => setTimeout(resolve, isTest ? 0 : 1500))
      ]);
      
      const isSuicideTriggered = res.data?.suicide_risk_triggered;
      if (isSuicideTriggered && !hasShownSafetyPanel) {
        setHasShownSafetyPanel(true);
        setSafetyPanelPendingAction('submit');
        setShowSafetyPanel(true);
        return;
      }

      completeSubmissionWorkflow();
    } catch (err: any) {
      setError('Failed to submit questionnaire. Please try again.');
    } finally {
      submittingRef.current = false;
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

  if (error || scaleGroups.length === 0 || !currentScaleGroup) {
    return (
      <div className="max-w-md mx-auto border border-zinc-200 rounded-xl p-10 text-center mt-12 space-y-6 bg-white shadow-sm">
        <AlertCircle className="w-12 h-12 text-zinc-400 mx-auto" />
        <h2 className="text-xl font-semibold text-zinc-800">Error</h2>
        <p className="text-zinc-500 text-sm">{error || 'Unable to load questionnaire data.'}</p>
        <button onClick={() => navigate('/dashboard')} className="w-full py-3 bg-zinc-800 text-white rounded-lg font-medium text-sm hover:bg-zinc-700 transition-colors">Back to Dashboard</button>
      </div>
    );
  }

  // Branch for Sociodemographic Form (Display Rules applied)
  if (questionnaire?.assessment_type === 'SOCIODEMOGRAPHIC') {
    return (
      <div className="max-w-4xl mx-auto py-12 px-4 md:px-8">
        <SociodemographicForm 
          questions={questions}
          responseSetId={responseSetId!}
          initialResponses={responses}
          submitting={submitting || transitioning}
          onComplete={(finalResponses) => {
            setResponses(finalResponses);
            submitAll(finalResponses);
          }}
        />
      </div>
    );
  }



  const splitQuestionContent = (content: string) => {
    const cleanContent = content.replace(/^\[.*?\]\s*/, '');
    if (cleanContent.includes('|')) {
      const parts = cleanContent.split('|').map(p => p.trim());
      return { english: parts[0], urdu: parts[1] };
    }
    return { english: cleanContent, urdu: '' };
  };

  return (
    <div className="max-w-4xl mx-auto py-12 px-4">
      {/* Sticky Header for Save Status */}
      <div className="sticky top-0 z-10 bg-zinc-50/90 backdrop-blur-md border-b border-zinc-200 py-4 px-6 flex justify-between items-center -mx-4 mb-8">
        <h2 className="text-sm font-bold text-zinc-950">{questionnaire?.title}</h2>
        <div className="flex items-center gap-2 text-xs text-zinc-500 font-medium">
          {isSaving ? (
            <>
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
              <span>Saving draft...</span>
            </>
          ) : lastSaved ? (
            <>
              <Save className="w-3.5 h-3.5 text-zinc-400" />
              <span>Draft Saved ({lastSaved.toLocaleTimeString()})</span>
            </>
          ) : (
            <span>Ready</span>
          )}
        </div>
      </div>

      {/* Header & Progress */}
      <div className="mb-16 space-y-6">
        <div className="flex justify-between items-center text-[10px] font-black uppercase tracking-[0.3em]">
          <span className="text-zinc-400 text-xs font-medium">Scale {currentIndex + 1} / {scaleGroups.length}</span>
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
          key={currentScaleGroup.name}
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -20 }}
          transition={{ duration: 0.3 }}
          className="space-y-12"
        >
          <div className="space-y-8">
            {/* Gratitude Response Key — stem + bilingual legend (no separate TEXT header in DB) */}
            {currentScaleGroup.name === 'Gratitude' && (
              <div className="border border-zinc-200 rounded-xl p-5 md:p-6 bg-zinc-50/80 shadow-sm space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pb-3 border-b border-zinc-200">
                  <p className="text-sm font-medium text-zinc-700 leading-relaxed">Please indicate how strongly you agree with each statement.</p>
                  <p className="text-sm font-medium text-zinc-700 leading-relaxed font-urdu text-right" dir="rtl">براہ کرم نشاندہی کیجیے کہ آپ ہر بیان سے کس حد تک متفق ہیں۔</p>
                </div>
                <div className="text-xs font-bold text-zinc-500 uppercase tracking-wider">Response Key / جوابات کی کنجی</div>
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3">
                  {[
                    { val: 0, en: 'Completely disagree', ur: 'بالکل غیر متفق' },
                    { val: 1, en: 'Disagree', ur: 'غیر متفق' },
                    { val: 2, en: 'Neutral', ur: 'غیر جانبدار' },
                    { val: 3, en: 'Agree', ur: 'متفق' },
                    { val: 4, en: 'Completely agree', ur: 'مکمل متفق' },
                  ].map((anchor) => (
                    <div key={anchor.val} className="flex flex-col items-center text-center border border-zinc-200 rounded-lg bg-white px-2 py-3 gap-1">
                      <span className="text-lg font-bold text-zinc-700">{anchor.val}</span>
                      <span className="text-[11px] font-medium text-zinc-600 leading-tight">{anchor.en}</span>
                      <span className="text-[11px] font-medium text-zinc-500 font-urdu leading-tight" dir="rtl">{anchor.ur}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
            {currentScaleGroup.questions.map((question: any, idx: number) => {
              if (currentScaleGroup.name === 'SIDAS' && idx > 0) {
                const firstSidasQ = currentScaleGroup.questions[0];
                if (firstSidasQ && responses[firstSidasQ.id] === 0) {
                  return null;
                }
              }

              const { english, urdu } = splitQuestionContent(question.content);

              // Non-required TEXT questions are section headers / instructions.
              // Render stem banner first, then the response key directly below it
              // so the one-liner always sits above the key (not the other way around).
              if (question.type === 'TEXT' && !question.required) {
                const isPhqGad = currentScaleGroup.name === 'PHQ-9' || currentScaleGroup.name === 'GAD-7';
                const isPanas = currentScaleGroup.name === 'PANAS';
                return (
                  <React.Fragment key={question.id}>
                    <div className="border border-zinc-200 rounded-xl p-5 md:p-6 bg-gradient-to-br from-zinc-50 to-white shadow-sm">
                      {urdu ? (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-start">
                          <div className="text-left">
                            <p className="text-sm md:text-base font-medium text-zinc-700 leading-relaxed">{english}</p>
                          </div>
                          <div className="text-right" dir="rtl">
                            <p className="text-sm md:text-base font-medium text-zinc-700 leading-relaxed font-urdu">{urdu}</p>
                          </div>
                        </div>
                      ) : (
                        <p className="text-sm md:text-base font-medium text-zinc-700 leading-relaxed">{english}</p>
                      )}
                    </div>
                    {isPhqGad && (
                      <div className="border border-zinc-200 rounded-xl p-5 md:p-6 bg-zinc-50/80 shadow-sm">
                        <div className="text-xs font-bold text-zinc-500 uppercase tracking-wider mb-3">Response Key / جوابات کی کنجی</div>
                        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                          {[
                            { val: 0, en: 'Not at all', ur: 'بالکل نہیں' },
                            { val: 1, en: 'Several days', ur: 'کئی دن' },
                            { val: 2, en: 'More than half the days', ur: 'ایک ہفتے سے زیادہ' },
                            { val: 3, en: 'Nearly every day', ur: 'تقریباً روزانہ' },
                          ].map((anchor) => (
                            <div key={anchor.val} className="flex flex-col items-center text-center border border-zinc-200 rounded-lg bg-white px-2 py-3 gap-1">
                              <span className="text-lg font-bold text-zinc-700">{anchor.val}</span>
                              <span className="text-[11px] font-medium text-zinc-600 leading-tight">{anchor.en}</span>
                              <span className="text-[11px] font-medium text-zinc-500 font-urdu leading-tight" dir="rtl">{anchor.ur}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                    {isPanas && (
                      <div className="border border-zinc-200 rounded-xl p-5 md:p-6 bg-zinc-50/80 shadow-sm">
                        <div className="text-xs font-bold text-zinc-500 uppercase tracking-wider mb-3">Response Key / جوابات کی کنجی</div>
                        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3">
                          {[
                            { val: 0, en: 'Very slightly or not at all', ur: 'کبھی نہیں' },
                            { val: 1, en: 'A little', ur: 'بہت کم' },
                            { val: 2, en: 'Moderately', ur: 'درمیانہ' },
                            { val: 3, en: 'Quite a bit', ur: 'کافی حد تک' },
                            { val: 4, en: 'Extremely', ur: 'بہت زیادہ' },
                          ].map((anchor) => (
                            <div key={anchor.val} className="flex flex-col items-center text-center border border-zinc-200 rounded-lg bg-white px-2 py-3 gap-1">
                              <span className="text-lg font-bold text-zinc-700">{anchor.val}</span>
                              <span className="text-[11px] font-medium text-zinc-600 leading-tight">{anchor.en}</span>
                              <span className="text-[11px] font-medium text-zinc-500 font-urdu leading-tight" dir="rtl">{anchor.ur}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </React.Fragment>
                );
              }

              // Count only scorable questions (skip non-required TEXT headers) for the counter
              const scorableQuestions = currentScaleGroup.questions.filter(
                (q: any) => !(q.type === 'TEXT' && !q.required)
              );
              const scorableIdx = scorableQuestions.indexOf(question);

              return (
                <div key={question.id} className="border border-zinc-200 rounded-xl p-6 md:p-8 bg-white shadow-sm space-y-6">
                  <div className="flex justify-between items-center pb-4 border-b border-zinc-100">
                    <span className="text-xs font-medium text-zinc-400">Question {scorableIdx + 1} of {scorableQuestions.length}</span>
                    {question.required && <span className="text-xs font-semibold text-zinc-400">* Required</span>}
                  </div>
                  
                  {/* Bilingual Question Text or Single Language Fallback */}
                  {urdu ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-start mb-4">
                      <div className="text-left font-latin">
                        <span className="text-[10px] font-bold text-zinc-400 uppercase block mb-1">English</span>
                        <p className="text-base md:text-lg font-medium text-zinc-800 leading-relaxed">{english}</p>
                      </div>
                      <div className="text-right" dir="rtl">
                        <span className="text-[10px] font-bold text-zinc-400 uppercase block mb-1">اردو</span>
                        <p className="text-base md:text-lg font-medium text-zinc-800 leading-relaxed font-urdu">{urdu}</p>
                      </div>
                    </div>
                  ) : (
                    <div className="text-left mb-4 font-latin">
                      <p className="text-base md:text-lg font-medium text-zinc-800 leading-relaxed">{english}</p>
                    </div>
                  )}

                  {/* Input options */}
                  <div className="pt-4">
                    {question.type === 'CHOICE' && (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {question.options.map((option: any) => (
                          <button
                            key={option.id}
                            onClick={() => handleResponseChange(question.id, option.id)}
                            className={`group p-4 border rounded-lg text-left transition-all duration-200 flex items-center justify-between ${
                              responses[question.id] === option.id
                                ? 'border-zinc-700 bg-zinc-800 text-white shadow-md'
                                : 'border-zinc-200 bg-white hover:border-zinc-300 hover:shadow-sm'
                            }`}
                          >
                            <span className="font-medium text-sm">{option.label}</span>
                            <CheckCircle2 className={`w-5 h-5 transition-opacity ${responses[question.id] === option.id ? 'opacity-100' : 'opacity-0'}`} />
                          </button>
                        ))}
                      </div>
                    )}

                    {question.type === 'SCALE' && (
                      <LikertSlider
                        options={question.options}
                        value={getNumericValueForResponse(question, responses[question.id])}
                        onChange={(val) => handleResponseChange(question.id, val)}
                      />
                    )}

                    {question.type === 'TEXT' && (
                      <textarea
                        className="w-full min-h-[150px] bg-white border border-zinc-200 rounded-lg p-4 text-base outline-none focus:ring-2 focus:ring-zinc-200 transition-all resize-none"
                        placeholder="Type your response..."
                        value={responses[question.id] || ''}
                        onChange={(e) => handleResponseChange(question.id, e.target.value)}
                      />
                    )}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Navigation panel */}
          <div className="pt-8 border-t border-zinc-200 flex justify-between items-center">
            <button
              onClick={handleBack}
              disabled={currentIndex === 0 || transitioning || submitting}
              className="flex items-center gap-2 text-zinc-400 hover:text-zinc-700 disabled:opacity-0 transition-all font-medium text-sm"
            >
              <ArrowLeft className="w-4 h-4" /> Previous
            </button>

            <button
              onClick={handleNext}
              disabled={submitting || transitioning || !isScaleGroupCompleted}
              className="px-8 py-3 bg-zinc-800 text-white font-medium rounded-lg text-sm hover:bg-zinc-700 transition-colors min-w-[140px] flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {submitting || transitioning ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <>
                  {currentIndex === scaleGroups.length - 1 ? 'Complete' : 'Continue'}
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </div>
        </motion.div>
      </AnimatePresence>

      <SafetyPanelModal
        isOpen={showSafetyPanel}
        onConfirm={handleSafetyPanelConfirm}
        submitting={submittingOptIn}
      />
    </div>
  );
};

export default QuestionnairePage;
