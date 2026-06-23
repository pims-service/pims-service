import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, Phone, Mail, HelpCircle, FileText, ShieldAlert, Home, Info, ExternalLink, ChevronDown } from 'lucide-react';
import pimsLogo from '../assets/pims_logo.png';
import ukmLogo from '../assets/ukm_logo.jpeg';


// Timeline Milestone Component for Program Sequence
const Timeline: React.FC = () => {
  const steps = [
    { en: 'Sign-up', ur: 'رجسٹریشن' },
    { en: 'Day 7', ur: 'ساتواں دن' },
    { en: 'Day 30', ur: 'تیسواں دن' },
    { en: '3 Months', ur: 'تین ماہ' },
    { en: '6 Months', ur: 'چھ ماہ' },
    { en: '12 Months', ur: 'بارہ ماہ' }
  ];

  return (
    <div className="my-10 w-full bg-zinc-50 border border-zinc-200 rounded-2xl p-6 shadow-sm">
      <h3 className="text-xs font-bold uppercase text-zinc-400 tracking-wider mb-8 text-center">
        Program Timeline / پروگرام کا ٹائم لائن
      </h3>
      
      {/* Desktop Horizontal Timeline */}
      <div className="hidden md:flex relative items-center justify-between">
        <div className="absolute left-4 right-4 top-1/2 h-1 bg-zinc-200 -translate-y-1/2 z-0" />
        {steps.map((step, idx) => (
          <div key={idx} className="relative z-10 flex flex-col items-center">
            <div className="w-8 h-8 rounded-full bg-white border-2 border-[#2E4E90] hover:border-[#C8A951] flex items-center justify-center text-xs font-bold text-[#2E4E90] shadow transition-colors duration-200">
              {idx + 1}
            </div>
            <div className="text-[10px] sm:text-xs font-semibold mt-3 text-center bg-zinc-50 px-1 whitespace-nowrap">
              <div className="text-zinc-800 font-latin">{step.en}</div>
              <div className="font-urdu leading-none text-[#C8A951] mt-1">{step.ur}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Mobile Vertical Timeline */}
      <div className="md:hidden relative flex flex-col gap-6 pl-4">
        <div className="absolute left-[29px] top-4 bottom-4 w-0.5 bg-zinc-200 z-0" />
        {steps.map((step, idx) => (
          <div key={idx} className="relative z-10 flex items-center gap-4">
            <div className="w-8 h-8 rounded-full bg-white border-2 border-[#2E4E90] flex items-center justify-center text-xs font-bold text-[#2E4E90] shadow shrink-0">
              {idx + 1}
            </div>
            <div className="flex flex-col text-left">
              <span className="text-sm font-bold text-zinc-800 font-latin">{step.en}</span>
              <span className="text-xs font-semibold font-urdu text-[#C8A951]">{step.ur}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// Side-by-Side Bilingual Section Wrapper
interface BilingualSectionProps {
  titleEn: string;
  titleUr: string;
  children: React.ReactNode;
}

const BilingualSection: React.FC<BilingualSectionProps> = ({ titleEn, titleUr, children }) => (
  <div className="border-b border-zinc-150 pb-8 mb-8 last:border-0 last:pb-0 last:mb-0">
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 items-start pb-4 border-b border-zinc-100">
      <h2 className="text-lg md:text-xl font-bold text-[#2E4E90] font-latin tracking-tight">{titleEn}</h2>
      <h2 className="text-lg md:text-xl font-bold text-[#2E4E90] font-urdu text-right dir-rtl leading-normal">{titleUr}</h2>
    </div>
    <div className="mt-4 space-y-4">{children}</div>
  </div>
);

// Side-by-Side Paragraph Row
const BilingualPara: React.FC<{ en: string; ur: string; highlight?: boolean }> = ({ en, ur, highlight }) => (
  <div className={`grid grid-cols-1 md:grid-cols-2 gap-6 py-2 px-3 rounded-lg transition-colors ${highlight ? 'bg-amber-50/60 border-l-4 border-[#C8A951]' : ''}`}>
    <p className="text-sm md:text-base text-zinc-700 font-latin leading-relaxed text-left">{en}</p>
    <p className="text-sm md:text-base text-zinc-800 font-urdu leading-loose text-right dir-rtl">{ur}</p>
  </div>
);

// Side-by-Side Bullet Row
const BilingualBullet: React.FC<{ en: string; ur: string }> = ({ en, ur }) => (
  <div className="grid grid-cols-1 md:grid-cols-2 gap-6 py-2 px-3 hover:bg-zinc-50 rounded-lg transition-colors duration-150">
    <div className="flex items-start gap-2 text-left">
      <span className="text-[#C8A951] font-bold text-lg leading-none mt-1">•</span>
      <p className="text-sm md:text-base text-zinc-700 font-latin leading-relaxed">{en}</p>
    </div>
    <div className="flex items-start justify-end gap-2 text-right dir-rtl">
      <p className="text-sm md:text-base text-zinc-800 font-urdu leading-loose">{ur}</p>
      <span className="text-[#C8A951] font-bold text-lg leading-none mt-1">•</span>
    </div>
  </div>
);

// Side-by-Side FAQ Row
const BilingualFAQ: React.FC<{ qEn: string; qUr: string; aEn: string; aUr: string }> = ({ qEn, qUr, aEn, aUr }) => (
  <div className="border border-zinc-200 bg-white rounded-xl p-4 md:p-5 shadow-sm hover:shadow-md transition-shadow">
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 border-b border-zinc-100 pb-3 font-bold text-[#2E4E90]">
      <div className="text-left font-latin flex gap-2">
        <span className="text-[#C8A951]">Q:</span>
        <span>{qEn}</span>
      </div>
      <div className="text-right font-urdu dir-rtl flex justify-end gap-2 leading-snug">
        <span>{qUr}</span>
        <span className="text-[#C8A951]">:سوال</span>
      </div>
    </div>
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-3 text-zinc-650">
      <div className="text-left font-latin text-sm md:text-base leading-relaxed flex gap-2">
        <span className="text-[#C8A951] font-bold">A:</span>
        <span>{aEn}</span>
      </div>
      <div className="text-right font-urdu dir-rtl text-sm md:text-base leading-loose flex justify-end gap-2">
        <span>{aUr}</span>
        <span className="text-[#C8A951] font-bold">جو اب:</span>
      </div>
    </div>
  </div>
);

// Side-by-Side Helpline Row
const BilingualHelpline: React.FC<{ nameEn: string; nameUr: string; phone: string; hoursEn: string; hoursUr: string; descEn: string; descUrdu: string }> = ({
  nameEn, nameUr, phone, hoursEn, hoursUr, descEn, descUrdu
}) => (
  <div className="border border-zinc-200 bg-zinc-50 rounded-xl p-4 flex flex-col md:flex-row md:items-center justify-between gap-4 hover:border-zinc-300 transition-colors shadow-sm">
    <div className="space-y-1.5 flex-1">
      <div className="flex flex-wrap items-center gap-2">
        <span className="font-bold text-zinc-900 text-base font-latin">{nameEn}</span>
        <span className="text-zinc-300">|</span>
        <span className="font-bold text-[#2E4E90] text-base font-urdu" dir="rtl">{nameUr}</span>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs md:text-sm text-zinc-500">
        <div className="font-latin text-left">{descEn}</div>
        <div className="font-urdu text-right dir-rtl leading-normal">{descUrdu}</div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-[10px] md:text-xs font-bold uppercase tracking-wider text-[#C8A951]">
        <div className="text-left font-latin">Hours: {hoursEn}</div>
        <div className="text-right font-urdu dir-rtl">اوقات: {hoursUr}</div>
      </div>
    </div>
    <a
      href={`tel:${phone.replace(/[^0-9]/g, '')}`}
      className="bg-white border-2 border-black hover:bg-black hover:text-white px-5 py-2.5 rounded-xl font-bold text-xs md:text-sm flex items-center justify-center gap-2 transition-all shrink-0"
    >
      <Phone className="w-4 h-4" />
      <span>Call {phone}</span>
    </a>
  </div>
);

const NAV_ITEMS = [
  { id: 'home', en: 'Home', ur: 'ہوم', icon: <Home size={16} /> },
  { id: 'info', en: 'Information', ur: 'معلومات', icon: <Info size={16} /> },
  { id: 'faq', en: 'FAQ', ur: 'سوالات', icon: <HelpCircle size={16} /> },
  { id: 'crisis', en: 'Crisis Resources', ur: 'ہنگامی مدد', icon: <ShieldAlert size={16} /> },
  { id: 'contact', en: 'Contact', ur: 'رابطہ', icon: <Mail size={16} /> },
  { id: 'register', en: 'Registration', ur: 'رجسٹریشن', icon: <FileText size={16} /> },
] as const;

const LandingPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'home' | 'info' | 'faq' | 'crisis' | 'contact' | 'register'>('home');
  const [isMobileNavOpen, setIsMobileNavOpen] = useState(false);
  const activeNavItem = NAV_ITEMS.find(t => t.id === activeTab)!;

  return (
    <div className="w-full max-w-6xl mx-auto px-4 py-6 md:py-10 flex flex-col gap-8">
      {/* Brand Hero Header */}
      <header className="border border-zinc-200 bg-white rounded-2xl p-6 shadow-sm flex flex-col md:flex-row items-center justify-between gap-6">
        <div className="flex items-center gap-4 shrink-0">
          <div className="border border-zinc-200 p-1.5 rounded-xl bg-zinc-50 shadow-sm shrink-0">
            <img src={ukmLogo} alt="UKM Logo" className="h-9 md:h-10 w-auto object-contain select-none" />
          </div>
          <span className="text-zinc-300 text-2xl hidden md:inline">|</span>
          <div className="border border-zinc-200 p-1.5 rounded-xl bg-zinc-50 shadow-sm shrink-0">
            <img src={pimsLogo} alt="PIMS Logo" className="h-9 md:h-10 w-auto object-contain select-none" />
          </div>
        </div>
        
        <div className="flex-grow text-center md:text-left md:pl-4">
          <h1 className="text-2xl md:text-3xl font-extrabold text-[#2E4E90] tracking-tight">Psycheversity</h1>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-1 mt-1 text-sm text-zinc-500 font-medium">
            <p className="font-latin md:text-left">A free, science-based wellbeing program</p>
            <p className="font-urdu md:text-right dir-rtl font-semibold text-[#C8A951]">مفت، سائنس پر مبنی فلاح و بہبود کا پروگرام</p>
          </div>
        </div>
      </header>

      {/* Mobile Nav Dropdown — visible only below lg */}
      <div className="lg:hidden relative">
        <button
          onClick={() => setIsMobileNavOpen(!isMobileNavOpen)}
          className="w-full flex items-center justify-between gap-3 bg-white border border-zinc-200 rounded-xl px-4 py-3 shadow-sm font-semibold text-sm text-zinc-700"
        >
          <span className="flex items-center gap-2 text-[#2E4E90]">
            <span className="text-zinc-500">{activeNavItem.icon}</span>
            {activeNavItem.en}
            <span className="font-urdu text-zinc-500 text-xs" dir="rtl">{activeNavItem.ur}</span>
          </span>
          <ChevronDown size={18} className={`text-zinc-400 transition-transform duration-200 ${isMobileNavOpen ? 'rotate-180' : ''}`} />
        </button>
        {isMobileNavOpen && (
          <div className="absolute top-full left-0 right-0 z-40 mt-1 bg-white border border-zinc-200 rounded-xl shadow-lg overflow-hidden">
            {NAV_ITEMS.map((tab) => (
              <button
                key={tab.id}
                onClick={() => { setActiveTab(tab.id as any); setIsMobileNavOpen(false); }}
                className={`w-full flex items-center justify-between gap-3 px-4 py-3 text-sm font-semibold border-b border-zinc-100 last:border-0 transition-colors ${activeTab === tab.id ? 'bg-[#2E4E90] text-white' : 'text-zinc-700 hover:bg-zinc-50'}`}
              >
                <span className="flex items-center gap-2">{tab.icon} {tab.en}</span>
                <span className="font-urdu text-xs" dir="rtl">{tab.ur}</span>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Main Microsite Body */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8 items-start">
        {/* Navigation Sidebar — desktop only */}
        <aside className="hidden lg:block lg:col-span-1 bg-white border border-zinc-200 rounded-2xl p-4 shadow-sm">
          <nav className="flex flex-col gap-2">
            {NAV_ITEMS.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`flex flex-row items-center justify-between gap-4 w-full px-4 py-3 rounded-xl font-semibold text-sm transition-all text-left outline-none border-l-4 ${
                  activeTab === tab.id
                    ? 'bg-[#2E4E90] text-white border-[#C8A951] shadow-md'
                    : 'text-zinc-600 hover:bg-zinc-50 hover:text-zinc-900 border-transparent'
                }`}
              >
                <div className="flex items-center gap-1.5">
                  <span className={activeTab === tab.id ? 'text-white' : 'text-zinc-500'}>{tab.icon}</span>
                  <span className="font-latin">{tab.en}</span>
                </div>
                <span className="font-urdu text-sm leading-none">{tab.ur}</span>
              </button>
            ))}
          </nav>
        </aside>

        {/* Dynamic Content Area */}
        <main className="lg:col-span-3 bg-white border border-zinc-200 rounded-2xl p-6 md:p-8 shadow-sm min-h-[450px]">
          {/* TAB 1: HOME */}
          {activeTab === 'home' && (
            <div className="space-y-6">
              <BilingualSection titleEn="Welcome to Psycheversity!" titleUr="سائیکی ورسٹی میں خوش آمدید!">
                <BilingualPara
                  en="Psycheversity offers a free, online wellbeing program based on Positive Psychology. It has been developed at Universiti Kebangsaan Malaysia (UKM) in collaboration with the Pakistan Institute of Mind Sciences (PIMS), Islamabad, for adults living in Pakistan or holding Pakistani nationality."
                  ur="سائیکی ورسٹی مثبت نفسیات (Positive Psychology) پر مبنی ایک مفت آن لائن فلاح و بہبود کا پروگرام پیش کرتی ہے۔ یہ پروگرام یونیورسٹی کبانگسان ملائیشیا (UKM) نے پاکستان انسٹیٹیوٹ آف مائنڈ سائنسز (PIMS)، اسلام آباد کے اشتراک سے، پاکستانی شہریت رکھنے والے بالغ افراد کے لیے تیار کیا ہے۔"
                />
                <BilingualPara
                  en="Positive Psychology is the scientific study of what makes life most worth living. Researchers in this field design and test simple, evidence-based activities that can help people build wellbeing, gratitude, and a sense of meaning in everyday life. This program has been developed according to that scientific tradition."
                  ur="مثبت نفسیات اس بات کا سائنسی مطالعہ ہے کہ زندگی کو سب سے زیادہ قابلِ قدر کیا چیز بناتی ہے۔ اس شعبے کے محققین سادہ اور شواہد پر مبنی سرگرمیاں تیار اور جانچتے ہیں جو روزمرہ زندگی میں فلاح، شکرگزاری اور بامقصد ہونے کے احساس کو بڑھانے میں مدد دے سکتی ہیں۔ یہ پروگرام اسی سائنسی روایت کے مطابق تیار کیا گیا ہے۔"
                />

                {/* Introduction Video */}
                <div className="my-6 border border-zinc-200 bg-zinc-50/50 rounded-2xl p-4 md:p-6 shadow-sm hover:shadow-md transition-all duration-300">
                  <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 mb-4">
                    <h3 className="text-sm md:text-base font-bold text-[#2E4E90] font-latin">
                      Introduction Video
                    </h3>
                    <h3 className="text-sm md:text-base font-bold text-[#2E4E90] font-urdu text-right dir-rtl leading-normal">
                      تعارفی ویڈیو
                    </h3>
                  </div>
                  <div className="relative w-full aspect-video rounded-xl overflow-hidden border border-zinc-200 shadow-inner bg-black">
                    <iframe
                      src="https://www.youtube.com/embed/SbJs0Dyr8bQ?rel=0&modestbranding=1"
                      title="Psycheversity Introduction Video"
                      className="absolute top-0 left-0 w-full h-full border-0"
                      allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
                      allowFullScreen
                      loading="lazy"
                    />
                  </div>
                </div>

                <BilingualPara
                  en="The program consists of short daily writing activities that you complete from your phone or computer, in English or Urdu, taking about 10–15 minutes a day. Your participation also supports scientific research on wellbeing in Pakistan."
                  ur="اس پروگرام میں مختصر روزانہ تحریری سرگرمیاں شامل ہیں جو آپ اپنے موبائل یا کمپیوٹر سے، انگریزی یا اردو میں، روزانہ تقریباً 10 تا 15 منٹ میں مکمل کر سکتے ہیں۔ آپ کی شرکت پاکستان میں فلاح و بہبود سے متعلق سائنسی تحقیق میں بھی معاون ہوگی۔"
                />
                <BilingualPara
                  en="Registration is open. Click 'Registration' to sign up, or visit the 'Information' page to learn how the program works."
                  ur="رجسٹریشن جاری ہے۔ شامل ہونے کے لیے 'رجسٹریشن' پر کلک کریں، یا یہ جاننے کے لیے کہ پروگرام کیسے کام کرتا ہے، 'معلومات' کا صفحہ دیکھیں۔"
                  highlight={true}
                />
              </BilingualSection>

              {/* Call to Actions */}
              <div className="flex flex-col sm:flex-row gap-4 pt-4 border-t border-zinc-100">
                <button
                  onClick={() => setActiveTab('register')}
                  className="flex-1 bg-[#2E4E90] hover:bg-[#203768] text-white border-2 border-[#2E4E90] hover:border-[#203768] py-3.5 px-6 rounded-xl font-bold text-sm md:text-base flex items-center justify-center gap-2 shadow-lg transition-all"
                >
                  <span>Register Now / ابھی رجسٹر کریں</span>
                  <ArrowRight size={18} />
                </button>
                <Link
                  to="/login"
                  className="flex-1 bg-white border-2 border-black hover:bg-zinc-50 text-black py-3.5 px-6 rounded-xl font-bold text-sm md:text-base flex items-center justify-center gap-2 transition-all shadow-sm"
                >
                  <span>Existing Participant? Login / لاگ ان</span>
                </Link>
              </div>
            </div>
          )}

          {/* TAB 2: INFORMATION */}
          {activeTab === 'info' && (
            <div className="space-y-8">
              <BilingualSection titleEn="Key Points" titleUr="اہم نکات">
                <BilingualBullet
                  en="The program consists of brief daily writing exercises designed to support wellbeing. These exercises are based on published scientific research in psychology."
                  ur="اس پروگرام میں مختصر روزانہ تحریری مشقیں شامل ہیں جو فلاح و بہبود کو بہتر بنانے کے لیے ترتیب دی گئی ہیں۔ یہ مشقیں نفسیات کی شائع شدہ سائنسی تحقیق پر مبنی ہیں۔"
                />
                <BilingualBullet
                  en="Participation is completely free of charge."
                  ur="شرکت مکمل طور پر مفت ہے۔"
                />
                <BilingualBullet
                  en="Everything is done online from home. You only need internet access on a phone or computer."
                  ur="تمام سرگرمیاں گھر بیٹھے آن لائن مکمل کی جاتی ہیں۔ آپ کو صرف موبائل یا کمپیوٹر پر انٹرنیٹ درکار ہے۔"
                />
                <BilingualBullet
                  en="The daily activities consist of three short written entries per day and take about 10–15 minutes in total."
                  ur="روزانہ کی سرگرمیوں میں تین مختصر تحریری اندراجات شامل ہیں جن میں مجموعی طور پر تقریباً 10 تا 15 منٹ لگتے ہیں۔"
                />
                <BilingualBullet
                  en="You will be assigned to one of several daily writing programs. All programs involve the same daily time commitment."
                  ur="آپ کو کئی روزانہ تحریری پروگراموں میں سے کسی ایک میں شامل کیا جائے گا۔ تمام پروگراموں میں روزانہ کا وقت یکساں درکار ہوتا ہے۔"
                />
                <BilingualBullet
                  en="The program is scientifically supervised and evaluated. For this purpose, you will be asked to complete questionnaires at several points over twelve months."
                  ur="اس پروگرام کی سائنسی نگرانی اور جانچ کی جاتی ہے۔ اس مقصد کے لیے آپ سے بارہ ماہ کے دوران مختلف مواقع پر سوالنامے مکمل کرنے کی درخواست کی جائے گی۔"
                />
                <BilingualBullet
                  en="You will receive a wellbeing feedback summary after the three-month assessment, and a personal report together with a certificate of completion after the twelve-month assessment."
                  ur="تین ماہ کی جانچ کے بعد آپ کو فلاح و بہبود کا خلاصہ موصول ہوگا، اور بارہ ماہ کی جانچ مکمل ہونے پر ذاتی رپورٹ اور تکمیل کا سرٹیفکیٹ دیا جائے گا۔"
                />
                <BilingualBullet
                  en="This is a newly developed program under scientific evaluation. It is possible that you may not experience positive effects from it."
                  ur="یہ ایک نیا تیار کردہ پروگرام ہے جس کی سائنسی جانچ جاری ہے۔ ممکن ہے کہ آپ کو اس سے مثبت اثرات محسوس نہ ہوں۔"
                />
                <BilingualBullet
                  en="If you would like further information, please use the Contact page. We are happy to help."
                  ur="مزید معلومات کے لیے براہِ کرم رابطہ کا صفحہ استعمال کریں۔ ہم آپ کی مدد کے لیے حاضر ہیں۔"
                />
              </BilingualSection>

              <BilingualSection titleEn="Program Sequence" titleUr="پروگرام کی ترتیب">
                <Timeline />
                <BilingualPara
                  en="Step 1 — Sign-up and starting questionnaires: After registering and giving your consent, you complete a set of scientifically validated questionnaires. This takes about 25–30 minutes and is required to participate. It includes a brief wellbeing safety check."
                  ur="مرحلہ 1 — رجسٹریشن اور ابتدائی سوالنامے: رجسٹریشن اور رضامندی کے بعد آپ سائنسی طور پر تصدیق شدہ سوالناموں کا ایک سیٹ مکمل کرتے ہیں۔ اس میں تقریباً 25 تا 30 منٹ لگتے ہیں اور شرکت کے لیے یہ لازمی ہے۔ اس میں فلاح و بہبود سے متعلق ایک مختصر حفاظتی جائزہ بھی شامل ہے۔"
                />
                <BilingualPara
                  en="Step 2 — Daily writing week: You complete your assigned daily writing activities (three short entries per day) for seven days. On Day 7, you fill in a short set of questionnaires (about 15–20 minutes)."
                  ur="مرحلہ 2 — روزانہ تحریر کا ہفتہ: آپ سات دن تک اپنی مقررہ روزانہ تحریری سرگرمیاں (روزانہ تین مختصر اندراجات) مکمل کرتے ہیں۔ ساتویں دن آپ مختصر سوالنامے (تقریباً 15 تا 20 منٹ) مکمل کرتے ہیں۔"
                />
                <BilingualPara
                  en="Step 3 — First-Month Results: About one month (30 days) after you start, following a short refresher week of writing activities, you complete another short set of questionnaires."
                  ur="مرحلہ 3 — پہلے مہینے کے نتائج: شروع کرنے کے تقریباً ایک ماہ (30 دن) بعد، تحریری سرگرمیوں کے ایک مختصر اعادہ ہفتے کے بعد، آپ ایک اور مختصر سوالناموں کا سیٹ مکمل کرتے ہیں۔"
                />
                <BilingualPara
                  en="Step 4 — Three-month check-in: A refresher week of writing activities followed by questionnaires. After this point, you receive your wellbeing feedback summary."
                  ur="مرحلہ 4 — تین ماہ کا جائزہ: تحریری سرگرمیوں کا ایک اعادہ ہفتہ اور اس کے بعد سوالنامے۔ اس مرحلے کے بعد آپ کو فلاح و بہبود کا خلاصہ موصول ہوتا ہے۔"
                />
                <BilingualPara
                  en="Step 5 — Six-month check-in: Another refresher week followed by questionnaires."
                  ur="مرحلہ 5 — چھ ماہ کا جائزہ: ایک اور اعادہ ہفتہ اور اس کے بعد سوالنامے۔"
                />
                <BilingualPara
                  en="Step 6 — Twelve-month completion: A final refresher week and questionnaires. After completing this step, you receive your personal report and certificate of completion, together with full information about the study."
                  ur="مرحلہ 6 — بارہ ماہ پر تکمیل: ایک آخری اعادہ ہفتہ اور سوالنامے۔ یہ مرحلہ مکمل کرنے کے بعد آپ کو اپنی ذاتی رپورٹ، تکمیل کا سرٹیفکیٹ اور مطالعے کے بارے میں مکمل معلومات موصول ہوتی ہیں۔"
                />
              </BilingualSection>

              <BilingualSection titleEn="Conditions of Participation" titleUr="شرکت کی شرائط">
                <BilingualBullet en="You are 18 years of age or older." ur="آپ کی عمر 18 سال یا اس سے زیادہ ہے۔" />
                <BilingualBullet en="You hold Pakistani nationality." ur="آپ پاکستانی شہریت رکھتے ہیں۔" />
                <BilingualBullet en="You can read and write in English or Urdu and have internet access." ur="آپ انگریزی یا اردو پڑھ اور لکھ سکتے ہیں اور آپ کو انٹرنیٹ تک رسائی حاصل ہے۔" />
                <BilingualPara
                  en="During sign-up, a brief wellbeing safety screening is included in the starting questionnaires. Depending on its results, some applicants may be advised that this program is not suitable for them at this time and will be guided towards appropriate professional support. Full details are explained during the consent process."
                  ur="رجسٹریشن کے دوران ابتدائی سوالناموں میں فلاح و بہبود کا ایک مختصر حفاظتی جائزہ شامل ہے۔ اس کے نتائج کی بنیاد پر بعض درخواست دہندگان کو مشورہ دیا جا سکتا ہے کہ یہ پروگرام اس وقت ان کے لیے موزوں نہیں، اور انہیں مناسب پیشہ ورانہ مدد کی طرف رہنمائی فراہم کی جائے گی۔ مکمل تفصیلات رضامندی کے عمل کے دوران بیان کی جاتی ہیں۔"
                />
                <BilingualPara
                  en="Important: This program is neither psychotherapy nor a replacement for therapy. If you are experiencing a psychological crisis or need professional help, please contact a psychologist, psychiatrist, or your nearest hospital, or see our Crisis Resources page."
                  ur="اہم: یہ پروگرام نہ تو سائیکوتھراپی ہے اور نہ ہی علاج کا متبادل۔ اگر آپ کسی نفسیاتی بحران سے گزر رہے ہیں یا پیشہ ورانہ مدد کی ضرورت ہے تو براہِ کرم کسی ماہرِ نفسیات، سائیکاٹرسٹ یا قریبی ہسپتال سے رابطہ کریں، یا ہمارا ہنگامی مدد کا صفحہ دیکھیں۔"
                  highlight={true}
                />
              </BilingualSection>

              <BilingualSection titleEn="Data Protection" titleUr="ڈیٹا کا تحفظ">
                <BilingualPara
                  en="All information you provide on this website will be used solely for research purposes by the research team at Universiti Kebangsaan Malaysia (UKM) and the Pakistan Institute of Mind Sciences (PIMS). All analyses are conducted anonymously and do not allow anyone to identify who took part."
                  ur="اس ویب سائٹ پر آپ کی فراہم کردہ تمام معلومات صرف تحقیقی مقاصد کے لیے یونیورسٹی کبانگسان ملائیشیا (UKM) اور پاکستان انسٹیٹیوٹ آف مائنڈ سائنسز (PIMS) کی تحقیقی ٹیم استعمال کرے گی۔ تمام تجزیے گمنام طریقے سے کیے جاتے ہیں اور ان سے کسی شریک کی شناخت ممکن نہیں۔"
                />
                <BilingualPara
                  en="No information will be passed on to third parties. To register, you only need to provide an email address; participating with an anonymous email address is perfectly possible. Identifying details are stored separately from your questionnaire responses."
                  ur="کوئی معلومات کسی تیسرے فریق کو فراہم نہیں کی جائیں گی۔ رجسٹریشن کے لیے صرف ایک ای میل ایڈریس درکار ہے؛ گمنام ای میل ایڈریس کے ساتھ شرکت بالکل ممکن ہے۔ شناختی تفصیلات آپ کے سوالناموں کے جوابات سے الگ محفوظ رکھی جاتی ہیں۔"
                />
                <BilingualPara
                  en="This study has been reviewed and approved by the Research Ethics Committee of Universiti Kebangsaan Malaysia (RECUKM), approval reference JEP-2024-262."
                  ur="اس مطالعے کا جائزہ یونیورسٹی کبانگسان ملائیشیا کی ریسرچ ایتھکس کمیٹی (RECUKM) نے لیا ہے اور اسے منظوری دی ہے، منظوری حوالہ JEP-2024-262۔"
                />
              </BilingualSection>
            </div>
          )}

          {/* TAB 3: FAQ */}
          {activeTab === 'faq' && (
            <div className="space-y-6">
              <BilingualSection titleEn="Frequently Asked Questions" titleUr="اکثر پوچھے جانے والے سوالات">
                <div className="space-y-4">
                  <BilingualFAQ
                    qEn="How much does it cost?"
                    qUr="اس کی قیمت کیا ہے؟"
                    aEn="Nothing. Participation is completely free."
                    aUr="کچھ نہیں۔ شرکت مکمل طور پر مفت ہے۔"
                  />
                  <BilingualFAQ
                    qEn="How much time does it take?"
                    qUr="اس میں کتنا وقت لگتا ہے؟"
                    aEn="About 10–15 minutes a day during writing weeks, plus questionnaires at six points over twelve months (the first set takes about 25–30 minutes; later sets are shorter)."
                    aUr="تحریری ہفتوں کے دوران روزانہ تقریباً 10 تا 15 منٹ، اور بارہ ماہ کے دوران چھ مواقع پر سوالنامے (پہلا سیٹ تقریباً 25 تا 30 منٹ کا ہے؛ بعد کے سیٹ مختصر ہیں)۔"
                  />
                  <BilingualFAQ
                    qEn="Can I participate from my phone?"
                    qUr="کیا میں موبائل سے شرکت کر سکتا/سکتی ہوں؟"
                    aEn="Yes. The website works on phones, tablets, and computers."
                    aUr="جی ہاں۔ یہ ویب سائٹ موبائل، ٹیبلٹ اور کمپیوٹر پر کام کرتی ہے۔"
                  />
                  <BilingualFAQ
                    qEn="Can I write in Urdu?"
                    qUr="کیا میں اردو میں لکھ سکتا/سکتی ہوں؟"
                    aEn="Yes. All activities and questionnaires are available in both English and Urdu, and you may write your entries in either language."
                    aUr="جی ہاں۔ تمام سرگرمیاں اور سوالنامے انگریزی اور اردو دونوں میں دستیاب ہیں، اور آپ اپنے اندراجات کسی بھی زبان میں لکھ سکتے ہیں۔"
                  />
                  <BilingualFAQ
                    qEn="Why are there different writing programs?"
                    qUr="مختلف تحریری پروگرام کیوں ہیں؟"
                    aEn="Because this is a scientific study, participants are assigned to different versions of the daily writing program. Comparing them is how researchers learn which activities work best. You will receive full information about the study after the twelve-month assessment."
                    aUr="چونکہ یہ ایک سائنسی مطالعہ ہے، شرکاء کو روزانہ تحریری پروگرام کی مختلف صورتوں میں شامل کیا جاتا ہے۔ ان کا موازنہ کرکے ہی محققین جان پاتے ہیں کہ کون سی سرگرمیاں سب سے مؤثر ہیں۔ بارہ ماہ کی جانچ کے بعد آپ کو مطالعے کی مکمل معلومات فراہم کی جائیں گی۔"
                  />
                  <BilingualFAQ
                    qEn="Will this treat my depression or anxiety?"
                    qUr="کیا یہ میرے ڈپریشن یا بے چینی کا علاج کرے گا؟"
                    aEn="No. This is a wellbeing program, not a treatment. It is not psychotherapy and not a replacement for professional care. If you need help, please consult a mental health professional or see our Crisis Resources page."
                    aUr="۔ نہیں۔ یہ فلاح و بہبود کا پروگرام ہے، علاج نہیں۔ یہ نہ سائیکوتھراپی ہے اور نہ پیشہ ورانہ علاج کا متبادل۔ اگر آپ کو مدد درکار ہو تو براہِ کرم کسی ماہرِ ذہنی صحت سے رجوع کریں یا ہمارا ہنگامی مدد کا صفحہ دیکھیں۔"
                  />
                  <BilingualFAQ
                    qEn="What if I miss a day?"
                    qUr="اگر میں کوئی دن چھوڑ دوں تو؟"
                    aEn="Try to complete your entries every day, as regular practice matters most. If you miss a day, simply continue the next day."
                    aUr="کوشش کریں کہ روزانہ اپنے اندراجات مکمل کریں، کیونکہ باقاعدگی سب سے اہم ہے۔ اگر کوئی دن رہ جائے تو اگلے دن سے سلسلہ جاری رکھیں۔"
                  />
                  <BilingualFAQ
                    qEn="Can I withdraw from the study?"
                    qUr="کیا میں مطالعے سے دستبردار ہو سکتا/سکتی ہوں؟"
                    aEn="Yes. Participation is voluntary and you may withdraw at any time without giving a reason and without any negative consequences."
                    aUr="جی ہاں۔ شرکت رضاکارانہ ہے اور آپ کسی بھی وقت، بغیر کوئی وجہ بتائے اور بغیر کسی نقصان کے، دستبردار ہو سکتے ہیں۔"
                  />
                  <BilingualFAQ
                    qEn="What do I receive for participating?"
                    qUr="شرکت پر مجھے کیا ملے گا؟"
                    aEn="A wellbeing feedback summary after the three-month assessment, and a personal report plus a certificate of completion after the twelve-month assessment."
                    aUr="تین ماہ کی جانچ کے بعد فلاح و بہبود کا خلاصہ، اور بارہ ماہ کی جانچ کے بعد ذاتی رپورٹ اور تکمیل کا سرٹیفکیٹ۔"
                  />
                </div>
              </BilingualSection>
            </div>
          )}

          {/* TAB 4: CRISIS RESOURCES */}
          {activeTab === 'crisis' && (
            <div className="space-y-6">
              <BilingualSection titleEn="If You Need Help Now" titleUr="اگر آپ کو ابھی مدد درکار ہے">
                <BilingualPara
                  en="This program is not a crisis service and is not monitored around the clock. If you are in distress, feel unsafe, or are having thoughts of harming yourself, please seek help immediately."
                  ur="یہ پروگرام ہنگامی خدمت نہیں ہے اور اس کی چوبیس گھنٹے نگرانی نہیں کی جاتی۔ اگر آپ شدید پریشانی میں ہیں، خود کو غیر محفوظ محسوس کرتے ہیں، یا خود کو نقصان پہنچانے کے خیالات آ رہے ہیں تو براہِ کرم فوری مدد حاصل کریں۔"
                  highlight={true}
                />
                
                <div className="space-y-4 pt-4">
                  <BilingualHelpline
                    nameEn="Umang Pakistan"
                    nameUr="امنگ پاکستان"
                    phone="0311-7786264"
                    hoursEn="24/7"
                    hoursUr="24/7"
                    descEn="Suicide prevention and mental health support helpline."
                    descUrdu="خودکشی کی روک تھام اور ذہنی صحت کی معاونت کے لیے ہیلپ لائن۔"
                  />
                  <BilingualHelpline
                    nameEn="Taskeen Health Initiative"
                    nameUr="تسکین ذہنی صحت معاونت"
                    phone="0316-8275336"
                    hoursEn="Mon–Sat 11 AM–11 PM"
                    hoursUr="پیر تا ہفتہ 11 بجے صبح تا 11 بجے رات"
                    descEn="Emotional well-being support and guidance."
                    descUrdu="جذباتی فلاح و بہبود کے لیے مدد اور رہنمائی۔"
                  />
                  <BilingualHelpline
                    nameEn="Rozan Counselling Helpline"
                    nameUr="روزن کونسلنگ ہیلپ لائن"
                    phone="0304-1118666 / 0800-22444"
                    hoursEn="Mon–Sat 10 AM–6 PM"
                    hoursUr="پیر تا ہفتہ 10 بجے صبح تا 6 بجے شام"
                    descEn="Professional counseling and psychological support."
                    descUrdu="پیشہ ورانہ مشاورت اور نفسیاتی مدد۔"
                  />
                  <BilingualHelpline
                    nameEn="Emergency Rescue Services"
                    nameUr="ایمرجنسی ریسکیو سروسز"
                    phone="1122"
                    hoursEn="24/7"
                    hoursUr="24/7"
                    descEn="Immediate medical emergency rescue team."
                    descUrdu="فوری طبی اور بچاؤ کی خدمات۔"
                  />
                  <BilingualHelpline
                    nameEn="Edhi Ambulance"
                    nameUr="ایدھی ایمبولینس"
                    phone="115"
                    hoursEn="24/7"
                    hoursUr="24/7"
                    descEn="Emergency ambulance transport service."
                    descUrdu="ہنگامی ایمبولینس کی منتقلی کی خدمت۔"
                  />
                </div>
              </BilingualSection>
            </div>
          )}

          {/* TAB 5: CONTACT */}
          {activeTab === 'contact' && (
            <div className="space-y-6">
              <BilingualSection titleEn="Contact Us" titleUr="رابطہ کریں">
                <BilingualPara
                  en="If you have any questions about the program or your participation, please email us at the address below. We aim to respond within a few working days."
                  ur="اگر پروگرام یا اپنی شرکت کے بارے میں کوئی سوال ہو تو براہِ کرم ہمیں نیچے دیے گئے ای میل ایڈریس پر ای میل کریں۔ ہم چند کاروباری دنوں میں جواب دینے کی کوشش کرتے ہیں۔"
                />
                
                {/* Obfuscated Contact Card mimicking Zurich site */}
                <div className="border border-zinc-200 rounded-xl p-6 bg-zinc-50 flex items-center justify-between gap-4 max-w-lg">
                  <div className="flex items-center gap-3">
                    <div className="bg-[#2E4E90] text-white p-2.5 rounded-lg">
                      <Mail size={20} />
                    </div>
                    <div>
                      <div className="text-[10px] text-zinc-400 font-bold uppercase tracking-wider">Research Desk Email / ای میل</div>
                      <div className="text-sm md:text-base font-bold text-zinc-800 select-all font-latin">contact@psycheversity.com</div>
                    </div>
                  </div>
                  <span className="text-[10px] bg-[#C8A951]/20 text-[#C8A951] font-bold px-2 py-1 rounded-md uppercase tracking-wide">Official</span>
                </div>

                <BilingualPara
                  en="For questions about your rights as a research participant, you may contact the Research Ethics Committee, Universiti Kebangsaan Malaysia (RECUKM), quoting approval reference JEP-2024-262."
                  ur="بطور تحقیقی شریک اپنے حقوق سے متعلق سوالات کے لیے آپ ریسرچ ایتھکس کمیٹی، یونیورسٹی کبانگسان ملائیشیا (RECUKM) سے رابطہ کر سکتے ہیں، منظوری حوالہ JEP-2024-262 کے ساتھ۔"
                />
                
                <BilingualPara
                  en="This email address is not monitored continuously and must not be used in an emergency. In a crisis, please see our Crisis Resources page."
                  ur="یہ ای میل ایڈریس مسلسل مانیٹر نہیں کیا جاتا اور ہنگامی صورتِ حال میں استعمال نہیں کیا جانا چاہیے۔ بحران کی صورت میں براہِ کرم ہمارا ہنگامی مدد کا صفحہ دیکھیں۔"
                  highlight={true}
                />
              </BilingualSection>
            </div>
          )}

          {/* TAB 6: REGISTRATION */}
          {activeTab === 'register' && (
            <div className="space-y-6">
              <BilingualSection titleEn="Registration" titleUr="رجسٹریشن">
                <BilingualPara
                  en="To join the program, please click the registration button below to fill out your details and begin. You will verify your email address via OTP, after which you will be guided to read the full participant information and give your informed consent."
                  ur="پروگرام میں شامل ہونے کے لیے، براہِ کرم نیچے رجسٹریشن کے بٹن پر کلک کریں تاکہ آپ اپنی تفصیلات درج کر کے شروعات کر سکیں۔ آپ او ٹی پی (OTP) کے ذریعے اپنے ای میل ایڈریس کی تصدیق کریں گے، جس کے بعد آپ کو شرکاء کے لیے معلوماتی پرچہ پڑھنے اور اپنی باخبر رضامندی دینے کی رہنمائی کی جائے گی۔"
                />
                <BilingualPara
                  en="Before any questionnaires begin, you will read the full participant information and give your informed consent. Participation is voluntary, and you may withdraw at any time."
                  ur="سوالنامے شروع ہونے سے پہلے آپ شرکاء کی مکمل معلومات پڑھیں گے اور اپنی باخبر رضامندی دیں گے۔ شرکت رضاکارانہ ہے اور آپ کسی بھی وقت دستبردار ہو سکتے ہیں۔"
                />
                <BilingualPara
                  en="You may register with an anonymous email address if you prefer."
                  ur="اگر آپ چاہیں تو گمنام ای میل ایڈریس کے ساتھ بھی رجسٹر ہو سکتے ہیں۔"
                />

                {/* Styled Registration Card */}
                <div className="mt-8 border-2 border-dashed border-zinc-200 rounded-2xl p-6 md:p-8 text-center bg-zinc-50/50 flex flex-col items-center gap-4">
                  <div className="bg-[#2E4E90]/10 text-[#2E4E90] p-4 rounded-full">
                    <FileText size={32} />
                  </div>
                  <div className="space-y-2">
                    <h3 className="text-base font-bold font-latin text-zinc-900">Are you ready to build your wellbeing?</h3>
                    <h4 className="text-sm font-semibold font-urdu text-zinc-600 leading-snug" dir="rtl">کیا آپ اپنی فلاح و بہبود کو بہتر بنانے کے لیے تیار ہیں؟</h4>
                  </div>
                  
                  <Link
                    to="/register"
                    className="mt-2 inline-flex items-center justify-center gap-2 bg-[#2E4E90] hover:bg-[#203768] text-white py-3.5 px-10 rounded-xl font-bold text-sm md:text-base shadow-lg transition-all"
                  >
                    <span>Start Registration / رجسٹریشن شروع کریں</span>
                    <ArrowRight size={18} />
                  </Link>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-2 max-w-lg text-[10px] md:text-xs text-zinc-400 font-medium">
                    <p className="font-latin text-left">Requires a valid email address for OTP verification and self-selected password.</p>
                    <p className="font-urdu text-right dir-rtl">او ٹی پی کی تصدیق کے لیے ایک درست ای میل ایڈریس اور خود منتخب کردہ پاس ورڈ درکار ہے۔</p>
                  </div>
                </div>
              </BilingualSection>
            </div>
          )}
        </main>
      </div>

      {/* Site-wide Footer */}
      <footer className="border border-zinc-200 bg-white rounded-2xl p-6 shadow-sm mt-4 text-xs md:text-sm text-zinc-500 font-medium leading-relaxed">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pb-4 border-b border-zinc-100">
          <p className="font-latin text-left">
            © 2026 Psycheversity.com — A research project of Universiti Kebangsaan Malaysia (UKM) in collaboration with the Pakistan Institute of Mind Sciences (PIMS), Islamabad. Ethics approval: RECUKM JEP-2024-262.
          </p>
          <p className="font-urdu text-right dir-rtl leading-loose text-zinc-650">
            © 2026 سائیکی ورسٹی ڈاٹ کام — یونیورسٹی کبانگسان ملائیشیا (UKM) کا تحقیقی منصوبہ، پاکستان انسٹیٹیوٹ آف مائنڈ سائنسز (PIMS)، اسلام آباد کے اشتراک سے۔ اخلاقی منظوری: RECUKM JEP-2024-262۔
          </p>
        </div>
        
        <div className="flex flex-col sm:flex-row justify-between items-center gap-4 pt-4 text-xs">
          {/* External references */}
          <div className="flex items-center gap-4">
            <button
              onClick={() => setActiveTab('crisis')}
              className="text-[#2E4E90] hover:underline flex items-center gap-1.5"
            >
              <ShieldAlert size={14} />
              <span>Crisis Resources / ہنگامی مدد</span>
            </button>
            <span className="text-zinc-200">|</span>
            <a
              href="https://trainyourstrengths.com/"
              target="_blank"
              rel="noopener noreferrer"
              className="text-zinc-400 hover:text-zinc-650 flex items-center gap-1"
            >
              <span> Zurich Reference</span>
              <ExternalLink size={10} />
            </a>
          </div>

          <div className="flex items-center gap-2">
            <span className="font-latin">Ethics Ref: JEP-2024-262</span>
            <span className="text-zinc-200">|</span>
            <span className="font-urdu">منظوری حوالہ: JEP-2024-262</span>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
