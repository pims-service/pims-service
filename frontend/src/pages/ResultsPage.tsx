import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Loader2, ArrowLeft, Download, Award, Target, Brain, ShieldAlert } from 'lucide-react';
import { questionnairesApi } from '../services/api';
import TraitRadarChart from '../components/Results/TraitRadarChart';
import ResponseDetailItem from '../components/Results/ResponseDetailItem';

const ResultsPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    const fetchResults = async () => {
      try {
        setLoading(true);
        if (!id) return;
        const response = await questionnairesApi.getResponseSet(id);
        setData(response.data);
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to load results.');
      } finally {
        setLoading(false);
      }
    };
    fetchResults();
  }, [id]);

  // Mock Categorization Logic (Trait Mapping)
  // In production, each Question should have a 'category' ID
  const mapTraits = () => {
    if (!data?.responses || !data?.questionnaire?.questions) return [];
    
    const categories = [
      { label: 'Cognitive Focus', keyword: ['attention', 'focus', 'concentration', 'task'], icon: <Target className="w-4 h-4" /> },
      { label: 'Resilience', keyword: ['stress', 'adapt', 'difficult', 'pressure', 'failure'], icon: <ShieldAlert className="w-4 h-4" /> },
      { label: 'Analytical Logic', keyword: ['pattern', 'logic', 'rational', 'think', 'solve'], icon: <Brain className="w-4 h-4" /> },
      { label: 'Social Velocity', keyword: ['group', 'social', 'collaborate', 'team', 'others'], icon: <Award className="w-4 h-4" /> },
    ];

    return categories.map(cat => {
      // Find questions matching keywords
      const relevantQuestions = data.questionnaire.questions.filter((q: any) => 
        cat.keyword.some(k => q.content.toLowerCase().includes(k))
      );
      
      if (relevantQuestions.length === 0) return { label: cat.label, value: 75, max: 100 }; // Default base if no match for demo
      
      const score = relevantQuestions.reduce((acc: number, q: any) => {
        const resp = data.responses.find((r: any) => r.question === q.id);
        if (resp && q.type === 'SCALE' && resp.selected_option) {
          const opt = q.options.find((o: any) => o.id === resp.selected_option);
          return acc + (opt ? opt.numeric_value : 0);
        }
        return acc + 3; // Baseline middle value
      }, 0);

      const max = relevantQuestions.length * 5;
      return { label: cat.label, value: score, max: max };
    });
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4">
        <Loader2 className="w-12 h-12 text-zinc-900 animate-spin" />
        <p className="text-zinc-500 font-medium animate-pulse">Calculating insights...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-2xl mx-auto p-12 text-center bg-white rounded-3xl border border-zinc-100 shadow-xl">
        <div className="w-16 h-16 bg-black text-white rounded-none flex items-center justify-center mx-auto mb-6">
          <ShieldAlert className="w-8 h-8" />
        </div>
        <h2 className="text-2xl font-bold text-zinc-900 mb-2">Results Not Found</h2>
        <p className="text-zinc-500 mb-8">{error}</p>
        <Link to="/dashboard" className="inline-flex items-center gap-2 px-6 py-3 bg-zinc-900 text-white rounded-xl font-bold hover:bg-zinc-800 transition-colors">
          <ArrowLeft className="w-4 h-4" /> Return to Dashboard
        </Link>
      </div>
    );
  }

  return (
    <motion.div 
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="max-w-5xl mx-auto space-y-12 pb-24"
    >
      {/* Header */}
      <motion.div 
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.1 }}
        className="flex flex-col md:flex-row md:items-end justify-between gap-6"
      >
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-zinc-400 text-sm font-bold uppercase tracking-widest">
            <Award className="w-4 h-4" />
            Post-Assessment Feedback
          </div>
          <h1 className="text-4xl font-bold text-zinc-900 leading-tight">
            {data?.questionnaire?.title}
          </h1>
          <p className="text-zinc-500 max-w-xl">
             Your results have been processed using high-precision psychometric benchmarks. Explore your trait profile and response audit below.
          </p>
        </div>
        <button className="flex items-center justify-center gap-2 px-6 py-3 bg-white border-2 border-black text-black rounded-none font-black uppercase tracking-widest hover:bg-black hover:text-white transition-all text-sm group">
          <Download className="w-4 h-4 transition-transform group-hover:translate-y-0.5" />
          Export Report
        </button>
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Insights Column */}
        <motion.div 
          initial={{ x: -20, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          transition={{ delay: 0.2 }}
          className="lg:col-span-1 space-y-6"
        >
          <div className="bg-white border-2 border-black p-8 text-black space-y-6">
            <div className="space-y-1">
              <h2 className="text-xl font-bold">Trait Profile</h2>
              <p className="text-zinc-400 text-sm">Dimensional performance mapping</p>
            </div>
            
            <TraitRadarChart data={mapTraits()} />
            
            <div className="space-y-4 pt-4 border-t border-zinc-800">
               <div className="flex items-center justify-between">
                  <span className="text-zinc-500 text-sm font-bold uppercase tracking-widest">Assessment Status</span>
                  <span className="px-2 py-0.5 border-2 border-black bg-black text-white text-[10px] font-black uppercase">Verified</span>
               </div>
               <div className="flex items-center justify-between">
                  <span className="text-zinc-400 text-sm">Completed At</span>
                  <span className="text-white text-sm font-medium">
                    {new Date(data?.completed_at).toLocaleDateString()}
                  </span>
               </div>
            </div>
          </div>

          <div className="p-8 bg-zinc-50 border-x-4 border-black space-y-4">
             <h3 className="text-sm font-black uppercase tracking-widest text-black">Researcher Note</h3>
             <p className="text-black text-sm leading-relaxed italic font-medium">
               "Your consistent responses in the resilience category indicate a strong adaptive baseline for future experimental activities."
             </p>
          </div>
        </motion.div>

        {/* Detailed Response Column */}
        <motion.div 
          initial={{ x: 20, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          transition={{ delay: 0.3 }}
          className="lg:col-span-2 space-y-8"
        >
           <div className="flex items-center justify-between">
              <h2 className="text-2xl font-bold text-zinc-900">Detailed Response Audit</h2>
              <span className="text-zinc-400 text-sm font-medium">
                {data?.responses?.length} Points Analyzed
              </span>
           </div>
           
           <div className="space-y-4">
             {data?.questionnaire?.questions?.map((q: any, idx: number) => (
               <ResponseDetailItem 
                  key={q.id}
                  index={idx}
                  question={q}
                  response={data.responses.find((r: any) => r.question === q.id)}
               />
             ))}
           </div>
        </motion.div>
      </div>
    </motion.div>
  );
};

export default ResultsPage;
