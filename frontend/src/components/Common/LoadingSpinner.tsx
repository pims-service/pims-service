import React from 'react';
import { Loader2 } from 'lucide-react';

const LoadingSpinner: React.FC = () => {
  return (
    <div className="flex flex-col items-center justify-center min-h-[40vh] w-full py-20 animate-in fade-in duration-500">
      <Loader2 className="w-8 h-8 text-zinc-400 animate-spin mb-4" />
      <span className="text-zinc-500 text-sm font-medium tracking-tight">Initializing Module...</span>
    </div>
  );
};

export default LoadingSpinner;
