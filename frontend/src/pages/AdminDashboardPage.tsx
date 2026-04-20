import React, { useState, useEffect } from 'react';
import { Users, FileText, TrendingUp, Loader2, AlertTriangle } from 'lucide-react';
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
        <Loader2 className="w-8 h-8 text-zinc-400 animate-spin" />
        <p className="text-zinc-500 font-medium text-sm">Loading analytics...</p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="border border-zinc-200 rounded-xl p-12 text-center space-y-4 max-w-2xl mx-auto mt-20 bg-white shadow-sm">
        <AlertTriangle className="w-10 h-10 text-zinc-400 mx-auto" />
        <h2 className="text-lg font-semibold text-zinc-800">Analytics Unavailable</h2>
        <p className="text-zinc-500 text-sm">{error}</p>
      </div>
    );
  }

  const chartData = {
    labels: (data.engagement_trend || []).map(item => item.date),
    datasets: [
      {
        label: 'Submissions',
        data: (data.engagement_trend || []).map(item => item.count),
        borderColor: '#3f3f46',
        backgroundColor: 'rgba(63, 63, 70, 0.05)',
        fill: true,
        tension: 0.3,
        borderWidth: 2,
        pointBackgroundColor: '#3f3f46',
        pointRadius: 4,
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
        grid: { color: 'rgba(0, 0, 0, 0.05)', drawTicks: false },
        border: { display: false },
        beginAtZero: true,
        ticks: { color: '#71717a' }
      },
      x: {
        grid: { display: false },
        ticks: { color: '#71717a' }
      },
    },
  };

  return (
    <div className="space-y-8 pt-0">
      <header className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-zinc-200 py-6 mb-8">
        <div>
          <h1 className="text-3xl font-bold text-zinc-900 leading-tight">Admin Console</h1>
          <p className="text-zinc-400 mt-1 text-sm font-medium tracking-tight">Experimental Analytics & System Management</p>
        </div>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-5">
        <div className="border border-zinc-200 rounded-xl p-5 text-center bg-white hover:shadow-md transition-shadow">
          <Users className="mx-auto mb-2 text-zinc-500" size={22} />
          <div className="text-2xl font-bold text-zinc-800">{data.total_participants}</div>
          <div className="text-zinc-500 text-xs font-medium uppercase tracking-wider mt-1">Participants</div>
        </div>
        <div className="border border-zinc-200 rounded-xl p-5 text-center bg-white hover:shadow-md transition-shadow">
          <FileText className="mx-auto mb-2 text-zinc-500" size={22} />
          <div className="text-2xl font-bold text-zinc-800">{data.total_submissions.toLocaleString()}</div>
          <div className="text-zinc-500 text-xs font-medium uppercase tracking-wider mt-1">Submissions</div>
        </div>
        <div className="border border-zinc-200 rounded-xl p-5 text-center bg-white hover:shadow-md transition-shadow">
          <TrendingUp className="mx-auto mb-2 text-zinc-500" size={22} />
          <div className="text-2xl font-bold text-zinc-800">{data.active_rate_percentage}%</div>
          <div className="text-zinc-500 text-xs font-medium uppercase tracking-wider mt-1">Growth Rate</div>
        </div>
        <div className="border border-zinc-200 rounded-xl p-5 text-center bg-zinc-800 text-white">
          <div className="text-xl font-bold mb-1">{data.current_phase_name}</div>
          <div className="text-zinc-300 text-xs font-medium uppercase tracking-wider">Current Status</div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="border border-zinc-200 rounded-xl p-6 flex flex-col bg-white shadow-sm">
          <h3 className="text-base font-semibold text-zinc-800 mb-4">Engagement Trend</h3>
          <div className="flex-grow min-h-[250px]">
            <Line data={chartData} options={options} />
          </div>
        </div>

        <div className="border border-zinc-200 rounded-xl p-6 overflow-hidden flex flex-col bg-white shadow-sm">
          <h3 className="text-base font-semibold text-zinc-800 mb-4">Recent Participants</h3>
          <div className="overflow-x-auto flex-grow">
            <table className="w-full text-left text-sm">
              <thead className="bg-zinc-50 border-b border-zinc-200">
                <tr>
                  <th className="p-3 text-xs font-semibold text-zinc-500 uppercase tracking-wider">User</th>
                  <th className="p-3 text-xs font-semibold text-zinc-500 uppercase tracking-wider">Group</th>
                  <th className="p-3 text-xs font-semibold text-zinc-500 uppercase tracking-wider">Submissions</th>
                  <th className="p-3 text-xs font-semibold text-zinc-500 uppercase tracking-wider">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-100">
                {(data.recent_participants || []).map((user) => (
                  <tr key={user.id} className="hover:bg-zinc-50 transition-colors">
                    <td className="p-3 font-medium text-zinc-800">{user.username}</td>
                    <td className="p-3">
                      <span className="px-2 py-0.5 text-xs font-medium bg-zinc-100 text-zinc-700 rounded-md">
                        {user.group}
                      </span>
                    </td>
                    <td className="p-3 text-zinc-600">{user.submissions_count}</td>
                    <td className={`p-3 text-xs font-medium ${user.status === 'Active' ? 'text-zinc-800' : 'text-zinc-400'}`}>
                      {user.status}
                    </td>
                  </tr>
                ))}
                {(!data.recent_participants || data.recent_participants.length === 0) && (
                  <tr>
                    <td colSpan={4} className="p-4 text-center text-zinc-400 italic text-sm">No recent participants found.</td>
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
