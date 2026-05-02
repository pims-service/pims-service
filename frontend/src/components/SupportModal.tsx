import React, { useState, useEffect } from 'react';
import { X, Send, Loader2, CheckCircle2, MessageSquare, Clock } from 'lucide-react';
import api from '../services/api';

interface SupportModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const SupportModal: React.FC<SupportModalProps> = ({ isOpen, onClose }) => {
  const [activeTab, setActiveTab] = useState<'new' | 'history'>('new');
  const [subject, setSubject] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [tickets, setTickets] = useState<any[]>([]);
  const [loadingTickets, setLoadingTickets] = useState(false);
  const [expandedTicketId, setExpandedTicketId] = useState<number | null>(null);

  useEffect(() => {
    if (isOpen) {
      fetchTickets();
      setActiveTab('history');
    }
  }, [isOpen]);

  const fetchTickets = async () => {
    try {
      setLoadingTickets(true);
      const res = await api.get('/support/tickets/');
      const data = Array.isArray(res.data) ? res.data : res.data?.results || [];
      setTickets(data);
      if (data.length === 0) {
        setActiveTab('new');
      }
    } catch (err) {
      console.error('Failed to load tickets', err);
    } finally {
      setLoadingTickets(false);
    }
  };

  const handleMarkRead = async (ticketId: number) => {
    try {
      await api.post(`/support/tickets/${ticketId}/mark_read/`);
      setTickets(tickets.map(t => t.id === ticketId ? { ...t, is_read_by_user: true } : t));
    } catch (err) {
      console.error('Failed to mark read', err);
    }
  };

  const toggleTicket = (ticket: any) => {
    if (expandedTicketId === ticket.id) {
      setExpandedTicketId(null);
    } else {
      setExpandedTicketId(ticket.id);
      if (ticket.admin_reply && !ticket.is_read_by_user) {
        handleMarkRead(ticket.id);
      }
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await api.post('/support/tickets/', { subject, message });
      setSuccess(true);
      setTimeout(() => {
        setSuccess(false);
        setSubject('');
        setMessage('');
        fetchTickets();
        setActiveTab('history');
      }, 2000);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to submit query. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'Resolved':
        return <span className="px-2 py-0.5 bg-emerald-50 text-emerald-700 rounded text-[10px] font-bold uppercase tracking-wider">Resolved</span>;
      case 'In Progress':
        return <span className="px-2 py-0.5 bg-amber-50 text-amber-700 rounded text-[10px] font-bold uppercase tracking-wider">In Progress</span>;
      default:
        return <span className="px-2 py-0.5 bg-zinc-100 text-zinc-700 rounded text-[10px] font-bold uppercase tracking-wider">Open</span>;
    }
  };

  return (
    <div className="fixed inset-0 z-[60] bg-zinc-900/40 backdrop-blur-sm flex items-center justify-center p-4 animate-in fade-in duration-200">
      <div className="bg-white rounded-2xl w-full max-w-2xl shadow-xl overflow-hidden flex flex-col max-h-[90vh]">
        <div className="px-6 py-4 border-b border-zinc-100 flex items-center justify-between shrink-0">
          <h2 className="text-xl font-bold text-zinc-900 flex items-center gap-2">
            <MessageSquare size={20} className="text-zinc-500" />
            Support Center
          </h2>
          <button onClick={onClose} className="text-zinc-400 hover:text-zinc-600 transition-colors">
            <X size={20} />
          </button>
        </div>

        <div className="flex border-b border-zinc-100 px-6 shrink-0 bg-zinc-50/50">
          <button
            onClick={() => setActiveTab('history')}
            className={`py-3 px-4 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'history' ? 'border-zinc-900 text-zinc-900' : 'border-transparent text-zinc-500 hover:text-zinc-700'
            }`}
          >
            My Tickets
          </button>
          <button
            onClick={() => setActiveTab('new')}
            className={`py-3 px-4 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'new' ? 'border-zinc-900 text-zinc-900' : 'border-transparent text-zinc-500 hover:text-zinc-700'
            }`}
          >
            New Ticket
          </button>
        </div>

        <div className="p-6 overflow-y-auto flex-1">
          {activeTab === 'new' && (
            <div>
              {success ? (
                <div className="flex flex-col items-center justify-center py-8 space-y-4 animate-in zoom-in-95 duration-300">
                  <div className="w-16 h-16 bg-emerald-100 text-emerald-600 rounded-full flex items-center justify-center">
                    <CheckCircle2 size={32} />
                  </div>
                  <h3 className="text-xl font-bold text-zinc-900">Ticket Submitted</h3>
                  <p className="text-zinc-500 text-center max-w-xs text-sm">
                    We've received your message and our team will reply shortly. Check back in the 'My Tickets' tab.
                  </p>
                </div>
              ) : (
                <form onSubmit={handleSubmit} className="space-y-4">
                  {error && (
                    <div className="p-3 bg-red-50 text-red-600 text-sm rounded-lg border border-red-100">
                      {error}
                    </div>
                  )}
                  <div className="space-y-1.5">
                    <label className="text-sm font-medium text-zinc-700">Subject</label>
                    <input
                      type="text"
                      required
                      value={subject}
                      onChange={(e) => setSubject(e.target.value)}
                      placeholder="What do you need help with?"
                      className="input-minimal"
                      maxLength={200}
                    />
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-sm font-medium text-zinc-700">Message</label>
                    <textarea
                      required
                      value={message}
                      onChange={(e) => setMessage(e.target.value)}
                      placeholder="Describe your issue or question in detail..."
                      className="input-minimal min-h-[120px] resize-y"
                      maxLength={2000}
                    />
                  </div>
                  <div className="pt-2 flex justify-end">
                    <button
                      type="submit"
                      disabled={loading || !subject.trim() || !message.trim()}
                      className="btn-minimal flex items-center gap-2"
                    >
                      {loading ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
                      Submit Ticket
                    </button>
                  </div>
                </form>
              )}
            </div>
          )}

          {activeTab === 'history' && (
            <div className="space-y-4">
              {loadingTickets ? (
                <div className="flex justify-center py-8">
                  <Loader2 className="w-6 h-6 animate-spin text-zinc-400" />
                </div>
              ) : tickets.length === 0 ? (
                <div className="text-center py-8 text-zinc-500 text-sm">
                  You haven't submitted any support tickets yet.
                </div>
              ) : (
                <div className="space-y-3">
                  {tickets.map(ticket => (
                    <div key={ticket.id} className="border border-zinc-200 rounded-xl overflow-hidden bg-white">
                      <button 
                        onClick={() => toggleTicket(ticket)}
                        className="w-full text-left px-5 py-4 flex items-center justify-between hover:bg-zinc-50 transition-colors"
                      >
                        <div className="flex items-center gap-4">
                          <div className="flex flex-col">
                            <div className="flex items-center gap-2">
                              <span className="font-semibold text-zinc-900">{ticket.subject}</span>
                              {ticket.admin_reply && !ticket.is_read_by_user && (
                                <span className="bg-red-500 text-white text-[10px] font-bold px-1.5 py-0.5 rounded-full">New Reply</span>
                              )}
                            </div>
                            <span className="text-xs text-zinc-500 font-mono mt-0.5">{ticket.ticket_number} • {new Date(ticket.created_at).toLocaleDateString()}</span>
                          </div>
                        </div>
                        {getStatusBadge(ticket.status)}
                      </button>
                      
                      {expandedTicketId === ticket.id && (
                        <div className="px-5 py-4 border-t border-zinc-100 bg-zinc-50/50 space-y-4">
                          <div>
                            <div className="text-xs font-semibold text-zinc-500 uppercase mb-1">Your Message</div>
                            <div className="text-sm text-zinc-800 whitespace-pre-wrap bg-white p-3 rounded-lg border border-zinc-200">
                              {ticket.message}
                            </div>
                          </div>
                          
                          {ticket.admin_reply && (
                            <div>
                              <div className="text-xs font-semibold text-emerald-600 uppercase mb-1 flex items-center gap-1">
                                <MessageSquare size={12} /> Admin Reply
                              </div>
                              <div className="text-sm text-emerald-900 whitespace-pre-wrap bg-emerald-50 p-3 rounded-lg border border-emerald-100">
                                {ticket.admin_reply}
                              </div>
                            </div>
                          )}
                          {!ticket.admin_reply && ticket.status !== 'Resolved' && (
                            <div className="text-xs text-zinc-400 flex items-center gap-1 italic">
                              <Clock size={12} /> Awaiting response from support team...
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SupportModal;
