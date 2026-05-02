import React, { lazy, Suspense } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, Outlet } from 'react-router-dom';
import Navbar from './components/Navbar';
import LoadingSpinner from './components/Common/LoadingSpinner';

// Lazy Loaded Components
const LandingPage = lazy(() => import('./pages/LandingPage'));
const LoginPage = lazy(() => import('./pages/LoginPage'));
const RegisterPage = lazy(() => import('./pages/RegisterPage'));
const DashboardPage = lazy(() => import('./pages/DashboardPage'));
const ActivityPage = lazy(() => import('./pages/ActivityPage'));
const AdminDashboardPage = lazy(() => import('./pages/AdminDashboardPage'));
const AdminReportsPage = lazy(() => import('./pages/AdminReportsPage'));
const GroupsManagementPage = lazy(() => import('./pages/GroupsManagementPage'));
const GroupDetailPage = lazy(() => import('./pages/GroupDetailPage'));
const AdminBaselineResultsPage = lazy(() => import('./pages/AdminBaselineResultsPage'));
const AdminPosttestResultsPage = lazy(() => import('./pages/AdminPosttestResultsPage'));
const AdminSupportQueriesPage = lazy(() => import('./pages/AdminSupportQueriesPage'));
const AdminLayout = lazy(() => import('./components/Admin/AdminLayout'));
const ProfilePage = lazy(() => import('./pages/ProfilePage'));
const ResultsPage = lazy(() => import('./pages/ResultsPage'));
const QuestionnairePage = lazy(() => import('./pages/QuestionnairePage'));
const AuthOnboardingGuard = lazy(() => import('./components/Auth/OnboardingGuard'));
const BaselineRedirect = lazy(() => import('./components/Auth/BaselineRedirect'));

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
                element={<div className="container mx-auto px-4 py-8 flex-grow">{checkAuth() ? (isAdminUser() ? <Navigate to="/admin" replace /> : <Navigate to="/dashboard" replace />) : <LandingPage />}</div>}
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

              {/* Participant Routes - Wrapped in Container */}
              <Route element={<div className="container mx-auto px-4 py-8 flex-grow"><AuthOnboardingGuard><Outlet /></AuthOnboardingGuard></div>}>
                <Route path="/dashboard" element={<DashboardPage />} />
                <Route path="/profile" element={<ProfilePage />} />
                <Route path="/activity/:id" element={<ActivityPage />} />
                <Route path="/results/:id" element={<ResultsPage />} />
                <Route path="/questionnaire/:id" element={<QuestionnairePage />} />
                <Route path="/baseline-questionnaire" element={<BaselineRedirect />} />
              </Route>
              
              {/* Admin Hub - Nested Routes with Sidebar Layout */}
              <Route element={<AuthOnboardingGuard requireAdmin={true}><AdminLayout /></AuthOnboardingGuard>}>
                  <Route path="/admin" element={<AdminDashboardPage />} />
                  <Route path="/admin/groups" element={<GroupsManagementPage />} />
                  <Route path="/admin/groups/:id" element={<GroupDetailPage />} />
                 <Route path="/admin/baseline-data" element={<AdminBaselineResultsPage />} />
                 <Route path="/admin/posttest-data" element={<AdminPosttestResultsPage />} />
                 <Route path="/admin/support-queries" element={<AdminSupportQueriesPage />} />
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
