import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../services/api';
import { Save, CheckCircle, ArrowLeft, Loader2 } from 'lucide-react';
import { useTranslation } from 'react-i18next';

const GROUP_3_SCHEDULE: Record<number, string[]> = {
  1: ['Pleasure', 'Engagement', 'Meaning'],
  2: ['Relationships', 'Accomplishment', 'Pleasure'],
  3: ['Engagement', 'Meaning', 'Accomplishment'],
  4: ['Pleasure', 'Relationships', 'Meaning'],
  5: ['Engagement', 'Accomplishment', 'Relationships'],
  6: ['Meaning', 'Pleasure', 'Accomplishment'],
  7: ['Relationships', 'Engagement', 'Pleasure']
};

interface CategoryDetail {
  label: { en: string; ur: string };
  definition: { en: string; ur: string };
  example: { en: string; ur: string };
}

const CATEGORY_DETAILS: Record<string, CategoryDetail> = {
  Pleasure: {
    label: { en: 'Pleasure', ur: 'لطف' },
    definition: {
      en: 'A moment of enjoyment, comfort, or fun today.',
      ur: 'آج کا کوئی لمحہ جس میں لطف، سکون، یا تفریح محسوس ہوئی ہو۔'
    },
    example: {
      en: 'Example: Sipping chai on the balcony at sunrise. The weather was cool and quiet, and I had ten minutes of stillness before the day started.',
      ur: 'مثال: طلوعِ آفتاب کے وقت بالکونی میں چائے کی چسکیاں۔ موسم ٹھنڈا اور پُرسکون تھا، اور دن شروع ہونے سے پہلے دس منٹ کا سکون میسر تھا۔'
    }
  },
  Engagement: {
    label: { en: 'Engagement', ur: 'مشغولیت' },
    definition: {
      en: 'A moment today when you were so absorbed in something that time seemed to disappear.',
      ur: 'آج کا کوئی لمحہ جب آپ کسی کام میں اس قدر مگن تھے کہ وقت کا احساس نہ رہا۔'
    },
    example: {
      en: 'Example: Reading a novel after Maghrib. What felt like twenty minutes was nearly an hour. The story pulled me in completely.',
      ur: 'مثال: مغرب کے بعد ناول کا مطالعہ۔ جو وقت بیس منٹ کا لگا، وہ تقریباً ایک گھنٹہ نکلا۔ کہانی میں ایسی کشش تھی کہ توجہ مکمل طور پر اسی پر مرکوز رہی۔'
    }
  },
  Relationships: {
    label: { en: 'Positive Relationships', ur: 'مثبت تعلقات' },
    definition: {
      en: 'A meaningful interaction today with another person.',
      ur: 'آج کسی دوسرے فرد کے ساتھ کوئی بامقصد ملاقات یا رابطہ۔'
    },
    example: {
      en: 'Example: My neighbour saw me carrying shopping bags upstairs and silently took two from me. It mattered because I did not have to ask.',
      ur: 'مثال: پڑوسی نے سیڑھیوں پر سامان لے جاتے دیکھا اور خاموشی سے دو تھیلے ہاتھ سے لے لیے۔ یہ بات اس لیے اہم تھی کہ مانگنے کی ضرورت نہ پڑی۔'
    }
  },
  Meaning: {
    label: { en: 'Meaning', ur: 'مقصد' },
    definition: {
      en: 'Something you did today that felt purposeful or significant.',
      ur: 'آج کوئی ایسا کام جو بامقصد یا اہم محسوس ہوا ہو۔'
    },
    example: {
      en: 'Example: Helped my mother sort her medications for the week. She has trouble with the dosing schedule, and she relied on me to get it right.',
      ur: 'مثال: امی کی ہفتے بھر کی دوائیاں ترتیب دینے میں مدد کی۔ انہیں دوا کے اوقات یاد رکھنے میں دشواری ہوتی ہے، اور درست ترتیب کے لیے ان کا بھروسہ تھا۔'
    }
  },
  Accomplishment: {
    label: { en: 'Accomplishment', ur: 'کامیابی' },
    definition: {
      en: 'Something today that gave you a sense of doing well.',
      ur: 'آج کا کوئی کام جس نے اچھا کرنے کا احساس دلایا ہو۔'
    },
    example: {
      en: 'Example: Finished the proposal section I had been stuck on for three days. It is not perfect but it is done.',
      ur: 'مثال: تجویز کا وہ حصہ مکمل ہو گیا جس پر تین دن سے کام رکا ہوا تھا۔ یہ کامل نہیں ہے، مگر مکمل ہے۔'
    }
  }
};

const ActivityPage: React.FC = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { i18n, t } = useTranslation();

  const saveTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    return () => {
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current);
      }
    };
  }, []);

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

  const getEntryLabels = (groupName: string, dayNumber: number, lang: string) => {
    const isGroup1 = groupName === 'Group 1';
    const isGroup2 = groupName === 'Group 2';
    const isGroup3 = groupName === 'Group 3';

    if (isGroup3) {
      const day = dayNumber || 1;
      const cats = GROUP_3_SCHEDULE[day] || ['Pleasure', 'Engagement', 'Meaning'];
      return cats.map((cat, idx) => {
        const detail = CATEGORY_DETAILS[cat];
        if (!detail) return lang === 'ur' ? `اندراج ${idx + 1}` : `Entry ${idx + 1}`;
        if (lang === 'ur') {
          return `اندراج ${idx + 1}: ${detail.label.ur}`;
        }
        return `Entry ${idx + 1}: ${detail.label.en}`;
      });
    }

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

    if (saveTimeoutRef.current) {
      clearTimeout(saveTimeoutRef.current);
    }

    // Simulate short save status toggle
    saveTimeoutRef.current = setTimeout(() => setSaving(false), 500);
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
  const labels = getEntryLabels(activity?.group_name, activity?.day_number, i18n.language);

  const w1 = countWords(entry1);
  const w2 = countWords(entry2);
  const w3 = countWords(entry3);

  const isValidCount = (w: number) => w >= 20 && w <= 200;
  const canSubmit = !isLocked && isValidCount(w1) && isValidCount(w2) && isValidCount(w3);

  const renderTextarea = (index: number, value: string, count: number, label: string) => {
    const isWarning = count >= 180 && count <= 200;
    const isError = count > 200;
    const isBelowMin = count > 0 && count < 20;

    // Retrieve category details if Group 3
    let categoryDetail = null;
    if (activity?.group_name === 'Group 3') {
      const dayNum = activity?.day_number || 1;
      const cats = GROUP_3_SCHEDULE[dayNum] || [];
      const cat = cats[index - 1];
      if (cat) {
        categoryDetail = CATEGORY_DETAILS[cat];
      }
    }

    return (
      <div className="space-y-2" key={index}>
        <label className="text-sm font-medium text-zinc-700 block">
          {label}
        </label>

        {categoryDetail && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 bg-zinc-50/50 rounded-xl p-4 border border-zinc-300 text-xs text-zinc-600 mt-1 mb-2">
            <div className="space-y-1">
              <p className="font-bold text-zinc-800 text-sm">{categoryDetail.label.en}</p>
              <p className="italic">{categoryDetail.definition.en}</p>
              <p className="text-zinc-500 font-medium">{categoryDetail.example.en}</p>
            </div>
            <div className="space-y-1 text-right font-urdu" dir="rtl">
              <p className="font-bold text-zinc-800 text-base">{categoryDetail.label.ur}</p>
              <p className="italic text-sm">{categoryDetail.definition.ur}</p>
              <p className="text-zinc-500 font-medium text-sm">{categoryDetail.example.ur}</p>
            </div>
          </div>
        )}

        <div className="relative w-full">
          <textarea
            className={`w-full h-40 bg-white border border-zinc-300 rounded-xl p-4 pb-12 focus:ring-2 focus:ring-zinc-900 focus:border-zinc-900 outline-none transition-all resize-none text-zinc-800 shadow-sm ${isLocked ? 'bg-zinc-50 text-zinc-500 cursor-not-allowed' : ''}`}
            placeholder={i18n.language === 'ur' ? "یہاں لکھنا شروع کریں..." : "Reflect and write here..."}
            value={value}
            onChange={(e) => handleEntryChange(index, e.target.value)}
            required
            readOnly={isLocked}
          />
          <div className={`absolute bottom-3 right-4 text-xs font-semibold px-2 py-1 rounded bg-zinc-100/80 backdrop-blur-sm pointer-events-none select-none border border-zinc-200 ${isError ? 'text-red-500 border-red-200 bg-red-50/80' : isWarning ? 'text-amber-500 border-amber-200 bg-amber-50/80' : 'text-zinc-500'}`}>
            {count} / 200 {t('dashboard.words', 'words')}
          </div>
        </div>
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
          {bilingualDesc.ur && bilingualDesc.ur !== bilingualDesc.en ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-zinc-700 leading-relaxed text-sm font-medium">
              <div>{bilingualDesc.en}</div>
              <div className="text-right font-urdu" dir="rtl">{bilingualDesc.ur}</div>
            </div>
          ) : (
            <div className="text-zinc-700 leading-relaxed text-sm whitespace-pre-wrap font-medium">
              {currentDesc}
            </div>
          )}
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
