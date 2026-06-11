import React, { useEffect, useState } from 'react';
import { AlertTriangle, Loader2, Trash2, X } from 'lucide-react';

const CONFIRMATION_PHRASE = 'Confirm Delete';

interface DeleteUserModalProps {
  isOpen: boolean;
  username: string;
  fullName?: string;
  deleting: boolean;
  error: string | null;
  onClose: () => void;
  onConfirm: () => void;
}

const DeleteUserModal: React.FC<DeleteUserModalProps> = ({
  isOpen,
  username,
  fullName,
  deleting,
  error,
  onClose,
  onConfirm,
}) => {
  const [confirmation, setConfirmation] = useState('');

  useEffect(() => {
    if (isOpen) {
      setConfirmation('');
    }
  }, [isOpen, username]);

  if (!isOpen) {
    return null;
  }

  const canDelete = confirmation === CONFIRMATION_PHRASE && !deleting;
  const displayName = fullName || username;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40">
      <div className="bg-white border border-zinc-200 rounded-xl shadow-xl max-w-lg w-full p-6 space-y-5">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-start gap-3">
            <div className="w-10 h-10 rounded-lg bg-red-50 text-red-600 flex items-center justify-center shrink-0">
              <AlertTriangle size={20} />
            </div>
            <div>
              <h2 className="text-lg font-bold text-zinc-900">Permanently Delete User</h2>
              <p className="text-sm text-zinc-500 mt-1">
                This will permanently remove <strong className="text-zinc-800">{displayName}</strong> (@{username}) and all related data, including submissions, assessments, support tickets, and notifications. This cannot be undone.
              </p>
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
          <label htmlFor="delete-confirmation" className="text-sm font-medium text-zinc-700">
            Type <span className="font-mono text-red-700">{CONFIRMATION_PHRASE}</span> to confirm
          </label>
          <input
            id="delete-confirmation"
            type="text"
            value={confirmation}
            onChange={(e) => setConfirmation(e.target.value)}
            placeholder={CONFIRMATION_PHRASE}
            className="input-minimal"
            autoComplete="off"
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
            Cancel
          </button>
          <button
            type="button"
            onClick={onConfirm}
            disabled={!canDelete}
            className="px-4 py-2.5 rounded-lg bg-red-600 text-white text-sm font-medium hover:bg-red-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {deleting ? <Loader2 size={16} className="animate-spin" /> : <Trash2 size={16} />}
            Delete User
          </button>
        </div>
      </div>
    </div>
  );
};

export default DeleteUserModal;
