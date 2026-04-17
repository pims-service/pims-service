import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { questionnairesApi } from '../../services/api';
import { Loader2 } from 'lucide-react';

const BaselineRedirect: React.FC = () => {
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchBaselineId = async () => {
      try {
        const response = await questionnairesApi.list();
        const questionnaires = response.data;

        // Priority: Find an active questionnaire marked explicitly as 'is_baseline'
        // Fallback: Use the first active questionnaire
        const baseline = questionnaires.find((q: any) => q.is_active && q.is_baseline) ||
          questionnaires.find((q: any) => q.is_active);

        if (baseline) {
          navigate(`/questionnaire/${baseline.id}`, { replace: true });
        } else {
          setError('No active assessments found. Please contact an administrator.');
        }
      } catch (err) {
        setError('Failed to load assessment information. Please try again later.');
        console.error('Baseline fetch error:', err);
      }
    };

    fetchBaselineId();
  }, [navigate]);

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[40vh] p-8 text-center bg-white rounded-xl shadow-sm border border-zinc-100">
        <p className="text-red-500 font-medium">{error}</p>
        <button
          onClick={() => window.location.reload()}
          className="mt-4 text-zinc-900 font-bold underline hover:no-underline"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-[40vh] gap-4">
      <Loader2 className="w-10 h-10 animate-spin text-zinc-900" />
      <p className="text-zinc-500 font-serif italic">Redirecting to mandatory assessment...</p>
    </div>
  );
};

export default BaselineRedirect;
