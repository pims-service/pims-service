import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { User, Mail, Shield, Award, Edit2, Check } from 'lucide-react';

const ProfilePage: React.FC = () => {
  const [user, setUser] = useState<any>(null);
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
      <div className="bg-white border-4 border-black p-10 relative overflow-hidden">
        <div className="absolute top-0 left-0 w-full h-4 bg-black"></div>
        
        <div className="relative mt-8 flex flex-col items-center">
          <div className="w-24 h-24 rounded-none bg-black flex items-center justify-center text-white mb-4">
            <User size={48} />
          </div>
          <h2 className="text-3xl font-black uppercase tracking-tighter">{user?.username}</h2>
          <p className="text-zinc-600 flex items-center gap-2 mt-1 font-bold uppercase tracking-widest text-xs">
            <Mail size={14} /> {user?.email}
          </p>
        </div>

        <div className="mt-10 space-y-6">
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-white p-6 border-2 border-black">
              <div className="text-black mb-2 font-black uppercase tracking-widest text-xs flex items-center gap-2">
                <Shield size={16} /> Group
              </div>
              <div className="text-2xl font-black tracking-tighter uppercase">{user?.group_name || 'Unassigned'}</div>
            </div>
            <div className="bg-white p-6 border-2 border-black">
              <div className="text-black mb-2 font-black uppercase tracking-widest text-xs flex items-center gap-2">
                <Award size={16} /> Joined
              </div>
              <div className="text-2xl font-black tracking-tighter uppercase">Day 12</div>
            </div>
          </div>

          <div className="border-2 border-black p-8 bg-black text-white">
            <div className="flex justify-between items-center mb-6">
              <h3 className="font-black uppercase tracking-widest text-sm">Psychological Traits</h3>
              <button className="text-white hover:underline">
                <Edit2 size={18} />
              </button>
            </div>
            <div className="flex flex-wrap gap-3">
              {Object.entries(user?.traits || {}).map(([key, value]: [string, any]) => (
                <span key={key} className="px-4 py-2 bg-white text-black text-xs font-black uppercase tracking-tight flex items-center gap-2 border border-white">
                  <Check size={14} /> {key}: {value}
                </span>
              ))}
              {Object.keys(user?.traits || {}).length === 0 && (
                <p className="text-white/70 italic text-sm">No traits assessed yet.</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProfilePage;
