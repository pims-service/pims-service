import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, Brain, Zap, Shield, Users } from 'lucide-react';

const LandingPage: React.FC = () => {
  return (
    <div className="flex flex-col items-center justify-center py-20 text-center">
      <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full glass border-indigo-500/30 text-indigo-400 mb-8 animate-bounce">
        <Zap size={16} /> Now live: Phase 1 Enrollment Open
      </div>
      
      <h1 className="text-6xl font-extrabold mb-6 leading-tight">
        Discover the <span className="bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400">Psychology of Achievement</span>
      </h1>
      <p className="text-xl text-slate-400 max-w-2xl mb-12">
        Join over 2,000 participants in a phased psychological experiment designed to unlock human potential through daily activities and behavioral analysis.
      </p>
      
      <div className="flex gap-4">
        <Link to="/register" className="btn-premium flex items-center gap-2">
          Start Experiment <ArrowRight size={20} />
        </Link>
        <Link to="/login" className="glass px-8 py-3 font-semibold hover:bg-white/5 transition-all">
          Already a participant?
        </Link>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mt-24 max-w-6xl">
        <div className="glass p-8 text-left">
          <Brain className="text-indigo-400 mb-4" size={32} />
          <h3 className="text-xl font-bold mb-2">Scientific Approach</h3>
          <p className="text-slate-400">Our experiment is designed by clinical psychologists to ensure accurate behavioral tracking.</p>
        </div>
        <div className="glass p-8 text-left">
          <Shield className="text-indigo-400 mb-4" size={32} />
          <h3 className="text-xl font-bold mb-2">Secure & Private</h3>
          <p className="text-slate-400">Your data is encrypted and anonymized, complying with international research standards.</p>
        </div>
        <div className="glass p-8 text-left">
          <Users className="text-indigo-400 mb-4" size={32} />
          <h3 className="text-xl font-bold mb-2">Global Community</h3>
          <p className="text-slate-400">Join a network of thousands of participants sharing the same growth journey.</p>
        </div>
      </div>
    </div>
  );
};

export default LandingPage;
