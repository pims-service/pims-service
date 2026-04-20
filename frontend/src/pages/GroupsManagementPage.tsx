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
      setGroups(Array.isArray(response.data) ? response.data : []);
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
    if (!Array.isArray(groups) || groups.length === 0) return 0;
    const total = groups.reduce((acc, g) => acc + (g.member_count || 0), 0);
    return total / groups.length;
  };

  const avgCount = calculateAverage();

  const getGroupStatus = (count: number) => {
    if (count === 0) return { label: 'Empty', color: 'text-zinc-500', bg: 'bg-zinc-100', border: 'border-zinc-200' };
    if (count < avgCount * 0.8) return { label: 'Low', color: 'text-zinc-600', bg: 'bg-zinc-50', border: 'border-zinc-200' };
    return { label: 'Balanced', color: 'text-zinc-700', bg: 'bg-zinc-100', border: 'border-zinc-200' };
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
        <RotateCw className="w-8 h-8 text-zinc-400 animate-spin" />
        <p className="text-zinc-500 font-medium text-sm">Loading groups...</p>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto space-y-6 animate-in fade-in duration-700 pt-0">
      <header className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-zinc-200 pb-6">
        <div className="space-y-1">
          <h1 className="text-3xl font-bold text-zinc-900">Group Management</h1>
          <p className="text-zinc-500 text-sm">Experimental Balance & Distribution Oversight</p>
        </div>

        <div className="flex items-center gap-3">
          <div className="hidden lg:flex items-center gap-2 px-3 py-1.5 border border-zinc-200 bg-white rounded-lg text-xs font-medium text-zinc-600">
            <Info size={14} />
            Avg. Size: <span className="font-mono">{avgCount.toFixed(1)}</span>
          </div>
          <button 
            onClick={fetchData} 
            disabled={refreshing}
            className="w-full md:w-auto px-5 py-2.5 bg-zinc-800 text-white rounded-lg flex items-center justify-center gap-2 hover:bg-zinc-700 transition-colors disabled:opacity-40 font-medium text-sm"
          >
            <RotateCw size={16} className={refreshing ? 'animate-spin' : ''} />
            {refreshing ? 'Refreshing' : 'Refresh'}
          </button>
        </div>
      </header>

      {error ? (
        <div className="border border-zinc-200 rounded-xl p-12 text-center space-y-4 bg-white shadow-sm">
          <AlertTriangle className="w-10 h-10 text-zinc-400 mx-auto" />
          <p className="text-zinc-700 font-medium">{error}</p>
          <button onClick={fetchData} className="px-6 py-2.5 bg-zinc-800 text-white rounded-lg font-medium text-sm hover:bg-zinc-700 transition-colors">Retry</button>
        </div>
      ) : groups.length === 0 ? (
        <div className="border border-zinc-200 rounded-xl p-16 text-center space-y-4 bg-white shadow-sm">
          <Users className="w-12 h-12 text-zinc-300 mx-auto" />
          <h3 className="text-lg font-semibold text-zinc-700">No Groups Yet</h3>
          <p className="text-zinc-500 text-sm max-w-md mx-auto">
            Experimental groups have not been initialized.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
          {(groups || []).map((group, index) => {
            const status = getGroupStatus(group.member_count);
            return (
              <motion.div
                key={group.group_id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
                onClick={() => navigate(`/admin/groups/${group.group_id}`)}
                className="bg-white border border-zinc-200 rounded-xl p-5 cursor-pointer hover:shadow-lg hover:border-zinc-300 transition-all"
              >
                <div className="space-y-4">
                  <div className="flex justify-between items-start">
                    <h3 className="font-semibold text-zinc-900">
                      {group.name}
                    </h3>
                    <div className={`px-2 py-0.5 text-xs font-medium rounded-md ${status.bg} ${status.color}`}>
                      {status.label}
                    </div>
                  </div>

                  <div>
                    <div className="text-3xl font-bold text-zinc-800">{group.member_count}</div>
                    <div className="text-xs text-zinc-500 font-medium mt-0.5">Members</div>
                  </div>

                  <p className="text-xs text-zinc-500 h-8 line-clamp-2">
                    {group.description || 'No description provided.'}
                  </p>

                  <div className="pt-3 flex items-center justify-between text-xs text-zinc-400 border-t border-zinc-100">
                    <span className="flex items-center gap-1">
                      <CheckCircle2 size={12} className={group.member_count > 0 ? 'text-zinc-600' : 'text-zinc-300'} />
                      Active
                    </span>
                    <span className="flex items-center gap-1 hover:text-zinc-700">
                      View <ChevronRight size={14} />
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
