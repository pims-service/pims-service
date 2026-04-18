import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import api from '../services/api';
import { User, Mail, Phone, ArrowRight, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react';

const RegisterPage: React.FC = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    username: '',
    full_name: '',
    email: '',
    whatsapp_number: '',
    password: '',
    confirm_password: '',
    consent_agreed: false,
    consent_version: '1.0',
  });

  const [errors, setErrors] = useState<Record<string, string[]>>({});
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
    // Clear error when user types
    if (errors[name]) {
      const newErrors = { ...errors };
      delete newErrors[name];
      setErrors(newErrors);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setErrors({});

    try {
      const response = await api.post('/register/', formData);
      if (response.status === 201) {
        setSuccess(true);
        setTimeout(() => {
          navigate('/login', { state: { message: 'Account created successfully. Please log in.' } });
        }, 2000);
      }
    } catch (err: any) {
      if (err.response?.data) {
        console.error('Registration Error:', err.response.data);
        const data = err.response.data;
        if (typeof data === 'string') {
          setErrors({ non_field_errors: [data] });
        } else if (typeof data === 'object' && !Array.isArray(data)) {
          // Normalize: ensure each value is an array of strings
          const normalized: Record<string, string[]> = {};
          for (const [key, val] of Object.entries(data)) {
            if (Array.isArray(val)) {
              normalized[key] = val.map(String);
            } else {
              normalized[key] = [String(val)];
            }
          }
          setErrors(normalized);
        } else {
          setErrors({ non_field_errors: [String(data)] });
        }
      } else {
        setErrors({ non_field_errors: ['An unexpected error occurred. Please try again.'] });
      }
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="min-h-[80vh] flex items-center justify-center p-4">
        <div className="card-minimal max-w-md w-full p-8 text-center space-y-4">
          <div className="flex justify-center">
            <CheckCircle2 className="w-16 h-16 text-green-500" />
          </div>
          <h2 className="text-2xl font-bold text-zinc-900">Registration Successful!</h2>
          <p className="text-zinc-600">Your account has been created. Redirecting to login...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-[90vh] flex items-center justify-center p-4 bg-zinc-50/50">
      <div className="card-minimal max-w-md w-full p-8 space-y-8">
        <div className="space-y-2 text-center">
          <h1 className="text-3xl font-bold tracking-tight text-zinc-900">Create an account</h1>
          <p className="text-zinc-500">Enter your details below to get started</p>
        </div>

        {Object.keys(errors).length > 0 && (
          <div className="p-4 rounded-lg bg-red-50 border border-red-200 space-y-2">
            <div className="flex items-center gap-2 text-red-800 font-semibold mb-1">
              <AlertCircle className="w-5 h-5" />
              <span>Registration Failed</span>
            </div>
            <ul className="list-disc list-inside text-sm text-red-700 space-y-1">
              {Object.entries(errors).map(([field, messages]) => (
                <li key={field}>
                  <span className="capitalize font-medium">{field.replace('_', ' ')}:</span> {messages[0]}
                </li>
              ))}
            </ul>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 gap-4">
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-zinc-700" htmlFor="username">Username</label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400" />
                <input
                  id="username"
                  name="username"
                  type="text"
                  required
                  placeholder="johndoe"
                  className={`input-minimal pl-10 ${errors.username ? 'border-red-300 ring-red-100' : ''}`}
                  value={formData.username}
                  onChange={handleChange}
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="text-sm font-medium text-zinc-700" htmlFor="full_name">Full Name</label>
              <input
                id="full_name"
                name="full_name"
                type="text"
                required
                placeholder="John Doe"
                className={`input-minimal ${errors.full_name ? 'border-red-300 ring-red-100' : ''}`}
                value={formData.full_name}
                onChange={handleChange}
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-sm font-medium text-zinc-700" htmlFor="email">Email Address</label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400" />
                <input
                  id="email"
                  name="email"
                  type="email"
                  required
                  placeholder="name@example.com"
                  className={`input-minimal pl-10 ${errors.email ? 'border-red-300 ring-red-100' : ''}`}
                  value={formData.email}
                  onChange={handleChange}
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="text-sm font-medium text-zinc-700" htmlFor="whatsapp_number">WhatsApp Number</label>
              <div className="relative">
                <Phone className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400" />
                <input
                  id="whatsapp_number"
                  name="whatsapp_number"
                  type="text"
                  required
                  placeholder="+1234567890"
                  className={`input-minimal pl-10 ${errors.whatsapp_number ? 'border-red-300 ring-red-100' : ''}`}
                  value={formData.whatsapp_number}
                  onChange={handleChange}
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <label className="text-sm font-medium text-zinc-700" htmlFor="password">Password</label>
                <input
                  id="password"
                  name="password"
                  type="password"
                  required
                  placeholder="••••••••"
                  className={`input-minimal ${errors.password ? 'border-red-300 ring-red-100' : ''}`}
                  value={formData.password}
                  onChange={handleChange}
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-sm font-medium text-zinc-700" htmlFor="confirm_password">Confirm</label>
                <input
                  id="confirm_password"
                  name="confirm_password"
                  type="password"
                  required
                  placeholder="••••••••"
                  className={`input-minimal ${errors.password ? 'border-red-300 ring-red-100' : ''}`}
                  value={formData.confirm_password}
                  onChange={handleChange}
                />
              </div>
            </div>
          </div>

          <div className="flex items-start gap-3 py-2">
            <input
              id="consent_agreed"
              name="consent_agreed"
              type="checkbox"
              required
              className="mt-1 w-4 h-4 rounded border-zinc-300 text-zinc-900 focus:ring-zinc-900"
              checked={formData.consent_agreed}
              onChange={handleChange}
            />
            <label htmlFor="consent_agreed" className="text-sm text-zinc-600 leading-tight">
              I agree to the <Link to="/terms" className="text-zinc-900 underline underline-offset-4 hover:text-zinc-700 font-medium">terms of service</Link> and data processing policy.
            </label>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="btn-minimal w-full flex items-center justify-center gap-2 group py-2.5"
          >
            {loading ? (
              <Loader2 className="w-5 h-5 animate-spin text-zinc-400" />
            ) : (
              <>
                Create Account
                <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
              </>
            )}
          </button>
        </form>

        <p className="text-center text-sm text-zinc-500 pt-2 border-t border-zinc-100">
          Already have an account?{' '}
          <Link to="/login" className="text-zinc-900 font-medium hover:underline underline-offset-4">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
};

export default RegisterPage;
