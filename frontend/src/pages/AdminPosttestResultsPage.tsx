import React, { useState, useEffect } from 'react';
import {
  ClipboardCheck,
  Search,
  RotateCw,
  AlertTriangle,
  X,
  User,
  Calendar,
  Clock,
  ChevronRight,
  Eye,
  ChevronLeft,
  Download,
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { questionnairesApi, API_URL } from '../services/api';

interface RawResponse {
  id: string;
  question: string;
  question_text: string;
  question_type: string;
  selected_option: string | null;
  selected_option_label: string | null;
  text_value: string | null;
}

interface PosttestSet {
  id: string;
  user: number;
  full_name: string;
  username: string;
  questionnaire: string;
  questionnaire_title: string;
  group_name: string | null;
  status: string;
  started_at: string;
  completed_at: string;
  responses?: RawResponse[];
}

const AdminPosttestResultsPage: React.FC = () => {
  const [submissions, setSubmissions] = useState<PosttestSet[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedGroup, setSelectedGroup] = useState<string>('All');

  // Pagination State
  const [currentPage, setCurrentPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [hasNext, setHasNext] = useState(false);
  const [hasPrev, setHasPrev] = useState(false);

  const [selectedSubmission, setSelectedSubmission] = useState<PosttestSet | null>(null);
  const [exportingId, setExportingId] = useState<string | null>(null);
  const [exportStatus, setExportStatus] = useState<'PENDING' | 'PROCESSING' | 'SUCCESS' | 'FAILED' | null>(null);

  const fetchSubmissions = async (page: number = 1) => {
    setLoading(true);
    try {
      const response = await questionnairesApi.getAdminPosttestResponses(page);
      
      const data = response.data;
      if (data && typeof data === 'object' && 'results' in data && Array.isArray(data.results)) {
        setSubmissions(data.results);
        setTotalCount(data.count || 0);
        setHasNext(!!data.next);
        setHasPrev(!!data.previous);
      } else if (Array.isArray(data)) {
        setSubmissions(data);
        setTotalCount(data.length);
        setHasNext(false);
        setHasPrev(false);
      } else {
        setSubmissions([]);
      }

      setCurrentPage(page);
      setError(null);
    } catch (err) {
      console.error('Failed to fetch post-test responses', err);
      setError('Failed to load post-test data. Please verify administrative privileges.');
      setSubmissions([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSubmissions();
  }, []);

  // Polling logic for Export Task
  useEffect(() => {
    let pollInterval: NodeJS.Timeout;

    if (exportingId && (exportStatus === 'PENDING' || exportStatus === 'PROCESSING')) {
      pollInterval = setInterval(async () => {
        try {
          const response = await questionnairesApi.getAdminBaselineExportStatus(exportingId);
          const { status, file_url } = response.data;
          
          setExportStatus(status);
          
          if (status === 'SUCCESS' && file_url) {
            setExportingId(null);
            setExportStatus(null);
            const link = document.createElement('a');
            link.href = file_url;
            link.setAttribute('download', 'posttest_export.csv');
            document.body.appendChild(link);
            link.click();
            link.remove();
          } else if (status === 'FAILED') {
            setExportingId(null);
          }
        } catch (err) {
          console.error('Polling failed', err);
          setExportingId(null);
          setExportStatus('FAILED');
        }
      }, 2000);
    }

    return () => {
      if (pollInterval) clearInterval(pollInterval);
    };
  }, [exportingId, exportStatus]);

  const handleViewDetail = async (id: string) => {
    try {
      const response = await questionnairesApi.getAdminPosttestDetail(id);
      setSelectedSubmission(response.data);
    } catch (err) {
      console.error('Failed to fetch submission detail', err);
    }
  };

  const handleExport = async () => {
    try {
      setExportStatus('PENDING');
      const response = await questionnairesApi.triggerAdminPosttestExport(selectedGroup);
      setExportingId(response.data.task_id);
      setError(null);
    } catch (err) {
      console.error('Failed to export posttest data', err);
      setError('Failed to initiate CSV export. Please check server logs.');
      setExportStatus(null);
    }
  };

  const filteredSubmissions = (submissions || []).filter(s => {
    if (!s) return false;
    const matchesSearch = s.full_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      s.username?.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesGroup = selectedGroup === 'All' ? true : (s.group_name || 'Unassigned') === selectedGroup;
    return matchesSearch && matchesGroup;
  });

  const uniqueGroups = Array.from(new Set((submissions || []).map(s => s?.group_name || 'Unassigned')));

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
        <RotateCw className="w-8 h-8 text-zinc-400 animate-spin" />
        <p className="text-zinc-500 font-medium text-sm">Loading post-test data...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-in fade-in duration-700 pt-0">
      <header className="flex flex-col md:flex-row md:items-end justify-between gap-6 border-b border-zinc-200 pb-6">
        <div className="space-y-1 flex-1">
          <div className="flex items-center gap-2 text-zinc-500 text-xs font-medium mb-1">
            <ClipboardCheck size={14} /> Day 7 Post-Test Data
          </div>
          <h1 className="text-3xl font-bold text-zinc-900">Post-Test Results</h1>
          <p className="text-zinc-500 text-sm">Day 7 reassessment data from completed participants</p>
        </div>

        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 w-full md:w-auto">
          <button
            onClick={handleExport}
            disabled={!!exportingId}
            className="flex items-center justify-center gap-2 px-5 py-2.5 bg-zinc-800 text-white rounded-lg font-medium text-sm hover:bg-zinc-700 transition-colors disabled:opacity-40 whitespace-nowrap mr-2"
          >
            {exportingId ? (
              <>
                <RotateCw size={16} className="animate-spin" />
                Preparing...
              </>
            ) : (
              <>
                <Download size={16} /> Export CSV
              </>
            )}
          </button>
          
          <div className="relative group flex-grow sm:w-72">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-400" size={16} />
            <input
              type="text"
              placeholder="Search participants..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2.5 bg-white border border-zinc-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-zinc-200 transition-all text-sm"
            />
          </div>

          <select
            value={selectedGroup}
            onChange={(e) => setSelectedGroup(e.target.value)}
            className="px-3 py-2.5 bg-white border border-zinc-200 rounded-lg focus:outline-none text-sm text-zinc-700 cursor-pointer"
          >
            <option value="All">All Groups</option>
            {uniqueGroups.sort().map(grp => (
              <option key={grp} value={grp}>{grp}</option>
            ))}
          </select>
        </div>
      </header>

      {exportStatus === 'FAILED' && (
        <div className="bg-white border border-zinc-200 rounded-lg p-4 flex items-center gap-3 text-zinc-700 shadow-sm">
          <AlertTriangle size={16} className="text-zinc-500" />
          <span className="text-sm font-medium">Export task failed. Please check server logs.</span>
          <button onClick={() => setExportStatus(null)} className="ml-auto text-xs font-medium text-zinc-500 hover:text-zinc-700">Dismiss</button>
        </div>
      )}

      {exportingId && (
        <div className="bg-zinc-800 text-white rounded-lg p-4 flex items-center gap-3 shadow-sm">
          <ClipboardCheck size={16} className="animate-bounce" />
          <span className="text-sm font-medium">Processing large dataset export. Please wait...</span>
        </div>
      )}

      {error ? (
        <div className="border border-zinc-200 rounded-xl p-12 text-center space-y-4 max-w-2xl mx-auto bg-white shadow-sm">
          <AlertTriangle className="w-10 h-10 text-zinc-400 mx-auto" />
          <h2 className="text-lg font-semibold text-zinc-800">Access Denied</h2>
          <p className="text-zinc-500 text-sm">{error}</p>
          <button onClick={() => fetchSubmissions(1)} className="px-6 py-2.5 bg-zinc-800 text-white rounded-lg font-medium text-sm hover:bg-zinc-700 transition-colors">Retry</button>
        </div>
      ) : (
        <div className="bg-white border border-zinc-200 rounded-xl overflow-hidden shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="bg-zinc-50 border-b border-zinc-200">
                  <th className="px-6 py-3 text-xs font-semibold text-zinc-500 uppercase tracking-wider">Participant</th>
                  <th className="px-6 py-3 text-xs font-semibold text-zinc-500 uppercase tracking-wider">Date</th>
                  <th className="px-6 py-3 text-xs font-semibold text-zinc-500 uppercase tracking-wider">Group</th>
                  <th className="px-6 py-3 text-xs font-semibold text-zinc-500 uppercase tracking-wider">Assessment</th>
                  <th className="px-6 py-3 text-xs font-semibold text-zinc-500 uppercase tracking-wider text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-100">
                {filteredSubmissions.map((s) => (
                  <tr key={s.id} className="hover:bg-zinc-50 transition-colors">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div className="w-9 h-9 bg-emerald-50 flex items-center justify-center text-emerald-600 rounded-lg">
                          <User size={16} />
                        </div>
                        <div>
                          <div className="font-medium text-zinc-800">{s.full_name || 'Anonymous'}</div>
                          <div className="text-xs text-zinc-400">@{s.username}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="space-y-0.5">
                        <div className="flex items-center gap-1.5 text-zinc-700 text-sm">
                          <Calendar size={13} className="text-zinc-400" />
                          {new Date(s.completed_at).toLocaleDateString()}
                        </div>
                        <div className="flex items-center gap-1.5 text-zinc-400 text-xs">
                          <Clock size={11} />
                          {new Date(s.completed_at).toLocaleTimeString()}
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      {s.group_name ? (
                        <span className="px-2 py-0.5 bg-zinc-100 text-xs font-medium text-zinc-700 rounded-md">
                          {s.group_name}
                        </span>
                      ) : (
                        <span className="text-xs text-zinc-400 italic">Unassigned</span>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      <span className="px-2 py-0.5 bg-emerald-50 text-xs font-medium text-emerald-700 border border-emerald-100 rounded-md">
                        {s.questionnaire_title}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <button
                        onClick={() => handleViewDetail(s.id)}
                        className="p-2 bg-white border border-zinc-200 text-zinc-600 hover:bg-zinc-50 hover:border-zinc-300 transition-all rounded-lg"
                      >
                        <Eye size={16} />
                      </button>
                    </td>
                  </tr>
                ))}
                {filteredSubmissions.length === 0 && (
                  <tr>
                    <td colSpan={5} className="px-6 py-16 text-center text-zinc-400 italic text-sm">
                      No post-test submissions yet. Results will appear here when participants complete Day 7.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination Controls */}
          {totalCount > 0 && (
            <div className="px-6 py-3 bg-zinc-50 border-t border-zinc-100 flex items-center justify-between">
              <div className="text-xs text-zinc-500">
                Showing <span className="font-medium text-zinc-700">{submissions.length}</span> of <span className="font-medium text-zinc-700">{totalCount}</span> results
              </div>
              <div className="flex items-center gap-1.5">
                <button
                  onClick={() => fetchSubmissions(currentPage - 1)}
                  disabled={!hasPrev || loading}
                  className={`p-1.5 border border-zinc-200 rounded-lg transition-all ${!hasPrev ? 'opacity-30 cursor-not-allowed' : 'hover:bg-zinc-100'}`}
                >
                  <ChevronLeft size={16} />
                </button>
                <div className="px-3 py-1.5 border border-zinc-200 rounded-lg text-xs font-medium text-zinc-700 bg-white">
                  Page {currentPage}
                </div>
                <button
                  onClick={() => fetchSubmissions(currentPage + 1)}
                  disabled={!hasNext || loading}
                  className={`p-1.5 border border-zinc-200 rounded-lg transition-all ${!hasNext ? 'opacity-30 cursor-not-allowed' : 'hover:bg-zinc-100'}`}
                >
                  <ChevronRight size={16} />
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Detail Inspection Modal */}
      <AnimatePresence>
        {selectedSubmission && (
          <div className="fixed inset-0 z-[100] flex items-center justify-end p-4 md:p-8 pointer-events-none">
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
              className="relative w-full max-w-2xl bg-white h-full shadow-2xl pointer-events-auto overflow-hidden flex flex-col rounded-l-2xl border border-zinc-200"
            >
              <div className="p-6 border-b border-zinc-200 flex items-center justify-between">
                <div>
                  <h3 className="text-xl font-bold text-zinc-900">Post-Test Response Detail</h3>
                  <p className="text-sm text-zinc-500 mt-0.5">{selectedSubmission.full_name}</p>
                </div>
                <button
                  onClick={() => setSelectedSubmission(null)}
                  className="p-2 bg-zinc-100 text-zinc-600 hover:bg-zinc-200 transition-all rounded-lg"
                >
                  <X size={18} />
                </button>
              </div>

              <div className="flex-grow overflow-y-auto p-6 space-y-6 scrollbar-hide">
                <div className="grid grid-cols-2 gap-3">
                  <div className="p-4 border border-zinc-200 rounded-lg bg-white">
                    <div className="text-xs text-zinc-500 mb-1">Status</div>
                    <div className="text-sm font-semibold text-zinc-800 flex items-center gap-1.5">
                      <div className="w-2 h-2 bg-emerald-500 rounded-full" />
                      {selectedSubmission.status}
                    </div>
                  </div>
                  <div className="p-4 border border-zinc-200 rounded-lg bg-white">
                    <div className="text-xs text-zinc-500 mb-1">Completed At</div>
                    <div className="text-sm font-semibold text-zinc-800 font-mono">
                      {new Date(selectedSubmission.completed_at).toLocaleTimeString()}
                    </div>
                  </div>
                </div>

                <div className="space-y-3">
                  <h4 className="text-xs font-semibold text-zinc-500 uppercase tracking-wider border-b border-zinc-100 pb-2">Responses</h4>
                  {selectedSubmission.responses?.map((resp, idx) => (
                    <div key={resp.id} className="p-4 border border-zinc-200 rounded-lg bg-white hover:bg-zinc-50 transition-colors">
                      <div className="flex gap-4">
                        <div className="text-lg font-bold text-zinc-300 border-r border-zinc-100 pr-4 min-w-[3rem] text-center">
                          {(idx + 1).toString().padStart(2, '0')}
                        </div>
                        <div className="space-y-2 flex-grow">
                          <div className="text-sm font-medium text-zinc-800">
                            {resp.question_text}
                          </div>
                          <div className="flex items-center gap-2">
                            <ChevronRight size={14} className="text-zinc-400" />
                            <div className="text-sm font-medium text-zinc-600 bg-zinc-100 px-3 py-1 rounded-md">
                              {resp.selected_option_label || resp.text_value || 'No response'}
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="p-6 border-t border-zinc-100">
                <button
                  onClick={() => setSelectedSubmission(null)}
                  className="w-full py-3 bg-zinc-800 text-white rounded-lg font-medium text-sm hover:bg-zinc-700 transition-colors"
                >
                  Close
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default AdminPosttestResultsPage;
