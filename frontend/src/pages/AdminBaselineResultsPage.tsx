import React, { useState, useEffect } from 'react';
import { 
  ClipboardList, 
  Search, 
  RotateCw, 
  AlertTriangle, 
  X,
  User,
  Calendar,
  Clock,
  ChevronRight,
  Eye,
  Download
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { questionnairesApi } from '../services/api';

interface RawResponse {
  id: string;
  question: string;
  question_text: string;
  question_type: string;
  selected_option: string | null;
  selected_option_label: string | null;
  text_value: string | null;
}

interface BaselineSet {
  id: string;
  user: number;
  full_name: string;
  username: string;
  questionnaire_title: string;
  group_name: string | null;
  status: string;
  started_at: string;
  completed_at: string;
  responses?: RawResponse[];
}

const AdminBaselineResultsPage: React.FC = () => {
  const [submissions, setSubmissions] = useState<BaselineSet[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedGroup, setSelectedGroup] = useState<string>('All');
  
  const [selectedSubmission, setSelectedSubmission] = useState<BaselineSet | null>(null);

  const fetchSubmissions = async () => {
    setLoading(true);
    try {
      const response = await questionnairesApi.getAdminBaselineResponses();
      setSubmissions(response.data);
      setError(null);
    } catch (err) {
      console.error('Failed to fetch baseline responses', err);
      setError('Failed to load raw research data. Please verify administrative privileges.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSubmissions();
  }, []);

  const handleViewDetail = async (id: string) => {
    try {
      const response = await questionnairesApi.getAdminBaselineDetail(id);
      setSelectedSubmission(response.data);
    } catch (err) {
      console.error('Failed to fetch submission detail', err);
    }
  };

  const filteredSubmissions = submissions.filter(s => {
    const matchesSearch = s.full_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
                          s.username?.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesGroup = selectedGroup === 'All' ? true : (s.group_name || 'Unassigned') === selectedGroup;
    return matchesSearch && matchesGroup;
  });

  const uniqueGroups = Array.from(new Set(submissions.map(s => s.group_name || 'Unassigned')));

  const handleExportCSV = async () => {
    try {
      const response = await questionnairesApi.exportAdminBaselinesCSV(selectedGroup);
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'baseline_experiment_data_spss.csv');
      document.body.appendChild(link);
      link.click();
      link.parentNode?.removeChild(link);
    } catch (err) {
      console.error('Failed to export baseline data', err);
      setError('Failed to export CSV. Please check server logs.');
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
        <RotateCw className="w-8 h-8 text-indigo-500 animate-spin" />
        <p className="text-slate-400 font-medium animate-pulse">Retrieving raw response sets...</p>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-in fade-in duration-700 pt-0">
      <header className="flex flex-col md:flex-row md:items-end justify-between gap-6 border-b border-zinc-200 py-4 mb-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2 text-indigo-500 text-[10px] font-black uppercase tracking-[0.2em] mb-2">
            <ClipboardList size={14} /> Research Data Hub
          </div>
          <h1 className="text-4xl font-black tracking-tighter text-zinc-900 uppercase">Baseline Raw Data</h1>
          <p className="text-slate-500 font-medium italic">Direct oversight of initial participant screening responses.</p>
        </div>

        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-4 w-full md:w-auto">
          <div className="relative group flex-grow sm:w-80">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-indigo-500 transition-colors" size={18} />
            <input 
              type="text" 
              placeholder="Search participants..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-12 pr-4 py-3 bg-white border border-zinc-200 rounded-2xl focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all text-sm"
            />
          </div>
          
          <select 
            value={selectedGroup}
            onChange={(e) => setSelectedGroup(e.target.value)}
            className="px-4 py-3 bg-white border border-zinc-200 rounded-2xl focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all text-sm font-medium text-zinc-700 cursor-pointer"
          >
            <option value="All">All Groups</option>
            {uniqueGroups.sort().map(grp => (
              <option key={grp} value={grp}>{grp}</option>
            ))}
          </select>

          <button  
            onClick={handleExportCSV}
            className="flex items-center justify-center gap-2 px-6 py-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded-2xl font-black text-xs uppercase tracking-widest transition-all shadow-md hover:shadow-lg whitespace-nowrap"
          >
            <Download size={16} /> Export SPSS CSV
          </button>
        </div>
      </header>

      {error ? (
        <div className="glass p-12 text-center space-y-4 border-red-500/20 max-w-2xl mx-auto">
          <AlertTriangle className="w-12 h-12 text-red-500 mx-auto" />
          <h2 className="text-xl font-bold text-white">Access Violation</h2>
          <p className="text-slate-400">{error}</p>
          <button onClick={fetchSubmissions} className="btn-premium px-8">Retry Connection</button>
        </div>
      ) : (
        <div className="bg-white border border-zinc-200 rounded-[2.5rem] overflow-hidden shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead>
                <tr className="bg-zinc-50/50 border-b border-zinc-100">
                  <th className="px-8 py-5 text-[10px] font-black uppercase tracking-widest text-slate-500">Participant</th>
                  <th className="px-8 py-5 text-[10px] font-black uppercase tracking-widest text-slate-500">Completion Date</th>
                  <th className="px-8 py-5 text-[10px] font-black uppercase tracking-widest text-slate-500">Group</th>
                  <th className="px-8 py-5 text-[10px] font-black uppercase tracking-widest text-slate-500">Assessment</th>
                  <th className="px-8 py-5 text-[10px] font-black uppercase tracking-widest text-slate-500 text-right">Raw Data</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-100">
                {filteredSubmissions.map((s) => (
                  <tr key={s.id} className="hover:bg-zinc-50/50 transition-colors group">
                    <td className="px-8 py-6">
                      <div className="flex items-center gap-4">
                        <div className="w-10 h-10 rounded-xl bg-indigo-50 flex items-center justify-center text-indigo-600 font-black border border-indigo-100">
                          <User size={18} />
                        </div>
                        <div>
                          <div className="font-black text-zinc-900 uppercase tracking-tight">{s.full_name || 'Anonymous'}</div>
                          <div className="text-xs text-slate-500 font-mono">@{s.username}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-8 py-6">
                      <div className="space-y-1">
                        <div className="flex items-center gap-2 text-zinc-900 font-bold text-sm">
                          <Calendar size={14} className="text-slate-400" />
                          {new Date(s.completed_at).toLocaleDateString()}
                        </div>
                        <div className="flex items-center gap-2 text-slate-400 text-[10px] font-medium font-mono uppercase">
                          <Clock size={12} />
                          {new Date(s.completed_at).toLocaleTimeString()}
                        </div>
                      </div>
                    </td>
                    <td className="px-8 py-6">
                      {s.group_name ? (
                        <span className="px-3 py-1 bg-indigo-50 rounded-full text-[10px] font-bold text-indigo-600 border border-indigo-100 inline-block uppercase tracking-widest">
                          {s.group_name}
                        </span>
                      ) : (
                        <span className="text-xs text-slate-400 italic">Unassigned</span>
                      )}
                    </td>
                    <td className="px-8 py-6">
                      <div className="px-3 py-1 bg-zinc-100 rounded-full text-[10px] font-bold text-zinc-600 border border-zinc-200 inline-block uppercase tracking-widest">
                        {s.questionnaire_title}
                      </div>
                    </td>
                    <td className="px-8 py-6 text-right">
                      <button 
                        onClick={() => handleViewDetail(s.id)}
                        className="p-2.5 rounded-xl bg-white border border-zinc-200 text-zinc-400 hover:text-indigo-600 hover:border-indigo-500/50 transition-all group-hover:shadow-md"
                      >
                        <Eye size={18} />
                      </button>
                    </td>
                  </tr>
                ))}
                {filteredSubmissions.length === 0 && (
                  <tr>
                    <td colSpan={5} className="px-8 py-20 text-center text-slate-400 italic">
                      No baseline responses match your criteria.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Detail Inspection Modal */}
      <AnimatePresence>
        {selectedSubmission && (
          <div className="fixed inset-0 z-[100] flex items-center justify-end p-4 md:p-10 pointer-events-none">
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setSelectedSubmission(null)}
              className="absolute inset-0 bg-zinc-950/20 backdrop-blur-sm pointer-events-auto"
            />
            <motion.div 
              initial={{ x: '100%', opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              exit={{ x: '100%', opacity: 0 }}
              className="relative w-full max-w-2xl bg-white h-full rounded-[2.5rem] shadow-2xl pointer-events-auto overflow-hidden flex flex-col border border-zinc-200"
            >
              <div className="p-8 border-b border-zinc-100 flex items-center justify-between bg-zinc-50/50">
                <div>
                  <h3 className="text-2xl font-black text-zinc-900 uppercase">Inspection Terminal</h3>
                  <p className="text-sm text-slate-500 font-medium">Reviewing: {selectedSubmission.full_name}</p>
                </div>
                <button 
                  onClick={() => setSelectedSubmission(null)}
                  className="p-3 bg-white border border-zinc-200 text-zinc-400 rounded-2xl hover:text-zinc-950 transition-colors"
                >
                  <X size={20} />
                </button>
              </div>

              <div className="flex-grow overflow-y-auto p-8 space-y-8 scrollbar-hide">
                <div className="grid grid-cols-2 gap-4">
                   <div className="p-4 rounded-3xl bg-zinc-50 border border-zinc-100">
                      <div className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">Status</div>
                      <div className="text-xs font-bold text-emerald-600 flex items-center gap-1.5 uppercase">
                         <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                         {selectedSubmission.status}
                      </div>
                   </div>
                   <div className="p-4 rounded-3xl bg-zinc-50 border border-zinc-100">
                      <div className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">Submission Time</div>
                      <div className="text-xs font-bold text-zinc-900 uppercase font-mono">
                         {new Date(selectedSubmission.completed_at).toLocaleTimeString()}
                      </div>
                   </div>
                </div>

                <div className="space-y-6">
                  <h4 className="text-xs font-black uppercase tracking-[0.2em] text-slate-400">Response Set Map</h4>
                  {selectedSubmission.responses?.map((resp, idx) => (
                    <div key={resp.id} className="p-6 rounded-3xl border border-zinc-100 bg-white hover:border-indigo-100 transition-colors group">
                       <div className="flex gap-4">
                          <div className="text-xs font-black text-slate-300 group-hover:text-indigo-200 transition-colors">
                            {(idx + 1).toString().padStart(2, '0')}
                          </div>
                          <div className="space-y-3 flex-grow">
                             <div className="text-sm font-bold text-zinc-900 leading-snug">
                               {resp.question_text}
                             </div>
                             <div className="flex items-center gap-3">
                               <ChevronRight size={14} className="text-indigo-400" />
                               <div className="text-sm font-black text-indigo-600 bg-indigo-50 px-3 py-1 rounded-xl uppercase tracking-tight">
                                  {resp.selected_option_label || resp.text_value || 'No response captured'}
                               </div>
                             </div>
                          </div>
                       </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="p-8 border-t border-zinc-100 bg-zinc-50/50">
                 <button 
                  onClick={() => setSelectedSubmission(null)}
                  className="w-full py-4 bg-zinc-900 text-white rounded-2xl font-black text-xs uppercase tracking-widest hover:bg-zinc-800 transition-all"
                 >
                   Clear Terminal
                 </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default AdminBaselineResultsPage;
