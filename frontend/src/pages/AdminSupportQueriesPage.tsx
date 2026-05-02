import React, { useState, useEffect } from 'react';
import { Loader2, Search, AlertCircle, HelpCircle, CheckCircle2, Clock, MoreVertical, MessageSquare, X } from 'lucide-react';
import api from '../services/api';

const AdminSupportQueriesPage: React.FC = () => {
  const [tickets, setTickets] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedTicket, setSelectedTicket] = useState<any>(null);
  const [adminNotes, setAdminNotes] = useState('');
  const [adminReply, setAdminReply] = useState('');
  const [statusUpdating, setStatusUpdating] = useState(false);

  const fetchTickets = async () => {
    try {
      setLoading(true);
      const res = await api.get('/support/tickets/');
      setTickets(Array.isArray(res.data) ? res.data : res.data?.results || []);
      setError(null);
    } catch (err: any) {
      setError('Failed to load support queries.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTickets();
  }, []);

  const handleUpdateTicket = async (id: number, status: string, notes: string, reply: string) => {
    setStatusUpdating(true);
    try {
      await api.patch(`/support/tickets/${id}/`, { status, admin_notes: notes, admin_reply: reply });
      await fetchTickets();
      setSelectedTicket(null);
    } catch (err: any) {
      alert('Failed to update ticket.');
    } finally {
      setStatusUpdating(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'Resolved':
        return <span className="px-2 py-1 bg-emerald-50 text-emerald-700 rounded-md text-xs font-medium flex items-center gap-1"><CheckCircle2 size={12} /> Resolved</span>;
      case 'In Progress':
        return <span className="px-2 py-1 bg-amber-50 text-amber-700 rounded-md text-xs font-medium flex items-center gap-1"><Clock size={12} /> In Progress</span>;
      default:
        return <span className="px-2 py-1 bg-zinc-100 text-zinc-700 rounded-md text-xs font-medium flex items-center gap-1"><HelpCircle size={12} /> Open</span>;
    }
  };

  return (
    <div className="space-y-6">
      <header className="flex flex-col sm:flex-row justify-between items-start sm:items-end gap-4">
        <div>
          <h1 className="text-2xl font-bold text-zinc-900 flex items-center gap-2">
            <MessageSquare size={24} className="text-zinc-500" />
            User Queries
          </h1>
          <p className="text-zinc-500 text-sm mt-1">Manage and resolve support tickets from participants.</p>
        </div>
      </header>

      {error && (
        <div className="p-4 bg-red-50 text-red-600 rounded-xl border border-red-100 flex items-center gap-2">
          <AlertCircle size={20} /> {error}
        </div>
      )}

      {loading ? (
        <div className="flex justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-zinc-400" />
        </div>
      ) : (
        <div className="bg-white rounded-xl shadow-sm border border-zinc-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm whitespace-nowrap">
              <thead className="bg-zinc-50 border-b border-zinc-200 text-zinc-500 font-medium">
                <tr>
                  <th className="px-6 py-4">Status</th>
                  <th className="px-6 py-4">Ticket ID</th>
                  <th className="px-6 py-4">User</th>
                  <th className="px-6 py-4">Subject</th>
                  <th className="px-6 py-4">Created</th>
                  <th className="px-6 py-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-100">
                {tickets.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="px-6 py-8 text-center text-zinc-500 italic">
                      No support queries found.
                    </td>
                  </tr>
                ) : (
                  tickets.map((ticket) => (
                    <tr key={ticket.id} className="hover:bg-zinc-50 transition-colors">
                      <td className="px-6 py-4">{getStatusBadge(ticket.status)}</td>
                      <td className="px-6 py-4 font-mono text-xs text-zinc-500">{ticket.ticket_number}</td>
                      <td className="px-6 py-4">
                        <div className="font-medium text-zinc-900">{ticket.user_full_name}</div>
                        <div className="text-xs text-zinc-500">{ticket.user_email}</div>
                      </td>
                      <td className="px-6 py-4 max-w-xs truncate" title={ticket.subject}>
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
                            setAdminReply(ticket.admin_reply || '');
                          }}
                          className="px-3 py-1.5 bg-zinc-900 text-white rounded-lg hover:bg-zinc-800 transition-colors text-xs font-medium"
                        >
                          Review
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

      {/* Ticket Review Modal */}
      {selectedTicket && (
        <div className="fixed inset-0 z-50 bg-zinc-900/40 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl w-full max-w-2xl shadow-xl overflow-hidden max-h-[90vh] flex flex-col">
            <div className="px-6 py-4 border-b border-zinc-100 flex items-center justify-between bg-zinc-50">
              <div className="flex items-center gap-3">
                <h3 className="font-bold text-zinc-900">Review Ticket {selectedTicket.ticket_number}</h3>
                {getStatusBadge(selectedTicket.status)}
              </div>
              <button onClick={() => setSelectedTicket(null)} className="text-zinc-400 hover:text-zinc-600">
                <X size={20} />
              </button>
            </div>
            
            <div className="p-6 overflow-y-auto flex-1 space-y-6">
              <div>
                <div className="text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-1">From</div>
                <div className="font-medium text-zinc-900">{selectedTicket.user_full_name} ({selectedTicket.user_email})</div>
              </div>

              <div>
                <div className="text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-1">Subject</div>
                <div className="font-medium text-zinc-900 text-lg">{selectedTicket.subject}</div>
              </div>

              <div>
                <div className="text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-1">Message</div>
                <div className="bg-zinc-50 p-4 rounded-xl text-sm text-zinc-800 whitespace-pre-wrap border border-zinc-100">
                  {selectedTicket.message}
                </div>
              </div>

              <div>
                <div className="text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-2">Admin Actions</div>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-zinc-700 mb-1">Status</label>
                    <select
                      value={selectedTicket.status}
                      onChange={(e) => setSelectedTicket({ ...selectedTicket, status: e.target.value })}
                      className="input-minimal"
                    >
                      <option value="Open">Open</option>
                      <option value="In Progress">In Progress</option>
                      <option value="Resolved">Resolved</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-zinc-700 mb-1">Internal Notes</label>
                    <textarea
                      value={adminNotes}
                      onChange={(e) => setAdminNotes(e.target.value)}
                      className="input-minimal min-h-[100px] resize-y"
                      placeholder="Add private notes here (not visible to user)..."
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-zinc-700 mb-1">Reply to User</label>
                    <textarea
                      value={adminReply}
                      onChange={(e) => setAdminReply(e.target.value)}
                      className="input-minimal min-h-[100px] resize-y border-emerald-200 focus:border-emerald-500 focus:ring-emerald-500"
                      placeholder="Write a response to the participant..."
                    />
                  </div>
                </div>
              </div>
            </div>

            <div className="px-6 py-4 border-t border-zinc-100 bg-zinc-50 flex justify-end gap-3">
              <button
                onClick={() => setSelectedTicket(null)}
                className="px-4 py-2 text-sm font-medium text-zinc-600 hover:bg-zinc-200 rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => handleUpdateTicket(selectedTicket.id, selectedTicket.status, adminNotes, adminReply)}
                disabled={statusUpdating}
                className="btn-minimal flex items-center gap-2"
              >
                {statusUpdating ? <Loader2 size={16} className="animate-spin" /> : <CheckCircle2 size={16} />}
                Save Changes
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminSupportQueriesPage;
