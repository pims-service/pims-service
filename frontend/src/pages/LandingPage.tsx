import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { ArrowRight, CheckCircle2, Sparkles } from 'lucide-react';

const LandingPage: React.FC = () => {
  const location = useLocation();
  const { t, i18n } = useTranslation();
  const accountDeleted = location.state?.accountDeleted;
  const isUrdu = i18n.language === 'ur' || i18n.language?.startsWith('ur');

  return (
    <div className="max-w-3xl mx-auto px-4 py-16 sm:py-24 space-y-10">
      {accountDeleted && (
        <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 flex items-start gap-3 animate-in fade-in slide-in-from-top-2 duration-500">
          <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
          <p className="text-sm font-semibold text-emerald-800">{t('profile.account_deleted_success')}</p>
        </div>
      )}

      <div className="flex flex-col items-center text-center space-y-8">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-zinc-100 border border-zinc-200 text-zinc-600 text-sm font-medium">
          <Sparkles size={14} className="text-zinc-900 shrink-0" />
          <span>{t('landing.tagline')}</span>
        </div>

        <div className="space-y-4">
          <h1 className="text-4xl sm:text-5xl font-bold tracking-tight text-black leading-tight">
            {t('landing.title')}
          </h1>
          <p className="text-sm sm:text-base text-zinc-500 max-w-2xl leading-relaxed">
            {t('landing.collaboration')}
          </p>
        </div>

        <div className="space-y-5 text-base sm:text-lg text-zinc-800 max-w-2xl leading-relaxed text-start w-full">
          <p>{t('landing.intro_1')}</p>
          <p>{t('landing.intro_2')}</p>
          <p>{t('landing.intro_3')}</p>
          <p className="font-medium text-zinc-900">{t('landing.registration_note')}</p>
        </div>

        <div className="flex flex-col sm:flex-row gap-4 pt-2 w-full sm:w-auto">
          <Link
            to="/register"
            className="btn-minimal px-10 py-4 text-lg border-2 border-black flex items-center justify-center gap-2 group hover:bg-black hover:text-white transition-all"
          >
            {t('landing.register_now')}
            <ArrowRight size={20} className={`transition-transform ${isUrdu ? 'rotate-180 group-hover:-translate-x-1' : 'group-hover:translate-x-1'}`} />
          </Link>
          <Link
            to="/login"
            className="px-10 py-4 text-lg font-bold text-black border-2 border-black rounded-lg hover:bg-zinc-50 transition-all flex items-center justify-center"
          >
            {t('landing.existing_participant')}
          </Link>
        </div>
      </div>
    </div>
  );
};

export default LandingPage;
