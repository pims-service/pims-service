import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import api from '../services/api';
import { useTranslation } from 'react-i18next';
import { User, Mail, Phone, Lock, Calendar, ArrowRight, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react';

const RegisterPage: React.FC = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    username: '',
    full_name: '',
    email: '',
    whatsapp_number: '',
    password: '',
    confirm_password: '',
    date_of_birth: '',
    consent_agreed: false,
    consent_version: '1.0',
    otp: '',
  });

  const [errors, setErrors] = useState<Record<string, string[]>>({});
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [phase, setPhase] = useState<'details' | 'otp'>('details');
  const [otpMessage, setOtpMessage] = useState('');
  const { t } = useTranslation();

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
    if (errors[name]) {
      const newErrors = { ...errors };
      delete newErrors[name];
      setErrors(newErrors);
    }
  };

  const handleSendOtp = async () => {
    if (!formData.email) {
      setErrors({ email: ['Email is required to send OTP.'] });
      return;
    }
    setLoading(true);
    setErrors({});
    try {
      const res = await api.post('/auth/send-otp/', { email: formData.email });
      setOtpMessage(res.data.message || 'OTP sent! Please check your email.');
      setPhase('otp');
    } catch (err: any) {
      if (err.response?.data?.error) {
        setErrors({ non_field_errors: [err.response.data.error] });
      } else {
        setErrors({ non_field_errors: ['Failed to send OTP. Please try again.'] });
      }
    } finally {
      setLoading(false);
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
            <CheckCircle2 className="w-16 h-16 text-black" />
          </div>
          <h2 className="text-2xl font-bold text-zinc-900">Registration Successful!</h2>
          <p className="text-zinc-600">Your account has been created. Redirecting to login...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-[90vh] flex flex-col p-4 bg-white relative">
      <div className="flex-1 flex items-center justify-center">
        <div className="card-minimal max-w-md w-full p-8 space-y-8">
          <div className="space-y-2 text-center">
            <h1 className="text-3xl font-bold tracking-tight text-zinc-900">{t('register.title')}</h1>
            <p className="text-zinc-500">{t('register.subtitle')}</p>
          </div>

        {Object.keys(errors).length > 0 && (
          <div className="p-4 rounded-none bg-white border-2 border-black space-y-2">
            <div className="flex items-center gap-2 text-black font-bold uppercase tracking-tight mb-1">
              <AlertCircle className="w-5 h-5" />
              <span>Registration Failed</span>
            </div>
            <ul className="list-disc list-inside text-sm text-black space-y-1">
              {Object.entries(errors).map(([field, messages]) => (
                <li key={field}>
                  <span className="capitalize font-bold">{field.replace('_', ' ')}:</span> {messages[0]}
                </li>
              ))}
            </ul>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 gap-4">
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-zinc-700" htmlFor="username">{t('register.username')}</label>
              <div className="relative">
                <User className="absolute start-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400" />
                <input
                  id="username"
                  name="username"
                  type="text"
                  required
                  placeholder={t('register.username_placeholder')}
                  className={`input-minimal !ps-10 ${errors.username ? 'border-black border-2 ring-0' : ''}`}
                  value={formData.username}
                  onChange={handleChange}
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="text-sm font-medium text-zinc-700" htmlFor="full_name">{t('register.full_name')}</label>
              <div className="relative">
                <User className="absolute start-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400" />
                <input
                  id="full_name"
                  name="full_name"
                  type="text"
                  required
                  placeholder={t('register.full_name_placeholder')}
                  className={`input-minimal !ps-10 ${errors.full_name ? 'border-black border-2 ring-0' : ''}`}
                  value={formData.full_name}
                  onChange={handleChange}
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="text-sm font-medium text-zinc-700" htmlFor="email">{t('register.email')}</label>
              <div className="relative">
                <Mail className="absolute start-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400" />
                <input
                  id="email"
                  name="email"
                  type="email"
                  required
                  placeholder={t('register.email_placeholder')}
                  className={`input-minimal !ps-10 ${errors.email ? 'border-black border-2 ring-0' : ''}`}
                  value={formData.email}
                  onChange={handleChange}
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="text-sm font-medium text-zinc-700" htmlFor="whatsapp_number">{t('register.whatsapp_number')}</label>
              <div className="relative">
                <Phone className="absolute start-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400" />
                <input
                  id="whatsapp_number"
                  name="whatsapp_number"
                  type="text"
                  required
                  placeholder={t('register.whatsapp_number_placeholder')}
                  className={`input-minimal !ps-10 ${errors.whatsapp_number ? 'border-black border-2 ring-0' : ''}`}
                  value={formData.whatsapp_number}
                  onChange={handleChange}
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="text-sm font-medium text-zinc-700" htmlFor="date_of_birth">{t('register.date_of_birth')}</label>
              <div className="relative">
                <Calendar className="absolute start-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400" />
                <input
                  id="date_of_birth"
                  name="date_of_birth"
                  type="date"
                  required
                  className={`input-minimal !ps-10 ${errors.date_of_birth ? 'border-black border-2 ring-0' : ''}`}
                  value={formData.date_of_birth}
                  onChange={handleChange}
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <label className="text-sm font-medium text-zinc-700" htmlFor="password">{t('register.password')}</label>
                <div className="relative">
                  <Lock className="absolute start-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400" />
                  <input
                    id="password"
                    name="password"
                    type="password"
                    required
                    placeholder={t('register.password_placeholder')}
                    className={`input-minimal !ps-10 ${errors.password ? 'border-black border-2 ring-0' : ''}`}
                    value={formData.password}
                    onChange={handleChange}
                  />
                </div>
              </div>
              <div className="space-y-1.5">
                <label className="text-sm font-medium text-zinc-700" htmlFor="confirm_password">{t('register.confirm_password')}</label>
                <div className="relative">
                  <Lock className="absolute start-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400" />
                  <input
                    id="confirm_password"
                    name="confirm_password"
                    type="password"
                    required
                    placeholder={t('register.confirm_password_placeholder')}
                    className={`input-minimal !ps-10 ${errors.password ? 'border-black border-2 ring-0' : ''}`}
                    value={formData.confirm_password}
                    onChange={handleChange}
                  />
                </div>
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
              {t('register.consent_text')}
            </label>
          </div>

          {phase === 'otp' && (
            <div className="space-y-1.5 pt-2 border-t border-zinc-100">
              <label className="text-sm font-medium text-emerald-700 font-bold" htmlFor="otp">Verification Code</label>
              <input
                id="otp"
                name="otp"
                type="text"
                required
                placeholder="6-digit code from email"
                className={`input-minimal ${errors.otp ? 'border-black border-2 ring-0' : 'border-emerald-200 bg-emerald-50'}`}
                value={formData.otp}
                onChange={handleChange}
                maxLength={6}
              />
              <p className="text-xs text-emerald-600">{otpMessage}</p>
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="btn-minimal w-full flex items-center justify-center gap-2 group py-2.5 bg-black"
          >
            {loading ? (
              <Loader2 className="w-5 h-5 animate-spin text-zinc-400" />
            ) : (
              <>
                {t('register.sign_up')} <ArrowRight className="w-4 h-4 rtl:rotate-180 rtl:group-hover:-translate-x-0.5 group-hover:translate-x-0.5 transition-transform" />
              </>
            )}
          </button>
        </form>

        <p className="text-center text-sm text-zinc-500 pt-2 border-t border-zinc-100">
          {t('register.has_account')}{' '}
          <Link to="/login" className="text-zinc-900 font-medium hover:underline underline-offset-4">
            {t('register.sign_in')}
          </Link>
        </p>
      </div>
      </div>
    </div>
  );
};

export default RegisterPage;
