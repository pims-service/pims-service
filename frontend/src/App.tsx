import React, { lazy, Suspense } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, Outlet } from 'react-router-dom';
import Navbar from './components/Navbar';
import LoadingSpinner from './components/Common/LoadingSpinner';

// Lazy Loaded Components
const LandingPage = lazy(() => import('./pages/LandingPage'));
const LoginPage = lazy(() => import('./pages/LoginPage'));
const RegisterPage = lazy(() => import('./pages/RegisterPage'));
const ForgotPasswordPage = lazy(() => import('./pages/ForgotPasswordPage'));
const DashboardPage = lazy(() => import('./pages/DashboardPage'));

const ActivityPage = lazy(() => import('./pages/ActivityPage'));
const AdminDashboardPage = lazy(() => import('./pages/AdminDashboardPage'));
const GroupsManagementPage = lazy(() => import('./pages/GroupsManagementPage'));
const GroupDetailPage = lazy(() => import('./pages/GroupDetailPage'));
const AdminT0ResultsPage = lazy(() => import('./pages/AdminT0ResultsPage'));
const AdminT1ResultsPage = lazy(() => import('./pages/AdminT1ResultsPage'));
const AdminTFirstMonthResultsPage = lazy(() => import('./pages/AdminTFirstMonthResultsPage'));
const AdminT2ResultsPage = lazy(() => import('./pages/AdminT2ResultsPage'));
const AdminT3ResultsPage = lazy(() => import('./pages/AdminT3ResultsPage'));
const AdminT4ResultsPage = lazy(() => import('./pages/AdminT4ResultsPage'));
const AdminSupportQueriesPage = lazy(() => import('./pages/AdminSupportQueriesPage'));
const AdminFollowUpsPage = lazy(() => import('./pages/AdminFollowUpsPage'));
const AdminSuicideRiskPage = lazy(() => import('./pages/AdminSuicideRiskPage'));
const AdminLayout = lazy(() => import('./components/Admin/AdminLayout'));
const ProfilePage = lazy(() => import('./pages/ProfilePage'));
const ResultsPage = lazy(() => import('./pages/ResultsPage'));
const QuestionnairePage = lazy(() => import('./pages/QuestionnairePage'));
const AuthOnboardingGuard = lazy(() => import('./components/Auth/OnboardingGuard'));
const SociodemographicRedirect = lazy(() => import('./components/Auth/SociodemographicRedirect'));

const App: React.FC = () => {
  // Helper to get fresh auth status
  const checkAuth = () => !!localStorage.getItem('access_token');
  const isAdminUser = () => localStorage.getItem('user_role') === 'Admin';

  return (
    <Router>
      <div className="min-h-screen flex flex-col bg-white">
        <Navbar />
        <main className="flex-grow flex flex-col">
          <Suspense fallback={<LoadingSpinner />}>
            <Routes>
              <Route
                path="/"
                element={<LandingPage />}
              />

              {/* Guest Only Routes */}
              <Route
                path="/login"
                element={<div className="container mx-auto px-4 py-8 flex-grow">{checkAuth() ? (isAdminUser() ? <Navigate to="/admin" /> : <Navigate to="/dashboard" />) : <LoginPage />}</div>}
              />
              <Route
                path="/register"
                element={<div className="container mx-auto px-4 py-8 flex-grow">{checkAuth() ? (isAdminUser() ? <Navigate to="/admin" /> : <Navigate to="/dashboard" />) : <RegisterPage />}</div>}
              />
              <Route
                path="/forgot-password"
                element={<div className="container mx-auto px-4 py-8 flex-grow">{checkAuth() ? (isAdminUser() ? <Navigate to="/admin" /> : <Navigate to="/dashboard" />) : <ForgotPasswordPage />}</div>}
              />


              {/* Participant Routes - Wrapped in Container */}
              <Route element={<div className="container mx-auto px-4 py-8 flex-grow"><AuthOnboardingGuard><Outlet /></AuthOnboardingGuard></div>}>
                <Route path="/dashboard" element={<DashboardPage />} />
                <Route path="/profile" element={<ProfilePage />} />
                <Route path="/activity/:id" element={<ActivityPage />} />
                <Route path="/results/:id" element={<ResultsPage />} />
                <Route path="/questionnaire/:id" element={<QuestionnairePage />} />
                <Route path="/sociodemographic" element={<SociodemographicRedirect />} />
              </Route>

              {/* Admin Hub - Nested Routes with Sidebar Layout */}
              <Route element={<AuthOnboardingGuard requireAdmin={true}><AdminLayout /></AuthOnboardingGuard>}>
                <Route path="/admin" element={<AdminDashboardPage />} />
                <Route path="/admin/groups" element={<GroupsManagementPage />} />
                <Route path="/admin/groups/:id" element={<GroupDetailPage />} />
                <Route path="/admin/t0-data" element={<AdminT0ResultsPage />} />
                <Route path="/admin/t1-data" element={<AdminT1ResultsPage />} />
                <Route path="/admin/t-first-month-data" element={<AdminTFirstMonthResultsPage />} />
                <Route path="/admin/t2-data" element={<AdminT2ResultsPage />} />
                <Route path="/admin/t3-data" element={<AdminT3ResultsPage />} />
                <Route path="/admin/t4-data" element={<AdminT4ResultsPage />} />
                <Route path="/admin/support-queries" element={<AdminSupportQueriesPage />} />
                <Route path="/admin/follow-ups" element={<AdminFollowUpsPage />} />
                <Route path="/admin/safety-risk" element={<AdminSuicideRiskPage />} />
              </Route>

              {/* Fallback */}
              <Route path="*" element={<Navigate to="/" />} />

            </Routes>
          </Suspense>
        </main>
      </div>
    </Router>
  );
};

export default App;
