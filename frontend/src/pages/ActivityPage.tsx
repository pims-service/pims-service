import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../services/api';
import { Save, CheckCircle, ArrowLeft, Loader2 } from 'lucide-react';

const ActivityPage: React.FC = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [activity, setActivity] = useState<any>(null);
  const [content, setContent] = useState('');
  const [saving, setSaving] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [lastSaved, setLastSaved] = useState<string | null>(null);

  useEffect(() => {
    // Fetch activity details
    // setActivity(stub)
    const mockActivity = {
      title: 'Daily Paragraph: Future Self',
      description: 'Describe your ideal life 5 years from now in 200-300 words. Focus on your emotions and daily routine.',
      activity_type: 'paragraph'
    };
    setActivity(mockActivity);

    // Autosave interval
    const interval = setInterval(() => {
      if (content.length > 10) handleSave();
    }, 60000); // Every minute
    return () => clearInterval(interval);
  }, [content]);

  const handleSave = async () => {
    setSaving(true);
    // await api.post('/activities/submit/', { activity: id, content, draft: true });
    setLastSaved(new Date().toLocaleTimeString());
    setTimeout(() => setSaving(false), 1000);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await api.post('/activities/submit/', { activity: id, content });
      alert('Activity submitted successfully!');
      navigate('/dashboard');
    } catch (err) {
      alert('Error submitting activity. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      <button 
        onClick={() => navigate('/dashboard')}
        className="flex items-center gap-2 text-slate-400 hover:text-white mb-8 transition-colors"
      >
        <ArrowLeft size={20} /> Back to Dashboard
      </button>

      <div className="glass p-10">
        <header className="mb-10">
          <h1 className="text-3xl font-bold mb-4">{activity?.title}</h1>
          <div className="p-6 bg-slate-900/50 rounded-2xl border border-slate-700 text-slate-300 leading-relaxed">
            {activity?.description}
          </div>
        </header>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-400 flex justify-between">
              Your Submission
              <span className="text-xs">{content.length} characters</span>
            </label>
            <textarea 
              className="w-full h-64 bg-slate-900 border border-slate-700 rounded-2xl p-6 focus:ring-2 focus:ring-indigo-500 outline-none transition-all resize-none text-slate-200"
              placeholder="Start typing your response here..."
              value={content}
              onChange={(e) => setContent(e.target.value)}
              required
            />
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button 
                type="button"
                onClick={handleSave}
                disabled={saving}
                className="flex items-center gap-2 text-slate-400 hover:text-white transition-colors text-sm"
              >
                {saving ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />} 
                {saving ? 'Autosaving...' : lastSaved ? `Last saved at ${lastSaved}` : 'Save Draft'}
              </button>
            </div>
            
            <button 
              type="submit" 
              disabled={submitting || content.length < 50}
              className="btn-premium flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {submitting ? <Loader2 className="animate-spin" /> : <CheckCircle size={20} />} 
              Submit Activity
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ActivityPage;
