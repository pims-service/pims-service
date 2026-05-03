import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { User, Mail, Calendar, Clock } from 'lucide-react';

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

  if (loading) return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-zinc-800"></div>
    </div>
  );

  const formatDate = (dateStr: string) => {
    if (!dateStr) return 'N/A';
    return new Intl.DateTimeFormat('en-US', { month: 'long', day: 'numeric', year: 'numeric' }).format(new Date(dateStr));
  };

  const formatTime = (dateStr: string) => {
    if (!dateStr) return 'N/A';
    return new Intl.DateTimeFormat('en-US', { hour: '2-digit', minute: '2-digit', hour12: true }).format(new Date(dateStr));
  };

  return (
    <div className="max-w-2xl mx-auto py-8">
      <div className="bg-white border border-zinc-200 rounded-xl shadow-sm overflow-hidden">
        {/* Header Header */}
        <div className="bg-zinc-800 p-8 text-white">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 bg-white/10 rounded-lg flex items-center justify-center">
              <User size={32} />
            </div>
            <div>
              <h1 className="text-2xl font-bold">{user?.full_name || user?.username}</h1>
              <p className="text-zinc-400 text-sm">{user?.email}</p>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="p-8 space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="p-4 bg-zinc-50 rounded-lg border border-zinc-100">
              <div className="flex items-center gap-2 text-zinc-500 text-xs font-bold uppercase tracking-wider mb-2">
                <Mail size={14} /> Email Address
              </div>
              <p className="text-zinc-900 font-semibold">{user?.email}</p>
            </div>

            <div className="p-4 bg-zinc-50 rounded-lg border border-zinc-100">
              <div className="flex items-center gap-2 text-zinc-500 text-xs font-bold uppercase tracking-wider mb-2">
                <User size={14} /> Full Name
              </div>
              <p className="text-zinc-900 font-semibold">{user?.full_name || user?.username}</p>
            </div>

            <div className="p-4 bg-zinc-50 rounded-lg border border-zinc-100">
              <div className="flex items-center gap-2 text-zinc-500 text-xs font-bold uppercase tracking-wider mb-2">
                <Calendar size={14} /> Date Joined
              </div>
              <p className="text-zinc-900 font-semibold">{formatDate(user?.created_at)}</p>
            </div>

            <div className="p-4 bg-zinc-50 rounded-lg border border-zinc-100">
              <div className="flex items-center gap-2 text-zinc-500 text-xs font-bold uppercase tracking-wider mb-2">
                <Clock size={14} /> Time Joined
              </div>
              <p className="text-zinc-900 font-semibold">{formatTime(user?.created_at)}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProfilePage;
