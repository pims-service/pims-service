import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, Brain, Zap, Shield, Users } from 'lucide-react';

const LandingPage: React.FC = () => {
  return (
    <div className="max-w-6xl mx-auto px-4 py-16 sm:py-24 space-y-24">
      {/* Hero Section */}
      <div className="flex flex-col items-center text-center space-y-8">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-zinc-100 border border-zinc-200 text-zinc-600 text-sm font-medium animate-in fade-in slide-in-from-bottom-4 duration-1000">
          <Zap size={14} className="text-zinc-900" />
          <span>Phase 1 Enrollment Now Open</span>
        </div>
        
        <h1 className="text-5xl sm:text-7xl font-bold tracking-tight text-black max-w-4xl leading-[1.1]">
          The Science of <span className="underline decoration-zinc-300 decoration-4 underline-offset-8">Human Achievement</span>
        </h1>
        
        <p className="text-lg sm:text-xl text-zinc-900 max-w-2xl leading-relaxed font-medium">
          Join a global cohort in a structured psychological study exploring the intersection of behavior, habit formation, and long-term potential.
        </p>
        
        <div className="flex flex-col sm:flex-row gap-4 pt-4">
          <Link to="/register" className="btn-minimal px-10 py-4 text-lg border-2 border-black flex items-center justify-center gap-2 group hover:bg-black hover:text-white transition-all">
            Begin Application
            <ArrowRight size={20} className="group-hover:translate-x-1 transition-transform" />
          </Link>
          <Link to="/login" className="px-10 py-4 text-lg font-bold text-black border-2 border-transparent hover:border-black rounded-lg transition-all flex items-center justify-center">
            Existing Participant
          </Link>
        </div>
      </div>

      {/* Features Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        <div className="p-8 rounded-2xl border border-zinc-200 bg-white shadow-sm hover:shadow-md transition-shadow space-y-4">
          <div className="w-12 h-12 rounded-lg bg-zinc-900 flex items-center justify-center text-white">
            <Brain size={24} />
          </div>
          <h3 className="text-xl font-bold text-zinc-900">Methodical Research</h3>
          <p className="text-zinc-600 leading-relaxed">
            Our protocols are built on peer-reviewed behavioral models to ensure scientific integrity and meaningful outcomes.
          </p>
        </div>

        <div className="p-8 rounded-2xl border border-zinc-200 bg-white shadow-sm hover:shadow-md transition-shadow space-y-4">
          <div className="w-12 h-12 rounded-lg bg-zinc-100 flex items-center justify-center text-zinc-900">
            <Shield size={24} />
          </div>
          <h3 className="text-xl font-bold text-zinc-900">Privacy First</h3>
          <p className="text-zinc-600 leading-relaxed">
            Encrypted data storage and anonymized reporting ensure your identity remains protected throughout the study.
          </p>
        </div>

        <div className="p-8 rounded-2xl border border-zinc-200 bg-white shadow-sm hover:shadow-md transition-shadow space-y-4">
          <div className="w-12 h-12 rounded-lg bg-zinc-100 flex items-center justify-center text-zinc-900">
            <Users size={24} />
          </div>
          <h3 className="text-xl font-bold text-zinc-900">Collective Insights</h3>
          <p className="text-zinc-600 leading-relaxed">
            Benefit from aggregate data patterns shared with the community to understand broader human behavioral trends.
          </p>
        </div>
      </div>

      {/* Stats Section */}
      <div className="border-y border-zinc-200 py-12 grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
        <div>
          <div className="text-3xl font-bold text-zinc-900">2.4k+</div>
          <div className="text-sm text-zinc-500 uppercase tracking-wider font-semibold mt-1">Participants</div>
        </div>
        <div>
          <div className="text-3xl font-bold text-zinc-900">12k</div>
          <div className="text-sm text-zinc-500 uppercase tracking-wider font-semibold mt-1">Data Points</div>
        </div>
        <div>
          <div className="text-3xl font-bold text-zinc-900">98%</div>
          <div className="text-sm text-zinc-500 uppercase tracking-wider font-semibold mt-1">Retention</div>
        </div>
        <div>
          <div className="text-3xl font-bold text-zinc-900">14</div>
          <div className="text-sm text-zinc-500 uppercase tracking-wider font-semibold mt-1">Countries</div>
        </div>
      </div>
    </div>
  );
};

export default LandingPage;
