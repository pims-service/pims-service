import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Loader2, Send, FlaskConical, RefreshCw, Users, AlertCircle, CheckCircle2 } from 'lucide-react';
import api from '../../services/api';

type Segment = 'not_started' | 'stopped' | 'd7_due' | 'all_eligible' | 'manual';

interface Recipient {
  user_id: number;
  name: string;
  email: string;
  joined: string;
}

interface Campaign {
  id: number;
  created_at: string;
  segment: string;
  segment_label: string;
  subject: string;
  recipient_count: number;
  sent: number;
  failed: number;
  pending: number;
  status: 'queued' | 'sending' | 'done';
  sent_by: string | null;
}

const SEGMENTS: { key: Segment; label: string; hint: string }[] = [
  { key: 'not_started', label: 'Not started', hint: 'Eligible, 0 activities, joined 2+ days ago' },
  { key: 'stopped', label: 'Stopped', hint: 'Did at least 1 activity, nothing in the last 3 days, 7-day check not done' },
  { key: 'd7_due', label: '7-day due', hint: '7-day check due or overdue' },
  { key: 'all_eligible', label: 'All eligible', hint: 'Everyone who passed the screener' },
  { key: 'manual', label: 'Pick by hand', hint: 'Tick names in the list' },
];

const TEMPLATES: { label: string; subject: string; body: string }[] = [
  {
    label: 'Not started',
    subject: 'Your Psycheversity programme is waiting / آپ کا سائیکیورسٹی پروگرام منتظر ہے',
    body:
      'Dear {first_name},\n\nThank you for joining Psycheversity. Your first daily exercise only takes a few minutes. '
      + 'Log in at https://psycheversity.com to start today.\n\n'
      + 'محترم {first_name}،\n\nسائیکیورسٹی میں شامل ہونے کا شکریہ۔ آپ کی پہلی روزانہ مشق صرف چند منٹ لیتی ہے۔ '
      + 'آج ہی شروع کرنے کے لیے https://psycheversity.com پر لاگ ان کریں۔',
  },
  {
    label: 'Stopped',
    subject: 'We miss you at Psycheversity / ہمیں آپ کی کمی محسوس ہو رہی ہے',
    body:
      "Dear {first_name},\n\nWe noticed you haven't done your daily exercise for a few days. Every entry counts. "
      + 'Log in at https://psycheversity.com to continue where you left off.\n\n'
      + 'محترم {first_name}،\n\nہم نے دیکھا کہ آپ نے کچھ دنوں سے اپنی روزانہ مشق نہیں کی۔ ہر اندراج اہم ہے۔ '
      + 'جہاں چھوڑا تھا وہیں سے جاری رکھنے کے لیے https://psycheversity.com پر لاگ ان کریں۔',
  },
  {
    label: '7-day check',
    subject: 'Your 7-day check is ready / آپ کا 7 روزہ جائزہ تیار ہے',
    body:
      'Dear {first_name},\n\nYour 7-day check is now ready. Please log in at https://psycheversity.com to complete it.\n\n'
      + 'محترم {first_name}،\n\nآپ کا 7 روزہ جائزہ اب تیار ہے۔ اسے مکمل کرنے کے لیے براہِ کرم https://psycheversity.com پر لاگ ان کریں۔',
  },
];

const formatDateTime = (value: string) =>
  new Intl.DateTimeFormat('en-GB', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value));

const errorText = (err: any, fallback: string) => {
  const data = err?.response?.data;
  if (!data) return fallback;
  if (typeof data === 'string') return data;
  return data.detail || Object.values(data).flat().join(' ') || fallback;
};

const ManualEmailPanel: React.FC = () => {
  const [segment, setSegment] = useState<Segment>('not_started');
  const [recipients, setRecipients] = useState<Recipient[]>([]);
  const [loadingRecipients, setLoadingRecipients] = useState(false);
  const [picked, setPicked] = useState<Set<number>>(new Set());
  const [search, setSearch] = useState('');
  const [subject, setSubject] = useState('');
  const [body, setBody] = useState('');
  const [busy, setBusy] = useState<'test' | 'send' | null>(null);
  const [notice, setNotice] = useState<{ kind: 'ok' | 'error'; text: string } | null>(null);
  const [history, setHistory] = useState<Campaign[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(false);

  const loadRecipients = useCallback(async (seg: Segment) => {
    setLoadingRecipients(true);
    try {
      const { data } = await api.get('/notifications/admin/manual-email/recipients/', { params: { segment: seg } });
      setRecipients(data.recipients || []);
    } catch (err) {
      setNotice({ kind: 'error', text: errorText(err, 'Could not load the group.') });
      setRecipients([]);
    } finally {
      setLoadingRecipients(false);
    }
  }, []);

  const loadHistory = useCallback(async () => {
    setLoadingHistory(true);
    try {
      const { data } = await api.get('/notifications/admin/manual-email/history/');
      setHistory(data || []);
    } catch {
      /* history is informational; keep the last list */
    } finally {
      setLoadingHistory(false);
    }
  }, []);

  useEffect(() => { loadRecipients(segment); }, [segment, loadRecipients]);
  useEffect(() => { loadHistory(); }, [loadHistory]);

  // While a send is in progress, refresh the history so the sent/failed counts move.
  useEffect(() => {
    if (!history.some(c => c.status !== 'done')) return;
    const timer = window.setTimeout(loadHistory, 10000);
    return () => window.clearTimeout(timer);
  }, [history, loadHistory]);

  const recipientCount = segment === 'manual' ? picked.size : recipients.length;

  const visibleRecipients = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return recipients;
    return recipients.filter(r => r.name.toLowerCase().includes(q) || r.email.toLowerCase().includes(q));
  }, [recipients, search]);

  const togglePick = (id: number) => {
    setPicked(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  };

  const applyTemplate = (index: number) => {
    const tpl = TEMPLATES[index];
    if (!tpl) return;
    if ((subject || body) && !window.confirm('Replace the current subject and message with this template?')) return;
    setSubject(tpl.subject);
    setBody(tpl.body);
  };

  const messageReady = subject.trim().length > 0 && body.trim().length > 0;

  const sendTest = async () => {
    setBusy('test');
    setNotice(null);
    try {
      const { data } = await api.post('/notifications/admin/manual-email/test/', { subject, body });
      setNotice({ kind: 'ok', text: `Test sent to ${data.sent_to}.` });
      loadHistory();
    } catch (err) {
      setNotice({ kind: 'error', text: errorText(err, 'Test email failed.') });
    } finally {
      setBusy(null);
    }
  };

  const send = async () => {
    if (recipientCount === 0) return;
    if (!window.confirm(`Send to ${recipientCount} ${recipientCount === 1 ? 'person' : 'people'}?`)) return;
    setBusy('send');
    setNotice(null);
    try {
      const { data } = await api.post('/notifications/admin/manual-email/send/', {
        segment,
        subject,
        body,
        expected_count: recipientCount,
        user_ids: segment === 'manual' ? Array.from(picked) : undefined,
      });
      setNotice({
        kind: 'ok',
        text: `Sending to ${data.count} ${data.count === 1 ? 'person' : 'people'} (about 20 a minute). Progress shows in the history below.`,
      });
      setPicked(new Set());
      loadHistory();
    } catch (err: any) {
      if (err?.response?.status === 409) loadRecipients(segment);
      setNotice({ kind: 'error', text: errorText(err, 'Sending failed.') });
    } finally {
      setBusy(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* 1. Group */}
      <section className="bg-white border border-zinc-200 rounded-xl shadow-sm p-6 space-y-4">
        <h2 className="text-lg font-bold text-zinc-900">1. Pick a group</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {SEGMENTS.map(s => (
            <label
              key={s.key}
              className={`flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${
                segment === s.key ? 'border-zinc-900 bg-zinc-50' : 'border-zinc-200 hover:border-zinc-400'
              }`}
            >
              <input
                type="radio"
                name="segment"
                className="mt-1"
                checked={segment === s.key}
                onChange={() => { setSegment(s.key); setSearch(''); }}
              />
              <span>
                <span className="block text-sm font-semibold text-zinc-900">{s.label}</span>
                <span className="block text-xs text-zinc-500 mt-0.5">{s.hint}</span>
              </span>
            </label>
          ))}
        </div>

        <div className="flex items-center gap-2 text-sm text-zinc-700">
          <Users size={16} />
          {loadingRecipients ? (
            <span className="flex items-center gap-2"><Loader2 size={14} className="animate-spin" /> Counting…</span>
          ) : (
            <span>
              <strong>{recipientCount}</strong> {recipientCount === 1 ? 'person' : 'people'} will get this email.
              <span className="text-zinc-500"> Disqualified people, staff accounts and anyone who unsubscribed are never included.</span>
            </span>
          )}
        </div>

        {segment === 'manual' && !loadingRecipients && (
          <div className="space-y-2">
            <div className="flex flex-col sm:flex-row gap-2 sm:items-center">
              <input
                type="search"
                value={search}
                onChange={e => setSearch(e.target.value)}
                placeholder="Search name or email"
                className="flex-1 px-3 py-2 border border-zinc-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-zinc-900"
              />
              <button
                type="button"
                onClick={() => setPicked(new Set(visibleRecipients.map(r => r.user_id)))}
                className="px-3 py-2 text-sm font-medium border border-zinc-300 rounded-lg hover:bg-zinc-50"
              >
                Tick all shown
              </button>
              <button
                type="button"
                onClick={() => setPicked(new Set())}
                className="px-3 py-2 text-sm font-medium border border-zinc-300 rounded-lg hover:bg-zinc-50"
              >
                Clear
              </button>
            </div>
            <div className="max-h-72 overflow-y-auto border border-zinc-200 rounded-lg divide-y divide-zinc-100">
              {visibleRecipients.length === 0 ? (
                <p className="p-4 text-sm text-zinc-500">No eligible participants found.</p>
              ) : visibleRecipients.map(r => (
                <label key={r.user_id} className="flex items-center gap-3 px-4 py-2 text-sm cursor-pointer hover:bg-zinc-50">
                  <input type="checkbox" checked={picked.has(r.user_id)} onChange={() => togglePick(r.user_id)} />
                  <span className="font-medium text-zinc-900 truncate">{r.name}</span>
                  <span className="text-zinc-500 truncate">{r.email}</span>
                  <span className="ml-auto text-xs text-zinc-400 shrink-0">joined {formatDateTime(r.joined)}</span>
                </label>
              ))}
            </div>
          </div>
        )}
      </section>

      {/* 2. Message */}
      <section className="bg-white border border-zinc-200 rounded-xl shadow-sm p-6 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <h2 className="text-lg font-bold text-zinc-900">2. Write the message</h2>
          <select
            defaultValue=""
            onChange={e => { applyTemplate(Number(e.target.value)); e.target.value = ''; }}
            className="px-3 py-2 border border-zinc-300 rounded-lg text-sm bg-white"
          >
            <option value="" disabled>Start from a template…</option>
            {TEMPLATES.map((tpl, i) => <option key={tpl.label} value={i}>{tpl.label}</option>)}
          </select>
        </div>
        <div>
          <label htmlFor="manual-subject" className="block text-sm font-semibold text-zinc-700 mb-1">Subject</label>
          <input
            id="manual-subject"
            value={subject}
            maxLength={200}
            onChange={e => setSubject(e.target.value)}
            className="w-full px-3 py-2 border border-zinc-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-zinc-900"
          />
        </div>
        <div>
          <label htmlFor="manual-body" className="block text-sm font-semibold text-zinc-700 mb-1">Message</label>
          <textarea
            id="manual-body"
            dir="auto"
            rows={10}
            value={body}
            onChange={e => setBody(e.target.value)}
            className="w-full px-3 py-2 border border-zinc-300 rounded-lg text-sm leading-relaxed focus:outline-none focus:ring-2 focus:ring-zinc-900"
          />
          <p className="text-xs text-zinc-500 mt-1">
            <code>{'{first_name}'}</code> is replaced with each person's first name. Leave an empty line between paragraphs.
            "Warm regards, Psycheversity Research Team" and an Unsubscribe link are added at the bottom automatically.
          </p>
        </div>
      </section>

      {/* 3. Send */}
      <section className="bg-white border border-zinc-200 rounded-xl shadow-sm p-6 space-y-4">
        <h2 className="text-lg font-bold text-zinc-900">3. Test, then send</h2>
        {notice && (
          <div className={`flex items-start gap-2 p-3 rounded-lg text-sm ${
            notice.kind === 'ok' ? 'bg-emerald-50 text-emerald-800' : 'bg-red-50 text-red-700'
          }`}>
            {notice.kind === 'ok' ? <CheckCircle2 size={16} className="mt-0.5 shrink-0" /> : <AlertCircle size={16} className="mt-0.5 shrink-0" />}
            <span>{notice.text}</span>
          </div>
        )}
        <div className="flex flex-col sm:flex-row gap-3">
          <button
            type="button"
            onClick={sendTest}
            disabled={!messageReady || busy !== null}
            className="flex items-center justify-center gap-2 px-4 py-2.5 border border-zinc-300 rounded-lg text-sm font-semibold hover:bg-zinc-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {busy === 'test' ? <Loader2 size={16} className="animate-spin" /> : <FlaskConical size={16} />}
            Send test to support@psycheversity.com
          </button>
          <button
            type="button"
            onClick={send}
            disabled={!messageReady || busy !== null || recipientCount === 0 || loadingRecipients}
            className="flex items-center justify-center gap-2 px-4 py-2.5 bg-zinc-900 text-white rounded-lg text-sm font-semibold hover:bg-zinc-800 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {busy === 'send' ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
            Send to {recipientCount} {recipientCount === 1 ? 'person' : 'people'}
          </button>
        </div>
      </section>

      {/* History */}
      <section className="bg-white border border-zinc-200 rounded-xl shadow-sm overflow-hidden">
        <div className="flex items-center justify-between p-6 pb-4">
          <h2 className="text-lg font-bold text-zinc-900">Sent history</h2>
          <button
            type="button"
            onClick={loadHistory}
            className="flex items-center gap-1.5 text-sm font-medium text-zinc-600 hover:text-zinc-900"
          >
            <RefreshCw size={14} className={loadingHistory ? 'animate-spin' : ''} /> Refresh
          </button>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-zinc-50 text-zinc-500 text-xs uppercase tracking-wider">
              <tr>
                <th className="px-6 py-3 text-left font-semibold">Date</th>
                <th className="px-6 py-3 text-left font-semibold">Group</th>
                <th className="px-6 py-3 text-left font-semibold">Subject</th>
                <th className="px-6 py-3 text-right font-semibold">Sent</th>
                <th className="px-6 py-3 text-left font-semibold">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-100">
              {history.length === 0 ? (
                <tr><td colSpan={5} className="px-6 py-6 text-center text-zinc-500">Nothing sent yet.</td></tr>
              ) : history.map(c => (
                <tr key={c.id}>
                  <td className="px-6 py-3 whitespace-nowrap text-zinc-700">{formatDateTime(c.created_at)}</td>
                  <td className="px-6 py-3 whitespace-nowrap text-zinc-700">{c.segment_label}</td>
                  <td className="px-6 py-3 max-w-xs truncate text-zinc-900 font-medium" title={c.subject}>{c.subject}</td>
                  <td className="px-6 py-3 text-right whitespace-nowrap text-zinc-700">
                    {c.sent} / {c.recipient_count}
                    {c.failed > 0 && <span className="text-red-600"> ({c.failed} failed)</span>}
                  </td>
                  <td className="px-6 py-3 whitespace-nowrap text-zinc-700 capitalize">
                    {c.status === 'done' ? 'Done' : `${c.status} (${c.pending} left)`}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
};

export default ManualEmailPanel;
