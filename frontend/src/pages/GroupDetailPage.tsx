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
  Trash2
} from 'lucide-react';
import { getGroupDetail } from '../services/api';

interface Participant {
  user_id: number;
  full_name: string;
  username: string;
  submission_count: number;
  has_completed_baseline: boolean;
  current_experiment_day: number | null;
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
    setIsEditing(false);
    if (group) {
        setGroup({ ...group, ...editForm });
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
    <div className="space-y-8 animate-in fade-in duration-700 pt-0">
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
              <p className="text-zinc-500 font-medium text-sm mt-2">{group.description || 'No descriptive metadata provided for this experimental segment.'}</p>
            </div>
          )}
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
              <button className="px-5 py-2.5 bg-white border border-zinc-200 text-red-600 rounded-lg font-medium text-sm hover:bg-red-50 hover:border-red-100 transition-all flex items-center gap-2">
                <Trash2 size={16} /> Purge
              </button>
            </div>
          )}
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
        <div className="lg:col-span-1 space-y-6">
          <div className="bg-white border border-zinc-200 rounded-xl p-6 shadow-sm">
            <h4 className="text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-6 border-b border-zinc-100 pb-2 text-center">Group Vitals</h4>
            <div className="space-y-6">
               <div className="text-center">
                  <div className="text-3xl font-bold text-zinc-900">{group.member_count}</div>
                  <div className="text-xs text-zinc-400 font-medium mt-1">Total Members</div>
               </div>
               <div className="text-center">
                  <div className="text-3xl font-bold text-zinc-900">
                    {Math.round((group.participants.filter(p => p.has_completed_baseline).length / (group.member_count || 1)) * 100)}%
                  </div>
                  <div className="text-xs text-zinc-400 font-medium mt-1 uppercase tracking-tight">Onboarding Health</div>
               </div>
               <div className="pt-4 border-t border-zinc-100 text-[10px] text-zinc-400 text-center">
                  Created on {new Date(group.created_at).toLocaleDateString()}
               </div>
            </div>
          </div>
        </div>

        <div className="lg:col-span-3">
          <div className="bg-white border border-zinc-200 rounded-xl overflow-hidden shadow-sm">
            <div className="px-6 py-4 border-b border-zinc-100 flex items-center justify-between bg-zinc-50/50">
               <h2 className="text-sm font-bold text-zinc-800 uppercase tracking-wider">Participant Roster</h2>
               <div className="text-[10px] font-bold py-1 px-3 bg-zinc-800 text-white rounded-full flex items-center gap-1.5 uppercase tracking-widest">
                  <CheckCircle2 size={10} /> Active Segment
               </div>
            </div>
            
            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <thead>
                  <tr className="bg-zinc-50/30 border-b border-zinc-100">
                    <th className="px-6 py-4 text-xs font-semibold text-zinc-500 uppercase tracking-wider">Participant</th>
                    <th className="px-6 py-4 text-xs font-semibold text-zinc-500 uppercase tracking-wider">Day Number</th>
                    <th className="px-6 py-4 text-xs font-semibold text-zinc-500 uppercase tracking-wider">Exp. Delta</th>
                    <th className="px-6 py-4 text-xs font-semibold text-zinc-500 uppercase tracking-wider">Status</th>
                    <th className="px-6 py-4 text-xs font-semibold text-zinc-500 uppercase tracking-wider text-right">Action</th>
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
                        <div className="flex items-center gap-2">
                           <div className="w-8 h-8 rounded-full bg-zinc-800 text-white flex items-center justify-center text-[10px] font-bold">
                              {p.current_experiment_day || 0}
                           </div>
                           <span className="text-xs font-medium text-zinc-500 uppercase">Day</span>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2">
                          <div className="text-sm font-bold text-zinc-800">{p.submission_count}</div>
                          <div className="text-[10px] text-zinc-400 font-medium uppercase tracking-wider">Submissions</div>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        {p.has_completed_baseline ? (
                           <div className="flex items-center gap-1.5 text-zinc-700 text-xs font-semibold">
                              <CheckCircle2 size={14} className="text-zinc-400" /> Terminal Ready
                           </div>
                        ) : (
                           <div className="flex items-center gap-1.5 text-zinc-400 text-xs font-medium">
                              <Clock size={14} /> Pending Sync
                           </div>
                        )}
                      </td>
                      <td className="px-6 py-4 text-right">
                         <button className="text-[10px] font-bold uppercase tracking-wider text-zinc-400 hover:text-zinc-900 transition-all">
                            Purge
                         </button>
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
    </div>
  );
};

export default GroupDetailPage;
