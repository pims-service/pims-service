import React from 'react';
import { NavLink } from 'react-router-dom';
import { 
  Users, 
  LayoutDashboard, 
  BarChart2,
  Database,
  ClipboardCheck
} from 'lucide-react';

interface AdminSidebarProps {
  onNavigate?: () => void;
}

const AdminSidebar: React.FC<AdminSidebarProps> = ({ onNavigate }) => {
  const navItems = [
    { label: 'Overview', path: '/admin', icon: <LayoutDashboard size={18} /> },
    { label: 'Baseline Raw Data', path: '/admin/baseline-data', icon: <Database size={18} /> },
    { label: 'Post-Test Data', path: '/admin/posttest-data', icon: <ClipboardCheck size={18} /> },
    { label: 'Experimental Reports', path: '/admin/reports', icon: <BarChart2 size={18} /> },
    { label: 'Groups Management', path: '/admin/groups', icon: <Users size={18} /> },
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
              flex items-center gap-3 px-5 py-2.5 text-sm font-medium transition-all rounded-lg mx-2
              ${isActive 
                ? 'bg-zinc-100 text-zinc-900' 
                : 'text-zinc-500 hover:text-zinc-800 hover:bg-zinc-50'}
            `}
          >
            <span>{item.icon}</span>
            {item.label}
          </NavLink>
        ))}
      </div>
    </aside>
  );
};

export default AdminSidebar;
