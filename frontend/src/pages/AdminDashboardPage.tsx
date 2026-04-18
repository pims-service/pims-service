import React, { useState, useEffect } from 'react';
import { Users, FileText, TrendingUp, Search, Loader2, AlertTriangle } from 'lucide-react';
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend } from 'chart.js';
import { Line } from 'react-chartjs-2';
import { questionnairesApi } from '../services/api';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend);

interface AnalyticsData {
  total_participants: number;
  total_submissions: number;
  active_rate_percentage: number;
  current_phase_name: string;
  engagement_trend: { date: string; count: number }[];
  recent_participants: {
    id: number;
    username: string;
    group: string;
    submissions_count: string;
    status: string;
  }[];
}

const AdminDashboardPage: React.FC = () => {
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        const response = await questionnairesApi.getDashboardAnalytics();
        setData(response.data);
      } catch (err) {
        console.error("Failed to load analytics", err);
        setError("Failed to load dashboard analytics.");
      } finally {
        setLoading(false);
      }
    };
    fetchAnalytics();
  }, []);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
        <Loader2 className="w-8 h-8 text-indigo-500 animate-spin" />
        <p className="text-slate-400 font-medium animate-pulse">Loading live analytics...</p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="glass p-12 text-center space-y-4 border-red-500/20 max-w-2xl mx-auto mt-20">
        <AlertTriangle className="w-12 h-12 text-red-500 mx-auto" />
        <h2 className="text-xl font-bold text-white">Analytics Unavailable</h2>
        <p className="text-slate-400">{error}</p>
      </div>
    );
  }

  const chartData = {
    labels: data.engagement_trend.map(item => item.date),
    datasets: [
      {
        label: 'Submissions',
        data: data.engagement_trend.map(item => item.count),
        borderColor: '#6366f1',
        backgroundColor: 'rgba(99, 102, 241, 0.5)',
        tension: 0.4,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
    },
    scales: {
      y: {
        grid: { color: 'rgba(255, 255, 255, 0.05)' },
        beginAtZero: true,
      },
      x: { grid: { display: false } },
    },
  };

  return (
    <div className="space-y-10 pt-0">
      <header className="flex justify-between items-center text-zinc-900 border-b border-zinc-200 py-4 mb-10">
        <div>
          <h1 className="text-4xl font-black tracking-tighter uppercase">Admin Console</h1>
          <p className="text-slate-400 mt-1 font-medium italic">Real-time experimental analytics and management.</p>
        </div>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="glass p-6 text-center">
          <Users className="mx-auto mb-2 text-indigo-400" size={24} />
          <div className="text-2xl font-bold text-zinc-900">{data.total_participants}</div>
          <div className="text-slate-500 text-sm">Total Participants</div>
        </div>
        <div className="glass p-6 text-center">
          <FileText className="mx-auto mb-2 text-indigo-400" size={24} />
          <div className="text-2xl font-bold text-zinc-900">{data.total_submissions.toLocaleString()}</div>
          <div className="text-slate-500 text-sm">Total Submissions</div>
        </div>
        <div className="glass p-6 text-center">
          <TrendingUp className="mx-auto mb-2 text-emerald-500" size={24} />
          <div className="text-2xl font-bold text-zinc-900">{data.active_rate_percentage}%</div>
          <div className="text-slate-500 text-sm">Active Rate (7 days)</div>
        </div>
        <div className="glass p-6 text-center">
          <div className="text-2xl font-bold text-indigo-500">{data.current_phase_name}</div>
          <div className="text-slate-500 text-sm">Current Status</div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div className="glass p-8 flex flex-col">
          <h3 className="text-xl font-bold mb-6 text-zinc-900">User Engagement Trend</h3>
          <div className="flex-grow min-h-[250px]">
            <Line data={chartData} options={options} />
          </div>
        </div>

        <div className="glass p-8 overflow-hidden flex flex-col">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-xl font-bold text-zinc-900">Recent Participants</h3>
          </div>
          <div className="overflow-x-auto flex-grow">
            <table className="w-full text-left text-sm">
              <thead className="bg-zinc-50 border-b border-zinc-200">
                <tr>
                  <th className="p-4 text-zinc-500 font-semibold uppercase text-xs">User</th>
                  <th className="p-4 text-zinc-500 font-semibold uppercase text-xs">Group</th>
                  <th className="p-4 text-zinc-500 font-semibold uppercase text-xs">Submissions</th>
                  <th className="p-4 text-zinc-500 font-semibold uppercase text-xs">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-100 bg-white">
                {data.recent_participants.map((user) => (
                  <tr key={user.id} className="hover:bg-zinc-50 transition-colors">
                    <td className="p-4 font-medium text-zinc-900">{user.username}</td>
                    <td className="p-4">
                      <span className="px-2.5 py-1 text-xs font-semibold bg-indigo-50 text-indigo-600 rounded-full border border-indigo-100">
                        {user.group}
                      </span>
                    </td>
                    <td className="p-4 text-zinc-600 font-medium">{user.submissions_count}</td>
                    <td className={`p-4 font-medium ${user.status === 'Active' ? 'text-emerald-500' : 'text-slate-400'}`}>
                      {user.status}
                    </td>
                  </tr>
                ))}
                {data.recent_participants.length === 0 && (
                  <tr>
                    <td colSpan={4} className="p-4 text-center text-slate-500 italic">No recent participants found.</td>
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

export default AdminDashboardPage;
