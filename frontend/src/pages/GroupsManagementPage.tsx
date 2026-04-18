import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Users, 
  RotateCw, 
  AlertTriangle, 
  CheckCircle2, 
  ChevronRight,
  Info
} from 'lucide-react';
import { motion } from 'framer-motion';
import { getGroups } from '../services/api';

interface Participant {
  user_id: number;
  full_name: string;
  username: string;
}

interface Group {
  group_id: number;
  name: string;
  description: string;
  member_count: number;
  participants?: Participant[];
}

const GroupsManagementPage: React.FC = () => {
  const navigate = useNavigate();
  const [groups, setGroups] = useState<Group[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    setRefreshing(true);
    try {
      const response = await getGroups();
      setGroups(response.data);
      setError(null);
    } catch (err) {
      setError('Failed to fetch group distribution data.');
      console.error(err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const calculateAverage = () => {
    if (groups.length === 0) return 0;
    const total = groups.reduce((acc, g) => acc + g.member_count, 0);
    return total / groups.length;
  };

  const avgCount = calculateAverage();

  const getGroupStatus = (count: number) => {
    if (count === 0) return { label: 'Empty', color: 'text-red-400', bg: 'bg-red-500/10', border: 'border-red-500/20' };
    if (count < avgCount * 0.8) return { label: 'Low Participation', color: 'text-amber-400', bg: 'bg-amber-500/10', border: 'border-amber-500/20' };
    return { label: 'Balanced', color: 'text-green-400', bg: 'bg-green-500/10', border: 'border-green-500/20' };
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
        <RotateCw className="w-8 h-8 text-indigo-500 animate-spin" />
        <p className="text-slate-400 animate-pulse">Loading distribution data...</p>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto space-y-8 animate-in fade-in duration-700 pt-0">
      <header className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="space-y-1">
          <h1 className="text-4xl font-bold tracking-tight">Group Management</h1>
          <p className="text-slate-400">Monitor participant distribution and ensure experimental balance.</p>
        </div>

        <div className="flex items-center gap-3">
          <div className="hidden lg:flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-900 border border-slate-800 text-xs text-slate-400">
            <Info size={14} className="text-indigo-400" />
            Target Average: <span className="text-white font-mono">{avgCount.toFixed(1)}</span>
          </div>
          <button 
            onClick={fetchData} 
            disabled={refreshing}
            className="glass px-4 py-2 flex items-center gap-2 hover:bg-slate-800 transition-all active:scale-95 disabled:opacity-50"
          >
            <RotateCw size={18} className={refreshing ? 'animate-spin' : ''} />
            {refreshing ? 'Refreshing...' : 'Refresh Data'}
          </button>
        </div>
      </header>

      {error ? (
        <div className="glass p-12 text-center space-y-4 border-red-500/20">
          <AlertTriangle className="w-12 h-12 text-red-500 mx-auto" />
          <p className="text-red-400">{error}</p>
          <button onClick={fetchData} className="btn-premium px-6">Try Again</button>
        </div>
      ) : groups.length === 0 ? (
        <div className="glass p-20 text-center space-y-4">
          <Users className="w-16 h-16 text-slate-700 mx-auto" />
          <h3 className="text-xl font-bold">No Groups Seeded</h3>
          <p className="text-slate-500 max-w-md mx-auto">
            Experimental groups haven't been initialized in the system yet. Please check the backend configuration.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {groups.map((group, index) => {
            const status = getGroupStatus(group.member_count);
            return (
              <motion.div
                key={group.group_id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
                onClick={() => navigate(`/admin/groups/${group.group_id}`)}
                className="glass group p-6 cursor-pointer hover:border-indigo-500/50 hover:shadow-lg hover:shadow-indigo-500/5 transition-all relative overflow-hidden"
              >
                <div className={`absolute top-0 right-0 w-24 h-24 ${status.bg} blur-3xl -mr-12 -mt-12 transition-colors`} />
                
                <div className="space-y-4 relative z-10">
                  <div className="flex justify-between items-start">
                    <h3 className="font-bold text-lg group-hover:text-indigo-400 transition-colors uppercase tracking-wider">
                      {group.name}
                    </h3>
                    <div className={`px-2 py-1 rounded text-[10px] font-bold ${status.bg} ${status.color} border ${status.border}`}>
                      {status.label}
                    </div>
                  </div>

                  <div className="space-y-1">
                    <div className="text-4xl font-mono font-bold">{group.member_count}</div>
                    <div className="text-xs text-slate-500 uppercase tracking-tighter">Participants</div>
                  </div>

                  <p className="text-sm text-slate-400 line-clamp-2 h-10 italic">
                    {group.description || 'No description provided.'}
                  </p>

                  <div className="pt-4 flex items-center justify-between text-xs text-slate-500 border-t border-slate-800">
                    <span className="flex items-center gap-1">
                      <CheckCircle2 size={12} className={group.member_count > 0 ? 'text-green-500' : 'text-slate-700'} />
                      Active
                    </span>
                    <span className="flex items-center gap-1 group-hover:text-indigo-400 transition-colors">
                      View List <ChevronRight size={14} />
                    </span>
                  </div>
                </div>
              </motion.div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default GroupsManagementPage;
