import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import api from '../services/api';
import { useTranslation } from 'react-i18next';
import { User, Mail, Phone, Calendar, ArrowRight, ArrowLeft, CheckCircle2, AlertCircle, Loader2, Key, RefreshCw } from 'lucide-react';
import PasswordInput from '../components/Auth/PasswordInput';

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
  const [resending, setResending] = useState(false);
  const [showConsentModal, setShowConsentModal] = useState(false);
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

  const handleSendOTP = async (isResend: boolean = false) => {
    if (isResend) {
      setResending(true);
    } else {
      setLoading(true);
    }
    setErrors({});
    setOtpMessage('');

    // Local validation before calling send-otp
    if (!formData.username.trim()) {
      setErrors({ username: ['Username is required'] });
      setLoading(false);
      setResending(false);
      return;
    }
    if (!formData.email.trim()) {
      setErrors({ email: ['Email is required'] });
      setLoading(false);
      setResending(false);
      return;
    }
    if (!formData.password || formData.password.length < 8) {
      setErrors({ password: ['Password must be at least 8 characters'] });
      setLoading(false);
      setResending(false);
      return;
    }
    if (formData.password !== formData.confirm_password) {
      setErrors({ confirm_password: ["Password fields didn't match"] });
      setLoading(false);
      setResending(false);
      return;
    }
    if (!formData.consent_agreed) {
      setErrors({ consent_agreed: ['You must agree to the Informed Consent Form.'] });
      setLoading(false);
      setResending(false);
      return;
    }

    try {
      const response = await api.post('/auth/send-otp/', { email: formData.email });
      if (response.status === 200) {
        setPhase('otp');
        setOtpMessage(isResend ? 'A new verification code has been sent to your email.' : 'Verification code sent to your email.');
      }
    } catch (err: any) {
      if (err.response?.data) {
        const data = err.response.data;
        if (typeof data === 'string') {
          setErrors({ non_field_errors: [data] });
        } else if (typeof data === 'object') {
          const normalized: Record<string, string[]> = {};
          for (const [key, val] of Object.entries(data)) {
            normalized[key] = Array.isArray(val) ? val.map(String) : [String(val)];
          }
          setErrors(normalized);
        }
      } else {
        setErrors({ non_field_errors: ['Failed to send verification code. Please check your email and try again.'] });
      }
    } finally {
      setLoading(false);
      setResending(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (phase === 'details') {
      await handleSendOTP(false);
      return;
    }

    if (!formData.otp.trim()) {
      setErrors({ otp: ['Verification code is required'] });
      return;
    }

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
          const normalized: Record<string, string[]> = {};
          for (const [key, val] of Object.entries(data)) {
            normalized[key] = Array.isArray(val) ? val.map(String) : [String(val)];
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
          {phase === 'details' ? (
            <>
              <div className="grid grid-cols-1 gap-4">
                <div className="space-y-3">
                  <label className="block text-sm font-medium text-zinc-700" htmlFor="username">{t('register.username')}</label>
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

                <div className="space-y-3">
                  <label className="block text-sm font-medium text-zinc-700" htmlFor="full_name">{t('register.full_name')}</label>
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

                <div className="space-y-3">
                  <label className="block text-sm font-medium text-zinc-700" htmlFor="email">{t('register.email')}</label>
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

                <div className="space-y-3">
                  <label className="block text-sm font-medium text-zinc-700" htmlFor="whatsapp_number">{t('register.whatsapp_number')}</label>
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

                <div className="space-y-3">
                  <label className="block text-sm font-medium text-zinc-700" htmlFor="date_of_birth">{t('register.date_of_birth')}</label>
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
                  <div className="space-y-3">
                    <label className="block text-sm font-medium text-zinc-700" htmlFor="password">{t('register.password')}</label>
                    <PasswordInput
                      id="password"
                      name="password"
                      required
                      placeholder={t('register.password_placeholder')}
                      className={errors.password ? 'border-black border-2 ring-0' : ''}
                      value={formData.password}
                      onChange={handleChange}
                    />
                  </div>
                  <div className="space-y-3">
                    <label className="block text-sm font-medium text-zinc-700" htmlFor="confirm_password">{t('register.confirm_password')}</label>
                    <PasswordInput
                      id="confirm_password"
                      name="confirm_password"
                      required
                      placeholder={t('register.confirm_password_placeholder')}
                      className={errors.confirm_password || errors.password ? 'border-black border-2 ring-0' : ''}
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
                  className="mt-1 w-4 h-4 rounded border-2 border-black text-black focus:ring-black cursor-pointer"
                  checked={formData.consent_agreed}
                  onChange={handleChange}
                />
                <label htmlFor="consent_agreed" className="text-xs text-zinc-700 leading-tight font-medium select-none">
                  {t('register.consent_checkbox_label')}{' '}
                  <button
                    type="button"
                    onClick={() => setShowConsentModal(true)}
                    className="text-black font-bold underline hover:text-zinc-800 cursor-pointer"
                  >
                    {t('register.consent_link')}
                  </button>
                </label>
              </div>
            </>
          ) : (
            <div className="space-y-6">
              <div className="p-4 bg-zinc-50 border-2 border-black space-y-2 text-zinc-800">
                <div className="flex items-center gap-2 font-bold uppercase tracking-tight text-sm">
                  <Mail className="w-5 h-5 text-black" />
                  <span>Verify your email</span>
                </div>
                <p className="text-xs leading-relaxed">
                  We've sent a 6-digit verification code to <strong className="text-black">{formData.email}</strong>. 
                  Please check your inbox and enter the code below to complete your registration.
                </p>
              </div>

              <div className="space-y-3">
                <label className="block text-sm font-medium text-zinc-700" htmlFor="otp">Verification Code</label>
                <div className="relative">
                  <Key className="absolute start-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400" />
                  <input
                    id="otp"
                    name="otp"
                    type="text"
                    required
                    placeholder="Enter 6-digit code"
                    className={`input-minimal !ps-10 tracking-[0.25em] text-center font-mono font-bold text-lg ${
                      errors.otp ? 'border-black border-2 ring-0' : 'border-zinc-300'
                    }`}
                    value={formData.otp}
                    onChange={handleChange}
                    maxLength={6}
                  />
                </div>
                {otpMessage && <p className="text-xs text-emerald-600 font-medium italic mt-1">{otpMessage}</p>}
              </div>
              <div className="flex justify-between items-center gap-4 mt-4">
                <button
                  type="button"
                  onClick={() => setPhase('details')}
                  className="flex-1 border-2 border-black py-2.5 px-4 uppercase font-bold text-xs flex items-center justify-center gap-2 hover:bg-zinc-50 cursor-pointer"
                >
                  <ArrowLeft className="w-4 h-4" />
                  Edit Details
                </button>
                <button
                  type="button"
                  onClick={() => handleSendOTP(true)}
                  disabled={resending}
                  className="flex-1 border-2 border-black py-2.5 px-4 uppercase font-bold text-xs flex items-center justify-center gap-2 hover:bg-zinc-50 disabled:opacity-50 cursor-pointer"
                >
                  {resending ? (
                    <Loader2 className="w-4 h-4 animate-spin text-zinc-500" />
                  ) : (
                    <RefreshCw className="w-4 h-4" />
                  )}
                  Resend Code
                </button>
              </div>
            </div>
          )}
          <button
            type="submit"
            disabled={loading || (phase === 'details' && !formData.consent_agreed)}
            className={`btn-minimal w-full flex items-center justify-center gap-2 group py-2.5 transition-all duration-200 ${
              (phase === 'details' && !formData.consent_agreed) || loading
                ? 'bg-zinc-200 text-zinc-400 cursor-not-allowed border-zinc-300'
                : 'bg-black text-white hover:bg-zinc-800 border-black'
            }`}
          >
            {loading ? (
              <Loader2 className="w-5 h-5 animate-spin text-zinc-400" />
            ) : (
              <>
                {phase === 'details' ? 'Send Verification Code' : 'Verify & Sign Up'}{' '}
                <ArrowRight className="w-4 h-4 rtl:rotate-180 rtl:group-hover:-translate-x-0.5 group-hover:translate-x-0.5 transition-transform" />
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

      {/* Consent Modal */}
      {showConsentModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-60 p-4 transition-opacity duration-200">
          <div className="bg-white border-2 border-black max-w-lg w-full p-6 space-y-4 max-h-[85vh] overflow-y-auto rounded-none shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] relative flex flex-col">
            <div className="flex justify-between items-center border-b-2 border-black pb-2">
              <h2 className="text-sm font-bold uppercase tracking-wider text-black">{t('register.consent_header')}</h2>
              <button 
                type="button" 
                onClick={() => setShowConsentModal(false)} 
                className="text-black font-bold text-xs uppercase tracking-wider border border-black px-2 py-0.5 hover:bg-zinc-100"
              >
                Close
              </button>
            </div>
            
            <div className="text-xs text-zinc-700 space-y-4 leading-relaxed font-sans overflow-y-auto pr-1">
              <div>
                <h4 className="font-bold text-black text-sm mb-1">{t('register.consent_section1_title')}</h4>
                <p>{t('register.consent_section1_text')}</p>
              </div>
              <div>
                <h4 className="font-bold text-black text-sm mb-1">{t('register.consent_section2_title')}</h4>
                <p>{t('register.consent_section2_text')}</p>
              </div>
              <div>
                <h4 className="font-bold text-black text-sm mb-1">{t('register.consent_section3_title')}</h4>
                <p className="text-black font-semibold bg-yellow-50 p-2 border border-dashed border-yellow-300 rounded-none leading-relaxed">
                  {t('register.consent_section3_text')}
                </p>
              </div>
              <div>
                <h4 className="font-bold text-black text-sm mb-1">{t('register.consent_section4_title')}</h4>
                <p>{t('register.consent_section4_text')}</p>
              </div>
            </div>
            
            <div className="pt-3 border-t-2 border-black flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setShowConsentModal(false)}
                className="border border-black px-3 py-1.5 text-xs font-bold uppercase tracking-wider hover:bg-zinc-100"
              >
                Read Later
              </button>
              <button
                type="button"
                onClick={() => {
                  setFormData(prev => ({ ...prev, consent_agreed: true }));
                  setShowConsentModal(false);
                }}
                className="bg-black text-white px-4 py-1.5 text-xs font-bold uppercase tracking-wider hover:bg-zinc-800"
              >
                Agree & Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default RegisterPage;
