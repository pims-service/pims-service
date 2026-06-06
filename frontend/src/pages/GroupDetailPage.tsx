import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  Users, 
  RotateCw, 
  AlertTriangle, 
  CheckCircle2, 
  Clock, 
  Edit3, 
  Save, 
  X,
  ArrowLeft
} from 'lucide-react';
import { getGroupDetail, updateGroup } from '../services/api';

interface Participant {
  user_id: number;
  full_name: string;
  username: string;
  submission_count: number;
  has_completed_sociodemographic: boolean;
  current_experiment_day: number | null;
  is_disqualified: boolean;
}

interface Group {
  group_id: number;
  name: string;
  description: string;
  member_count: number;
  created_at: string;
  participants: Participant[];
}

const GroupDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  
  const [group, setGroup] = useState<Group | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  const [isEditing, setIsEditing] = useState(false);
  const [editForm, setEditForm] = useState({ name: '', description: '' });

  const fetchDetail = async () => {
    if (!id) return;
    setLoading(true);
    try {
      const response = await getGroupDetail(parseInt(id));
      setGroup(response.data);
      setEditForm({ 
        name: response.data.name, 
        description: response.data.description || '' 
      });
      setError(null);
    } catch (err) {
      console.error('Failed to fetch group detail', err);
      setError('Failed to load group details. Please verify backend connectivity.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDetail();
  }, [id]);

  const handleUpdate = async () => {
    if (!id || !group) return;
    try {
      await updateGroup(parseInt(id), editForm);
      setGroup({ ...group, ...editForm });
      setIsEditing(false);
      setError(null);
    } catch (err) {
      console.error('Failed to update group', err);
      setError('Failed to save changes. Please try again.');
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
        <RotateCw className="w-8 h-8 text-zinc-400 animate-spin" />
        <p className="text-zinc-500 font-medium text-sm">Syncing Research Roster...</p>
      </div>
    );
  }

  if (error || !group) {
    return (
      <div className="border border-zinc-200 rounded-xl p-12 text-center space-y-4 max-w-2xl mx-auto bg-white shadow-sm mt-20">
        <AlertTriangle className="w-10 h-10 text-zinc-400 mx-auto" />
        <h2 className="text-lg font-semibold text-zinc-800">Roster Access Failure</h2>
        <p className="text-zinc-500 text-sm">{error || 'Group not found.'}</p>
        <button onClick={() => navigate('/admin/groups')} className="px-6 py-2.5 bg-zinc-800 text-white rounded-lg font-medium text-sm hover:bg-zinc-700 transition-colors">Return to Groups</button>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-in fade-in duration-700 pt-0">
      <button 
        onClick={() => navigate('/admin/groups')}
        className="inline-flex items-center gap-2 text-zinc-500 hover:text-zinc-900 transition-colors text-sm font-medium"
      >
        <ArrowLeft size={16} /> Back to Groups
      </button>

      <header className="flex flex-col md:flex-row md:items-end justify-between gap-6 border-b border-zinc-200 pb-8">
        <div className="space-y-3 flex-grow max-w-2xl">
          <div className="flex items-center gap-2 text-zinc-500 text-xs font-medium mb-1">
            <Users size={14} /> Group Command Center
          </div>
          
          {isEditing ? (
            <div className="space-y-4">
              <input 
                value={editForm.name}
                onChange={(e) => setEditForm({...editForm, name: e.target.value})}
                className="text-3xl font-bold bg-transparent border-b-2 border-zinc-900 outline-none w-full text-zinc-900"
              />
              <textarea 
                value={editForm.description}
                onChange={(e) => setEditForm({...editForm, description: e.target.value})}
                className="text-zinc-500 bg-transparent border-b border-zinc-200 outline-none w-full h-10 resize-none text-sm font-medium mt-1"
              />
            </div>
          ) : (
            <div>
              <h1 className="text-4xl font-bold text-zinc-900 tracking-tight">{group.name}</h1>
              <p className="text-zinc-500 font-medium text-sm mt-2">{group.description || 'No description provided.'}</p>
            </div>
          )}

          {/* Meta chips */}
          <div className="flex items-center gap-3 pt-1">
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-zinc-100 rounded-md text-xs font-medium text-zinc-600">
              <Users size={11} /> {group.member_count} members
            </span>
            <span className="text-[11px] text-zinc-400">Created {new Date(group.created_at).toLocaleDateString()}</span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {isEditing ? (
            <div className="flex gap-2">
              <button 
                onClick={handleUpdate}
                className="px-6 py-2.5 bg-zinc-800 text-white rounded-lg font-medium text-sm hover:bg-zinc-700 transition-colors flex items-center gap-2"
              >
                <Save size={16} /> Save Changes
              </button>
              <button 
                onClick={() => setIsEditing(false)}
                className="p-2.5 bg-zinc-100 text-zinc-500 rounded-lg hover:bg-zinc-200 transition-colors"
              >
                <X size={20} />
              </button>
            </div>
          ) : (
            <div className="flex gap-3">
              <button 
                onClick={() => setIsEditing(true)}
                className="px-5 py-2.5 bg-white border border-zinc-200 text-zinc-700 rounded-lg font-medium text-sm hover:border-zinc-300 hover:bg-zinc-50 transition-all flex items-center gap-2"
              >
                <Edit3 size={16} /> Edit
              </button>
            </div>
          )}
        </div>
      </header>

      <div>
          <div className="bg-white border border-zinc-200 rounded-xl overflow-hidden shadow-sm">
            <div className="px-6 py-4 border-b border-zinc-100 bg-zinc-50/50 flex items-center justify-between">
               <h2 className="text-sm font-bold text-zinc-800 uppercase tracking-wider">Participant Roster</h2>
               <div className="flex items-center gap-2 text-xs text-zinc-500 font-medium">
                 <CheckCircle2 size={13} className="text-emerald-500" />
                 {group.participants.filter(p => p.has_completed_sociodemographic && !p.is_disqualified).length} / {group.member_count} onboarded
               </div>
            </div>
            
            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <thead>
                  <tr className="bg-zinc-50/30 border-b border-zinc-100">
                    <th className="px-6 py-4 text-xs font-semibold text-zinc-500 uppercase tracking-wider">Participant</th>
                    <th className="px-6 py-4 text-xs font-semibold text-zinc-500 uppercase tracking-wider">Day Number</th>
                    <th className="px-6 py-4 text-xs font-semibold text-zinc-500 uppercase tracking-wider">Daily Submissions</th>
                    <th className="px-6 py-4 text-xs font-semibold text-zinc-500 uppercase tracking-wider">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-100">
                  {group.participants.map((p) => (
                    <tr key={p.user_id} className="hover:bg-zinc-50 transition-colors">
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 bg-zinc-100 flex items-center justify-center text-zinc-600 font-bold rounded-lg text-xs uppercase">
                             {p.username.substring(0,2)}
                          </div>
                          <div>
                            <div className="font-semibold text-zinc-900 leading-tight">{p.full_name || 'Anonymous Researcher'}</div>
                            <div className="text-xs text-zinc-400">@{p.username}</div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        {p.is_disqualified ? (
                          <span className="text-zinc-400 text-xs font-medium">—</span>
                        ) : (
                          <div className="flex items-center gap-2">
                             <div className="w-8 h-8 rounded-full bg-zinc-800 text-white flex items-center justify-center text-[10px] font-bold">
                                {p.current_experiment_day || 0}
                             </div>
                             <span className="text-xs font-medium text-zinc-500 uppercase">Day</span>
                          </div>
                        )}
                      </td>
                      <td className="px-6 py-4 text-sm font-semibold text-zinc-800">
                        {p.submission_count}
                      </td>
                      <td className="px-6 py-4">
                        {p.is_disqualified ? (
                           <div className="flex items-center gap-1.5 text-red-600 text-xs font-semibold">
                              <AlertTriangle size={14} className="text-red-500" /> Disqualified
                           </div>
                        ) : p.has_completed_sociodemographic ? (
                           <div className="flex items-center gap-1.5 text-emerald-700 text-xs font-semibold">
                              <CheckCircle2 size={14} className="text-emerald-500" /> Active
                           </div>
                        ) : (
                           <div className="flex items-center gap-1.5 text-zinc-500 text-xs font-medium">
                              <Clock size={14} className="text-zinc-400" /> Pending Onboarding
                           </div>
                        )}
                      </td>
                    </tr>
                  ))}
                  {group.participants.length === 0 && (
                    <tr>
                      <td colSpan={4} className="px-6 py-16 text-center text-zinc-400 italic text-sm">
                         No participants assigned to this experimental segment.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
      </div>
    </div>
  );
};

export default GroupDetailPage;
