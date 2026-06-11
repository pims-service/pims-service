import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import api from '../services/api';
import { useTranslation } from 'react-i18next';
import { Mail, Key, Lock, Loader2, ArrowRight, ArrowLeft, AlertCircle, CheckCircle2 } from 'lucide-react';

const ForgotPasswordPage: React.FC = () => {
  const navigate = useNavigate();
  const { t } = useTranslation();

  const [phase, setPhase] = useState<'request' | 'verify' | 'reset'>('request');
  const [email, setEmail] = useState('');
  const [otp, setOtp] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const handleRequestSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await api.post('/auth/forgot-password/', { email: email.trim().toLowerCase() });
      setSuccess(response.data.message || t('forgot_password.request_success_default'));
      // Wait a moment for UX before showing reset inputs
      setTimeout(() => {
        setPhase('verify');
        setError(null);
        setSuccess(null);
      }, 1500);
    } catch (err: any) {
      if (err.response?.data?.email) {
        setError(Array.isArray(err.response.data.email) ? err.response.data.email[0] : err.response.data.email);
      } else if (err.response?.data?.error) {
        setError(err.response.data.error);
      } else {
        setError(t('forgot_password.request_error'));
      }
    } finally {
      setLoading(false);
    }
  };

  const handleVerifySubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await api.post('/auth/verify-reset-otp/', {
        email: email.trim().toLowerCase(),
        otp: otp.trim(),
      });
      setSuccess(response.data.message || t('forgot_password.otp_verified_success', 'Verification code accepted.'));
      // Wait a moment for UX before showing password reset inputs
      setTimeout(() => {
        setPhase('reset');
        setError(null);
        setSuccess(null);
      }, 1500);
    } catch (err: any) {
      if (err.response?.data?.otp) {
        const otpErr = err.response.data.otp;
        setError(Array.isArray(otpErr) ? otpErr[0] : otpErr);
      } else if (err.response?.data?.error) {
        setError(err.response.data.error);
      } else {
        setError(t('forgot_password.verify_error', 'Invalid or expired verification code.'));
      }
    } finally {
      setLoading(false);
    }
  };

  const handleResetSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (password !== confirmPassword) {
      setError(t('forgot_password.password_mismatch'));
      return;
    }

    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      await api.post('/auth/reset-password/', {
        email: email.trim().toLowerCase(),
        otp: otp.trim(),
        password,
        confirm_password: confirmPassword,
      });
      
      // Redirect to login with success state
      navigate('/login', {
        state: { message: t('forgot_password.reset_success_banner') }
      });
    } catch (err: any) {
      if (err.response?.data?.password) {
        const passErr = err.response.data.password;
        setError(Array.isArray(passErr) ? passErr[0] : passErr);
      } else if (err.response?.data?.otp) {
        const otpErr = err.response.data.otp;
        setError(Array.isArray(otpErr) ? otpErr[0] : otpErr);
      } else if (err.response?.data?.error) {
        setError(err.response.data.error);
      } else if (err.response?.data?.non_field_errors) {
        const nfErr = err.response.data.non_field_errors;
        setError(Array.isArray(nfErr) ? nfErr[0] : nfErr);
      } else {
        setError(t('forgot_password.reset_error_default'));
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[80vh] flex flex-col p-4 bg-white relative">
      <div className="flex-grow flex items-center justify-center">
        <div className="card-minimal max-w-md w-full p-8 space-y-8">
          
          {/* Header */}
          <div className="space-y-2 text-center">
            <h1 className="text-3xl font-bold tracking-tight text-zinc-900">
              {phase === 'request'
                ? t('forgot_password.request_title')
                : phase === 'verify'
                  ? t('forgot_password.reset_title')
                  : t('forgot_password.set_password_title')}
            </h1>
            <p className="text-zinc-500">
              {phase === 'request' 
                ? t('forgot_password.request_subtitle') 
                : phase === 'verify'
                  ? t('forgot_password.reset_subtitle', { email })
                  : t('forgot_password.set_password_subtitle')}
            </p>
          </div>

          {/* Success Alerts */}
          {success && (
            <div className="p-4 rounded-lg bg-zinc-800 flex items-start gap-3 animate-in fade-in slide-in-from-top-2 duration-300">
              <CheckCircle2 className="w-5 h-5 text-white shrink-0 mt-0.5" />
              <p className="text-sm font-medium text-white">{success}</p>
            </div>
          )}

          {/* Error Alerts */}
          {error && (
            <div className="p-4 rounded-lg bg-zinc-50 border border-zinc-200 flex items-start gap-3 animate-in fade-in slide-in-from-top-2 duration-300">
              <AlertCircle className="w-5 h-5 text-zinc-600 shrink-0 mt-0.5" />
              <p className="text-sm font-medium text-zinc-700">{error}</p>
            </div>
          )}

          {phase === 'request' && (
            /* Phase 1: Request Password Reset Form */
            <form onSubmit={handleRequestSubmit} className="space-y-4">
              <div className="space-y-3">
                <label className="block text-sm font-medium text-zinc-700" htmlFor="reset-email">
                  {t('forgot_password.email_label')}
                </label>
                <div className="relative">
                  <Mail className="absolute start-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400" />
                  <input
                    id="reset-email"
                    name="email"
                    type="email"
                    required
                    placeholder={t('forgot_password.email_placeholder')}
                    className="input-minimal !ps-10"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    disabled={loading}
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="btn-minimal w-full flex items-center justify-center gap-2 py-2.5 mt-2 group"
              >
                {loading ? (
                  <Loader2 className="w-5 h-5 animate-spin text-zinc-400" />
                ) : (
                  <>
                    {t('forgot_password.send_code_btn')}
                    <ArrowRight className="w-4 h-4 rtl:rotate-180 group-hover:translate-x-0.5 rtl:group-hover:-translate-x-0.5 transition-transform" />
                  </>
                )}
              </button>

              <div className="pt-2 text-center border-t border-zinc-100">
                <Link to="/login" className="inline-flex items-center gap-1.5 text-sm font-medium text-zinc-500 hover:text-zinc-900 transition-colors">
                  <ArrowLeft className="w-4 h-4 rtl:rotate-180" />
                  {t('forgot_password.back_to_login')}
                </Link>
              </div>
            </form>
          )}

          {phase === 'verify' && (
            /* Phase 2: OTP Verification Form */
            <form onSubmit={handleVerifySubmit} className="space-y-4">
              <div className="space-y-3">
                <label className="block text-sm font-medium text-zinc-700" htmlFor="reset-otp">
                  {t('forgot_password.otp_label')}
                </label>
                <div className="relative">
                  <Key className="absolute start-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400" />
                  <input
                    id="reset-otp"
                    name="otp"
                    type="text"
                    required
                    maxLength={6}
                    placeholder={t('forgot_password.otp_placeholder')}
                    className="input-minimal !ps-10 font-mono tracking-[0.25em]"
                    value={otp}
                    onChange={(e) => setOtp(e.target.value)}
                    disabled={loading}
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="btn-minimal w-full flex items-center justify-center gap-2 py-2.5 mt-2 group"
              >
                {loading ? (
                  <Loader2 className="w-5 h-5 animate-spin text-zinc-400" />
                ) : (
                  <>
                    {t('forgot_password.verify_code_btn')}
                    <ArrowRight className="w-4 h-4 rtl:rotate-180 group-hover:translate-x-0.5 rtl:group-hover:-translate-x-0.5 transition-transform" />
                  </>
                )}
              </button>

              <div className="flex justify-between items-center pt-2 border-t border-zinc-100">
                <button
                  type="button"
                  onClick={() => {
                    setPhase('request');
                    setError(null);
                    setSuccess(null);
                  }}
                  className="inline-flex items-center gap-1 text-sm font-medium text-zinc-500 hover:text-zinc-900 transition-colors"
                >
                  <ArrowLeft className="w-4 h-4 rtl:rotate-180" />
                  {t('forgot_password.back_to_email')}
                </button>
                
                <Link to="/login" className="text-sm font-medium text-zinc-500 hover:text-zinc-900 transition-colors">
                  {t('forgot_password.cancel')}
                </Link>
              </div>
            </form>
          )}

          {phase === 'reset' && (
            /* Phase 3: New Password Reset Form */
            <form onSubmit={handleResetSubmit} className="space-y-4">
              <div className="space-y-4">
                {/* Password */}
                <div className="space-y-3">
                  <label className="block text-sm font-medium text-zinc-700" htmlFor="reset-password">
                    {t('forgot_password.new_password_label')}
                  </label>
                  <div className="relative">
                    <Lock className="absolute start-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400" />
                    <input
                      id="reset-password"
                      name="password"
                      type="password"
                      required
                      placeholder={t('forgot_password.new_password_placeholder')}
                      className="input-minimal !ps-10"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      disabled={loading}
                    />
                  </div>
                </div>

                {/* Confirm Password */}
                <div className="space-y-3">
                  <label className="block text-sm font-medium text-zinc-700" htmlFor="reset-confirm-password">
                    {t('forgot_password.confirm_password_label')}
                  </label>
                  <div className="relative">
                    <Lock className="absolute start-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400" />
                    <input
                      id="reset-confirm-password"
                      name="confirm_password"
                      type="password"
                      required
                      placeholder={t('forgot_password.confirm_password_placeholder')}
                      className="input-minimal !ps-10"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      disabled={loading}
                    />
                  </div>
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="btn-minimal w-full flex items-center justify-center gap-2 py-2.5 mt-2 group"
              >
                {loading ? (
                  <Loader2 className="w-5 h-5 animate-spin text-zinc-400" />
                ) : (
                  <>
                    {t('forgot_password.reset_password_btn')}
                    <ArrowRight className="w-4 h-4 rtl:rotate-180 group-hover:translate-x-0.5 rtl:group-hover:-translate-x-0.5 transition-transform" />
                  </>
                )}
              </button>

              <div className="flex justify-between items-center pt-2 border-t border-zinc-100">
                <button
                  type="button"
                  onClick={() => {
                    setPhase('verify');
                    setError(null);
                    setSuccess(null);
                  }}
                  className="inline-flex items-center gap-1 text-sm font-medium text-zinc-500 hover:text-zinc-900 transition-colors"
                >
                  <ArrowLeft className="w-4 h-4 rtl:rotate-180" />
                  {t('forgot_password.back_to_otp', 'Back to code entry')}
                </button>
                
                <Link to="/login" className="text-sm font-medium text-zinc-500 hover:text-zinc-900 transition-colors">
                  {t('forgot_password.cancel')}
                </Link>
              </div>
            </form>
          )}

        </div>
      </div>
    </div>
  );
};

export default ForgotPasswordPage;
