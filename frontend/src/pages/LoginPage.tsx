import React, { useState } from 'react';
import { useNavigate, Link, useLocation } from 'react-router-dom';
import api from '../services/api';
import { Mail, Lock, Loader2, ArrowRight, AlertCircle, CheckCircle2 } from 'lucide-react';

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
        
        // Redirection based on role
        if (data.user.role === 'Admin') {
          navigate('/admin');
        } else {
          navigate('/dashboard');
        }
        
        // Force a reload to ensure App.tsx checkAuth() returns fresh status
        window.location.reload();
      }
    } catch (err: any) {
      if (err.response?.status === 401) {
        setError('Invalid username or password. Please try again.');
      } else if (err.response?.status === 500) {
        setError('Server error (500). Please contact administration.');
      } else if (err.response?.data?.detail) {
        setError(err.response.data.detail);
      } else {
        setError('An unexpected error occurred. Please try again.');
      }
      console.error('Login Error:', err.response?.data || err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[80vh] flex items-center justify-center p-4 bg-zinc-50/50">
      <div className="card-minimal max-w-md w-full p-8 space-y-8">
        <div className="space-y-2 text-center">
          <h1 className="text-3xl font-bold tracking-tight text-zinc-900">Welcome back</h1>
          <p className="text-zinc-500">Enter your credentials to access your account</p>
        </div>

        {successMessage && (
          <div className="p-3 rounded-md bg-green-50 border border-green-100 flex items-start gap-3">
            <CheckCircle2 className="w-5 h-5 text-green-600 shrink-0 mt-0.5" />
            <p className="text-sm text-green-700">{successMessage}</p>
          </div>
        )}

        {error && (
          <div className="p-3 rounded-md bg-red-50 border border-red-100 flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
            <p className="text-sm text-red-700">{error}</p>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-4">
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-zinc-700" htmlFor="username">
                Username
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400" />
                <input
                  id="username"
                  name="username"
                  type="text"
                  required
                  placeholder="johndoe"
                  className="input-minimal pl-10"
                  value={formData.username}
                  onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <label className="text-sm font-medium text-zinc-700" htmlFor="password">
                  Password
                </label>
                <Link to="/forgot-password" title="Coming Soon" className="text-xs text-zinc-500 hover:text-zinc-900 transition-colors">
                  Forgot password?
                </Link>
              </div>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400" />
                <input
                  id="password"
                  name="password"
                  type="password"
                  required
                  placeholder="••••••••"
                  className="input-minimal pl-10"
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
                Sign In
                <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
              </>
            )}
          </button>
        </form>

        <p className="text-center text-sm text-zinc-500 pt-2 border-t border-zinc-100">
          Don't have an account?{' '}
          <Link to="/register" className="text-zinc-900 font-medium hover:underline underline-offset-4">
            Create one
          </Link>
        </p>
      </div>
    </div>
  );
};

export default LoginPage;
