import React, { useState, useEffect } from 'react';
import { 
  Download, 
  TrendingUp, 
  CheckCircle, 
  Clock, 
  BarChart3,
  AlertCircle,
  RefreshCcw
} from 'lucide-react';
import { motion } from 'framer-motion';
import { questionnairesApi, API_URL } from '../services/api';

interface AnalyticsSummary {
  questionnaire_id: string;
  title: string;
  total_starts: number;
  total_completions: number;
  completion_rate: number;
  loading?: boolean;
}

const AdminReportsPage: React.FC = () => {
  const [data, setData] = useState<AnalyticsSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchSummary = async () => {
    try {
      setLoading(true);
      const response = await questionnairesApi.getAnalyticsSummary();
      setData(response.data);
      setError(null);
    } catch (err) {
      console.error('Failed to fetch analytics summary', err);
      setError('Failed to load researcher metrics. Please verify backend connectivity.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSummary();
  }, []);

  const handleExport = (id: string) => {
    const exportUrl = `${API_URL}/questionnaires/${id}/export/`;
    window.open(exportUrl, '_blank');
  };

  if (loading && data.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
        <RefreshCcw className="w-8 h-8 text-indigo-500 animate-spin" />
        <p className="text-slate-400 font-medium animate-pulse">Aggregating experimental data...</p>
      </div>
    );
  }

  return (
    <div className="space-y-12 animate-in fade-in duration-700">
      <header>
        <h1 className="text-4xl font-bold tracking-tight text-zinc-900">Experimental Reports</h1>
        <p className="text-slate-500 mt-2">Monitor assessment completion rates and export wide-format participant data.</p>
      </header>

      {error && (
        <div className="p-6 bg-red-50 border border-red-100 rounded-3xl flex items-center gap-4 text-red-600">
          <AlertCircle size={24} />
          <p className="font-medium">{error}</p>
          <button onClick={fetchSummary} className="ml-auto px-4 py-2 bg-red-600 text-white rounded-xl text-sm font-bold">Retry Sync</button>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-8">
        {data.map((q, index) => (
          <motion.div 
            key={q.questionnaire_id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className="group bg-white border border-zinc-200 rounded-[2.5rem] p-8 hover:shadow-2xl hover:shadow-indigo-500/10 transition-all duration-300"
          >
            <div className="flex flex-col h-full space-y-8">
              <div className="flex items-start justify-between">
                <div className="w-14 h-14 rounded-2xl bg-indigo-50 flex items-center justify-center text-indigo-600 group-hover:bg-indigo-600 group-hover:text-white transition-all duration-300 shadow-inner">
                  <BarChart3 size={28} />
                </div>
                <div className="flex flex-col items-end">
                   <div className="text-[10px] font-black uppercase tracking-widest text-slate-400 mb-1">Success Rate</div>
                   <div className={`text-2xl font-mono font-black ${q.completion_rate > 70 ? 'text-green-500' : 'text-amber-500'}`}>
                     {Math.round(q.completion_rate)}%
                   </div>
                </div>
              </div>

              <div>
                <h3 className="text-xl font-black text-zinc-900 leading-tight uppercase tracking-tight group-hover:text-indigo-600 transition-colors">
                  {q.title}
                </h3>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="p-4 rounded-3xl bg-zinc-50 border border-zinc-100 group-hover:bg-white group-hover:border-indigo-100 transition-all">
                  <div className="flex items-center gap-2 text-slate-500 text-[10px] font-bold uppercase tracking-widest mb-1">
                    <Clock size={12} className="text-indigo-400" /> Starts
                  </div>
                  <div className="text-2xl font-black text-zinc-900">{q.total_starts}</div>
                </div>
                <div className="p-4 rounded-3xl bg-zinc-50 border border-zinc-100 group-hover:bg-white group-hover:border-indigo-100 transition-all">
                  <div className="flex items-center gap-2 text-slate-500 text-[10px] font-bold uppercase tracking-widest mb-1">
                    <CheckCircle size={12} className="text-green-500" /> Finalized
                  </div>
                  <div className="text-2xl font-black text-zinc-900">{q.total_completions}</div>
                </div>
              </div>

              <button 
                onClick={() => handleExport(q.questionnaire_id)}
                className="w-full py-5 bg-zinc-950 text-white rounded-[1.75rem] font-black text-xs uppercase tracking-[0.2em] flex items-center justify-center gap-3 hover:bg-indigo-600 transition-all active:scale-[0.98] shadow-xl shadow-zinc-950/20"
              >
                <Download size={18} />
                Export Research CSV
              </button>
            </div>
          </motion.div>
        ))}
      </div>

      <div className="p-10 bg-indigo-600/5 border border-indigo-600/10 rounded-[3rem] flex items-center justify-between">
         <div className="flex items-center gap-8">
            <div className="w-16 h-16 rounded-3xl bg-indigo-600 flex items-center justify-center text-white shadow-lg shadow-indigo-600/20">
               <TrendingUp size={32} />
            </div>
            <div>
               <h4 className="text-2xl font-black text-zinc-900">Advanced Aggregation</h4>
               <p className="text-slate-500 max-w-lg mt-1">Download the global longitudinal dataset including day-over-day participant delta and group assignment metrics.</p>
            </div>
         </div>
         <button className="px-8 py-5 bg-white border border-zinc-200 text-zinc-900 rounded-[2rem] font-black text-xs uppercase tracking-[0.2em] hover:border-indigo-600 hover:text-indigo-600 transition-all shadow-sm">
            Global SPSS Export
         </button>
      </div>
    </div>
  );
};

export default AdminReportsPage;
