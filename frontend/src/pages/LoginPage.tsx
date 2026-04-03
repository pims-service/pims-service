import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import { Mail, Lock, Loader2 } from 'lucide-react';

const LoginPage: React.FC = () => {
  const [formData, setFormData] = useState({ username: '', password: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const { data } = await api.post('/login/', formData);
      localStorage.setItem('access_token', data.access);
      localStorage.setItem('refresh_token', data.refresh);
      
      // Store user metadata for immediate UI updates
      if (data.user) {
        localStorage.setItem('user_role', data.user.role);
        localStorage.setItem('user_full_name', data.user.full_name);
        
        // Dynamic Role-Based Redirection
        if (data.user.role === 'Admin') {
          navigate('/admin');
        } else {
          navigate('/dashboard');
        }
      } else {
        navigate('/dashboard');
      }
    } catch (err: any) {
      setError('Invalid username or password');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto mt-20">
      <div className="glass p-10">
        <h2 className="text-3xl font-bold mb-8 text-center">Welcome Back</h2>
        {error && <div className="bg-rose-500/20 text-rose-300 p-4 rounded-lg mb-6 text-sm">{error}</div>}
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-400">Username</label>
            <div className="relative">
              <Mail className="absolute left-3 top-3 text-slate-500" size={20} />
              <input 
                type="text" 
                required
                className="w-full bg-slate-900 border border-slate-700 rounded-lg py-3 pl-10 pr-4 focus:ring-2 focus:ring-indigo-500 outline-none transition-all"
                value={formData.username}
                onChange={(e) => setFormData({ ...formData, username: e.target.value })}
              />
            </div>
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-400">Password</label>
            <div className="relative">
              <Lock className="absolute left-3 top-3 text-slate-500" size={20} />
              <input 
                type="password" 
                required
                className="w-full bg-slate-900 border border-slate-700 rounded-lg py-3 pl-10 pr-4 focus:ring-2 focus:ring-indigo-500 outline-none transition-all"
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              />
            </div>
          </div>
          <button 
            type="submit" 
            disabled={loading}
            className="w-full btn-premium flex items-center justify-center gap-2"
          >
            {loading ? <Loader2 className="animate-spin" /> : 'Log In'}
          </button>
        </form>
      </div>
    </div>
  );
};

export default LoginPage;
