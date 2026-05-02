import React, { useState } from 'react';
import { useNavigate, Link, useLocation } from 'react-router-dom';
import api from '../services/api';
import { useTranslation } from 'react-i18next';
import { User, Mail, Lock, Loader2, ArrowRight, AlertCircle, CheckCircle2 } from 'lucide-react';

const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [formData, setFormData] = useState({
    username: '',
    password: '',
  });

  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const successMessage = location.state?.message;
  const { t } = useTranslation();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await api.post('/login/', formData);
      const data = response.data;
      
      // Persist tokens
      localStorage.setItem('access_token', data.access);
      localStorage.setItem('refresh_token', data.refresh);
      
      if (data.user) {
        // Persist user info for UI/Logic
        localStorage.setItem('user_role', data.user.role);
        localStorage.setItem('user_full_name', data.user.full_name || data.user.username);
        localStorage.setItem('has_completed_baseline', String(data.user.has_completed_baseline));
        
        // Redirection based on role and onboarding status
        if (data.user.role === 'Admin') {
          navigate('/admin');
        } else if (data.user.has_completed_baseline === false) {
          navigate('/baseline-questionnaire');
        } else {
          navigate('/dashboard');
        }
        
        // Force a reload to ensure App.tsx checkAuth() returns fresh status
        window.location.reload();
      }
    } catch (err: any) {
      if (err.response?.status === 401) {
        setError(t('login.invalid_credentials'));
      } else if (err.response?.status === 500) {
        setError(t('login.server_error'));
      } else if (err.response?.data?.detail) {
        setError(err.response.data.detail);
      } else {
        setError(t('login.unexpected_error'));
      }
      console.error('Login Error:', err.response?.data || err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[80vh] flex flex-col p-4 bg-white relative">
      <div className="flex-1 flex items-center justify-center">
        <div className="card-minimal max-w-md w-full p-8 space-y-8">
          <div className="space-y-2 text-center">
            <h1 className="text-3xl font-bold tracking-tight text-zinc-900">{t('login.title')}</h1>
            <p className="text-zinc-500">{t('login.subtitle')}</p>
          </div>

        {successMessage && (
          <div className="p-4 rounded-lg bg-zinc-800 flex items-start gap-3">
            <CheckCircle2 className="w-5 h-5 text-white shrink-0 mt-0.5" />
            <p className="text-sm font-medium text-white">{successMessage}</p>
          </div>
        )}

        {error && (
          <div className="p-4 rounded-lg bg-zinc-50 border border-zinc-200 flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-zinc-600 shrink-0 mt-0.5" />
            <p className="text-sm font-medium text-zinc-700">{error}</p>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-4">
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-zinc-700" htmlFor="username">
                {t('login.username')}
              </label>
              <div className="relative">
                <User className="absolute start-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400" />
                <input
                  id="username"
                  name="username"
                  type="text"
                  required
                  placeholder={t('login.username_placeholder')}
                  className="input-minimal !ps-10"
                  value={formData.username}
                  onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <label className="text-sm font-medium text-zinc-700" htmlFor="password">
                  {t('login.password')}
                </label>
                <Link to="/forgot-password" title="Coming Soon" className="text-xs text-zinc-500 hover:text-zinc-900 transition-colors">
                  {t('login.forgot_password')}
                </Link>
              </div>
              <div className="relative">
                <Lock className="absolute start-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400" />
                <input
                  id="password"
                  name="password"
                  type="password"
                  required
                  placeholder={t('login.password_placeholder')}
                  className="input-minimal !ps-10"
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                />
              </div>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="btn-minimal w-full flex items-center justify-center gap-2 group py-2.5 mt-2"
          >
            {loading ? (
              <Loader2 className="w-5 h-5 animate-spin text-zinc-400" />
            ) : (
              <>
                {t('login.sign_in')}
                <ArrowRight className="w-4 h-4 rtl:rotate-180 rtl:group-hover:-translate-x-0.5 group-hover:translate-x-0.5 transition-transform" />
              </>
            )}
          </button>
        </form>

        <p className="text-center text-sm text-zinc-500 pt-2 border-t border-zinc-100">
          {t('login.no_account')}{' '}
          <Link to="/register" className="text-zinc-900 font-medium hover:underline underline-offset-4">
            {t('login.create_one')}
          </Link>
        </p>
      </div>
      </div>
    </div>
  );
};

export default LoginPage;
