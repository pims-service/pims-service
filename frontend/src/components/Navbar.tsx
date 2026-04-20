import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { LogOut, User, LayoutDashboard, Settings, Menu, X } from 'lucide-react';

const Navbar: React.FC = () => {
  const navigate = useNavigate();
  const isAuthenticated = !!localStorage.getItem('access_token');
  const userRole = localStorage.getItem('user_role');
  const isAdmin = userRole === 'Admin';
  const [isMenuOpen, setIsMenuOpen] = React.useState(false);

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
        
        {/* Desktop Menu */}
        <div className="hidden md:flex items-center gap-8">
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
                className="text-sm font-medium text-zinc-900 border border-zinc-200 px-3 py-1 rounded hover:bg-zinc-900 hover:text-white transition-all flex items-center gap-2"
              >
                <LogOut size={16} /> Logout
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

        {/* Mobile Hamburger Toggle */}
        <div className="md:hidden flex items-center">
          <button 
            onClick={() => setIsMenuOpen(!isMenuOpen)}
            className="text-zinc-600 hover:text-zinc-900 focus:outline-none"
          >
            {isMenuOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>
      </div>

      {/* Mobile Menu Drawer */}
      {isMenuOpen && (
        <div className="md:hidden border-t border-zinc-100 bg-white py-4 px-6 space-y-4 animate-in slide-in-from-top-2 duration-200">
          {isAuthenticated ? (
            <>
              <Link 
                to="/dashboard" 
                onClick={() => setIsMenuOpen(false)}
                className="flex items-center gap-3 text-sm font-medium text-zinc-600 py-2"
              >
                <LayoutDashboard size={20} /> Dashboard
              </Link>
              {isAdmin && (
                <Link 
                  to="/admin" 
                  onClick={() => setIsMenuOpen(false)}
                  className="flex items-center gap-3 text-sm font-medium text-zinc-600 py-2"
                >
                  <Settings size={20} /> Admin Hub
                </Link>
              )}
              <Link 
                to="/profile" 
                onClick={() => setIsMenuOpen(false)}
                className="flex items-center gap-3 text-sm font-medium text-zinc-600 py-2"
              >
                <User size={20} /> Profile
              </Link>
              <button 
                onClick={handleLogout}
                className="flex items-center gap-3 text-sm font-medium text-red-600 py-2 w-full text-left"
              >
                <LogOut size={20} /> Logout
              </button>
            </>
          ) : (
            <>
              <Link 
                to="/login" 
                onClick={() => setIsMenuOpen(false)}
                className="block text-sm font-medium text-zinc-600 py-2"
              >
                Log in
              </Link>
              <Link 
                to="/register" 
                onClick={() => setIsMenuOpen(false)}
                className="block text-sm font-bold text-zinc-900 py-2"
              >
                Sign up
              </Link>
            </>
          )}
        </div>
      )}
    </nav>
  );
};

export default Navbar;
