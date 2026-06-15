import React, { useRef } from 'react';

interface OtpInputProps {
  id?: string;
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
  error?: boolean;
}

const OtpInput: React.FC<OtpInputProps> = ({ id, value, onChange, disabled = false, error = false }) => {
  const inputsRef = useRef<(HTMLInputElement | null)[]>([]);

  // Split value into array of 6 characters
  const digits = value.split('').slice(0, 6);
  while (digits.length < 6) {
    digits.push('');
  }

  const handleInputChange = (index: number, e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    if (!val) {
      const newDigits = [...digits];
      newDigits[index] = '';
      onChange(newDigits.join(''));
      return;
    }

    // If a multi-character value is pasted/typed/programmatically set
    if (val.length > 1) {
      const cleanVal = val.replace(/\D/g, '').slice(0, 6);
      if (cleanVal) {
        onChange(cleanVal);
        const focusIndex = Math.min(cleanVal.length, 5);
        inputsRef.current[focusIndex]?.focus();
      }
      return;
    }

    // Only accept single digit
    if (!/^\d$/.test(val)) return;

    const newDigits = [...digits];
    newDigits[index] = val;
    const newValue = newDigits.join('');
    onChange(newValue);

    // Auto focus next input if not the last one
    if (index < 5) {
      inputsRef.current[index + 1]?.focus();
    }
  };

  const handleKeyDown = (index: number, e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Backspace') {
      const newDigits = [...digits];
      
      if (digits[index] !== '') {
        // Clear current box
        newDigits[index] = '';
        onChange(newDigits.join(''));
      } else if (index > 0) {
        // Clear previous box and focus it
        newDigits[index - 1] = '';
        onChange(newDigits.join(''));
        inputsRef.current[index - 1]?.focus();
      }
    }
  };

  const handlePaste = (e: React.ClipboardEvent<HTMLInputElement>) => {
    e.preventDefault();
    const pastedData = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6);
    if (pastedData) {
      onChange(pastedData);
      // Focus the last filled box or the 6th box
      const focusIndex = Math.min(pastedData.length, 5);
      inputsRef.current[focusIndex]?.focus();
    }
  };

  return (
    <div className="flex justify-between items-center gap-2 max-w-sm mx-auto" dir="ltr">
      {Array.from({ length: 6 }).map((_, index) => (
        <input
          key={index}
          id={index === 0 ? id : undefined}
          ref={(el) => {
            inputsRef.current[index] = el;
          }}
          type="text"
          inputMode="numeric"
          pattern="[0-9]*"
          maxLength={1}
          value={digits[index]}
          onChange={(e) => handleInputChange(index, e)}
          onKeyDown={(e) => handleKeyDown(index, e)}
          onPaste={handlePaste}
          disabled={disabled}
          className={`w-12 h-12 text-center text-xl font-bold rounded-xl border outline-none transition-all ${
            error 
              ? 'border-red-500 bg-red-50/10 focus:ring-2 focus:ring-red-500' 
              : 'border-zinc-200 bg-zinc-50/30 focus:border-zinc-950 focus:ring-2 focus:ring-zinc-950/10'
          } ${disabled ? 'opacity-50 cursor-not-allowed bg-zinc-100' : ''}`}
        />
      ))}
    </div>
  );
};

export default OtpInput;
