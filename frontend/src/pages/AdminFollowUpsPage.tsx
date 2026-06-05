import React, { useState, useEffect } from 'react';
import { Loader2, AlertCircle, HelpCircle, CheckCircle2, Clock, PhoneCall, X, Mail, Phone, User } from 'lucide-react';
import api from '../services/api';

const AdminFollowUpsPage: React.FC = () => {
  const [tickets, setTickets] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedTicket, setSelectedTicket] = useState<any>(null);
  const [adminNotes, setAdminNotes] = useState('');
  const [statusUpdating, setStatusUpdating] = useState(false);

  const fetchTickets = async () => {
    try {
      setLoading(true);
      const res = await api.get('/support/tickets/follow_ups/');
      setTickets(Array.isArray(res.data) ? res.data : res.data?.results || []);
      setError(null);
    } catch (err: any) {
      setError('Failed to load call protocol follow-ups.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTickets();
  }, []);

  const handleUpdateTicket = async (id: number, status: string, notes: string) => {
    setStatusUpdating(true);
    try {
      await api.patch(`/support/tickets/${id}/`, { status, admin_notes: notes });
      await fetchTickets();
      setSelectedTicket(null);
    } catch (err: any) {
      alert('Failed to update call protocol ticket.');
    } finally {
      setStatusUpdating(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'Resolved':
        return (
          <span className="px-2.5 py-1 bg-emerald-50 text-emerald-700 border border-emerald-200 rounded-lg text-xs font-semibold flex items-center gap-1.5 w-fit">
            <CheckCircle2 size={12} /> Resolved
          </span>
        );
      case 'In Progress':
        return (
          <span className="px-2.5 py-1 bg-amber-50 text-amber-700 border border-amber-200 rounded-lg text-xs font-semibold flex items-center gap-1.5 w-fit">
            <Clock size={12} /> In Progress
          </span>
        );
      default:
        return (
          <span className="px-2.5 py-1 bg-rose-50 text-rose-700 border border-rose-200 rounded-lg text-xs font-semibold flex items-center gap-1.5 w-fit">
            <HelpCircle size={12} /> Open
          </span>
        );
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-500 pt-0">
      <header className="flex flex-col sm:flex-row justify-between items-start sm:items-end gap-4 border-b border-zinc-200 pb-6 mb-6">
        <div>
          <h1 className="text-3xl font-bold text-zinc-900 flex items-center gap-3">
            <PhoneCall size={28} className="text-zinc-800" />
            Call Protocol Follow-Ups
          </h1>
          <p className="text-zinc-500 text-sm mt-1">
            Clinical outreach tasks for participants flagged under Tier 3 (high activity miss rate) and Tier 4 (overdue assessments).
          </p>
        </div>
      </header>

      {error && (
        <div className="p-4 bg-red-50 text-red-600 rounded-xl border border-red-100 flex items-center gap-2">
          <AlertCircle size={20} /> {error}
        </div>
      )}

      {loading ? (
        <div className="flex flex-col items-center justify-center py-20 space-y-4">
          <Loader2 className="w-8 h-8 animate-spin text-zinc-400" />
          <p className="text-zinc-500 font-medium text-sm">Syncing outreach list...</p>
        </div>
      ) : (
        <div className="bg-white rounded-xl shadow-sm border border-zinc-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm whitespace-nowrap">
              <thead className="bg-zinc-50 border-b border-zinc-200 text-zinc-500 font-semibold uppercase tracking-wider text-xs">
                <tr>
                  <th className="px-6 py-4">Status</th>
                  <th className="px-6 py-4">Ticket ID</th>
                  <th className="px-6 py-4">Participant Details</th>
                  <th className="px-6 py-4">Outreach Protocol Reason</th>
                  <th className="px-6 py-4">Flagged Date</th>
                  <th className="px-6 py-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-100">
                {tickets.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-6 py-12 text-center text-zinc-400 italic">
                      No call protocol follow-ups found.
                    </td>
                  </tr>
                ) : (
                  tickets.map((ticket) => (
                    <tr key={ticket.id} className="hover:bg-zinc-50 transition-colors">
                      <td className="px-6 py-4">{getStatusBadge(ticket.status)}</td>
                      <td className="px-6 py-4 font-mono text-xs text-zinc-500">{ticket.ticket_number}</td>
                      <td className="px-6 py-4">
                        <div className="space-y-1">
                          <div className="font-semibold text-zinc-900 flex items-center gap-1.5">
                            <User size={14} className="text-zinc-400" />
                            {ticket.user_full_name || 'Anonymous User'}
                          </div>
                          <div className="text-xs text-zinc-500 flex items-center gap-1.5">
                            <Mail size={12} className="text-zinc-400" />
                            {ticket.user_email}
                          </div>
                          <div className="text-xs text-zinc-500 flex items-center gap-1.5">
                            <Phone size={12} className="text-zinc-400" />
                            {ticket.user_whatsapp_number || 'No number provided'}
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 max-w-md truncate font-medium text-zinc-800" title={ticket.subject}>
                        {ticket.subject}
                      </td>
                      <td className="px-6 py-4 text-zinc-500">
                        {new Date(ticket.created_at).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 text-right">
                        <button
                          onClick={() => {
                            setSelectedTicket(ticket);
                            setAdminNotes(ticket.admin_notes || '');
                          }}
                          className="px-4 py-2 bg-zinc-900 text-white rounded-lg hover:bg-zinc-800 transition-colors text-xs font-semibold shadow-sm"
                        >
                          Review Call Status
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Outreach Ticket Detail / Modal */}
      {selectedTicket && (
        <div className="fixed inset-0 z-50 bg-zinc-900/40 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl w-full max-w-2xl shadow-xl overflow-hidden max-h-[90vh] flex flex-col border border-zinc-200">
            <div className="px-6 py-4 border-b border-zinc-150 flex items-center justify-between bg-zinc-50">
              <div className="flex items-center gap-3">
                <h3 className="font-bold text-zinc-900 text-lg">Outreach Task {selectedTicket.ticket_number}</h3>
                {getStatusBadge(selectedTicket.status)}
              </div>
              <button onClick={() => setSelectedTicket(null)} className="text-zinc-400 hover:text-zinc-600 rounded-lg p-1 hover:bg-zinc-100 transition-colors">
                <X size={20} />
              </button>
            </div>

            <div className="p-6 overflow-y-auto flex-1 space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 bg-zinc-50 p-4 rounded-xl border border-zinc-100">
                <div>
                  <div className="text-xs font-bold text-zinc-400 uppercase tracking-wider mb-1">Participant Name</div>
                  <div className="font-semibold text-zinc-900">{selectedTicket.user_full_name || 'Anonymous User'}</div>
                </div>
                <div>
                  <div className="text-xs font-bold text-zinc-400 uppercase tracking-wider mb-1">Email Address</div>
                  <div className="font-semibold text-zinc-900">{selectedTicket.user_email}</div>
                </div>
                <div className="md:col-span-2 pt-2 border-t border-zinc-100">
                  <div className="text-xs font-bold text-zinc-400 uppercase tracking-wider mb-1">WhatsApp / Phone Number</div>
                  <div className="font-semibold text-zinc-900 flex items-center gap-2 text-base">
                    <Phone size={16} className="text-zinc-500" />
                    {selectedTicket.user_whatsapp_number || 'No phone number provided'}
                  </div>
                </div>
              </div>

              <div>
                <div className="text-xs font-bold text-zinc-400 uppercase tracking-wider mb-1.5">Outreach Reason</div>
                <div className="font-semibold text-zinc-900 text-base mb-2">{selectedTicket.subject}</div>
                <div className="bg-zinc-50 p-4 rounded-xl text-sm text-zinc-700 whitespace-pre-wrap border border-zinc-100 leading-relaxed">
                  {selectedTicket.message}
                </div>
              </div>

              <div>
                <div className="text-xs font-bold text-zinc-400 uppercase tracking-wider mb-2">Outreach Actions & Clinical Notes</div>
                <div className="space-y-4">
                  <div>
                    <label className="block text-xs font-bold text-zinc-500 uppercase mb-1">Call Task Status</label>
                    <select
                      value={selectedTicket.status}
                      onChange={(e) => setSelectedTicket({ ...selectedTicket, status: e.target.value })}
                      className="w-full px-3 py-2 border border-zinc-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-zinc-900 text-sm bg-white"
                    >
                      <option value="Open">Open (Pending Call)</option>
                      <option value="In Progress">In Progress (Attempted Contact)</option>
                      <option value="Resolved">Resolved (Completed outreach / script spoken)</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-zinc-500 uppercase mb-1">Clinical Outreach Notes</label>
                    <textarea
                      value={adminNotes}
                      onChange={(e) => setAdminNotes(e.target.value)}
                      className="w-full px-3 py-2 border border-zinc-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-zinc-900 text-sm min-h-[120px] resize-y"
                      placeholder="Add call notes, follow-up script outcome, or details here..."
                    />
                  </div>
                </div>
              </div>
            </div>

            <div className="px-6 py-4 border-t border-zinc-150 bg-zinc-50 flex justify-end gap-3">
              <button
                onClick={() => setSelectedTicket(null)}
                className="px-4 py-2 text-sm font-semibold text-zinc-600 hover:bg-zinc-200 rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => handleUpdateTicket(selectedTicket.id, selectedTicket.status, adminNotes)}
                disabled={statusUpdating}
                className="px-5 py-2 bg-zinc-900 hover:bg-zinc-800 disabled:bg-zinc-400 text-white font-semibold text-sm rounded-lg shadow-sm flex items-center gap-2 transition-colors"
              >
                {statusUpdating && <Loader2 size={16} className="animate-spin" />}
                Save Outreach Updates
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminFollowUpsPage;
