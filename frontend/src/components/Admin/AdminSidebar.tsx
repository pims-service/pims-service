import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  Users,
  LayoutDashboard,
  BarChart2,
  ChevronRight,
  ShieldCheck,
  Zap
} from 'lucide-react';
import { motion } from 'framer-motion';

const AdminSidebar: React.FC = () => {
  const navItems = [
    { label: 'Overview', path: '/admin', icon: <LayoutDashboard size={20} />, description: 'System health & stats' },
    { label: 'Experimental Reports', path: '/admin/reports', icon: <BarChart2 size={20} />, description: 'Data exports & analytics' },
    { label: 'Groups Management', path: '/admin/groups', icon: <Users size={20} />, description: 'Participant segmentation' },
  ];

  return (
    <aside className="w-80 h-[calc(100vh-64px)] bg-zinc-950 border-r border-zinc-800 flex flex-col sticky top-16 shadow-2xl">
      <div className="p-8 pb-4">
        <div className="flex items-center gap-2 text-indigo-400 text-[10px] font-black uppercase tracking-[0.2em] mb-6">
          <Zap size={14} className="fill-current" />
          Administrative Terminal
        </div>

        <div className="space-y-1.5">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === '/admin'}
              className={({ isActive }) => `
                group flex items-center gap-4 p-4 rounded-2xl transition-all duration-300
                ${isActive
                  ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/20'
                  : 'text-zinc-500 hover:bg-zinc-900 hover:text-zinc-300'}
              `}
            >
              {({ isActive }) => (
                <>
                  <div className={`p-2.5 rounded-xl transition-colors ${isActive ? 'bg-indigo-500' : 'bg-zinc-900 group-hover:bg-zinc-800'
                    }`}>
                    {item.icon}
                  </div>
                  <div className="flex-grow">
                    <div className="text-sm font-bold tracking-tight">{item.label}</div>
                    <div className={`text-[10px] transition-colors ${isActive ? 'text-indigo-200' : 'text-zinc-600'
                      }`}>
                      {item.description}
                    </div>
                  </div>
                  {isActive && (
                    <motion.div
                      layoutId="activeTab"
                      className="text-indigo-200"
                    >
                      <ChevronRight size={16} />
                    </motion.div>
                  )}
                </>
              )}
            </NavLink>
          ))}
        </div>
      </div>

      <div className="mt-auto p-8 pt-0">
        <div className="p-6 rounded-3xl bg-gradient-to-br from-zinc-900 to-zinc-950 border border-zinc-800 space-y-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-green-500/10 flex items-center justify-center text-green-500 border border-green-500/10">
              <ShieldCheck size={20} />
            </div>
            <div>
              <div className="text-xs font-bold text-white">System Verified</div>
              <div className="text-[10px] text-zinc-500 leading-none">Standard Integrity</div>
            </div>
          </div>
          <p className="text-[10px] text-zinc-600 leading-relaxed font-medium">
            Your researcher session is cryptographically secured via platform-grade JWT persistence.
          </p>
          <div className="pt-2">
            <div className="h-1 w-full bg-zinc-800 rounded-full overflow-hidden">
              <div className="h-full w-4/5 bg-indigo-500/50" />
            </div>
            <div className="flex justify-between mt-1 text-[8px] font-black uppercase tracking-widest text-zinc-700">
              <span>Session Load</span>
              <span>80%</span>
            </div>
          </div>
        </div>
      </div>
    </aside>
  );
};

export default AdminSidebar;
