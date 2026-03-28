import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import { User, Mail, Lock, Loader2, Sparkles, Phone } from 'lucide-react';

const RegisterPage: React.FC = () => {
  const [formData, setFormData] = useState({ 
    username: '', 
    email: '', 
    password: '',
    whatsapp_number: '',
    email_consent: false,
    whatsapp_consent: false
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      await api.post('/users/register/', formData);
      navigate('/login', { state: { message: 'Registration successful! Please log in.' } });
    } catch (err: any) {
      setError('Registration failed. Please check your details.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto mt-20 pb-20">
      <div className="glass p-10">
        <div className="flex justify-center mb-6">
          <div className="p-4 rounded-2xl bg-gradient-to-tr from-indigo-500 to-pink-500">
            <Sparkles className="text-white" size={32} />
          </div>
        </div>
        <h2 className="text-3xl font-bold mb-2 text-center">Join the Experiment</h2>
        <p className="text-slate-400 text-center mb-8 text-sm">Start your 30-day psychological journey today.</p>
        
        {error && <div className="bg-rose-500/20 text-rose-300 p-4 rounded-lg mb-6 text-sm">{error}</div>}
        
        <form onSubmit={handleSubmit} className="space-y-5">
          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-400">Username</label>
            <div className="relative">
              <User className="absolute left-3 top-3 text-slate-500" size={20} />
              <input 
                type="text" 
                required
                className="w-full bg-slate-900 border border-slate-700 rounded-lg py-3 pl-10 pr-4 focus:ring-2 focus:ring-indigo-500 outline-none transition-all"
                value={formData.username}
                onChange={(e) => setFormData({ ...formData, username: e.target.value })}
              />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-400">Email Address</label>
              <div className="relative">
                <Mail className="absolute left-3 top-3 text-slate-500" size={20} />
                <input 
                  type="email" 
                  required
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg py-3 pl-10 pr-4 focus:ring-2 focus:ring-indigo-500 outline-none transition-all"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                />
              </div>
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-400">WhatsApp Number</label>
              <div className="relative">
                <Phone className="absolute left-3 top-3 text-slate-500" size={20} />
                <input 
                  type="text" 
                  required
                  placeholder="+1234567890"
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg py-3 pl-10 pr-4 focus:ring-2 focus:ring-indigo-500 outline-none transition-all"
                  value={formData.whatsapp_number}
                  onChange={(e) => setFormData({ ...formData, whatsapp_number: e.target.value })}
                />
              </div>
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

          <div className="space-y-4 pt-2">
            <label className="flex items-center gap-3 cursor-pointer group">
              <input 
                type="checkbox" 
                className="w-5 h-5 rounded border-slate-700 bg-slate-900 text-indigo-500 focus:ring-indigo-500"
                checked={formData.email_consent}
                onChange={(e) => setFormData({ ...formData, email_consent: e.target.checked })}
              />
              <span className="text-sm text-slate-400 group-hover:text-slate-300">I agree to receive experiment updates via Email.</span>
            </label>
            <label className="flex items-center gap-3 cursor-pointer group">
              <input 
                type="checkbox" 
                className="w-5 h-5 rounded border-slate-700 bg-slate-900 text-indigo-500 focus:ring-indigo-500"
                checked={formData.whatsapp_consent}
                onChange={(e) => setFormData({ ...formData, whatsapp_consent: e.target.checked })}
              />
              <span className="text-sm text-slate-400 group-hover:text-slate-300">I agree to receive daily notifications via WhatsApp.</span>
            </label>
          </div>
          <button 
            type="submit" 
            disabled={loading}
            className="w-full btn-premium flex items-center justify-center gap-2 mt-4"
          >
            {loading ? <Loader2 className="animate-spin" /> : 'Create Account'}
          </button>
        </form>
      </div>
    </div>
  );
};

export default RegisterPage;
