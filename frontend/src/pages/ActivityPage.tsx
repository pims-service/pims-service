import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../services/api';
import { Save, CheckCircle, ArrowLeft, Loader2 } from 'lucide-react';
import { useTranslation } from 'react-i18next';

const ActivityPage: React.FC = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { i18n, t } = useTranslation();

  const [activity, setActivity] = useState<any>(null);
  const [entry1, setEntry1] = useState('');
  const [entry2, setEntry2] = useState('');
  const [entry3, setEntry3] = useState('');

  const [saving, setSaving] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [lastSaved, setLastSaved] = useState<string | null>(null);

  const getBilingualText = (content: string) => {
    if (!content) return { en: '', ur: '' };
    const parts = content.split('|').map(s => s.trim());
    return {
      en: parts[0] || content,
      ur: parts[1] || parts[0] || content
    };
  };

  const getEntryLabels = (groupName: string, lang: string) => {
    const isGroup1 = groupName === 'Group 1';
    const isGroup2 = groupName === 'Group 2';

    if (lang === 'ur') {
      if (isGroup1) {
        return [
          "اندراج 1: یاد 1۔ جو یاد ہے اس کی تفصیل بیان کریں۔",
          "اندراج 2: یاد 2۔ جو یاد ہے اس کی تفصیل بیان کریں۔",
          "اندراج 3: یاد 3۔ جو یاد ہے اس کی تفصیل بیان کریں۔"
        ];
      }
      if (isGroup2) {
        return [
          "اندراج 1: اچھی بات 1۔ کیا ہوا، کون شامل تھا، اور یہ کیوں ہوا۔",
          "اندراج 2: اچھی بات 2۔ کیا ہوا، کون شامل تھا، اور یہ کیوں ہوا۔",
          "اندراج 3: اچھی بات 3۔ کیا ہوا، کون شامل تھا، اور یہ کیوں ہوا۔"
        ];
      }
      return ["اندراج 1", "اندراج 2", "اندراج 3"];
    }

    if (isGroup1) {
      return [
        "Entry 1: Memory 1. Describe what you remember.",
        "Entry 2: Memory 2. Describe what you remember.",
        "Entry 3: Memory 3. Describe what you remember."
      ];
    }
    if (isGroup2) {
      return [
        "Entry 1: Good Thing 1. What happened, who was involved, and why it happened.",
        "Entry 2: Good Thing 2. What happened, who was involved, and why it happened.",
        "Entry 3: Good Thing 3. What happened, who was involved, and why it happened."
      ];
    }
    return ["Entry 1", "Entry 2", "Entry 3"];
  };

  const countWords = (text: string): number => {
    if (!text) return 0;
    const clean = text.trim();
    if (clean === '') return 0;
    return clean.split(/\s+/).length;
  };

  useEffect(() => {
    const fetchActivity = async () => {
      try {
        const response = await api.get('/activities/daily/current/');
        const data = response.data;
        setActivity(data);

        if (data.submitted_today) {
          if (data.entry_1 || data.entry_2 || data.entry_3) {
            setEntry1(data.entry_1 || '');
            setEntry2(data.entry_2 || '');
            setEntry3(data.entry_3 || '');
          } else if (data.submission_content) {
            const parts = data.submission_content.split('\n\n---\n\n');
            setEntry1(parts[0] || '');
            setEntry2(parts[1] || '');
            setEntry3(parts[2] || '');
          }
        } else {
          // Attempt to load from localStorage drafts
          const draftStr = localStorage.getItem(`activity_draft_${id}`);
          if (draftStr) {
            try {
              const draft = JSON.parse(draftStr);
              setEntry1(draft.entry1 || '');
              setEntry2(draft.entry2 || '');
              setEntry3(draft.entry3 || '');
              setLastSaved(draft.timestamp || null);
            } catch (e) {
              console.error('Failed to parse draft from localStorage', e);
            }
          }
        }
      } catch (err) {
        console.error('Failed to load activity details');
        alert('Failed to load activity details.');
        navigate('/dashboard');
      }
    };

    if (id) fetchActivity();
  }, [id, navigate]);

  const handleEntryChange = (index: number, val: string) => {
    let e1 = entry1;
    let e2 = entry2;
    let e3 = entry3;

    if (index === 1) {
      setEntry1(val);
      e1 = val;
    } else if (index === 2) {
      setEntry2(val);
      e2 = val;
    } else if (index === 3) {
      setEntry3(val);
      e3 = val;
    }

    setSaving(true);
    const timestamp = new Date().toLocaleTimeString();
    setLastSaved(timestamp);

    const draft = {
      entry1: e1,
      entry2: e2,
      entry3: e3,
      timestamp
    };
    localStorage.setItem(`activity_draft_${id}`, JSON.stringify(draft));

    // Simulate short save status toggle
    setTimeout(() => setSaving(false), 500);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!canSubmit) return;

    setSubmitting(true);
    try {
      await api.post('/activities/daily/submit/', {
        activity: activity?.id,
        entry_1: entry1,
        entry_2: entry2,
        entry_3: entry3
      });
      
      // Clear draft on successful submission
      localStorage.removeItem(`activity_draft_${id}`);
      navigate('/dashboard');
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Error submitting activity. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const isLocked = activity?.submitted_today;
  const bilingualDesc = getBilingualText(activity?.description);
  const currentDesc = i18n.language === 'ur' ? bilingualDesc.ur : bilingualDesc.en;
  const labels = getEntryLabels(activity?.group_name, i18n.language);

  const w1 = countWords(entry1);
  const w2 = countWords(entry2);
  const w3 = countWords(entry3);

  const isValidCount = (w: number) => w >= 20 && w <= 200;
  const canSubmit = !isLocked && isValidCount(w1) && isValidCount(w2) && isValidCount(w3);

  const renderTextarea = (index: number, value: string, count: number, label: string) => {
    const isWarning = count >= 180 && count <= 200;
    const isError = count > 200;
    const isBelowMin = count > 0 && count < 20;

    return (
      <div className="space-y-2" key={index}>
        <label className="text-sm font-medium text-zinc-700 flex justify-between">
          <span>{label}</span>
          <span className={`text-xs font-semibold ${isError ? 'text-red-500' : isWarning ? 'text-amber-500' : 'text-zinc-400'}`}>
            {count} / 200 {t('dashboard.words', 'words')}
          </span>
        </label>
        <textarea
          className={`w-full h-40 bg-white border border-zinc-200 rounded-xl p-4 focus:ring-2 focus:ring-zinc-900 focus:border-zinc-900 outline-none transition-all resize-none text-zinc-800 shadow-sm ${isLocked ? 'bg-zinc-50 text-zinc-500 cursor-not-allowed' : ''}`}
          placeholder={i18n.language === 'ur' ? "یہاں لکھنا شروع کریں..." : "Reflect and write here..."}
          value={value}
          onChange={(e) => handleEntryChange(index, e.target.value)}
          required
          readOnly={isLocked}
        />
        <div className="flex justify-between items-center px-1">
          {isBelowMin && (
            <p className="text-xs text-amber-600 font-medium">
              {i18n.language === 'ur' ? "کم از کم 20 الفاظ درکار ہیں۔" : "Minimum 20 words required."}
            </p>
          )}
          {isWarning && (
            <p className="text-xs text-amber-500 font-medium animate-pulse">
              {i18n.language === 'ur' ? "انتباہ: 200 الفاظ کی حد کے قریب۔" : "Warning: Approaching 200-word limit."}
            </p>
          )}
          {isError && (
            <p className="text-xs text-red-500 font-semibold">
              {i18n.language === 'ur' ? "خرابی: 200 الفاظ کی حد سے تجاوز۔" : "Error: Maximum 200 words exceeded."}
            </p>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="max-w-4xl mx-auto py-6">
      <button
        onClick={() => navigate('/dashboard')}
        className="flex items-center gap-2 text-zinc-600 font-medium hover:text-zinc-900 mb-6 transition-colors"
      >
        <ArrowLeft size={18} /> {t('common.back', 'Back to Dashboard')}
      </button>

      <div className="bg-white border border-zinc-200 rounded-xl shadow-sm overflow-hidden">
        <header className="p-8 border-b border-zinc-100 bg-zinc-50/50">
          <div className="flex justify-between items-start mb-4">
            <h1 className="text-2xl font-bold text-zinc-900">{activity?.title || 'Loading Activity...'}</h1>
          </div>
          <div className="text-zinc-700 leading-relaxed text-sm whitespace-pre-wrap font-medium">
            {currentDesc}
          </div>
        </header>

        <form onSubmit={handleSubmit} className="p-8 space-y-6">
          {renderTextarea(1, entry1, w1, labels[0])}
          {renderTextarea(2, entry2, w2, labels[1])}
          {renderTextarea(3, entry3, w3, labels[2])}

          <div className="flex items-center justify-between pt-4 border-t border-zinc-100">
            <div className="flex items-center gap-4">
              {!isLocked && (
                <span className="flex items-center gap-2 text-zinc-400 text-sm">
                  {saving ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />}
                  {saving ? 'Autosaving...' : lastSaved ? `Draft auto-saved at ${lastSaved}` : 'Draft autosave active'}
                </span>
              )}
            </div>

            {!isLocked && (
              <button
                type="submit"
                disabled={submitting || !canSubmit}
                className="px-8 py-3 bg-zinc-800 text-white font-medium rounded-lg flex items-center gap-2 hover:bg-zinc-700 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
              >
                {submitting ? <Loader2 className="animate-spin" size={18} /> : <CheckCircle size={18} />}
                {t('dashboard.submit_activity', 'Submit Activity')}
              </button>
            )}
            
            {isLocked && (
              <div className="w-full text-center py-2 bg-zinc-50 text-zinc-500 rounded-lg text-sm font-semibold border border-zinc-200">
                {t('dashboard.submitted_locked', 'Daily activity submitted and locked.')}
              </div>
            )}
          </div>
        </form>
      </div>
    </div>
  );
};

export default ActivityPage;
