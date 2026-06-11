import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Phone, ArrowRight, ShieldAlert, CheckSquare, Square } from 'lucide-react';

interface SafetyPanelModalProps {
  isOpen: boolean;
  onConfirm: (optIn: boolean) => void;
  submitting: boolean;
}

const SafetyPanelModal: React.FC<SafetyPanelModalProps> = ({ isOpen, onConfirm, submitting }) => {
  const [optIn, setOptIn] = useState(false);

  if (!isOpen) return null;

  const helplineResources = [
    {
      name: "Umang",
      urduName: "امنگ",
      phone: "0311-7786264",
      timing: "24/7, free, multilingual",
      desc: "Suicide prevention and mental health support helpline.",
      descUrdu: "خودکشی کی روک تھام اور ذہنی صحت کی معاونت کے لیے ہیلپ لائن۔"
    },
    {
      name: "Taskeen",
      urduName: "تسکین",
      phone: "0316-8275336",
      timing: "Mon–Sat 11 am–11 pm, 24/7 chatbot",
      desc: "Emotional well-being support and guidance.",
      descUrdu: "جذباتی فلاح و بہبود کے لیے مدد اور رہنمائی۔"
    },
    {
      name: "Rozan Counselling Helpline",
      urduName: "روزن ہیلپ لائن",
      phone: "0304-1118666 / 0800-22444",
      timing: "Mon–Sat 10 am–6 pm",
      desc: "Professional counseling and psychological support.",
      descUrdu: "پیشہ ورانہ مشاورت اور نفسیاتی مدد۔"
    },
    {
      name: "Emergency Rescue 1122",
      urduName: "ریسکیو 1122",
      phone: "1122",
      timing: "24/7, emergency medical response",
      desc: "Immediate medical and rescue services.",
      descUrdu: "فوری طبی اور بچاؤ کی خدمات۔"
    },
    {
      name: "Ambulance: Edhi 115 / Chhipa 1020",
      urduName: "ایدھی 115 / چھیپا 1020",
      phone: "115 / 1020",
      timing: "24/7, urgent ambulance transfer",
      desc: "Emergency transport services to nearest hospital.",
      descUrdu: "قریبی ہسپتال میں ہنگامی منتقلی کی خدمات۔"
    }
  ];

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-zinc-950/80 backdrop-blur-md flex justify-center p-4 md:py-8">
      <motion.div
        initial={{ scale: 0.98, opacity: 0, y: 10 }}
        animate={{ scale: 1, opacity: 1, y: 0 }}
        transition={{ type: 'spring', damping: 25, stiffness: 350 }}
        className="w-full max-w-2xl bg-white border border-zinc-200 shadow-2xl rounded-2xl overflow-hidden flex flex-col my-auto"
      >
        {/* Urgent Alert Banner */}
        <div className="bg-red-50 border-b border-red-100 p-4 flex items-center gap-3">
          <div className="bg-red-500 rounded-lg p-2 text-white flex-shrink-0">
            <ShieldAlert className="w-5 h-5 animate-pulse" />
          </div>
          <div className="flex-1 flex justify-between items-center">
            <h2 className="text-sm font-bold text-red-900 tracking-wide uppercase font-latin">Support Resources Available</h2>
            <h3 className="text-sm font-bold text-red-900 font-urdu" dir="rtl">امدادی وسائل دستیاب ہیں</h3>
          </div>
        </div>

        {/* Message Panel */}
        <div className="p-5 md:p-6 space-y-4 flex-1">
          {/* Dual Language Warning Message */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pb-4 border-b border-zinc-150 text-xs md:text-sm">
            <p className="text-zinc-650 font-medium leading-relaxed font-latin">
              Your responses suggest you may be experiencing distress. To protect your well-being, please reach out to one of the support services below. You are not alone.
            </p>
            <p className="text-zinc-650 font-medium leading-relaxed font-urdu text-right" dir="rtl">
              آپ کے جوابات سے ظاہر ہوتا ہے کہ آپ پریشانی کا سامنا کر رہے ہیں۔ اپنی فلاح و بہبود کے لیے، براہ کرم نیچے دی گئی امدادی خدمات میں سے کسی ایک سے رابطہ کریں۔ آپ اکیلے نہیں ہیں۔
            </p>
          </div>

          {/* Resources List */}
          <div className="space-y-2.5">
            {helplineResources.map((res, index) => (
              <div 
                key={index}
                className="border border-zinc-200 bg-zinc-50 rounded-xl p-3 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:border-zinc-300 transition-colors"
              >
                <div className="space-y-1 flex-1">
                  <div className="flex flex-wrap items-center gap-x-2">
                    <span className="font-bold text-zinc-900 text-sm font-latin">{res.name}</span>
                    <span className="text-zinc-400 text-xs">|</span>
                    <span className="font-bold text-zinc-700 text-sm font-urdu" dir="rtl">{res.urduName}</span>
                  </div>
                  
                  <div className="text-[11px] text-zinc-500 leading-normal">
                    <span className="font-latin">{res.desc}</span> <span className="font-urdu" dir="rtl">{res.descUrdu}</span>
                  </div>
                  
                  <div className="text-[10px] text-zinc-400 font-semibold uppercase tracking-wider font-latin">
                    Timing: {res.timing}
                  </div>
                </div>

                <a 
                  href={`tel:${res.phone.split('/')[0].trim().replace(/[^0-9]/g, '')}`} 
                  className="bg-white border border-zinc-200 hover:bg-zinc-900 hover:text-white hover:border-zinc-900 px-4 py-2 rounded-lg font-bold text-xs flex items-center justify-center gap-1.5 transition-all shadow-sm shrink-0"
                >
                  <Phone className="w-3.5 h-3.5" />
                  <span>Call {res.phone.split('/')[0].trim()}</span>
                </a>
              </div>
            ))}
          </div>
        </div>

        {/* Action Panel */}
        <div className="bg-zinc-50 p-5 md:p-6 border-t border-zinc-150 space-y-4">
          {/* Follow-up Opt-In Checkbox */}
          <div 
            onClick={() => setOptIn(!optIn)}
            className={`border rounded-xl p-3 flex items-center gap-3 cursor-pointer transition-all duration-200 ${
              optIn 
                ? 'border-zinc-800 bg-white shadow-md' 
                : 'border-zinc-200 bg-white hover:border-zinc-300'
            }`}
          >
            <div className="text-zinc-950 flex-shrink-0">
              {optIn ? (
                <CheckSquare className="w-5 h-5 text-zinc-950 fill-zinc-950 stroke-white" />
              ) : (
                <Square className="w-5 h-5 text-zinc-400" />
              )}
            </div>
            
            <div className="flex flex-col sm:flex-row sm:justify-between items-start sm:items-center gap-1.5 flex-1">
              <div className="text-left font-latin">
                <span className="text-xs font-bold text-zinc-900">Request follow-up from researcher</span>
                <p className="text-[10px] text-zinc-400">We will check in with you in 48 hours.</p>
              </div>
              <div className="text-right font-urdu" dir="rtl">
                <span className="text-xs font-bold text-zinc-900 block">محقق سے رابطہ کی درخواست</span>
                <p className="text-[10px] text-zinc-400">ہم 48 گھنٹوں میں آپ سے رابطہ کریں گے۔</p>
              </div>
            </div>
          </div>

          {/* Confirm Button */}
          <div className="flex justify-end">
            <button
              onClick={() => onConfirm(optIn)}
              disabled={submitting}
              className="px-6 py-3 bg-zinc-900 hover:bg-zinc-800 text-white font-bold rounded-xl text-xs md:text-sm flex items-center justify-center gap-2 shadow-lg disabled:opacity-50 transition-colors w-full sm:w-auto"
            >
              {submitting ? (
                <span>Saving choice...</span>
              ) : (
                <>
                  <span>Proceed / آگے بڑھیں</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </div>
        </div>
      </motion.div>
    </div>
  );
};

export default SafetyPanelModal;
