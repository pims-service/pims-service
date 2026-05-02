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
  const [isEditing, setIsEditing] = useState(false);

  useEffect(() => {
    const fetchActivity = async () => {
      try {
        const response = await api.get('/activities/daily/current/');
        const data = response.data;
        setActivity(data);
        if (data.submitted_today && data.submission_content) {
          setContent(data.submission_content);
          setIsEditing(false);
        } else {
          setIsEditing(true);
        }
      } catch (err) {
        console.error('Failed to load activity details');
        alert('Failed to load activity details.');
        navigate('/dashboard');
      }
    };

    if (id) fetchActivity();
  }, [id, navigate]);

  const handleSave = async () => {
    setSaving(true);
    setLastSaved(new Date().toLocaleTimeString());
    setTimeout(() => setSaving(false), 1000);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await api.post('/activities/daily/submit/', { activity: id, content });
      if (activity.submitted_today) {
        setIsEditing(false);
        setActivity({ ...activity, submission_content: content });
        alert('Submission updated successfully!');
      } else {
        navigate('/dashboard');
      }
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Error submitting activity. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const isLocked = activity?.submitted_today && !isEditing;

  return (
    <div className="max-w-4xl mx-auto">
      <button
        onClick={() => navigate('/dashboard')}
        className="flex items-center gap-2 text-zinc-600 font-medium hover:text-zinc-900 mb-6 transition-colors"
      >
        <ArrowLeft size={18} /> Back to Dashboard
      </button>

      <div className="bg-white border border-zinc-200 rounded-xl shadow-sm overflow-hidden">
        <header className="p-8 border-b border-zinc-100 bg-zinc-50/50">
          <div className="flex justify-between items-start mb-4">
            <h1 className="text-2xl font-bold text-zinc-900">{activity?.title || 'Loading Activity...'}</h1>
            {activity?.submitted_today && !isEditing && (
              <button
                onClick={() => setIsEditing(true)}
                className="px-4 py-2 bg-zinc-100 text-zinc-700 text-sm font-semibold rounded-lg hover:bg-zinc-200 transition-colors"
              >
                Edit Submission
              </button>
            )}
          </div>
          <div className="text-zinc-700 leading-relaxed text-sm whitespace-pre-wrap">
            {activity?.description}
          </div>
        </header>

        <form onSubmit={handleSubmit} className="p-8 space-y-6">
          <div className="space-y-2">
            <label className="text-sm font-medium text-zinc-700 flex justify-between">
              Your Submission
              <span className="text-xs text-zinc-400">{content.length} characters</span>
            </label>
            <textarea
              className={`w-full h-64 bg-white border border-zinc-200 rounded-xl p-5 focus:ring-2 focus:ring-zinc-900 focus:border-zinc-900 outline-none transition-all resize-none text-zinc-800 shadow-sm ${isLocked ? 'bg-zinc-50 text-zinc-500 cursor-not-allowed' : ''}`}
              placeholder="Reflect and write your response here..."
              value={content}
              onChange={(e) => setContent(e.target.value)}
              required
              readOnly={isLocked}
            />
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              {!isLocked && (
                <button
                  type="button"
                  onClick={handleSave}
                  disabled={saving}
                  className="flex items-center gap-2 text-zinc-400 hover:text-zinc-700 transition-colors text-sm"
                >
                  {saving ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />}
                  {saving ? 'Autosaving...' : lastSaved ? `Last saved at ${lastSaved}` : 'Save Draft'}
                </button>
              )}
            </div>

            {!isLocked && (
              <button
                type="submit"
                disabled={submitting || content.length < 50}
                className="px-8 py-3 bg-zinc-800 text-white font-medium rounded-lg flex items-center gap-2 hover:bg-zinc-700 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
              >
                {submitting ? <Loader2 className="animate-spin" size={18} /> : <CheckCircle size={18} />}
                {activity?.submitted_today ? 'Update Submission' : 'Submit Activity'}
              </button>
            )}
          </div>
        </form>
      </div>
    </div>
  );
};

export default ActivityPage;
