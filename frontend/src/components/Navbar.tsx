import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { LogOut, User, LayoutDashboard, Settings, Menu, X, Globe } from 'lucide-react';
import LanguageSwitcher from './LanguageSwitcher';
import { useTranslation } from 'react-i18next';

const Navbar: React.FC = () => {
  const navigate = useNavigate();
  const { t } = useTranslation();
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
        <Link to="/" className="text-xl font-bold text-zinc-900 tracking-tight flex items-center gap-2">
          PsychPlatform
        </Link>

        {/* Desktop Menu */}
        <div className="hidden md:flex items-center gap-6">
          <div className="border-r border-zinc-100 pr-4 mr-2">
            <LanguageSwitcher />
          </div>

          {isAuthenticated ? (
            <>
              {!isAdmin && (
                <Link to="/dashboard" className="text-sm font-medium text-zinc-600 hover:text-zinc-900 transition-colors flex items-center gap-2">
                  <LayoutDashboard size={18} /> {t('navbar.dashboard')}
                </Link>
              )}
              {isAdmin && (
                <Link to="/admin" className="text-sm font-medium text-zinc-600 hover:text-zinc-900 transition-colors flex items-center gap-2">
                  <Settings size={18} /> {t('navbar.admin_dashboard')}
                </Link>
              )}
              <Link to="/profile" className="text-sm font-medium text-zinc-600 hover:text-zinc-900 transition-colors flex items-center gap-2">
                <User size={18} /> {t('navbar.profile')}
              </Link>
              <button
                onClick={handleLogout}
                className="text-sm font-medium text-zinc-900 border border-zinc-200 px-3 py-1 rounded hover:bg-zinc-900 hover:text-white transition-all flex items-center gap-2"
              >
                <LogOut size={16} /> {t('navbar.logout')}
              </button>
            </>
          ) : (
            <>
              <Link to="/login" className="text-sm font-medium text-zinc-600 hover:text-zinc-900 transition-colors">
                {t('navbar.login')}
              </Link>
              <Link to="/register" className="btn-minimal !py-1.5 !px-4 text-sm">
                {t('navbar.signup')}
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
          <div className="flex items-center justify-between pb-2 border-b border-zinc-50">
            <span className="text-xs font-semibold text-zinc-400 uppercase tracking-wider">Language</span>
            <LanguageSwitcher />
          </div>
          {isAuthenticated ? (
            <>
              {!isAdmin && (
                <Link
                  to="/dashboard"
                  onClick={() => setIsMenuOpen(false)}
                  className="flex items-center gap-3 text-sm font-medium text-zinc-600 py-2"
                >
                  <LayoutDashboard size={20} /> {t('navbar.dashboard')}
                </Link>
              )}
              {isAdmin && (
                <Link
                  to="/admin"
                  onClick={() => setIsMenuOpen(false)}
                  className="flex items-center gap-3 text-sm font-medium text-zinc-600 py-2"
                >
                  <Settings size={20} /> {t('navbar.admin_dashboard')}
                </Link>
              )}
              <Link
                to="/profile"
                onClick={() => setIsMenuOpen(false)}
                className="flex items-center gap-3 text-sm font-medium text-zinc-600 py-2"
              >
                <User size={20} /> {t('navbar.profile')}
              </Link>
              <button
                onClick={handleLogout}
                className="flex items-center gap-3 text-sm font-medium text-red-600 py-2 w-full text-left"
              >
                <LogOut size={20} /> {t('navbar.logout')}
              </button>
            </>
          ) : (
            <>
              <Link
                to="/login"
                onClick={() => setIsMenuOpen(false)}
                className="block text-sm font-medium text-zinc-600 py-2"
              >
                {t('navbar.login')}
              </Link>
              <Link
                to="/register"
                onClick={() => setIsMenuOpen(false)}
                className="block text-sm font-bold text-zinc-900 py-2"
              >
                {t('navbar.signup')}
              </Link>
            </>
          )}
        </div>
      )}
    </nav>
  );
};

export default Navbar;
