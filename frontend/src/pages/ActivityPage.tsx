import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../services/api';
import { Save, CheckCircle, ArrowLeft, Loader2, CheckCircle2 } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { motion } from 'framer-motion';

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

const INTEGRATED_CATEGORY_DETAILS: Record<string, CategoryDetail> = {
  Pleasure: {
    label: { en: 'Pleasure with Gratitude', ur: 'لطف بمعہ شکر گزاری' },
    definition: {
      en: 'An enjoyable moment today that you feel grateful for. Describe what happened, why you are grateful for it, and what or who made it possible.',
      ur: 'آج کا کوئی لطف بھرا لمحہ جس کے لیے آپ شکر گزار ہیں۔ بیان کریں کہ کیا ہوا، آپ اس کے لیے کیوں شکر گزار ہیں، اور کس یا کس چیز نے اسے ممکن بنایا۔'
    },
    example: {
      en: 'Example: My sister made karak chai exactly the way I like it without my asking. I felt grateful because she remembered, and I felt cared for. It happened because she had been paying attention to small details about me lately.',
      ur: "مثال: بہن نے بِنا کہے بالکل ویسی کڑک چائے بنائی جیسی پسند ہے۔ شکر گزاری کا احساس اس لیے ہوا کہ اسے یاد تھا، اور خیال رکھے جانے کا احساس بھی پیدا ہوا۔ یہ اس لیے ہوا کہ وہ پچھلے کچھ عرصے سے چھوٹی چھوٹی باتوں پر دھیان دے رہی تھی۔"
    }
  },
  Engagement: {
    label: { en: 'Engagement with Gratitude', ur: 'مشغولیت بمعہ شکر گزاری' },
    definition: {
      en: 'A moment of deep focus today that you feel grateful for. Describe what you were doing, why you are grateful for it, and what or who made it possible.',
      ur: 'آج کا کوئی گہری مشغولیت کا لمحہ جس کے لیے آپ شکر گزار ہیں۔ بیان کریں کہ آپ کیا کر رہے تھے، اس کے لیے کیوں شکر گزار ہیں، اور کس یا کس چیز نے اسے ممکن بنایا۔'
    },
    example: {
      en: 'Example: I spent forty-five minutes lost in editing my proposal section. I am grateful because focused time has been rare lately. It happened because the house was unusually quiet and my phone was on silent.',
      ur: "مثال: تجویز کے سیکشن کی نوک پلک سنوارنے میں پینتالیس منٹ گزر گئے۔ شکر گزاری کا احساس اس لیے ہوا کہ آج کل توجہ مرکوز کرنے کا وقت کم ہی ملتا ہے۔ یہ اس لیے ممکن ہوا کہ گھر میں غیر معمولی خاموشی تھی اور فون خاموش حالت پر تھا۔"
    }
  },
  Relationships: {
    label: { en: 'Positive Relationships with Gratitude', ur: 'مثبت تعلقات بمعہ شکر گزاری' },
    definition: {
      en: 'A meaningful interaction today that you feel grateful for. Describe what happened, why you are grateful, and what or who made it possible.',
      ur: 'آج کا کوئی بامقصد رابطہ جس کے لیے آپ شکر گزار ہیں۔ بیان کریں کہ کیا ہوا، آپ کیوں شکر گزار ہیں، اور کس یا کس چیز نے اسے ممکن بنایا۔'
    },
    example: {
      en: 'Example: A friend called to check on me out of nowhere. I am grateful because I had been having a low week and did not expect anyone to notice. It happened because she follows my updates and acts on what she sees.',
      ur: "مثال: ایک دوست نے اچانک حال احوال پوچھنے کے لیے فون کیا۔ شکر گزاری کا احساس اس لیے ہوا کہ پچھلا ہفتہ مشکل تھا اور توقع نہ تھی کہ کوئی متوجہ ہو گا۔ یہ اس لیے ہوا کہ وہ اپنے حلقے کی خبر رکھتی ہے اور جو دیکھتی ہے اس پر عمل کرتی ہے۔"
    }
  },
  Meaning: {
    label: { en: 'Meaning with Gratitude', ur: 'مقصد بمعہ شکر گزاری' },
    definition: {
      en: 'Something purposeful you did today that you feel grateful for. Describe what you did, why you are grateful for it, and what or who made it possible.',
      ur: 'آج کوئی بامقصد کام جو آپ نے کیا اور جس کے لیے آپ شکر گزار ہیں۔ بیان کریں کہ آپ نے کیا کیا، اس کے لیے کیوں شکر گزار ہیں، اور کس یا کس چیز نے اسے ممکن بنایا۔'
    },
    example: {
      en: 'Example: I tutored my younger cousin for an hour. I am grateful because helping her felt purposeful at the end of a draining week. It happened because she asked, and because I had the energy to say yes.',
      ur: "مثال: چھوٹی کزن کو ایک گھنٹہ پڑھایا۔ شکر گزاری کا احساس اس لیے ہوا کہ تھکا دینے والے ہفتے کے اختتام پر اس کی مدد کرنا بامقصد لگا۔ یہ اس لیے ہوا کہ اس نے پوچھا، اور اس وقت 'ہاں' کہنے کی توانائی موجود تھی۔"
    }
  },
  Accomplishment: {
    label: { en: 'Accomplishment with Gratitude', ur: 'کامیابی بمعہ شکر گزاری' },
    definition: {
      en: 'Something you did well today that you feel grateful for. Describe what you accomplished, why you are grateful for it, and what or who made it possible.',
      ur: 'آج کوئی ایسا کام جو آپ نے اچھا کیا اور جس کے لیے آپ شکر گزار ہیں۔ بیان کریں کہ آپ نے کیا حاصل کیا، اس کے لیے کیوں شکر گزار ہیں، اور کس یا کس چیز نے اسے ممکن بنایا۔'
    },
    example: {
      en: 'Example: Submitted the section to my supervisor before deadline. I am grateful because I had been worried I would miss it. It happened because I planned the week tightly and a colleague reviewed it for me yesterday.',
      ur: "مثال: وقتِ مقررہ سے پہلے سپروائزر کو سیکشن جمع کروا دیا۔ شکر گزاری کا احساس اس لیے ہوا کہ پہلے یہ اندیشہ تھا کہ ڈیڈ لائن چھوٹ جائے گی۔ یہ اس لیے ممکن ہوا کہ پورے ہفتے کی منصوبہ بندی سخت رکھی گئی اور ایک ساتھی نے کل اسے دیکھ کر مشورہ دیا۔"
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

  const focusTimestampsRef = useRef<Record<number, string | null>>({ 1: null, 2: null, 3: null });
  const durationsRef = useRef<Record<number, number>>({ 1: 0, 2: 0, 3: 0 });
  const activeFocusRef = useRef<number | null>(null);
  const focusStartRef = useRef<number | null>(null);

  const [saving, setSaving] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const handleFocus = (index: number) => {
    if (activity?.submitted_today) return;
    if (!focusTimestampsRef.current[index]) {
      focusTimestampsRef.current[index] = new Date().toISOString();
    }
    activeFocusRef.current = index;
    focusStartRef.current = Date.now();
  };

  const handleBlur = (index: number) => {
    if (activity?.submitted_today) return;
    if (activeFocusRef.current === index && focusStartRef.current !== null) {
      const elapsedMs = Date.now() - focusStartRef.current;
      const elapsedSec = elapsedMs / 1000;
      durationsRef.current[index] += elapsedSec;
      activeFocusRef.current = null;
      focusStartRef.current = null;
    }
  };
  const [lastSaved, setLastSaved] = useState<string | null>(null);
  const [completed, setCompleted] = useState(false);

  const getBilingualText = (content: string) => {
    if (!content) return { en: '', ur: '' };
    const parts = content.split('|').map(s => s.trim());
    return {
      en: parts[0] || content,
      ur: parts[1] || parts[0] || content
    };
  };

  const getEntryLabels = (groupName: string, dayNumber: number): { en: string; ur: string }[] => {
    const isGroup1 = groupName === 'Group 1';
    const isGroup2 = groupName === 'Group 2';
    const isGroup3 = groupName === 'Group 3';
    const isGroup4 = groupName === 'Group 4';

    const toUrduNumerals = (num: number): string => {
      const urduDigits = ['۰', '۱', '۲', '۳', '۴', '۵', '۶', '۷', '۸', '۹'];
      return num.toString().split('').map(d => urduDigits[parseInt(d, 10)] || d).join('');
    };

    if (isGroup3) {
      const day = dayNumber || 1;
      const cats = GROUP_3_SCHEDULE[day] || ['Pleasure', 'Engagement', 'Meaning'];
      return cats.map((cat, idx) => {
        const detail = CATEGORY_DETAILS[cat];
        const urduIdx = toUrduNumerals(idx + 1);
        const enIdx = idx + 1;
        if (!detail) {
          return {
            en: `Entry ${enIdx}`,
            ur: `اندراج ${urduIdx}`
          };
        }
        return {
          en: `Entry ${enIdx}: ${detail.label.en}`,
          ur: `اندراج ${urduIdx}: ${detail.label.ur}`
        };
      });
    }

    if (isGroup4) {
      const day = dayNumber || 1;
      const cats = GROUP_3_SCHEDULE[day] || ['Pleasure', 'Engagement', 'Meaning'];
      return cats.map((cat, idx) => {
        const detail = INTEGRATED_CATEGORY_DETAILS[cat];
        const urduIdx = toUrduNumerals(idx + 1);
        const enIdx = idx + 1;
        if (!detail) {
          return {
            en: `Entry ${enIdx}`,
            ur: `اندراج ${urduIdx}`
          };
        }
        return {
          en: `Entry ${enIdx}: ${detail.label.en}`,
          ur: `اندراج ${urduIdx}: ${detail.label.ur}`
        };
      });
    }

    if (isGroup1) {
      return [
        {
          en: "Entry 1: Memory 1. Describe what you remember.",
          ur: "اندراج ۱: یاد ۱۔ جو یاد ہے اس کی تفصیل بیان کریں۔"
        },
        {
          en: "Entry 2: Memory 2. Describe what you remember.",
          ur: "اندراج ۲: یاد ۲۔ جو یاد ہے اس کی تفصیل بیان کریں۔"
        },
        {
          en: "Entry 3: Memory 3. Describe what you remember.",
          ur: "اندراج ۳: یاد ۳۔ جو یاد ہے اس کی تفصیل بیان کریں۔"
        }
      ];
    }
    if (isGroup2) {
      return [
        {
          en: "Entry 1: Good Thing 1. What happened, who was involved, and why it happened.",
          ur: "اندراج ۱: اچھی بات ۱۔ کیا ہوا، کون شامل تھا، اور یہ کیوں ہوا۔"
        },
        {
          en: "Entry 2: Good Thing 2. What happened, who was involved, and why it happened.",
          ur: "اندراج ۲: اچھی بات ۲۔ کیا ہوا، کون شامل تھا، اور یہ کیوں ہوا۔"
        },
        {
          en: "Entry 3: Good Thing 3. What happened, who was involved, and why it happened.",
          ur: "اندراج ۳: اچھی بات ۳۔ کیا ہوا، کون شامل تھا، اور یہ کیوں ہوا۔"
        }
      ];
    }
    return [
      { en: "Entry 1", ur: "اندراج ۱" },
      { en: "Entry 2", ur: "اندراج ۲" },
      { en: "Entry 3", ur: "اندراج ۳" }
    ];
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

    if (activeFocusRef.current !== null) {
      handleBlur(activeFocusRef.current);
    }

    setSubmitting(true);
    
    const nowIso = new Date().toISOString();
    const entry1SubmitTs = entry1 ? nowIso : null;
    const entry2SubmitTs = entry2 ? nowIso : null;
    const entry3SubmitTs = entry3 ? nowIso : null;

    const entry1FocusTs = entry1 ? (focusTimestampsRef.current[1] || nowIso) : null;
    const entry2FocusTs = entry2 ? (focusTimestampsRef.current[2] || nowIso) : null;
    const entry3FocusTs = entry3 ? (focusTimestampsRef.current[3] || nowIso) : null;

    const entry1Duration = entry1 ? Math.round(durationsRef.current[1]) : 0;
    const entry2Duration = entry2 ? Math.round(durationsRef.current[2]) : 0;
    const entry3Duration = entry3 ? Math.round(durationsRef.current[3]) : 0;

    try {
      await api.post('/activities/daily/submit/', {
        activity: activity?.id,
        entry_1: entry1,
        entry_2: entry2,
        entry_3: entry3,
        entry_1_focus_ts: entry1FocusTs,
        entry_2_focus_ts: entry2FocusTs,
        entry_3_focus_ts: entry3FocusTs,
        entry_1_submit_ts: entry1SubmitTs,
        entry_2_submit_ts: entry2SubmitTs,
        entry_3_submit_ts: entry3SubmitTs,
        entry_1_duration_sec: entry1Duration,
        entry_2_duration_sec: entry2Duration,
        entry_3_duration_sec: entry3Duration,
      });
      
      // Clear draft on successful submission
      localStorage.removeItem(`activity_draft_${id}`);
      setCompleted(true);

      const isDay7 = activity?.day_number === 7 || activity?.current_day === 7;

      if (isDay7) {
        const fetchProfileAndRedirect = async (retries = 3, delay = 500) => {
          try {
            const profileRes = await api.get('/users/profile/');
            const dueMilestone = profileRes.data?.due_milestone;
            if (dueMilestone && dueMilestone !== 'SIGNUP') {
              localStorage.setItem('due_milestone', dueMilestone);
              const { questionnairesApi } = await import('../services/api');
              const questionnaires = await questionnairesApi.list();
              const qList = Array.isArray(questionnaires.data) ? questionnaires.data : questionnaires.data?.results || [];
              const battery = qList.find((q: any) => q.is_active && q.assessment_type === 'PSYCHOMETRIC');
              if (battery) {
                setTimeout(() => {
                  setCompleted(false);
                  navigate(`/questionnaire/${battery.id}?milestone=${dueMilestone}`, { replace: true });
                }, 1000);
                return;
              }
            }
            if (retries > 0) {
              setTimeout(() => {
                fetchProfileAndRedirect(retries - 1, delay * 2);
              }, delay);
            } else {
              setTimeout(() => {
                setCompleted(false);
                navigate('/dashboard', { replace: true });
              }, 1000);
            }
          } catch (err) {
            if (retries > 0) {
              setTimeout(() => {
                fetchProfileAndRedirect(retries - 1, delay * 2);
              }, delay);
            } else {
              setTimeout(() => {
                setCompleted(false);
                navigate('/dashboard', { replace: true });
              }, 1000);
            }
          }
        };
        fetchProfileAndRedirect();
      } else {
        setTimeout(() => {
          setCompleted(false);
          navigate('/dashboard');
        }, 1000);
      }
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Error submitting activity. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const isLocked = activity?.submitted_today;
  const bilingualDesc = getBilingualText(activity?.description);
  const currentDesc = i18n.language === 'ur' ? bilingualDesc.ur : bilingualDesc.en;
  const labels = getEntryLabels(activity?.group_name, activity?.day_number);

  const w1 = countWords(entry1);
  const w2 = countWords(entry2);
  const w3 = countWords(entry3);

  const isValidCount = (w: number) => w >= 20 && w <= 200;
  const canSubmit = !isLocked && isValidCount(w1) && isValidCount(w2) && isValidCount(w3);

  const renderTextarea = (index: number, value: string, count: number, label: { en: string; ur: string }) => {
    const isWarning = count >= 180 && count <= 200;
    const isError = count > 200;
    const isBelowMin = count > 0 && count < 20;

    // Retrieve category details if Group 3 or Group 4
    let categoryDetail = null;
    if (activity?.group_name === 'Group 3') {
      const dayNum = activity?.day_number || 1;
      const cats = GROUP_3_SCHEDULE[dayNum] || [];
      const cat = cats[index - 1];
      if (cat) {
        categoryDetail = CATEGORY_DETAILS[cat];
      }
    } else if (activity?.group_name === 'Group 4') {
      const dayNum = activity?.day_number || 1;
      const cats = GROUP_3_SCHEDULE[dayNum] || [];
      const cat = cats[index - 1];
      if (cat) {
        categoryDetail = INTEGRATED_CATEGORY_DETAILS[cat];
      }
    }

    return (
      <div className="space-y-2" key={index}>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 items-start mb-1">
          <span className="text-sm font-semibold text-zinc-700 font-latin text-left">
            {label.en}
          </span>
          <span className="text-base font-semibold text-zinc-800 font-urdu text-right" dir="rtl">
            {label.ur}
          </span>
        </div>

        {categoryDetail && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 bg-zinc-50/50 rounded-xl p-4 border border-zinc-300 text-xs text-zinc-600 mt-1 mb-2">
            <div className="space-y-1 font-latin">
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
            placeholder="Reflect and write here... / یہاں لکھنا شروع کریں..."
            value={value}
            onChange={(e) => handleEntryChange(index, e.target.value)}
            onFocus={() => handleFocus(index)}
            onBlur={() => handleBlur(index)}
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

  if (completed) {
    return (
      <div className="max-w-md mx-auto py-24 px-4 text-center space-y-8">
        <motion.div
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ type: 'spring', damping: 12 }}
          className="w-20 h-20 bg-zinc-800 rounded-xl flex items-center justify-center mx-auto shadow-lg"
        >
          <CheckCircle2 className="w-12 h-12 text-white" />
        </motion.div>

        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.2 }}
          className="space-y-4"
        >
          <h2 className="text-3xl font-bold text-zinc-900">Activity Finalized</h2>
          <p className="text-zinc-500 text-sm max-w-xs mx-auto">
            Reflection submission complete. Synchronizing results with research matrix.
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="flex items-center justify-center gap-2 text-zinc-500 text-xs font-medium"
        >
          <Loader2 className="w-4 h-4 animate-spin" />
          Synchronizing Environment
        </motion.div>
      </div>
    );
  }

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
              <div className="font-latin">{bilingualDesc.en}</div>
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
