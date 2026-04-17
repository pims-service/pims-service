import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api, { questionnairesApi } from '../services/api';
import { Calendar, CheckCircle2, Clock, ArrowRight, Bell, FileText } from 'lucide-react';

const DashboardPage: React.FC = () => {
  const [activities, setActivities] = useState<any[]>([]);
  const [submissions, setSubmissions] = useState<any[]>([]);
  const [phase, setPhase] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [actRes, phaseRes, subRes] = await Promise.all([
          api.get('/activities/'),
          api.get('/phases/current/'),
          questionnairesApi.listResponseSets()
        ]);
        setActivities(actRes.data);
        setPhase(phaseRes.data);
        setSubmissions(subRes.data.filter((s: any) => s.status === 'COMPLETED').slice(0, 5));
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  return (
    <div className="space-y-8">
      <header className="flex justify-between items-end">
        <div>
          <h1 className="text-4xl font-bold mb-2">Welcome Back</h1>
          <p className="text-slate-400">You are currently in <span className="text-indigo-400 font-semibold">{phase?.name || 'Initialization'}</span></p>
        </div>
        <div className="glass px-4 py-2 flex items-center gap-3">
          <Calendar className="text-indigo-400" size={20} />
          <span className="text-sm font-medium">Day 12 of 30</span>
        </div>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="md:col-span-2 space-y-6">
          <section className="glass p-8 relative overflow-hidden">
            <div className="absolute top-0 right-0 w-32 h-32 bg-indigo-500/10 blur-3xl -mr-16 -mt-16"></div>
            <h2 className="text-2xl font-bold mb-6 flex items-center gap-2">
              <Clock className="text-indigo-400" /> Today's Focus
            </h2>
            
            <div className="space-y-4">
              {activities.map((activity) => (
                <div key={activity.id} className="bg-slate-900/50 border border-slate-700 p-6 rounded-2xl flex items-center justify-between hover:border-indigo-500/50 transition-all cursor-pointer group">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 rounded-xl bg-indigo-500/20 flex items-center justify-center text-indigo-400">
                      <Brain size={24} />
                    </div>
                    <div>
                      <h4 className="font-bold text-lg">{activity.title}</h4>
                      <p className="text-slate-400 text-sm overflow-hidden text-ellipsis whitespace-nowrap max-w-[200px]">{activity.description}</p>
                    </div>
                  </div>
                  <Link to={`/activity/${activity.id}`} className="btn-premium py-2 px-4 text-sm group-hover:scale-105">
                    Start <ArrowRight size={16} className="inline ml-1" />
                  </Link>
                </div>
              ))}
              {activities.length === 0 && !loading && (
                <div className="text-center py-10 text-slate-500 italic">No activities scheduled for today. Check back later!</div>
              )}
            </div>
          </section>

          <section className="glass p-8">
            <h2 className="text-2xl font-bold mb-6 flex items-center gap-2">
              <CheckCircle2 className="text-green-400" /> Recent Submissions
            </h2>
            <div className="divide-y divide-slate-700/50">
              {submissions.map((sub) => (
                <div key={sub.id} className="py-4 flex items-center justify-between group">
                  <div className="flex items-center gap-3">
                    <FileText size={18} className="text-slate-500" />
                    <div>
                       <span className="block font-medium">{sub.questionnaire_title || 'Assessment Result'}</span>
                       <span className="text-slate-500 text-xs">{new Date(sub.completed_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                  <Link to={`/results/${sub.id}`} className="flex items-center gap-1 text-indigo-400 text-sm font-bold opacity-0 group-hover:opacity-100 transition-opacity">
                    View Insights <ArrowRight size={14} />
                  </Link>
                </div>
              ))}
              {submissions.length === 0 && (
                <div className="py-8 text-center text-slate-500 italic text-sm">
                  No submissions yet. Complete your baseline to see insights.
                </div>
              )}
            </div>
          </section>
        </div>

        <div className="space-y-6">
          <div className="glass p-6 border-l-4 border-l-indigo-500">
            <div className="flex items-center gap-2 text-indigo-400 font-bold mb-4">
              <Bell size={20} /> Latest Notification
            </div>
            <p className="text-sm leading-relaxed text-slate-300">
              "Great job completing yesterday's task! Phase 2 begins in 3 days. Get ready for new challenges."
            </p>
          </div>

          <div className="glass p-6 text-center">
            <div className="inline-block p-4 rounded-full bg-indigo-500/10 mb-4">
              <div className="text-3xl font-bold text-indigo-400">85%</div>
            </div>
            <h4 className="font-bold">Completion Rate</h4>
            <p className="text-slate-500 text-xs mt-1">Keep it up! You're above average.</p>
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
