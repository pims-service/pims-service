import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import api, { usersApi } from '../services/api';
import { User, Mail, Calendar, Clock, Trash2 } from 'lucide-react';
import DeleteAccountModal from '../components/Auth/DeleteAccountModal';

const ProfilePage: React.FC = () => {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  React.useEffect(() => {
    const fetchUser = async () => {
      try {
        const { data } = await api.get('/users/profile/');
        setUser(data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchUser();
  }, []);

  const clearSession = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user_role');
    localStorage.removeItem('user_full_name');
    localStorage.removeItem('has_completed_sociodemographic');
    localStorage.removeItem('due_milestone');
    localStorage.removeItem('is_disqualified');
  };

  const handleDeleteAccount = async (confirmation: string, password: string) => {
    if (!user?.username) return;
    setDeleteLoading(true);
    setDeleteError(null);
    try {
      await usersApi.deleteAccount(confirmation, password);
      clearSession();
      navigate('/', {
        replace: true,
        state: { accountDeleted: true },
      });
    } catch (err: any) {
      setDeleteError(err.response?.data?.detail || 'Failed to delete account. Please try again.');
    } finally {
      setDeleteLoading(false);
    }
  };

  const isAdmin = user?.role_name === 'Admin';

  if (loading) return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-zinc-800"></div>
    </div>
  );

  const formatDate = (dateStr: string) => {
    if (!dateStr) return 'N/A';
    return new Intl.DateTimeFormat('en-US', { month: 'long', day: 'numeric', year: 'numeric' }).format(new Date(dateStr));
  };

  const formatTime = (dateStr: string) => {
    if (!dateStr) return 'N/A';
    return new Intl.DateTimeFormat('en-US', { hour: '2-digit', minute: '2-digit', hour12: true }).format(new Date(dateStr));
  };

  return (
    <div className="max-w-2xl mx-auto py-8 space-y-6">
      <div className="bg-white border border-zinc-200 rounded-xl shadow-sm overflow-hidden">
        <div className="bg-zinc-800 p-8 text-white">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 bg-white/10 rounded-lg flex items-center justify-center">
              <User size={32} />
            </div>
            <div>
              <h1 className="text-2xl font-bold">{user?.full_name || user?.username}</h1>
              <p className="text-zinc-400 text-sm">{user?.email}</p>
            </div>
          </div>
        </div>

        <div className="p-8 space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="p-4 bg-zinc-50 rounded-lg border border-zinc-100">
              <div className="flex items-center gap-2 text-zinc-500 text-xs font-bold uppercase tracking-wider mb-2">
                <Mail size={14} /> Email Address
              </div>
              <p className="text-zinc-900 font-semibold">{user?.email}</p>
            </div>

            <div className="p-4 bg-zinc-50 rounded-lg border border-zinc-100">
              <div className="flex items-center gap-2 text-zinc-500 text-xs font-bold uppercase tracking-wider mb-2">
                <User size={14} /> Full Name
              </div>
              <p className="text-zinc-900 font-semibold">{user?.full_name || user?.username}</p>
            </div>

            <div className="p-4 bg-zinc-50 rounded-lg border border-zinc-100">
              <div className="flex items-center gap-2 text-zinc-500 text-xs font-bold uppercase tracking-wider mb-2">
                <Calendar size={14} /> Date Joined
              </div>
              <p className="text-zinc-900 font-semibold">{formatDate(user?.created_at)}</p>
            </div>

            <div className="p-4 bg-zinc-50 rounded-lg border border-zinc-100">
              <div className="flex items-center gap-2 text-zinc-500 text-xs font-bold uppercase tracking-wider mb-2">
                <Clock size={14} /> Time Joined
              </div>
              <p className="text-zinc-900 font-semibold">{formatTime(user?.created_at)}</p>
            </div>
          </div>
        </div>
      </div>

      {!isAdmin && (
      <div className="bg-white border border-red-200 rounded-xl shadow-sm p-6 space-y-4">
        <div>
          <h2 className="text-lg font-bold text-red-700">{t('profile.delete_account_section_title')}</h2>
          <p className="text-sm text-zinc-500 mt-1">{t('profile.delete_account_section_description')}</p>
        </div>
        <button
          type="button"
          onClick={() => {
            setDeleteError(null);
            setShowDeleteModal(true);
          }}
          className="inline-flex items-center gap-2 px-4 py-2.5 rounded-lg border border-red-200 text-red-700 text-sm font-semibold hover:bg-red-50 transition-colors"
        >
          <Trash2 size={16} />
          {t('profile.delete_account_open_button')}
        </button>
      </div>
      )}

      {!isAdmin && (
      <DeleteAccountModal
        isOpen={showDeleteModal}
        username={user?.username || ''}
        deleting={deleteLoading}
        error={deleteError}
        onClose={() => {
          if (!deleteLoading) {
            setShowDeleteModal(false);
            setDeleteError(null);
          }
        }}
        onConfirm={handleDeleteAccount}
      />
      )}
    </div>
  );
};

export default ProfilePage;
