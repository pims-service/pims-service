import React, { useState } from 'react';
import { API_URL } from '../services/api';
import { Users, FileText, Download, TrendingUp, Search } from 'lucide-react';
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend } from 'chart.js';
import { Line } from 'react-chartjs-2';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend);

const AdminDashboardPage: React.FC = () => {

  const chartData = {
    labels: ['Day 1', 'Day 2', 'Day 3', 'Day 4', 'Day 5', 'Day 6', 'Day 7'],
    datasets: [
      {
        label: 'Submission Rate (%)',
        data: [65, 78, 82, 75, 90, 88, 95],
        borderColor: '#6366f1',
        backgroundColor: 'rgba(99, 102, 241, 0.5)',
        tension: 0.4,
      },
    ],
  };

  const options = {
    responsive: true,
    plugins: {
      legend: { display: false },
    },
    scales: {
      y: { grid: { color: 'rgba(255, 255, 255, 0.05)' } },
      x: { grid: { display: false } },
    },
  };

  const handleExport = async () => {
    window.open(`${API_URL}/admin/tools/export/csv/`, '_blank');
  };

  return (
    <div className="space-y-10">
      <header className="flex justify-between items-center">
        <h1 className="text-4xl font-bold">Admin Console</h1>
        <button onClick={handleExport} className="btn-premium flex items-center gap-2">
          <Download size={20} /> Export All Data (SPSS)
        </button>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="glass p-6 text-center">
          <Users className="mx-auto mb-2 text-indigo-400" size={24} />
          <div className="text-2xl font-bold">2,142</div>
          <div className="text-slate-500 text-sm">Total Participants</div>
        </div>
        <div className="glass p-6 text-center">
          <FileText className="mx-auto mb-2 text-indigo-400" size={24} />
          <div className="text-2xl font-bold">12,854</div>
          <div className="text-slate-500 text-sm">Total Submissions</div>
        </div>
        <div className="glass p-6 text-center">
          <TrendingUp className="mx-auto mb-2 text-green-400" size={24} />
          <div className="text-2xl font-bold">92%</div>
          <div className="text-slate-500 text-sm">Active Rate</div>
        </div>
        <div className="glass p-6 text-center">
          <div className="text-2xl font-bold text-indigo-400">Phase 1</div>
          <div className="text-slate-500 text-sm">Current Status</div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div className="glass p-8">
          <h3 className="text-xl font-bold mb-6">User Engagement Trend</h3>
          <div className="h-64">
            <Line data={chartData} options={options} />
          </div>
        </div>
        
        <div className="glass p-8 overflow-hidden">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-xl font-bold">Recent Participants</h3>
            <div className="flex gap-2">
              <div className="relative">
                <Search size={16} className="absolute left-3 top-2.5 text-slate-500" />
                <input className="bg-slate-900 border border-slate-700 rounded-lg py-2 pl-9 pr-4 text-sm focus:outline-none" placeholder="Search..." />
              </div>
            </div>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-900">
                <tr>
                  <th className="p-4">User</th>
                  <th className="p-4">Group</th>
                  <th className="p-4">Submissions</th>
                  <th className="p-4">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                <tr>
                  <td className="p-4">alex_smith</td>
                  <td className="p-4">Gratitude</td>
                  <td className="p-4">12/30</td>
                  <td className="p-4 text-green-400">Active</td>
                </tr>
                <tr>
                  <td className="p-4">sarah_j</td>
                  <td className="p-4">Achievement</td>
                  <td className="p-4">28/30</td>
                  <td className="p-4 text-green-400">Active</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminDashboardPage;
