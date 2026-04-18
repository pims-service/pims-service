import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { LogOut, User, LayoutDashboard, Settings } from 'lucide-react';

const Navbar: React.FC = () => {
  const navigate = useNavigate();
  const isAuthenticated = !!localStorage.getItem('access_token');
  const userRole = localStorage.getItem('user_role');
  const isAdmin = userRole === 'Admin';

  const handleLogout = () => {
    localStorage.clear();
    navigate('/login');
    window.location.reload();
  };

  return (
    <nav className="border-b border-zinc-200 bg-white relative z-50">
      <div className="container mx-auto px-6 h-16 flex items-center justify-between">
        <Link to="/" className="text-xl font-bold text-zinc-900 tracking-tight">
          PsychPlatform
        </Link>
        
        <div className="flex items-center gap-8">
          {isAuthenticated ? (
            <>
              <Link to="/dashboard" className="text-sm font-medium text-zinc-600 hover:text-zinc-900 transition-colors flex items-center gap-2">
                <LayoutDashboard size={18} /> Dashboard
              </Link>
              {isAdmin && (
                <Link to="/admin" className="text-sm font-medium text-zinc-600 hover:text-zinc-900 transition-colors flex items-center gap-2">
                  <Settings size={18} /> Admin
                </Link>
              )}
              <Link to="/profile" className="text-sm font-medium text-zinc-600 hover:text-zinc-900 transition-colors flex items-center gap-2">
                <User size={18} /> Profile
              </Link>
              <button 
                onClick={handleLogout}
                className="text-sm font-medium text-red-600 hover:text-red-700 transition-colors flex items-center gap-2"
              >
                <LogOut size={18} /> Logout
              </button>
            </>
          ) : (
            <>
              <Link to="/login" className="text-sm font-medium text-zinc-600 hover:text-zinc-900 transition-colors">
                Log in
              </Link>
              <Link to="/register" className="btn-minimal !py-1.5 !px-4 text-sm">
                Sign up
              </Link>
            </>
          )}
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
