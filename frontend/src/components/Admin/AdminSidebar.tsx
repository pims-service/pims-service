import React, { useState, useEffect } from 'react';
import { NavLink } from 'react-router-dom';
import { 
  Users, 
  LayoutDashboard, 
  BarChart2,
  Database,
  ClipboardCheck,
  MessageSquare
} from 'lucide-react';
import api from '../../services/api';

interface AdminSidebarProps {
  onNavigate?: () => void;
}

const AdminSidebar: React.FC<AdminSidebarProps> = ({ onNavigate }) => {
  const [openQueriesCount, setOpenQueriesCount] = useState(0);

  useEffect(() => {
    const fetchOpenQueriesCount = async () => {
      try {
        const res = await api.get('/support/tickets/open_count/');
        setOpenQueriesCount(res.data.count || 0);
      } catch (err) {
        console.error('Failed to fetch open queries count', err);
      }
    };
    fetchOpenQueriesCount();
    // Poll every 30 seconds
    const interval = setInterval(fetchOpenQueriesCount, 30000);
    return () => clearInterval(interval);
  }, []);

  const navItems = [
    { label: 'Overview', path: '/admin', icon: <LayoutDashboard size={18} /> },
    { label: 'Baseline Raw Data', path: '/admin/baseline-data', icon: <Database size={18} /> },
    { label: 'Post-Test Data', path: '/admin/posttest-data', icon: <ClipboardCheck size={18} /> },
    { label: 'Experimental Reports', path: '/admin/reports', icon: <BarChart2 size={18} /> },
    { label: 'Groups Management', path: '/admin/groups', icon: <Users size={18} /> },
    { label: 'User Queries', path: '/admin/support-queries', icon: <MessageSquare size={18} />, badge: openQueriesCount },
  ];

  return (
    <aside className="w-64 h-full bg-white border-r border-zinc-200 flex flex-col overflow-y-auto">
      <div className="py-6 space-y-1">
        <div className="px-5 mb-4">
          <h2 className="text-xs font-semibold uppercase tracking-wider text-zinc-400">Navigation</h2>
        </div>
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            end={item.path === '/admin'}
            onClick={onNavigate}
            className={({ isActive }) => `
              flex items-center justify-between px-5 py-2.5 text-sm font-medium transition-all rounded-lg mx-2
              ${isActive 
                ? 'bg-zinc-100 text-zinc-900' 
                : 'text-zinc-500 hover:text-zinc-800 hover:bg-zinc-50'}
            `}
          >
            <div className="flex items-center gap-3">
              <span>{item.icon}</span>
              {item.label}
            </div>
            {item.badge !== undefined && item.badge > 0 && (
              <span className="bg-red-500 text-white text-[10px] font-bold px-2 py-0.5 rounded-full">
                {item.badge}
              </span>
            )}
          </NavLink>
        ))}
      </div>
    </aside>
  );
};

export default AdminSidebar;
