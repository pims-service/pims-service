import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api, { questionnairesApi } from '../services/api';
import { Calendar, CheckCircle2, Clock, ArrowRight, ClipboardCheck, AlertTriangle } from 'lucide-react';

const DashboardPage: React.FC = () => {
  const [activities, setActivities] = useState<any[]>([]);
  const [userProfile, setUserProfile] = useState<any>(null);
  const [posttestQuestionnaire, setPosttestQuestionnaire] = useState<any>(null);
  const [loading, setLoading] = useState(true);



  useEffect(() => {
    const fetchData = async () => {
      try {
        const [actRes, profileRes] = await Promise.all([
          api.get('/activities/daily/current/').catch(() => ({ data: null })),
          api.get('/users/profile/').catch(() => ({ data: null }))
        ]);

        const actData = actRes.data;
        setActivities(actData && !actData.detail ? [actData] : []);
        setUserProfile(profileRes.data);

        // Keep localStorage in sync with the server-side due_milestone
        if (profileRes.data) {
          localStorage.setItem('due_milestone', profileRes.data.due_milestone || '');
        }
        


        // If user is due for a milestone, find the psychometric questionnaire
        if (profileRes.data?.due_milestone) {
          try {
            const questionnaires = await questionnairesApi.list();
            const qList = Array.isArray(questionnaires.data) ? questionnaires.data : questionnaires.data?.results || [];
            const battery = qList.find((q: any) => q.is_active && q.assessment_type === 'PSYCHOMETRIC');
            if (battery) setPosttestQuestionnaire(battery);
          } catch (e) {
            console.error('Failed to fetch milestone questionnaire', e);
          }
        }

      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const getFirstName = () => {
    const rawName = userProfile?.full_name || userProfile?.username || '';
    const firstWord = rawName.replace(/[._]/g, ' ').trim().split(/\s+/)[0];
    if (!firstWord) return '';
    return firstWord.charAt(0).toUpperCase() + firstWord.slice(1);
  };

  if (userProfile?.is_disqualified) {
    return (
      <div className="max-w-2xl mx-auto py-12 px-4">
        <div className="bg-white border border-zinc-200 rounded-2xl p-8 md:p-12 shadow-sm text-center space-y-6 animate-in fade-in zoom-in-95 duration-500">
          <div className="w-16 h-16 bg-zinc-50 border border-zinc-200 rounded-2xl flex items-center justify-center mx-auto shadow-sm">
            <CheckCircle2 className="w-8 h-8 text-emerald-600" />
          </div>
          
          <div className="space-y-4">
            <h1 className="text-3xl font-bold text-zinc-900 leading-tight">Thank You / شکریہ</h1>
            
            <div className="border-t border-zinc-100 my-6"></div>
            
            <div className="space-y-6 text-left">
              <div className="space-y-2 font-latin">
                <span className="text-xs font-black uppercase tracking-wider text-zinc-400">English</span>
                <p className="text-zinc-650 font-medium leading-relaxed">
                  Thank you for your interest in our study. Based on your responses, you do not meet the inclusion criteria for this research experiment. We sincerely appreciate your time and willingness to participate.
                </p>
              </div>
              
              <div className="space-y-2 text-right" dir="rtl">
                <span className="text-xs font-black uppercase tracking-wider text-zinc-400 block text-left md:text-right" dir="ltr">Urdu</span>
                <p className="text-zinc-650 font-medium leading-relaxed font-urdu text-lg">
                  ہمارے مطالعے میں دلچسپی لینے کا شکریہ۔ آپ کے جوابات کی بنیاد پر، آپ اس تحقیقی تجربے میں شمولیت کے معیار پر پورا نہیں اترتے۔ ہم شرکت کے لیے آپ کے وقت اور آمادگی کی تہہ دل سے تعریف کرتے ہیں۔
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <header className="flex flex-col md:flex-row justify-between items-start md:items-end gap-4">
        <div>
          <h1 className="text-3xl font-bold mb-2 text-zinc-900 leading-tight">
            Welcome Back, {getFirstName()}
          </h1>
        </div>
        <div className="bg-white border border-zinc-200 rounded-lg px-4 py-2 flex items-center gap-3 shadow-sm">
          <Calendar className="text-zinc-500" size={18} />
          {activities.length > 0 && activities[0].current_day ? (
            <span className="text-sm font-semibold text-zinc-700 flex items-center gap-1.5">
              <span>Day {activities[0].current_day} of 7</span>
              <span className="text-zinc-300">|</span>
              <span dir="rtl" className="font-urdu text-sm">7 میں سے {activities[0].current_day} دن</span>
            </span>
          ) : (
            <span className="text-sm font-semibold text-zinc-700">
              Main Intervention Phase / مرکزی مرحلہ
            </span>
          )}
        </div>
      </header>

      {/* Bilingual Instruction Note */}
      <section className="bg-zinc-50 border border-zinc-200 rounded-xl p-6 shadow-sm">
        <h3 className="text-base font-bold text-zinc-900 mb-4 flex items-center gap-2 border-b border-zinc-200 pb-2">
          <span>How to Participate / حصہ لینے کا طریقہ</span>
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-zinc-650">
          <div className="space-y-2">
            <span className="text-xs font-bold uppercase tracking-wider text-[#2E4E90]">Instructions (English)</span>
            <p className="text-sm font-medium leading-relaxed">
              Click the active link under <strong>Today's Focus</strong>, write your reflection, and submit. You will then be redirected to any due questionnaires.
            </p>
          </div>
          <div className="space-y-2 text-right border-t md:border-t-0 md:border-l border-zinc-200 pt-4 md:pt-0 md:pl-6" dir="rtl">
            <span className="text-xs font-bold uppercase tracking-wider text-[#2E4E90] block text-left md:text-right" dir="ltr">ہدایات (اردو)</span>
            <p className="text-base font-medium leading-relaxed font-urdu">
              آج کی توجہ (Today's Focus) کے تحت دیے گئے عنوان پر کلک کریں، اپنے خیالات لکھیں اور جمع کرائیں۔ اس کے بعد آپ کو مطلوبہ سوالناموں پر خودکار طور پر بھیج دیا جائے گا۔
            </p>
          </div>
        </div>
      </section>

      {userProfile?.has_consecutive_misses && (
        <section className="border-2 border-amber-200 rounded-xl p-5 bg-amber-50 text-amber-900 shadow-sm flex items-start gap-4 animate-in slide-in-from-top duration-300">
          <div className="w-10 h-10 rounded-lg bg-amber-500 text-white flex items-center justify-center shrink-0">
            <AlertTriangle size={20} />
          </div>
          <div>
            <h3 className="font-bold text-amber-950">Consistency Nudge</h3>
            <p className="text-sm text-amber-800 mt-1 font-medium">{userProfile.consecutive_misses_message}</p>
          </div>
        </section>
      )}

      <div className="space-y-6">
          {/* Milestone Banner */}
          {userProfile?.due_milestone && posttestQuestionnaire && (() => {
            const getMilestoneDetails = (milestone: string) => {
              switch (milestone) {
                case 'SIGNUP':
                  return {
                    title: 'Baseline Psychometric Scales Available',
                    description: 'Please complete the baseline assessment to finalize your signup.',
                    buttonText: 'Start Baseline Assessment',
                    colorClass: 'from-emerald-50 to-white border-emerald-200 text-emerald-600 bg-emerald-600 hover:bg-emerald-700'
                  };
                case '7_DAYS':
                  return {
                    title: 'Day 7 Post-Test Available',
                    description: 'Congratulations on completing 7 days! Please take the final assessment to wrap up your experiment.',
                    buttonText: 'Start Post-Test',
                    colorClass: 'from-emerald-50 to-white border-emerald-200 text-emerald-600 bg-emerald-600 hover:bg-emerald-700'
                  };
                case '1_MONTH':
                  return {
                    title: '1-Month Follow-Up Available',
                    description: 'Please complete the 1-Month follow-up assessment.',
                    buttonText: 'Start Month 1 Assessment',
                    colorClass: 'from-teal-50 to-white border-teal-200 text-teal-600 bg-teal-600 hover:bg-teal-700'
                  };
                case '3_MONTHS':
                  return {
                    title: 'Month 3 Follow-Up Available',
                    description: 'Please complete the Month 3 follow-up assessment.',
                    buttonText: 'Start Month 3 Assessment',
                    colorClass: 'from-blue-50 to-white border-blue-200 text-blue-600 bg-blue-600 hover:bg-blue-700'
                  };
                case '6_MONTHS':
                  return {
                    title: 'Month 6 Follow-Up Available',
                    description: 'Please complete the Month 6 follow-up assessment.',
                    buttonText: 'Start Month 6 Assessment',
                    colorClass: 'from-purple-50 to-white border-purple-200 text-purple-600 bg-purple-600 hover:bg-purple-700'
                  };
                case '1_YEAR':
                  return {
                    title: 'T4 Month 12 Follow-Up Available',
                    description: 'Please complete the T4 12-month follow-up assessment (PERMA, PHQ-9, GAD-7, PANAS, Gratitude, SIDAS).',
                    buttonText: 'Start T4 Assessment',
                    colorClass: 'from-indigo-50 to-white border-indigo-200 text-indigo-600 bg-indigo-600 hover:bg-indigo-700'
                  };
                default:
                  return null;
              }
            };

            const details = getMilestoneDetails(userProfile.due_milestone);
            if (!details) return null;

            return (
              <section className={`border-2 rounded-xl p-6 md:p-8 bg-gradient-to-r shadow-sm font-latin ${details.colorClass.split(' ').slice(0, 2).join(' ')}`} dir="ltr">
                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                  <div className="flex items-center gap-4">
                    <div className={`w-12 h-12 rounded-xl flex items-center justify-center text-white shrink-0 ${details.colorClass.split(' ').slice(4, 5).join(' ')}`}>
                      <ClipboardCheck size={24} />
                    </div>
                    <div>
                      <h3 className="text-lg font-bold text-zinc-900 leading-snug">{details.title}</h3>
                      <p className="text-sm text-zinc-500 mt-0.5 leading-normal">{details.description}</p>
                    </div>
                  </div>
                  <Link
                    to={`/questionnaire/${posttestQuestionnaire.id}?milestone=${userProfile.due_milestone}`}
                    className={`inline-flex items-center justify-center gap-2 px-6 py-3 min-h-11 text-white rounded-lg font-semibold text-sm leading-none transition-colors shrink-0 ${details.colorClass.split(' ').slice(4, 6).join(' ')}`}
                  >
                    {details.buttonText}
                    <ArrowRight size={16} className="shrink-0" />
                  </Link>
                </div>
              </section>
            );
          })()}

          <section className="border border-zinc-200 rounded-xl p-6 md:p-8 bg-white shadow-sm">
            <h2 className="text-xl font-bold text-zinc-900 mb-6 flex items-center gap-2">
              <Clock className="text-zinc-500" size={20} /> Today's Focus / آج کی توجہ
            </h2>

            <div className="space-y-3">
              {(activities || []).map((activity) => (
                <Link
                  to={`/activity/${activity.id}`}
                  key={activity.id}
                  className={`bg-white border rounded-lg p-5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 hover:shadow-md transition-all cursor-pointer group block${!activity.submitted_today ? ' activity-pending-ring border-transparent' : ' border-zinc-200'}`}
                >
                  {/* Marching-ants SVG border — only shown when activity is pending */}
                  {!activity.submitted_today && (
                    <svg
                      className="activity-border-svg"
                      aria-hidden="true"
                      focusable="false"
                    >
                      <rect
                        x="1"
                        y="1"
                        width="calc(100% - 2px)"
                        height="calc(100% - 2px)"
                        rx="7"
                        ry="7"
                      />
                    </svg>
                  )}
                  <div className="flex items-center gap-4 flex-1 min-w-0 w-full">
                    <div className="w-10 h-10 shrink-0 rounded-lg bg-zinc-800 flex items-center justify-center text-white">
                      <Brain size={20} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <h4 className="font-semibold text-zinc-900 truncate">{activity.title}</h4>
                      <p className="text-sm text-zinc-500 truncate">{activity.description}</p>
                    </div>
                  </div>
                  {activity.submitted_today ? (
                    <div className="px-5 py-2 bg-emerald-50 text-emerald-600 border border-emerald-100 text-xs font-semibold rounded-lg flex items-center gap-2 shrink-0">
                      <CheckCircle2 size={16} /> Completed / مکمل
                    </div>
                  ) : (
                    <div className="px-5 py-2 bg-zinc-800 text-white text-xs font-semibold rounded-lg group-hover:bg-zinc-700 transition-colors flex items-center gap-1 shrink-0">
                      Open / کھولیں <ArrowRight size={14} />
                    </div>
                  )}
                </Link>
              ))}
              {activities.length === 0 && !loading && (
                <div className="text-center py-10 text-zinc-400 italic">No activities scheduled for today. / آج کے لیے کوئی مشقیں نہیں ہیں۔</div>
              )}
            </div>
          </section>
      </div>
    </div>
  );
};

const Brain: React.FC<{ size?: number }> = ({ size = 24 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.96.44 2.5 2.5 0 0 1-2.96-3.08 3 3 0 0 1-.34-5.58 2.5 2.5 0 0 1 1.32-4.24 2.5 2.5 0 0 1 4.44-2.08Z" />
    <path d="M14.5 2A2.5 2.5 0 0 0 12 4.5v15a2.5 2.5 0 0 0 4.96.44 2.5 2.5 0 0 0 2.96-3.08 3 3 0 0 0 .34-5.58 2.5 2.5 0 0 0-1.32-4.24 2.5 2.5 0 0 0-4.44-2.08Z" />
  </svg>
);

export default DashboardPage;
