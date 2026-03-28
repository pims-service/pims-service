import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { LogOut, User, LayoutDashboard, Settings } from 'lucide-react';

const Navbar: React.FC = () => {
  const navigate = useNavigate();
  const isAuthenticated = !!localStorage.getItem('access_token');
  const isAdmin = true; // Temporary stub

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    navigate('/login');
  };

  return (
    <nav className="glass mx-4 mt-4 px-6 py-4 flex items-center justify-between sticky top-4 z-50">
      <Link to="/" className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 to-pink-400">
        PsychPlatform
      </Link>
      
      <div className="flex items-center gap-6">
        {isAuthenticated ? (
          <>
            <Link to="/dashboard" className="flex items-center gap-2 hover:text-indigo-400 transition-colors">
              <LayoutDashboard size={20} /> Dashboard
            </Link>
            {isAdmin && (
              <Link to="/admin" className="flex items-center gap-2 hover:text-indigo-400 transition-colors">
                <Settings size={20} /> Admin
              </Link>
            )}
            <Link to="/profile" className="flex items-center gap-2 hover:text-indigo-400 transition-colors">
              <User size={20} /> Profile
            </Link>
            <button 
              onClick={handleLogout}
              className="flex items-center gap-2 text-rose-400 hover:text-rose-300 transition-colors"
            >
              <LogOut size={20} /> Logout
            </button>
          </>
        ) : (
          <>
            <Link to="/login" className="hover:text-indigo-400 transition-colors">Login</Link>
            <Link to="/register" className="btn-premium">Sign Up</Link>
          </>
        )}
      </div>
    </nav>
  );
};

export default Navbar;
