import React, { useState, useRef, useEffect } from 'react';

interface Option {
  id: string;
  label: string;
  numeric_value: number;
  order: number;
}

interface LikertSliderProps {
  options: Option[];
  value?: number;
  onChange: (value: number) => void;
}

const LikertSlider: React.FC<LikertSliderProps> = ({ options, value, onChange }) => {
  const sortedOptions = [...options].sort((a, b) => a.numeric_value - b.numeric_value);
  const min = sortedOptions[0]?.numeric_value || 0;
  const max = sortedOptions[sortedOptions.length - 1]?.numeric_value || 10;
  
  const [isDragging, setIsDragging] = useState(false);
  const sliderRef = useRef<HTMLDivElement>(null);

  const calculateValue = (clientX: number) => {
    if (!sliderRef.current) return;
    const rect = sliderRef.current.getBoundingClientRect();
    const percentage = Math.max(0, Math.min(1, (clientX - rect.left) / rect.width));
    const rawValue = min + percentage * (max - min);
    
    // Snap to nearest integer (or closest available numeric_value)
    const snappedValue = Math.round(rawValue);
    onChange(snappedValue);
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    setIsDragging(true);
    calculateValue(e.clientX);
  };

  const handleTouchStart = (e: React.TouchEvent) => {
    setIsDragging(true);
    calculateValue(e.touches[0].clientX);
  };

  useEffect(() => {
    const handleMove = (e: MouseEvent) => {
      if (isDragging) calculateValue(e.clientX);
    };
    const handleTouchMove = (e: TouchEvent) => {
      if (isDragging) calculateValue(e.touches[0].clientX);
    };
    const handleUp = () => setIsDragging(false);

    if (isDragging) {
      window.addEventListener('mousemove', handleMove);
      window.addEventListener('mouseup', handleUp);
      window.addEventListener('touchmove', handleTouchMove);
      window.addEventListener('touchend', handleUp);
    }

    return () => {
      window.removeEventListener('mousemove', handleMove);
      window.removeEventListener('mouseup', handleUp);
      window.removeEventListener('touchmove', handleTouchMove);
      window.removeEventListener('touchend', handleUp);
    };
  }, [isDragging]);

  const percentage = (( (value || min) - min) / (max - min)) * 100;

  return (
    <div className="py-8 px-4 select-none">
      <div 
        ref={sliderRef}
        className="relative h-2 bg-zinc-100 rounded-full cursor-pointer mb-12"
        onMouseDown={handleMouseDown}
        onTouchStart={handleTouchStart}
      >
        {/* Track highlight */}
        <div 
          className="absolute h-full bg-zinc-900 rounded-full transition-all duration-75"
          style={{ width: `${percentage}%` }}
        />
        
        {/* Handle */}
        <div 
          className={`absolute top-1/2 -translate-y-1/2 -ml-3 w-6 h-6 bg-white border-2 border-zinc-900 rounded-full shadow-lg transition-transform duration-75 ${isDragging ? 'scale-125' : ''}`}
          style={{ left: `${percentage}%` }}
        >
          {isDragging && (
             <div className="absolute -top-10 left-1/2 -translate-x-1/2 bg-zinc-900 text-white text-xs py-1 px-2 rounded whitespace-nowrap animate-in fade-in zoom-in">
                {value ?? min}
             </div>
          )}
        </div>

        {/* Labels at extremes */}
        <div className="absolute top-6 w-full flex justify-between text-xs text-zinc-500 font-medium tracking-tight">
          <span>{sortedOptions[0]?.label} ({min})</span>
          <span>{sortedOptions[sortedOptions.length - 1]?.label} ({max})</span>
        </div>
      </div>

      <div className="flex justify-between gap-1 px-1">
        {sortedOptions.map((opt) => (
          <button
            key={opt.id}
            onClick={() => onChange(opt.numeric_value)}
            className={`flex-1 flex flex-col items-center py-3 rounded-lg border transition-all duration-200 ${
              value === opt.numeric_value 
                ? 'bg-zinc-900 border-zinc-900 text-white shadow-md -translate-y-1' 
                : 'bg-white border-zinc-100 text-zinc-600 hover:border-zinc-300'
            }`}
          >
            <span className="text-lg font-bold">{opt.numeric_value}</span>
            <span className="text-[10px] uppercase font-semibold text-zinc-400">
                {value === opt.numeric_value ? 'Selected' : ''}
            </span>
          </button>
        ))}
      </div>
    </div>
  );
};

export default LikertSlider;
