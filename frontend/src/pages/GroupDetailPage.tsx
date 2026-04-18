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
import { motion, AnimatePresence } from 'framer-motion';
import { getGroupDetail } from '../services/api';

interface Participant {
  user_id: number;
  full_name: string;
  username: string;
  submission_count: number;
  has_completed_baseline: boolean;
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
        <RotateCw className="w-8 h-8 text-indigo-500 animate-spin" />
        <p className="text-slate-400 font-medium animate-pulse">Syncing research roster...</p>
      </div>
    );
  }

  if (error || !group) {
    return (
      <div className="glass p-12 text-center space-y-4 border-red-500/20 max-w-2xl mx-auto">
        <AlertTriangle className="w-12 h-12 text-red-500 mx-auto" />
        <h2 className="text-xl font-bold text-white">Roster Access Failure</h2>
        <p className="text-slate-400">{error || 'Group not found.'}</p>
        <button onClick={() => navigate('/admin/groups')} className="btn-premium px-8">Return to Groups</button>
      </div>
    );
  }

  return (
    <div className="space-y-10 animate-in fade-in duration-700 pt-0">
      <header className="flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div className="space-y-4 flex-grow max-w-2xl">
          <div className="flex items-center gap-3 text-indigo-400 text-[10px] font-black uppercase tracking-[0.2em]">
            <Users size={14} /> Group Command Center
          </div>
          
          {isEditing ? (
            <div className="space-y-4">
              <input 
                value={editForm.name}
                onChange={(e) => setEditForm({...editForm, name: e.target.value})}
                className="text-4xl font-bold bg-transparent border-b-2 border-indigo-500 outline-none w-full text-zinc-900"
              />
              <textarea 
                value={editForm.description}
                onChange={(e) => setEditForm({...editForm, description: e.target.value})}
                className="text-slate-500 bg-transparent border-b border-zinc-200 outline-none w-full h-10 resize-none"
              />
            </div>
          ) : (
            <div>
              <h1 className="text-5xl font-black tracking-tighter text-zinc-900">{group.name}</h1>
              <p className="text-slate-500 mt-2 text-lg">{group.description || 'No description provided for this experimental segment.'}</p>
            </div>
          )}
        </div>

        <div className="flex items-center gap-3">
          {isEditing ? (
            <div className="flex gap-2">
              <button 
                onClick={handleUpdate}
                className="px-6 py-3 bg-indigo-600 text-white rounded-2xl font-bold flex items-center gap-2 shadow-lg shadow-indigo-600/20"
              >
                <Save size={18} /> Save Changes
              </button>
              <button 
                onClick={() => setIsEditing(false)}
                className="px-3 py-3 bg-zinc-100 text-zinc-500 rounded-2xl hover:bg-zinc-200"
              >
                <X size={20} />
              </button>
            </div>
          ) : (
            <div className="flex gap-3">
              <button 
                onClick={() => setIsEditing(true)}
                className="px-6 py-3 bg-white border border-zinc-200 text-zinc-900 rounded-2xl font-bold flex items-center gap-2 hover:border-indigo-500/50 transition-all"
              >
                <Edit3 size={18} /> Edit Metadata
              </button>
              <button className="px-6 py-3 bg-white border border-red-50 text-red-600 rounded-2xl font-bold hover:bg-red-50 transition-all flex items-center gap-2 group">
                <Trash2 size={18} className="group-hover:scale-110 transition-transform" /> Delete Segment
              </button>
            </div>
          )}
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
        <div className="lg:col-span-1 space-y-6">
          <div className="bg-white border border-zinc-200 rounded-[2.5rem] p-8">
            <h3 className="text-xs font-black uppercase tracking-[0.2em] text-slate-400 mb-8">Group Vitals</h3>
            <div className="space-y-8">
               <div>
                  <div className="text-4xl font-black text-zinc-900">{group.member_count}</div>
                  <div className="text-xs text-slate-500 font-bold uppercase mt-1">Total Members</div>
               </div>
               <div>
                  <div className="text-4xl font-black text-indigo-600">
                    {Math.round((group.participants.filter(p => p.has_completed_baseline).length / (group.member_count || 1)) * 100)}%
                  </div>
                  <div className="text-xs text-slate-500 font-bold uppercase mt-1">Onboarding Health</div>
               </div>
               <div className="pt-4 border-t border-zinc-100 text-[10px] text-zinc-400">
                  Created on {new Date(group.created_at).toLocaleDateString()}
               </div>
            </div>
          </div>
        </div>

        <div className="lg:col-span-3">
          <div className="bg-white border border-zinc-200 rounded-[2.5rem] overflow-hidden">
            <div className="p-8 border-b border-zinc-100 flex items-center justify-between">
               <h2 className="text-xl font-black text-zinc-900 uppercase tracking-tight">Participant Roster</h2>
               <div className="text-[10px] font-bold py-1.5 px-3 bg-emerald-50 text-emerald-600 rounded-full border border-emerald-100 flex items-center gap-1.5 uppercase tracking-widest">
                  <CheckCircle2 size={12} /> Active Segment
               </div>
            </div>
            
            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <thead>
                  <tr className="bg-zinc-50/50 border-b border-zinc-100">
                    <th className="px-8 py-5 text-[10px] font-black uppercase tracking-widest text-slate-500">Participant</th>
                    <th className="px-8 py-5 text-[10px] font-black uppercase tracking-widest text-slate-500">Exp. Progress</th>
                    <th className="px-8 py-5 text-[10px] font-black uppercase tracking-widest text-slate-500">Status</th>
                    <th className="px-8 py-5 text-[10px] font-black uppercase tracking-widest text-slate-500 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-100">
                  {group.participants.map((p) => (
                    <tr key={p.user_id} className="hover:bg-zinc-50/50 transition-colors group">
                      <td className="px-8 py-6">
                        <div className="flex items-center gap-4">
                          <div className="w-12 h-12 rounded-2xl bg-indigo-50 flex items-center justify-center text-indigo-600 font-black border border-indigo-100 group-hover:bg-indigo-600 group-hover:text-white transition-all text-sm uppercase">
                             {p.username.substring(0,2)}
                          </div>
                          <div>
                            <div className="font-black text-zinc-900 uppercase tracking-tight">{p.full_name || 'Anonymous Researcher'}</div>
                            <div className="text-xs text-slate-500 font-mono">@{p.username}</div>
                          </div>
                        </div>
                      </td>
                      <td className="px-8 py-6">
                        <div className="flex items-center gap-3">
                          <div className="text-lg font-black text-zinc-900">{p.submission_count}</div>
                          <div className="text-[10px] text-slate-400 font-bold uppercase tracking-widest">Submissions</div>
                        </div>
                      </td>
                      <td className="px-8 py-6">
                        {p.has_completed_baseline ? (
                           <div className="flex items-center gap-1.5 text-emerald-600 text-xs font-bold uppercase tracking-tighter">
                              <CheckCircle2 size={14} /> Baseline Done
                           </div>
                        ) : (
                           <div className="flex items-center gap-1.5 text-amber-500 text-xs font-bold uppercase tracking-tighter">
                              <Clock size={14} /> Pending Onboarding
                           </div>
                        )}
                      </td>
                      <td className="px-8 py-6 text-right">
                         <button className="text-[10px] font-black uppercase tracking-widest text-slate-400 hover:text-red-500 transition-colors py-2 px-4 rounded-xl border border-zinc-100 hover:border-red-100">
                            Remove
                         </button>
                      </td>
                    </tr>
                  ))}
                  {group.participants.length === 0 && (
                    <tr>
                      <td colSpan={4} className="px-8 py-20 text-center text-slate-400 italic">
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
