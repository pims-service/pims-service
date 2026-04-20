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
      setData(Array.isArray(response.data) ? response.data : []);
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
        <RefreshCcw className="w-8 h-8 text-zinc-400 animate-spin" />
        <p className="text-zinc-500 font-medium text-sm">Loading reports...</p>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-in fade-in duration-700 pt-0">
      <header className="border-b border-zinc-200 pb-6">
        <h1 className="text-3xl font-bold text-zinc-900">Experimental Reports</h1>
        <p className="text-zinc-500 mt-1 text-sm">Monitor assessment completion rates and export participant data.</p>
      </header>

      {error && (
        <div className="p-5 bg-white border border-zinc-200 rounded-xl flex items-center gap-4 shadow-sm">
          <AlertCircle size={20} className="text-zinc-500" />
          <p className="text-zinc-700 font-medium text-sm">{error}</p>
          <button onClick={fetchSummary} className="ml-auto px-4 py-1.5 bg-zinc-800 text-white rounded-lg font-medium text-xs hover:bg-zinc-700 transition-colors">Retry</button>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
        {(data || []).map((q, index) => (
          <motion.div 
            key={q.questionnaire_id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className="group bg-white border border-zinc-200 rounded-xl p-6 hover:shadow-lg hover:border-zinc-300 transition-all"
          >
            <div className="flex flex-col h-full space-y-6">
              <div className="flex items-start justify-between">
                <div className="w-11 h-11 bg-zinc-100 flex items-center justify-center text-zinc-700 rounded-lg">
                  <BarChart3 size={22} />
                </div>
                <div className="flex flex-col items-end">
                   <div className="text-xs font-medium text-zinc-500 mb-0.5">Success Rate</div>
                   <div className="text-xl font-bold text-zinc-800">
                     {Math.round(q.completion_rate)}%
                   </div>
                </div>
              </div>

              <div>
                <h3 className="text-lg font-semibold text-zinc-900 leading-tight">
                  {q.title}
                </h3>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="p-3 border border-zinc-100 rounded-lg bg-zinc-50/50">
                  <div className="flex items-center gap-1.5 text-zinc-500 text-xs font-medium mb-1">
                    <Clock size={12} /> Starts
                  </div>
                  <div className="text-xl font-bold text-zinc-800">{q.total_starts}</div>
                </div>
                <div className="p-3 border border-zinc-100 rounded-lg bg-zinc-50/50">
                  <div className="flex items-center gap-1.5 text-zinc-500 text-xs font-medium mb-1">
                    <CheckCircle size={12} /> Completed
                  </div>
                  <div className="text-xl font-bold text-zinc-800">{q.total_completions}</div>
                </div>
              </div>

              <button 
                onClick={() => handleExport(q.questionnaire_id)}
                className="w-full py-3 bg-zinc-800 text-white rounded-lg font-medium text-sm hover:bg-zinc-700 transition-colors flex items-center justify-center gap-2"
              >
                <Download size={16} />
                Export CSV
              </button>
            </div>
          </motion.div>
        ))}
      </div>

      <div className="p-6 md:p-8 border border-zinc-200 rounded-xl bg-white flex flex-col lg:flex-row lg:items-center justify-between gap-6 shadow-sm">
         <div className="flex items-center gap-4 md:gap-6">
            <div className="w-12 h-12 bg-zinc-100 flex-shrink-0 flex items-center justify-center text-zinc-700 rounded-xl">
               <TrendingUp size={24} />
            </div>
            <div>
               <h4 className="text-lg font-semibold text-zinc-900 leading-tight">Advanced Aggregation</h4>
               <p className="text-zinc-500 text-sm max-w-lg mt-1">Download the global longitudinal dataset including day-over-day participant delta and group assignment metrics.</p>
            </div>
         </div>
         <button className="w-full lg:w-auto px-6 py-3 bg-zinc-800 text-white rounded-lg font-medium text-sm hover:bg-zinc-700 transition-colors whitespace-nowrap">
            Global SPSS Export
         </button>
      </div>
    </div>
  );
};

export default AdminReportsPage;
