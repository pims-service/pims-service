import React from 'react';
import { NavLink } from 'react-router-dom';
import { 
  Users, 
  LayoutDashboard, 
  BarChart2
} from 'lucide-react';

const AdminSidebar: React.FC = () => {
  const navItems = [
    { label: 'Overview', path: '/admin', icon: <LayoutDashboard size={20} /> },
    { label: 'Experimental Reports', path: '/admin/reports', icon: <BarChart2 size={20} /> },
    { label: 'Groups Management', path: '/admin/groups', icon: <Users size={20} /> },
  ];

  return (
    <aside className="w-64 h-[calc(100vh-64px)] bg-white border-r border-zinc-200 flex flex-col sticky top-0">
      <div className="p-4 py-8 space-y-1">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            end={item.path === '/admin'}
            className={({ isActive }) => `
              flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-colors
              ${isActive 
                ? 'bg-zinc-100 text-zinc-900' 
                : 'text-zinc-500 hover:text-zinc-900 hover:bg-zinc-50'}
            `}
          >
            <span className="text-zinc-400 group-hover:text-zinc-900">{item.icon}</span>
            {item.label}
          </NavLink>
        ))}
      </div>
    </aside>
  );
};

export default AdminSidebar;
