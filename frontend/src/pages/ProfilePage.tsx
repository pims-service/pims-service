import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { User, Mail, Shield, Award, Edit2, Check } from 'lucide-react';

const ProfilePage: React.FC = () => {
  const [user, setUser] = useState<any>(null);
  const [editing, setEditing] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchUser = async () => {
      try {
        const { data } = await api.get('/users/profile/');
        setUser(data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchUser();
  }, []);

  if (loading) return <div className="text-center mt-20">Loading profile...</div>;

  return (
    <div className="max-w-2xl mx-auto">
      <div className="glass p-10 relative overflow-hidden">
        <div className="absolute top-0 left-0 w-full h-32 bg-gradient-to-r from-indigo-500/20 to-pink-500/20"></div>
        
        <div className="relative mt-8 flex flex-col items-center">
          <div className="w-24 h-24 rounded-full bg-slate-800 border-4 border-slate-900 flex items-center justify-center text-indigo-400 mb-4 shadow-xl">
            <User size={48} />
          </div>
          <h2 className="text-3xl font-bold">{user?.username}</h2>
          <p className="text-slate-400 flex items-center gap-2 mt-1">
            <Mail size={16} /> {user?.email}
          </p>
        </div>

        <div className="mt-10 space-y-6">
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-slate-900/50 p-6 rounded-2xl border border-slate-700">
              <div className="text-indigo-400 mb-2 font-semibold flex items-center gap-2">
                <Shield size={18} /> Group
              </div>
              <div className="text-xl font-bold">{user?.group_name || 'Unassigned'}</div>
            </div>
            <div className="bg-slate-900/50 p-6 rounded-2xl border border-slate-700">
              <div className="text-pink-400 mb-2 font-semibold flex items-center gap-2">
                <Award size={18} /> Joined
              </div>
              <div className="text-xl font-bold">Day 12</div>
            </div>
          </div>

          <div className="glass p-8 bg-white/5 border-none">
            <div className="flex justify-between items-center mb-6">
              <h3 className="font-bold text-lg">Psychological Traits</h3>
              <button className="text-indigo-400 hover:text-indigo-300">
                <Edit2 size={18} />
              </button>
            </div>
            <div className="flex flex-wrap gap-3">
              {Object.entries(user?.traits || {}).map(([key, value]: [string, any]) => (
                <span key={key} className="px-4 py-2 rounded-full bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 text-sm flex items-center gap-2">
                  <Check size={14} /> {key}: {value}
                </span>
              ))}
              {Object.keys(user?.traits || {}).length === 0 && (
                <p className="text-slate-500 italic text-sm">No traits assessed yet.</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProfilePage;
