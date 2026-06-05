import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api, { questionnairesApi } from '../services/api';
import { useTranslation } from 'react-i18next';
import { Calendar, CheckCircle2, Clock, ArrowRight, Bell, FileText, ClipboardCheck, AlertTriangle } from 'lucide-react';

const DashboardPage: React.FC = () => {
  const [activities, setActivities] = useState<any[]>([]);
  const [submissions, setSubmissions] = useState<any[]>([]);
  const [phase, setPhase] = useState<any>(null);
  const [userProfile, setUserProfile] = useState<any>(null);
  const [posttestQuestionnaire, setPosttestQuestionnaire] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const { t } = useTranslation();

  const [notifications, setNotifications] = useState<any[]>([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [actRes, phaseRes, subRes, activitySubRes, profileRes, notifRes] = await Promise.all([
          api.get('/activities/daily/current/').catch(() => ({ data: null })),
          api.get('/phases/current/').catch(() => ({ data: null })),
          api.get('/questionnaires/response-sets/').catch(() => ({ data: { results: [] } })),
          api.get('/activities/all-submissions/').catch(() => ({ data: { results: [] } })),
          api.get('/users/profile/').catch(() => ({ data: null })),
          api.get('/notifications/').catch(() => ({ data: [] }))
        ]);

        const actData = actRes.data;
        setActivities(actData && !actData.detail ? [actData] : []);
        setPhase(phaseRes.data);
        setUserProfile(profileRes.data);

        // Keep localStorage in sync with the server-side due_milestone
        if (profileRes.data) {
          localStorage.setItem('due_milestone', profileRes.data.due_milestone || '');
        }
        
        // Handle notifications
        const notifData = Array.isArray(notifRes.data) ? notifRes.data : notifRes.data?.results || [];
        setNotifications(notifData.slice(0, 3));

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

        const questionnaireSubmissions = (Array.isArray(subRes.data) ? subRes.data : subRes.data?.results || [])
          .filter((s: any) => s.status === 'COMPLETED')
          .map((s: any) => ({
            ...s,
            type: 'questionnaire',
            display_title: s.questionnaire_title || 'Assessment Result',
            date: s.completed_at
          }));

        const dailySubmissions = (Array.isArray(activitySubRes.data) ? activitySubRes.data : activitySubRes.data?.results || []).map((s: any) => ({
          ...s,
          type: 'activity',
          display_title: s.activity_title || 'Daily Activity',
          date: s.submission_date
        }));

        const combinedSubmissions = [...questionnaireSubmissions, ...dailySubmissions]
          .filter(s => s.date)
          .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());

        setSubmissions(combinedSubmissions.slice(0, 5));
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const getPerformanceLabel = (rate: number) => {
    if (rate >= 90) return t('dashboard.optimal');
    if (rate >= 70) return 'Good';
    if (rate >= 40) return 'Average';
    return 'Action Required';
  };

  return (
    <div className="space-y-8">
      <header className="flex flex-col md:flex-row justify-between items-start md:items-end gap-4">
        <div>
          <h1 className="text-3xl font-bold mb-2 text-zinc-900 leading-tight">{t('dashboard.welcome')}</h1>
          <p className="text-zinc-500 font-medium text-sm">{t('dashboard.welcome_new')} <span className="text-zinc-800 font-semibold">{phase?.name || t('dashboard.initialization')}</span></p>
        </div>
        <div className="bg-white border border-zinc-200 rounded-lg px-4 py-2 flex items-center gap-3 shadow-sm">
          <Calendar className="text-zinc-500" size={18} />
          <span className="text-sm font-semibold text-zinc-700">
            {activities.length > 0 && activities[0].current_day
              ? t('dashboard.day_of', { current: activities[0].current_day, total: 7 })
              : t('dashboard.welcome_new')}
          </span>
        </div>
      </header>

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

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
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
              <section className={`border-2 rounded-xl p-6 md:p-8 bg-gradient-to-r shadow-sm ${details.colorClass.split(' ').slice(0, 2).join(' ')}`}>
                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                  <div className="flex items-center gap-4">
                    <div className={`w-12 h-12 rounded-xl flex items-center justify-center text-white shrink-0 ${details.colorClass.split(' ').slice(4, 5).join(' ')}`}>
                      <ClipboardCheck size={24} />
                    </div>
                    <div>
                      <h3 className="text-lg font-bold text-zinc-900">{details.title}</h3>
                      <p className="text-sm text-zinc-500 mt-0.5">{details.description}</p>
                    </div>
                  </div>
                  <Link
                    to={`/questionnaire/${posttestQuestionnaire.id}?milestone=${userProfile.due_milestone}`}
                    className={`px-6 py-3 text-white rounded-lg font-semibold text-sm transition-colors flex items-center gap-2 shrink-0 ${details.colorClass.split(' ').slice(4, 6).join(' ')}`}
                  >
                    {details.buttonText} <ArrowRight size={16} />
                  </Link>
                </div>
              </section>
            );
          })()}

          <section className="border border-zinc-200 rounded-xl p-6 md:p-8 bg-white shadow-sm">
            <h2 className="text-xl font-bold text-zinc-900 mb-6 flex items-center gap-2">
              <Clock className="text-zinc-500" size={20} /> {t('dashboard.todays_focus')}
            </h2>

            <div className="space-y-3">
              {(activities || []).map((activity) => (
                <Link
                  to={`/activity/${activity.id}`}
                  key={activity.id}
                  className="bg-white border border-zinc-200 rounded-lg p-5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 hover:border-zinc-400 hover:shadow-md transition-all cursor-pointer group block"
                >
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
                      <CheckCircle2 size={16} /> Completed
                    </div>
                  ) : (
                    <div className="px-5 py-2 bg-zinc-800 text-white text-xs font-semibold rounded-lg group-hover:bg-zinc-700 transition-colors flex items-center gap-1 shrink-0">
                      Open <ArrowRight size={14} />
                    </div>
                  )}
                </Link>
              ))}
              {activities.length === 0 && !loading && (
                <div className="text-center py-10 text-zinc-400 italic">{t('dashboard.no_activities')}</div>
              )}
            </div>
          </section>

          <section className="border border-zinc-200 rounded-xl p-6 md:p-8 bg-white shadow-sm">
            <h2 className="text-xl font-bold text-zinc-900 mb-6 flex items-center gap-2">
              <CheckCircle2 className="text-zinc-500" size={20} /> {t('dashboard.recent_submissions')}
            </h2>
            <div className="divide-y divide-zinc-100">
              {(submissions || []).map((sub) => (
                <div key={`${sub.type}-${sub.id}`} className="py-4 flex items-center justify-between group">
                  <div className="flex items-center gap-3">
                    <FileText size={18} className="text-zinc-400" />
                    <div>
                      <span className="block font-medium text-zinc-800">{sub.display_title}</span>
                      <span className="text-zinc-400 text-xs">{new Date(sub.date).toLocaleDateString()}</span>
                    </div>
                  </div>
                  {sub.type === 'questionnaire' ? (
                    <Link to={`/results/${sub.id}`} className="flex items-center gap-1 text-zinc-600 text-sm font-medium hover:text-zinc-900 opacity-0 group-hover:opacity-100 transition-all">
                      {t('dashboard.view_insights')} <ArrowRight size={14} />
                    </Link>
                  ) : (
                    <Link to={`/activity/${sub.activity}`} className="flex items-center gap-1 text-zinc-600 text-sm font-medium hover:text-zinc-900 opacity-0 group-hover:opacity-100 transition-all">
                      Edit <ArrowRight size={14} />
                    </Link>
                  )}
                </div>
              ))}
              {submissions.length === 0 && (
                <div className="py-8 text-center text-zinc-400 italic text-sm">
                  {t('dashboard.no_submissions')}
                </div>
              )}
            </div>
          </section>
        </div>

        <div className="space-y-6">
          <div className="border border-zinc-200 rounded-xl p-6 bg-zinc-800 text-white shadow-sm">
            <div className="flex items-center gap-2 font-semibold text-xs mb-4 text-zinc-300 uppercase tracking-wider">
              <Bell size={14} /> {t('dashboard.notifications')}
            </div>
            {notifications.length > 0 ? (
              <div className="space-y-4">
                {notifications.map((n) => (
                  <div key={n.id} className="text-sm leading-relaxed border-b border-zinc-700 pb-2 last:border-0">
                    {n.message}
                    <div className="text-[10px] text-zinc-400 mt-1">{new Date(n.created_at).toLocaleString()}</div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm italic text-zinc-400">No new notifications</p>
            )}
          </div>

          <div className="border border-zinc-200 rounded-xl p-6 text-center bg-white shadow-sm">
            <div className="inline-block p-5 rounded-xl bg-zinc-800 text-white mb-4">
              <div className="text-3xl font-bold">{userProfile?.completion_rate || 0}%</div>
            </div>
            <h4 className="font-semibold text-zinc-800 text-sm">{t('dashboard.completion_rate')}</h4>
            <p className="text-zinc-400 text-xs mt-1">
              {t('dashboard.performance')}: {getPerformanceLabel(userProfile?.completion_rate || 0)}
            </p>
          </div>
        </div>
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
