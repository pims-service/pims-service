import React, { useEffect, useState } from 'react';
import { AlertTriangle, Loader2, Trash2, X } from 'lucide-react';
import { useTranslation } from 'react-i18next';

interface DeleteAccountModalProps {
  isOpen: boolean;
  username: string;
  deleting: boolean;
  error: string | null;
  onClose: () => void;
  onConfirm: (confirmation: string, password: string) => void;
}

const DeleteAccountModal: React.FC<DeleteAccountModalProps> = ({
  isOpen,
  username,
  deleting,
  error,
  onClose,
  onConfirm,
}) => {
  const { t } = useTranslation();
  const [confirmation, setConfirmation] = useState('');
  const [password, setPassword] = useState('');
  const confirmationPhrase = `${username} Confirm Delete`;

  useEffect(() => {
    if (isOpen) {
      setConfirmation('');
      setPassword('');
    }
  }, [isOpen, username]);

  if (!isOpen) {
    return null;
  }

  const canDelete = confirmation === confirmationPhrase && password.length > 0 && !deleting;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40">
      <div className="bg-white border border-zinc-200 rounded-xl shadow-xl max-w-lg w-full p-6 space-y-5">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-start gap-3">
            <div className="w-10 h-10 rounded-lg bg-red-50 text-red-600 flex items-center justify-center shrink-0">
              <AlertTriangle size={20} />
            </div>
            <div>
              <h2 className="text-lg font-bold text-zinc-900">{t('profile.delete_account_title')}</h2>
              <p className="text-sm text-zinc-500 mt-1">{t('profile.delete_account_description')}</p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            disabled={deleting}
            className="p-2 text-zinc-400 hover:text-zinc-700 transition-colors disabled:opacity-50"
            aria-label="Close"
          >
            <X size={18} />
          </button>
        </div>

        <div className="space-y-2">
          <label htmlFor="self-delete-confirmation" className="text-sm font-medium text-zinc-700">
            {t('profile.delete_account_confirmation_label', { phrase: confirmationPhrase })}
          </label>
          <input
            id="self-delete-confirmation"
            type="text"
            value={confirmation}
            onChange={(e) => setConfirmation(e.target.value)}
            placeholder={confirmationPhrase}
            className="input-minimal font-mono text-sm"
            autoComplete="off"
            disabled={deleting}
          />
        </div>

        <div className="space-y-2">
          <label htmlFor="self-delete-password" className="text-sm font-medium text-zinc-700">
            {t('profile.delete_account_password_label')}
          </label>
          <input
            id="self-delete-password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder={t('profile.delete_account_password_placeholder')}
            className="input-minimal"
            autoComplete="current-password"
            disabled={deleting}
          />
        </div>

        {error && (
          <div className="p-3 rounded-lg bg-red-50 border border-red-100 text-sm text-red-700">
            {error}
          </div>
        )}

        <div className="flex justify-end gap-3 pt-2">
          <button
            type="button"
            onClick={onClose}
            disabled={deleting}
            className="px-4 py-2.5 rounded-lg border border-zinc-200 text-zinc-700 text-sm font-medium hover:bg-zinc-50 transition-colors disabled:opacity-50"
          >
            {t('profile.delete_account_cancel')}
          </button>
          <button
            type="button"
            onClick={() => onConfirm(confirmation, password)}
            disabled={!canDelete}
            className="px-4 py-2.5 rounded-lg bg-red-600 text-white text-sm font-medium hover:bg-red-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {deleting ? <Loader2 size={16} className="animate-spin" /> : <Trash2 size={16} />}
            {t('profile.delete_account_confirm_button')}
          </button>
        </div>
      </div>
    </div>
  );
};

export default DeleteAccountModal;
