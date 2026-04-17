import React from 'react';
import { CheckCircle2, Circle } from 'lucide-react';
import { motion } from 'framer-motion';

interface ResponseDetailItemProps {
  question: {
    id: string;
    content: string;
    type: 'CHOICE' | 'SCALE' | 'TEXT';
    options?: { id: string; label: string; numeric_value: number }[];
  };
  response: {
    selected_option?: string;
    text_value?: string;
  };
  index: number;
}

const ResponseDetailItem: React.FC<ResponseDetailItemProps> = ({ question, response, index }) => {
  const getScaleValue = () => {
    if (!question.options || !response.selected_option) return 0;
    const opt = question.options.find(o => o.id === response.selected_option);
    return opt ? opt.numeric_value : 0;
  };

  const maxScale = question.options ? Math.max(...question.options.map(o => o.numeric_value)) : 5;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05 }}
      className="p-6 bg-white rounded-2xl border border-zinc-100 shadow-sm space-y-4"
    >
      <div className="flex items-start gap-4">
        <span className="flex-shrink-0 w-8 h-8 rounded-full bg-zinc-50 flex items-center justify-center text-xs font-bold text-zinc-400 border border-zinc-100">
          {index + 1}
        </span>
        <h3 className="text-base font-medium text-zinc-900 pt-1 leading-relaxed">
          {question.content}
        </h3>
      </div>

      <div className="pl-12">
        {question.type === 'TEXT' && (
          <div className="p-4 bg-zinc-50 rounded-xl text-zinc-600 text-sm italic border border-zinc-100/50">
            "{response.text_value || 'No response provided'}"
          </div>
        )}

        {question.type === 'CHOICE' && (
          <div className="space-y-2">
            {question.options?.map((option) => {
              const isSelected = response.selected_option === option.id;
              return (
                <div
                  key={option.id}
                  className={`flex items-center gap-3 p-3 rounded-lg border transition-colors ${
                    isSelected 
                      ? 'bg-zinc-900 border-zinc-900 text-white shadow-md' 
                      : 'bg-white border-zinc-100 text-zinc-500'
                  }`}
                >
                  {isSelected ? (
                    <CheckCircle2 className="w-4 h-4" />
                  ) : (
                    <Circle className="w-4 h-4 opacity-20" />
                  )}
                  <span className="text-sm font-medium">{option.label}</span>
                </div>
              );
            })}
          </div>
        )}

        {question.type === 'SCALE' && (
          <div className="space-y-4 py-2">
            <div className="relative h-2 w-full bg-zinc-100 rounded-full">
              <motion.div 
                initial={{ width: 0 }}
                animate={{ width: `${(getScaleValue() / maxScale) * 100}%` }}
                className="absolute h-full bg-zinc-900 rounded-full"
              />
              {/* Markers */}
              {question.options?.map((opt) => (
                <div 
                  key={opt.id}
                  style={{ left: `${(opt.numeric_value / maxScale) * 100}%` }}
                  className="absolute top-1/2 -translate-y-1/2 w-1.5 h-1.5 rounded-full bg-zinc-300"
                />
              ))}
            </div>
            <div className="flex justify-between text-[10px] font-bold text-zinc-400 tracking-wider uppercase">
              <span>{question.options?.[0]?.label}</span>
              <span>{question.options?.[question.options.length - 1]?.label}</span>
            </div>
            <div className="text-center">
               <span className="inline-block px-3 py-1 bg-zinc-900 text-white text-[10px] font-bold rounded-full uppercase tracking-widest">
                  Selected Score: {getScaleValue()}
               </span>
            </div>
          </div>
        )}
      </div>
    </motion.div>
  );
};

export default ResponseDetailItem;
