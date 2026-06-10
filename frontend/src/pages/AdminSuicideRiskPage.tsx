import React, { useState, useEffect, useCallback } from 'react';
import {
  Loader2,
  AlertCircle,
  ShieldAlert,
  User,
  Mail,
  Phone,
  CheckCircle2,
  XCircle,
  HelpCircle,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import api from '../services/api';

type SuicideRiskCase = {
  response_set_id: string;
  user_id: number;
  username: string;
  email: string;
  full_name: string;
  whatsapp_number: string;
  group_name: string | null;
  milestone_label: string;
  completed_at: string | null;
  suicide_risk_opt_in: boolean | null;
  phq9_total: number | null;
  sidas_total: number | null;
};

const AdminSuicideRiskPage: React.FC = () => {
  const [cases, setCases] = useState<SuicideRiskCase[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showFilter, setShowFilter] = useState<'opt_in' | 'all'>('opt_in');
  const [meta, setMeta] = useState({
    last_refreshed_at: null as string | null,
    total_flagged: 0,
    opt_in_count: 0,
  });

  // Pagination State
  const [currentPage, setCurrentPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [hasNext, setHasNext] = useState(false);
  const [hasPrev, setHasPrev] = useState(false);

  const fetchCases = useCallback(async (filter: 'opt_in' | 'all' = showFilter, page: number = 1) => {
    try {
      setLoading(true);
      const res = await api.get('/questionnaires/admin/suicide-risk-follow-ups/', {
        params: { show: filter, page },
      });
      setCases(res.data.cases || []);
      setMeta({
        last_refreshed_at: res.data.last_refreshed_at,
        total_flagged: res.data.total_flagged ?? 0,
        opt_in_count: res.data.opt_in_count ?? 0,
      });
      setTotalCount(res.data.count ?? 0);
      setHasNext(!!res.data.next);
      setHasPrev(!!res.data.previous);
      setCurrentPage(page);
      setError(null);
    } catch {
      setError('Failed to load suicide risk follow-up data.');
    } finally {
      setLoading(false);
    }
  }, [showFilter]);

  useEffect(() => {
    fetchCases(showFilter, 1);
  }, [showFilter, fetchCases]);

  const optInBadge = (optIn: boolean | null) => {
    if (optIn === true) {
      return (
        <span className="px-2.5 py-1 bg-emerald-50 text-emerald-700 border border-emerald-200 rounded-lg text-xs font-semibold flex items-center gap-1.5 w-fit">
          <CheckCircle2 size={12} /> Opted in
        </span>
      );
    }
    if (optIn === false) {
      return (
        <span className="px-2.5 py-1 bg-zinc-100 text-zinc-600 border border-zinc-200 rounded-lg text-xs font-semibold flex items-center gap-1.5 w-fit">
          <XCircle size={12} /> Declined
        </span>
      );
    }
    return (
      <span className="px-2.5 py-1 bg-amber-50 text-amber-700 border border-amber-200 rounded-lg text-xs font-semibold flex items-center gap-1.5 w-fit">
        <HelpCircle size={12} /> No response
      </span>
    );
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-500 pt-0">
      <header className="flex flex-col sm:flex-row justify-between items-start sm:items-end gap-4 border-b border-zinc-200 pb-6 mb-6">
        <div>
          <h1 className="text-3xl font-bold text-zinc-900 flex items-center gap-3">
            <ShieldAlert size={28} className="text-red-600" />
            Safety Risk Follow-Ups
          </h1>
          <p className="text-zinc-500 text-sm mt-1 max-w-2xl">
            Participants flagged for suicidal risk who requested researcher follow-up. The list updates
            automatically when someone opts in, when a new risk flag is raised, and once daily via a background job.
          </p>
          {meta.last_refreshed_at && (
            <p className="text-zinc-400 text-xs mt-2">
              Last updated: {new Date(meta.last_refreshed_at).toLocaleString()} ·{' '}
              {meta.opt_in_count} opted in · {meta.total_flagged} total flagged
            </p>
          )}
        </div>
        <select
          value={showFilter}
          onChange={(e) => setShowFilter(e.target.value as 'opt_in' | 'all')}
          className="text-sm border border-zinc-200 rounded-lg px-3 py-2 bg-white text-zinc-700"
        >
          <option value="opt_in">Opted in only</option>
          <option value="all">All flagged cases</option>
        </select>
      </header>

      {error && (
        <div className="p-4 bg-red-50 text-red-600 rounded-xl border border-red-100 flex items-center gap-2">
          <AlertCircle size={20} /> {error}
        </div>
      )}

      {loading ? (
        <div className="flex flex-col items-center justify-center py-20 space-y-4">
          <Loader2 className="w-8 h-8 animate-spin text-zinc-400" />
          <p className="text-zinc-500 font-medium text-sm">Loading cached follow-up list...</p>
        </div>
      ) : (
        <div className="bg-white rounded-xl shadow-sm border border-zinc-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm whitespace-nowrap">
              <thead className="bg-zinc-50 border-b border-zinc-200 text-zinc-500 font-semibold uppercase tracking-wider text-xs">
                <tr>
                  <th className="px-6 py-4">Follow-up</th>
                  <th className="px-6 py-4">Participant</th>
                  <th className="px-6 py-4">Contact</th>
                  <th className="px-6 py-4">Assessment</th>
                  <th className="px-6 py-4">Scores</th>
                  <th className="px-6 py-4">Flagged Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-100">
                {cases.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-6 py-12 text-center text-zinc-400 italic">
                      {showFilter === 'opt_in'
                        ? 'No participants have opted in for researcher follow-up.'
                        : 'No flagged suicide risk cases found.'}
                    </td>
                  </tr>
                ) : (
                  cases.map((item) => (
                    <tr key={item.response_set_id} className="hover:bg-zinc-50 transition-colors">
                      <td className="px-6 py-4">{optInBadge(item.suicide_risk_opt_in)}</td>
                      <td className="px-6 py-4">
                        <div className="space-y-1">
                          <div className="font-semibold text-zinc-900 flex items-center gap-1.5">
                            <User size={14} className="text-zinc-400" />
                            {item.full_name || item.username}
                          </div>
                          <div className="text-xs text-zinc-500">@{item.username}</div>
                          {item.group_name && (
                            <div className="text-xs text-zinc-400">Group: {item.group_name}</div>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="space-y-1 text-xs text-zinc-600">
                          <div className="flex items-center gap-1.5">
                            <Mail size={12} className="text-zinc-400" />
                            {item.email}
                          </div>
                          <div className="flex items-center gap-1.5">
                            <Phone size={12} className="text-zinc-400" />
                            {item.whatsapp_number || 'No number provided'}
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 font-medium text-zinc-800">{item.milestone_label}</td>
                      <td className="px-6 py-4 text-xs text-zinc-500">
                        PHQ-9: {item.phq9_total ?? '—'} · SIDAS: {item.sidas_total ?? '—'}
                      </td>
                      <td className="px-6 py-4 text-zinc-500">
                        {item.completed_at
                          ? new Date(item.completed_at).toLocaleDateString()
                          : '—'}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination Controls */}
          {totalCount > 0 && (
            <div className="px-6 py-3 bg-zinc-50 border-t border-zinc-150 flex items-center justify-between">
              <div className="text-xs text-zinc-500">
                Showing <span className="font-medium text-zinc-700">{cases.length}</span> of <span className="font-medium text-zinc-700">{totalCount}</span> results
              </div>
              <div className="flex items-center gap-1.5">
                <button
                  onClick={() => fetchCases(showFilter, currentPage - 1)}
                  disabled={!hasPrev || loading}
                  className={`p-1.5 border border-zinc-200 rounded-lg transition-all ${!hasPrev ? 'opacity-30 cursor-not-allowed' : 'hover:bg-zinc-100'}`}
                >
                  <ChevronLeft size={16} />
                </button>
                <div className="px-3 py-1.5 border border-zinc-200 rounded-lg text-xs font-medium text-zinc-700 bg-white">
                  Page {currentPage}
                </div>
                <button
                  onClick={() => fetchCases(showFilter, currentPage + 1)}
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
    </div>
  );
};

export default AdminSuicideRiskPage;
