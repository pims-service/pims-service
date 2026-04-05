import React, { useState } from 'react';
import { useNavigate, Link, useLocation } from 'react-router-dom';
import axios from 'axios';
import { User, Lock, ArrowRight, AlertCircle, CheckCircle2 } from 'lucide-react';

const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [formData, setFormData] = useState({
    username: '',
    password: '',
  });

  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  // Get message from navigation state (e.g. from registration)
  const registrationMessage = (location.state as any)?.message;

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value,
    }));
    if (error) setError(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      // The API endpoint is configured in the backend to handle TokenObtainPair
      const response = await axios.post(`${import.meta.env.VITE_API_URL}/login/`, formData);
      
      const { access, refresh, user } = response.data;
      
      // Persist tokens and user info
      localStorage.setItem('access_token', access);
      localStorage.setItem('refresh_token', refresh);
      localStorage.setItem('user_role', user.role);
      localStorage.setItem('user_name', user.full_name || user.username);

      setSuccess(true);
      
      // Role-based redirection
      setTimeout(() => {
        if (user.role === 'Admin') {
          navigate('/admin');
        } else {
          navigate('/dashboard');
        }
        // Force a reload to ensure App.tsx auth state is fresh
        window.location.reload();
      }, 1000);

    } catch (err: any) {
      if (err.response?.status === 401) {
        setError('Invalid username or password.');
      } else if (err.response?.data?.detail) {
        setError(err.response.data.detail);
      } else {
        setError('An unexpected error occurred. Please try again.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  if (success) {
    return (
      <div className="min-h-[80vh] flex items-center justify-center p-4">
        <div className="card-minimal max-w-md w-full p-8 text-center space-y-4">
          <div className="flex justify-center">
            <CheckCircle2 className="w-16 h-16 text-green-500" />
          </div>
          <h2 className="text-2xl font-bold text-zinc-900">Welcome Back!</h2>
          <p className="text-zinc-600">Authentication successful. Redirecting...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-[90vh] flex items-center justify-center p-4 bg-zinc-50/50">
      <div className="card-minimal max-w-md w-full p-8 space-y-8">
        <div className="space-y-2">
          <h1 className="text-3xl font-bold tracking-tight text-zinc-900">Sign in</h1>
          <p className="text-zinc-500">Enter your credentials to access your account</p>
        </div>

        {registrationMessage && !error && (
          <div className="p-3 rounded-md bg-green-50 border border-green-100 flex items-start gap-3">
            <CheckCircle2 className="w-5 h-5 text-green-600 shrink-0 mt-0.5" />
            <p className="text-sm text-green-700">{registrationMessage}</p>
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
              <label className="text-sm font-medium text-zinc-700" htmlFor="username">Username</label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400" />
                <input
                  id="username"
                  name="username"
                  type="text"
                  required
                  placeholder="johndoe"
                  className="input-minimal pl-10"
                  value={formData.username}
                  onChange={handleChange}
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <label className="text-sm font-medium text-zinc-700" htmlFor="password">Password</label>
                <Link to="/forgot-password" title="Coming Soon" className="text-xs text-zinc-500 hover:text-zinc-900">
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
                  onChange={handleChange}
                />
              </div>
            </div>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="btn-minimal w-full flex items-center justify-center gap-2 group py-2.5 mt-2"
          >
            {isLoading ? (
              <span className="w-5 h-5 border-2 border-zinc-400 border-t-white rounded-full animate-spin" />
            ) : (
              <>
                Sign In
                <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
              </>
            )}
          </button>
        </form>

        <div className="pt-4 border-t border-zinc-100">
          <p className="text-center text-sm text-zinc-500">
            Don't have an account?{' '}
            <Link to="/register" className="text-zinc-900 font-medium hover:underline underline-offset-4">
              Create an account
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
