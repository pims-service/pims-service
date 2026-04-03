import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import api from '../services/api';
import { User, Mail, Lock, Loader2, Sparkles, Phone, CheckCircle2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

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
      console.error('Registration error:', err);
      setError('Registration failed. Please check if your email or username is already taken.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 relative overflow-hidden overflow-y-auto pt-20 pb-20">
      {/* Background Blobs */}
      <div className="absolute top-0 -left-4 w-96 h-96 bg-indigo-500 rounded-full mix-blend-multiply filter blur-3xl opacity-10 animate-blob"></div>
      <div className="absolute top-0 -right-4 w-96 h-96 bg-purple-500 rounded-full mix-blend-multiply filter blur-3xl opacity-10 animate-blob animation-delay-2000"></div>
      <div className="absolute -bottom-8 left-20 w-96 h-96 bg-pink-500 rounded-full mix-blend-multiply filter blur-3xl opacity-10 animate-blob animation-delay-4000"></div>

      <motion.div 
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5 }}
        className="w-full max-w-2xl relative z-10"
      >
        <div className="glass p-8 md:p-12 shadow-2xl backdrop-blur-2xl border border-white/10">
          <div className="text-center mb-10">
            <motion.div 
              initial={{ rotate: -10, opacity: 0 }}
              animate={{ rotate: 0, opacity: 1 }}
              transition={{ delay: 0.2 }}
              className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-tr from-pink-500 to-indigo-500 mb-6 shadow-lg shadow-pink-500/20"
            >
              <Sparkles className="text-white" size={32} />
            </motion.div>
            <h2 className="text-4xl font-extrabold text-white tracking-tight mb-2">Create Your Account</h2>
            <p className="text-slate-400 font-medium">Join our 30-day psychological experiment platform</p>
          </div>

          <AnimatePresence mode="wait">
            {error && (
              <motion.div 
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="bg-rose-500/10 border border-rose-500/20 text-rose-400 p-4 rounded-xl mb-8 text-sm font-medium"
              >
                {error}
              </motion.div>
            )}
          </AnimatePresence>

          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-2 group">
                <label className="text-sm font-semibold text-slate-400 ml-1 group-focus-within:text-indigo-400 transition-colors">
                  Full Name / Username
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-slate-500 group-focus-within:text-indigo-400 transition-colors">
                    <User size={20} />
                  </div>
                  <input 
                    type="text" 
                    required
                    placeholder="John Doe"
                    className="w-full bg-slate-800/50 border border-slate-700/50 rounded-2xl py-3.5 pl-11 pr-4 text-white placeholder-slate-600 focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500/50 outline-none transition-all duration-300"
                    value={formData.username}
                    onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                  />
                </div>
              </div>

              <div className="space-y-2 group">
                <label className="text-sm font-semibold text-slate-400 ml-1 group-focus-within:text-indigo-400 transition-colors">
                  Email Address
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-slate-500 group-focus-within:text-indigo-400 transition-colors">
                    <Mail size={20} />
                  </div>
                  <input 
                    type="email" 
                    required
                    placeholder="john@example.com"
                    className="w-full bg-slate-800/50 border border-slate-700/50 rounded-2xl py-3.5 pl-11 pr-4 text-white placeholder-slate-600 focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500/50 outline-none transition-all duration-300"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  />
                </div>
              </div>

              <div className="space-y-2 group">
                <label className="text-sm font-semibold text-slate-400 ml-1 group-focus-within:text-indigo-400 transition-colors">
                  WhatsApp Number
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-slate-500 group-focus-within:text-indigo-400 transition-colors">
                    <Phone size={20} />
                  </div>
                  <input 
                    type="text" 
                    required
                    placeholder="+1 (555) 000-0000"
                    className="w-full bg-slate-800/50 border border-slate-700/50 rounded-2xl py-3.5 pl-11 pr-4 text-white placeholder-slate-600 focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500/50 outline-none transition-all duration-300"
                    value={formData.whatsapp_number}
                    onChange={(e) => setFormData({ ...formData, whatsapp_number: e.target.value })}
                  />
                </div>
              </div>

              <div className="space-y-2 group">
                <label className="text-sm font-semibold text-slate-400 ml-1 group-focus-within:text-indigo-400 transition-colors">
                  Password
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-slate-500 group-focus-within:text-indigo-400 transition-colors">
                    <Lock size={20} />
                  </div>
                  <input 
                    type="password" 
                    required
                    placeholder="••••••••"
                    className="w-full bg-slate-800/50 border border-slate-700/50 rounded-2xl py-3.5 pl-11 pr-4 text-white placeholder-slate-600 focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500/50 outline-none transition-all duration-300"
                    value={formData.password}
                    onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  />
                </div>
              </div>
            </div>

            <div className="space-y-4 pt-4 border-t border-white/5 mt-6">
              <label className="flex items-center gap-4 cursor-pointer group p-3 rounded-xl hover:bg-white/5 transition-all">
                <div className="relative flex items-center justify-center">
                  <input 
                    type="checkbox" 
                    className="peer appearance-none w-6 h-6 rounded-lg border-2 border-slate-700 bg-slate-800/50 checked:bg-indigo-600 checked:border-indigo-600 transition-all cursor-pointer"
                    checked={formData.email_consent}
                    onChange={(e) => setFormData({ ...formData, email_consent: e.target.checked })}
                  />
                  <CheckCircle2 className="absolute text-white opacity-0 peer-checked:opacity-100 transition-opacity pointer-events-none" size={16} />
                </div>
                <span className="text-sm text-slate-400 font-medium group-hover:text-slate-300 transition-colors">I agree to receive experiment updates and results via Email.</span>
              </label>

              <label className="flex items-center gap-4 cursor-pointer group p-3 rounded-xl hover:bg-white/5 transition-all">
                <div className="relative flex items-center justify-center">
                  <input 
                    type="checkbox" 
                    className="peer appearance-none w-6 h-6 rounded-lg border-2 border-slate-700 bg-slate-800/50 checked:bg-indigo-600 checked:border-indigo-600 transition-all cursor-pointer"
                    checked={formData.whatsapp_consent}
                    onChange={(e) => setFormData({ ...formData, whatsapp_consent: e.target.checked })}
                  />
                  <CheckCircle2 className="absolute text-white opacity-0 peer-checked:opacity-100 transition-opacity pointer-events-none" size={16} />
                </div>
                <span className="text-sm text-slate-400 font-medium group-hover:text-slate-300 transition-colors">I agree to receive daily check-in notifications via WhatsApp.</span>
              </label>
            </div>

            <div className="pt-4">
              <button 
                type="submit" 
                disabled={loading}
                className="w-full bg-gradient-to-r from-indigo-600 to-purple-600 text-white font-bold py-4 rounded-2xl shadow-xl shadow-indigo-600/20 hover:shadow-indigo-600/40 hover:scale-[1.01] active:scale-[0.99] transition-all duration-300 disabled:opacity-70 disabled:pointer-events-none"
              >
                {loading ? (
                  <span className="flex items-center justify-center gap-2">
                    <Loader2 className="animate-spin" size={22} />
                    Creating Account...
                  </span>
                ) : 'Join Experiment'}
              </button>
            </div>
          </form>

          <p className="mt-8 text-center text-slate-500 font-medium text-sm transition-colors">
            Already have an account? {' '}
            <Link to="/login" className="text-indigo-400 font-bold hover:underline transition-all">
              Sign in here
            </Link>
          </p>
        </div>
      </motion.div>
    </div>
  );
};

export default RegisterPage;
