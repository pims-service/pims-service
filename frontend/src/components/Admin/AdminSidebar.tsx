import React, { useState, useEffect } from 'react';
import { NavLink } from 'react-router-dom';
import {
  Users,
  LayoutDashboard,
  ClipboardCheck,
  MessageSquare,
  PhoneCall,
  ShieldAlert
} from 'lucide-react';
import api from '../../services/api';
import { useNotifications } from '../../hooks/useNotifications';

interface AdminSidebarProps {
  onNavigate?: () => void;
}

const AdminSidebar: React.FC<AdminSidebarProps> = ({ onNavigate }) => {
  const [openQueriesCount, setOpenQueriesCount] = useState(0);
  const { ticketCount } = useNotifications();

  useEffect(() => {
    setOpenQueriesCount(ticketCount);
  }, [ticketCount]);

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
  }, []);

  const navItems = [
    { label: 'Overview', path: '/admin', icon: <LayoutDashboard size={18} /> },
    { label: 'T0 Results', path: '/admin/t0-data', icon: <ClipboardCheck size={18} /> },
    { label: 'T1 Results', path: '/admin/t1-data', icon: <ClipboardCheck size={18} /> },
    { label: 'T2 Results', path: '/admin/t2-data', icon: <ClipboardCheck size={18} /> },
    { label: 'T3 Results', path: '/admin/t3-data', icon: <ClipboardCheck size={18} /> },
    { label: 'T4 Results', path: '/admin/t4-data', icon: <ClipboardCheck size={18} /> },
    { label: 'Groups Management', path: '/admin/groups', icon: <Users size={18} /> },
    { label: 'User Queries', path: '/admin/support-queries', icon: <MessageSquare size={18} />, badge: openQueriesCount },
    { label: 'Follow-ups', path: '/admin/follow-ups', icon: <PhoneCall size={18} /> },
    { label: 'Safety Risk', path: '/admin/safety-risk', icon: <ShieldAlert size={18} /> },
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
