import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import api from '../services/api';
import { useTranslation } from 'react-i18next';
import { User, Mail, Phone, Calendar, ArrowRight, ArrowLeft, CheckCircle2, AlertCircle, Loader2, Key, RefreshCw, X, ShieldCheck } from 'lucide-react';
import PasswordInput from '../components/Auth/PasswordInput';
import OtpInput from '../components/Auth/OtpInput';

const COUNTRY_CODES = [
  { code: '+92', name: 'PK', label: 'Pakistan (+92)' },
  { code: '+60', name: 'MY', label: 'Malaysia (+60)' },
  { code: '+44', name: 'GB', label: 'United Kingdom (+44)' },
  { code: '+1', name: 'US', label: 'United States (+1)' },
  { code: '+966', name: 'SA', label: 'Saudi Arabia (+966)' },
  { code: '+971', name: 'AE', label: 'United Arab Emirates (+971)' },
];

// ── Password strength rules (mirrors Django's AUTH_PASSWORD_VALIDATORS) ────────
const COMMON_PASSWORDS = ['password', '12345678', '123456789', 'qwerty123', 'iloveyou', 'admin123', 'letmein', 'welcome1', 'monkey123'];

function validatePassword(password: string, username: string): string | null {
  if (!password || password.length < 8) return 'Password must be at least 8 characters. / پاس ورڈ کم از کم 8 حروف کا ہونا چاہیے۔';
  if (/^\d+$/.test(password)) return 'Password cannot be entirely numeric. / پاس ورڈ صرف نمبروں پر مشتمل نہیں ہو سکتا۔';
  if (username && password.toLowerCase().includes(username.toLowerCase()) && username.length >= 4)
    return 'Password is too similar to your username. / پاس ورڈ یوزر نیم سے بہت ملتا جلتا ہے۔';
  if (COMMON_PASSWORDS.includes(password.toLowerCase())) return 'Password is too common. / پاس ورڈ بہت عام ہے۔';
  return null;
}

// ── Field-level bilingual label helper ────────────────────────────────────────
const BiLabel: React.FC<{ en: string; ur: string; htmlFor?: string }> = ({ en, ur, htmlFor }) => (
  <label className="block text-sm font-medium text-zinc-700" htmlFor={htmlFor}>
    {en} <span className="font-urdu text-zinc-400 font-normal text-xs">/ {ur}</span>
  </label>
);

// ── Inline field error ─────────────────────────────────────────────────────────
const FieldError: React.FC<{ msg?: string }> = ({ msg }) =>
  msg ? <p className="text-xs text-red-600 mt-1 flex items-center gap-1"><AlertCircle className="w-3 h-3 shrink-0" />{msg}</p> : null;

const RegisterPage: React.FC = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    username: '',
    full_name: '',
    email: '',
    whatsapp_number: '+92',
    password: '',
    confirm_password: '',
    date_of_birth: '',
    consent_agreed: false,
    consent_version: '1.0',
    otp: '',
  });

  const [countryCode, setCountryCode] = useState('+92');
  const [rawPhone, setRawPhone] = useState('');

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

  const handlePhoneChange = (code: string, number: string) => {
    setCountryCode(code);
    setRawPhone(number);
    const digitsOnly = number.replace(/\D/g, '');
    const cleanNumber = digitsOnly.replace(/^0+/, '');
    setFormData(prev => ({ ...prev, whatsapp_number: `${code}${cleanNumber}` }));
    if (errors.whatsapp_number) {
      const newErrors = { ...errors };
      delete newErrors.whatsapp_number;
      setErrors(newErrors);
    }
  };

  // ── Full client-side validation before hitting the API ─────────────────────
  const validateForm = (): Record<string, string[]> => {
    const errs: Record<string, string[]> = {};
    if (!formData.username.trim()) errs.username = ['Username is required. / یوزر نیم درج کریں۔'];
    if (!formData.full_name.trim()) errs.full_name = ['Full name is required. / پورا نام درج کریں۔'];
    if (!formData.email.trim()) errs.email = ['Email is required. / ای میل درج کریں۔'];
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) errs.email = ['Enter a valid email address. / درست ای میل درج کریں۔'];

    const phoneDigits = rawPhone.replace(/\D/g, '').replace(/^0+/, '');
    if (!phoneDigits || phoneDigits.length < 7) errs.whatsapp_number = ['Enter a valid WhatsApp number. / درست واٹس ایپ نمبر درج کریں۔'];

    if (!formData.date_of_birth) errs.date_of_birth = ['Date of birth is required. / تاریخ پیدائش درج کریں۔'];
    else {
      const dob = new Date(formData.date_of_birth);
      const age = (Date.now() - dob.getTime()) / (365.25 * 24 * 3600 * 1000);
      if (age < 18) errs.date_of_birth = ['You must be at least 18 years old. / عمر کم از کم 18 سال ہونی چاہیے۔'];
    }

    const pwdErr = validatePassword(formData.password, formData.username);
    if (pwdErr) errs.password = [pwdErr];
    else if (formData.password !== formData.confirm_password)
      errs.confirm_password = ["Passwords don't match. / پاس ورڈ مماثل نہیں ہیں۔"];

    if (!formData.consent_agreed) errs.consent_agreed = ['You must agree to the Informed Consent Form. / رضامندی فارم پر اتفاق ضروری ہے۔'];
    return errs;
  };

  const handleSendOTP = async (isResend: boolean = false) => {
    if (isResend) { setResending(true); } else { setLoading(true); }
    setErrors({});
    setOtpMessage('');

    if (!isResend) {
      const clientErrors = validateForm();
      if (Object.keys(clientErrors).length > 0) {
        setErrors(clientErrors);
        setLoading(false);
        setResending(false);
        return;
      }
    }

    try {
      const response = await api.post('/auth/send-otp/', isResend ? { email: formData.email } : formData);
      if (response.status === 200) {
        setPhase('otp');
        setOtpMessage(isResend
          ? 'A new code has been sent. / نیا کوڈ بھیج دیا گیا ہے۔'
          : 'Verification code sent. / تصدیقی کوڈ بھیج دیا گیا۔');
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
        setErrors({ non_field_errors: ['Failed to send verification code. Please try again. / تصدیقی کوڈ بھیجنے میں ناکامی۔'] });
      }
    } finally {
      setLoading(false);
      setResending(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (phase === 'details') { await handleSendOTP(false); return; }

    if (!formData.otp.trim()) {
      setErrors({ otp: ['Verification code is required. / تصدیقی کوڈ درج کریں۔'] });
      return;
    }

    setLoading(true);
    setErrors({});

    try {
      const response = await api.post('/register/', formData);
      if (response.status === 201) {
        setSuccess(true);
        setTimeout(() => navigate('/login', { state: { message: 'Account created successfully. Please log in.' } }), 2000);
      }
    } catch (err: any) {
      if (err.response?.data) {
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
        setErrors({ non_field_errors: ['An unexpected error occurred. Please try again. / غیر متوقع خرابی۔'] });
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
          <p className="font-urdu text-zinc-500 text-sm">آپ کا اکاؤنٹ بن گیا۔ لاگ ان صفحے پر جا رہے ہیں۔</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-[90vh] flex flex-col p-4 bg-white relative">
      <div className="flex-1 flex items-center justify-center">
        <div className="card-minimal max-w-md w-full p-8 space-y-8">
          <div className="space-y-1 text-center">
            <h1 className="text-3xl font-bold tracking-tight text-zinc-900">{t('register.title')}</h1>
            <p className="text-zinc-500 text-sm">{t('register.subtitle')}</p>
            <p className="font-urdu text-zinc-400 text-xs">اکاؤنٹ بنانے کے لیے تمام معلومات درج کریں</p>
          </div>

          {/* Top-level error banner — only for non-field / server errors */}
          {errors.non_field_errors && (
            <div className="p-4 rounded-2xl bg-red-50/40 border border-red-100 flex items-start gap-2 animate-in fade-in duration-200">
              <AlertCircle className="w-4 h-4 text-red-600 shrink-0 mt-0.5" />
              <p className="text-xs text-red-700">{errors.non_field_errors[0]}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4" noValidate>
            {phase === 'details' ? (
              <>
                <div className="grid grid-cols-1 gap-4">

                  {/* Username */}
                  <div className="space-y-1.5">
                    <BiLabel en="Username" ur="یوزر نیم" htmlFor="username" />
                    <div className="relative">
                      <User className="absolute start-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400" />
                      <input
                        id="username" name="username" type="text" required
                        placeholder="e.g. john_doe"
                        className={`input-minimal !ps-10 ${errors.username ? 'border-red-400 border-2 ring-0' : ''}`}
                        value={formData.username}
                        onChange={handleChange}
                      />
                    </div>
                    <FieldError msg={errors.username?.[0]} />
                  </div>

                  {/* Full Name */}
                  <div className="space-y-1.5">
                    <BiLabel en="Full Name" ur="پورا نام" htmlFor="full_name" />
                    <div className="relative">
                      <User className="absolute start-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400" />
                      <input
                        id="full_name" name="full_name" type="text" required
                        placeholder={t('register.full_name_placeholder')}
                        className={`input-minimal !ps-10 ${errors.full_name ? 'border-red-400 border-2 ring-0' : ''}`}
                        value={formData.full_name}
                        onChange={handleChange}
                      />
                    </div>
                    <FieldError msg={errors.full_name?.[0]} />
                  </div>

                  {/* Email */}
                  <div className="space-y-1.5">
                    <BiLabel en="Email Address" ur="ای میل" htmlFor="email" />
                    <div className="relative">
                      <Mail className="absolute start-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400" />
                      <input
                        id="email" name="email" type="email" required
                        placeholder={t('register.email_placeholder')}
                        className={`input-minimal !ps-10 ${errors.email ? 'border-red-400 border-2 ring-0' : ''}`}
                        value={formData.email}
                        onChange={handleChange}
                      />
                    </div>
                    <FieldError msg={errors.email?.[0]} />
                  </div>

                  {/* WhatsApp */}
                  <div className="space-y-1.5">
                    <BiLabel en="WhatsApp Number" ur="واٹس ایپ نمبر" htmlFor="raw_whatsapp_number" />
                    <div className="flex gap-2">
                      <div className="relative w-32 shrink-0">
                        <select
                          value={countryCode}
                          onChange={(e) => handlePhoneChange(e.target.value, rawPhone)}
                          className="w-full h-10 px-3 bg-white border border-zinc-300 rounded-xl text-xs font-semibold text-zinc-700 focus:ring-2 focus:ring-zinc-900 focus:border-zinc-900 outline-none transition-all shadow-sm cursor-pointer appearance-none"
                          style={{
                            backgroundImage: `url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='%2371717a' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><polyline points='6 9 12 15 18 9'></polyline></svg>")`,
                            backgroundRepeat: 'no-repeat',
                            backgroundPosition: 'right 0.5rem center',
                            backgroundSize: '1.25em'
                          }}
                        >
                          {COUNTRY_CODES.map((c) => (
                            <option key={c.code} value={c.code}>{c.name} ({c.code})</option>
                          ))}
                        </select>
                      </div>
                      <div className="relative flex-1">
                        <Phone className="absolute start-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400" />
                        <input
                          id="raw_whatsapp_number" type="tel" required
                          placeholder="3001234567"
                          className={`input-minimal !ps-10 ${errors.whatsapp_number ? 'border-red-400 border-2 ring-0' : ''}`}
                          value={rawPhone}
                          onChange={(e) => handlePhoneChange(countryCode, e.target.value)}
                        />
                      </div>
                    </div>
                    <FieldError msg={errors.whatsapp_number?.[0]} />
                  </div>

                  {/* Date of Birth */}
                  <div className="space-y-1.5">
                    <BiLabel en="Date of Birth" ur="تاریخ پیدائش" htmlFor="date_of_birth" />
                    <div className="relative">
                      <Calendar className="absolute start-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400" />
                      <input
                        id="date_of_birth" name="date_of_birth" type="date" required
                        className={`input-minimal !ps-10 ${errors.date_of_birth ? 'border-red-400 border-2 ring-0' : ''}`}
                        value={formData.date_of_birth}
                        onChange={handleChange}
                      />
                    </div>
                    <FieldError msg={errors.date_of_birth?.[0]} />
                  </div>

                  {/* Password fields */}
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-1.5">
                      <BiLabel en="Password" ur="پاس ورڈ" htmlFor="password" />
                      <PasswordInput
                        id="password" name="password" required
                        placeholder="Min. 8 characters"
                        className={errors.password ? 'border-red-400 border-2 ring-0' : ''}
                        value={formData.password}
                        onChange={handleChange}
                      />
                    </div>
                    <div className="space-y-1.5">
                      <BiLabel en="Confirm" ur="تصدیق" htmlFor="confirm_password" />
                      <PasswordInput
                        id="confirm_password" name="confirm_password" required
                        placeholder="Re-enter"
                        className={errors.confirm_password ? 'border-red-400 border-2 ring-0' : ''}
                        value={formData.confirm_password}
                        onChange={handleChange}
                      />
                    </div>
                  </div>

                  {/* Password hint — turns red when there's a password error */}
                  {(() => {
                    const pwdErr = errors.password?.[0] || errors.confirm_password?.[0];
                    const hasErr = !!pwdErr;
                    return (
                      <div className={`flex items-start gap-2 rounded-lg p-3 border ${hasErr ? 'bg-red-50 border-red-200' : 'bg-zinc-50 border-zinc-100'}`}>
                        <ShieldCheck className={`w-3.5 h-3.5 shrink-0 mt-0.5 ${hasErr ? 'text-red-400' : 'text-zinc-400'}`} />
                        <p className={`text-xs leading-relaxed ${hasErr ? 'text-red-600' : 'text-zinc-500'}`}>
                          {hasErr ? pwdErr : 'At least 8 characters, not all numbers, not too common.'}
                          {!hasErr && <span className="font-urdu text-zinc-400 block">کم از کم 8 حروف، صرف نمبر نہیں، عام پاس ورڈ نہیں۔</span>}
                        </p>
                      </div>
                    );
                  })()}
                </div>

                {/* Consent checkbox */}
                <div className="flex items-start gap-3 py-2">
                  <input
                    id="consent_agreed" name="consent_agreed" type="checkbox" required
                    className="h-4 w-4 mt-0.5 shrink-0 rounded border-2 border-black text-black focus:ring-black cursor-pointer"
                    checked={formData.consent_agreed}
                    onChange={handleChange}
                  />
                  <label htmlFor="consent_agreed" className="text-xs text-zinc-700 leading-relaxed font-medium select-none">
                    {t('register.consent_checkbox_label')}{' '}
                    <button
                      type="button"
                      onClick={() => setShowConsentModal(true)}
                      className="text-black font-bold underline hover:text-zinc-800 cursor-pointer"
                    >
                      {t('register.consent_link')}
                    </button>
                    <span className="font-urdu text-zinc-400 block text-xs mt-0.5">/ رضامندی فارم پڑھ کر اتفاق کریں۔</span>
                  </label>
                </div>
                <FieldError msg={errors.consent_agreed?.[0]} />
              </>
            ) : (
              /* ── OTP Phase ───────────────────────────────────────────────── */
              <div className="space-y-6">
                <div className="p-5 bg-zinc-50/50 border border-zinc-150 rounded-2xl text-center space-y-3">
                  <div className="w-12 h-12 bg-zinc-100/60 rounded-full flex items-center justify-center mx-auto text-zinc-900 shadow-sm border border-zinc-200/40">
                    <Mail className="w-5 h-5 text-zinc-800" />
                  </div>
                  <div className="space-y-1">
                    <h3 className="text-sm font-bold text-zinc-900">
                      Verify your email <span className="font-urdu font-normal text-zinc-500">/ ای میل تصدیق</span>
                    </h3>
                    <p className="text-xs text-zinc-500 leading-relaxed max-w-xs mx-auto">
                      We've sent a 6-digit code to{' '}
                      <span className="text-zinc-900 font-semibold">{formData.email}</span>.
                      <span className="block font-urdu mt-1">آپ کی ای میل پر 6 ہندسوں کا کوڈ بھیجا گیا ہے۔</span>
                    </p>
                  </div>
                </div>

                <div className="space-y-3">
                  <div className="flex items-center gap-1.5 text-zinc-400">
                    <Key className="w-3.5 h-3.5" />
                    <label className="block text-xs font-bold uppercase tracking-wider" htmlFor="otp">
                      Verification Code <span className="font-urdu normal-case font-normal">/ تصدیقی کوڈ</span>
                    </label>
                  </div>
                  <OtpInput
                    id="otp"
                    value={formData.otp}
                    onChange={(val) => {
                      setFormData(prev => ({ ...prev, otp: val }));
                      if (errors.otp) { const e = { ...errors }; delete e.otp; setErrors(e); }
                    }}
                    disabled={loading}
                    error={!!errors.otp}
                  />
                  <FieldError msg={errors.otp?.[0]} />
                  {otpMessage && <p className="text-xs text-emerald-600 font-medium italic mt-1">{otpMessage}</p>}
                </div>

                <div className="flex justify-between items-center gap-4 mt-4">
                  <button
                    type="button"
                    onClick={() => setPhase('details')}
                    className="flex-1 py-2.5 px-4 bg-white hover:bg-zinc-50 border border-zinc-200 text-zinc-700 hover:text-zinc-900 font-semibold text-xs rounded-xl flex items-center justify-center gap-1.5 transition-all cursor-pointer shadow-sm"
                  >
                    <ArrowLeft className="w-3.5 h-3.5" />
                    Edit Details <span className="font-urdu font-normal">/ تفصیل بدلیں</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => handleSendOTP(true)}
                    disabled={resending}
                    className="flex-1 py-2.5 px-4 bg-white hover:bg-zinc-50 border border-zinc-200 text-zinc-700 hover:text-zinc-900 font-semibold text-xs rounded-xl flex items-center justify-center gap-1.5 transition-all disabled:opacity-50 cursor-pointer shadow-sm"
                  >
                    {resending ? <Loader2 className="w-3.5 h-3.5 animate-spin text-zinc-400" /> : <RefreshCw className="w-3.5 h-3.5" />}
                    Resend <span className="font-urdu font-normal">/ دوبارہ بھیجیں</span>
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
                  {phase === 'details'
                    ? <><span>Send Verification Code</span><span className="font-urdu font-normal text-xs opacity-80">/ کوڈ بھیجیں</span></>
                    : <><span>Verify & Sign Up</span><span className="font-urdu font-normal text-xs opacity-80">/ تصدیق کریں</span></>
                  }
                  <ArrowRight className="w-4 h-4 rtl:rotate-180 rtl:group-hover:-translate-x-0.5 group-hover:translate-x-0.5 transition-transform shrink-0" />
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
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-zinc-900/60 backdrop-blur-sm p-4 transition-opacity duration-200 animate-in fade-in duration-150">
          <div className="bg-white rounded-2xl border border-zinc-200 max-w-4xl w-full p-8 shadow-2xl relative flex flex-col max-h-[85vh] animate-in zoom-in-95 duration-200">
            <div className="flex justify-between items-center border-b border-zinc-100 pb-4 mb-4">
              <div className="space-y-1">
                <h2 className="text-xl font-extrabold text-zinc-900 tracking-tight">{t('register.consent_header')}</h2>
                <p className="text-xs text-zinc-500 font-semibold uppercase tracking-wider">
                  Participant Informed Consent / باضابطہ رضامندی نامہ
                </p>
              </div>
              <button type="button" onClick={() => setShowConsentModal(false)}
                className="text-zinc-400 hover:text-zinc-600 transition-colors p-2 hover:bg-zinc-100 rounded-full cursor-pointer">
                <X size={20} />
              </button>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 overflow-y-auto pr-1 flex-1 py-2">
              <div className="space-y-5 text-xs text-zinc-600 leading-relaxed text-left font-latin pr-2 md:border-r md:border-zinc-100">
                <p className="font-semibold text-zinc-800 text-sm bg-zinc-50 p-3 rounded-xl border border-zinc-100">{t('register.consent_intro', { lng: 'en' })}</p>
                <div className="space-y-1"><h4 className="font-bold text-zinc-900 text-sm">{t('register.consent_section1_title', { lng: 'en' })}</h4><p>{t('register.consent_section1_text', { lng: 'en' })}</p></div>
                <div className="space-y-1"><h4 className="font-bold text-zinc-900 text-sm">{t('register.consent_section2_title', { lng: 'en' })}</h4><p>{t('register.consent_section2_text', { lng: 'en' })}</p></div>
                <div className="bg-amber-50 border border-amber-200 p-4 rounded-xl space-y-1"><h4 className="font-bold text-amber-900 text-sm">{t('register.consent_section3_title', { lng: 'en' })}</h4><p className="text-amber-800 font-medium leading-relaxed">{t('register.consent_section3_text', { lng: 'en' })}</p></div>
                <div className="space-y-1"><h4 className="font-bold text-zinc-900 text-sm">{t('register.consent_section4_title', { lng: 'en' })}</h4><p>{t('register.consent_section4_text', { lng: 'en' })}</p></div>
                <div className="space-y-1"><h4 className="font-bold text-zinc-900 text-sm">{t('register.consent_section5_title', { lng: 'en' })}</h4><p>{t('register.consent_section5_text', { lng: 'en' })}</p></div>
              </div>
              <div className="space-y-5 text-sm text-zinc-600 leading-relaxed text-right font-urdu pl-2" dir="rtl">
                <p className="font-semibold text-zinc-800 text-base bg-zinc-50 p-3 rounded-xl border border-zinc-100">{t('register.consent_intro', { lng: 'ur' })}</p>
                <div className="space-y-1"><h4 className="font-bold text-zinc-900 text-base">{t('register.consent_section1_title', { lng: 'ur' })}</h4><p className="text-sm">{t('register.consent_section1_text', { lng: 'ur' })}</p></div>
                <div className="space-y-1"><h4 className="font-bold text-zinc-900 text-base">{t('register.consent_section2_title', { lng: 'ur' })}</h4><p className="text-sm">{t('register.consent_section2_text', { lng: 'ur' })}</p></div>
                <div className="bg-amber-50 border border-amber-200 p-4 rounded-xl space-y-1"><h4 className="font-bold text-amber-900 text-base">{t('register.consent_section3_title', { lng: 'ur' })}</h4><p className="text-amber-800 font-medium text-sm leading-relaxed">{t('register.consent_section3_text', { lng: 'ur' })}</p></div>
                <div className="space-y-1"><h4 className="font-bold text-zinc-900 text-base">{t('register.consent_section4_title', { lng: 'ur' })}</h4><p className="text-sm">{t('register.consent_section4_text', { lng: 'ur' })}</p></div>
                <div className="space-y-1"><h4 className="font-bold text-zinc-900 text-base">{t('register.consent_section5_title', { lng: 'ur' })}</h4><p className="text-sm">{t('register.consent_section5_text', { lng: 'ur' })}</p></div>
              </div>
            </div>
            <div className="pt-4 border-t border-zinc-100 flex justify-end gap-3 mt-4">
              <button type="button" onClick={() => setShowConsentModal(false)}
                className="px-5 py-2.5 rounded-xl border border-zinc-300 text-zinc-700 text-xs font-semibold uppercase tracking-wider hover:bg-zinc-50 hover:text-zinc-950 transition-colors cursor-pointer">
                Read Later / بعد میں پڑھیں
              </button>
              <button type="button"
                onClick={() => { setFormData(prev => ({ ...prev, consent_agreed: true })); setShowConsentModal(false); }}
                className="bg-zinc-900 text-white px-6 py-2.5 rounded-xl text-xs font-semibold uppercase tracking-wider hover:bg-zinc-800 transition-colors shadow-md hover:shadow-lg cursor-pointer">
                Agree & Close / متفق ہوں اور بند کریں
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default RegisterPage;
