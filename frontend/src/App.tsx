import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, Outlet } from 'react-router-dom';
import Navbar from './components/Navbar';
import LandingPage from './pages/LandingPage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import DashboardPage from './pages/DashboardPage';
import ActivityPage from './pages/ActivityPage';
import AdminDashboardPage from './pages/AdminDashboardPage';
import AdminReportsPage from './pages/AdminReportsPage';
import GroupsManagementPage from './pages/GroupsManagementPage';
import GroupDetailPage from './pages/GroupDetailPage';
import AdminLayout from './components/Admin/AdminLayout';
import ProfilePage from './pages/ProfilePage';
import ResultsPage from './pages/ResultsPage';
import QuestionnairePage from './pages/QuestionnairePage';
import OnboardingGuard from './components/Auth/OnboardingGuard';
import BaselineRedirect from './components/Auth/BaselineRedirect';

const App: React.FC = () => {
  // Helper to get fresh auth status
  const checkAuth = () => !!localStorage.getItem('access_token');

  return (
    <Router>
      <div className="min-h-screen flex flex-col bg-white">
        <Navbar />
        <main className="flex-grow flex flex-col pt-16">
          <Routes>
            <Route
              path="/"
              element={<div className="container mx-auto px-4 py-8 flex-grow">{checkAuth() ? <Navigate to="/dashboard" replace /> : <LandingPage />}</div>}
            />

            {/* Guest Only Routes */}
            <Route
              path="/login"
              element={<div className="container mx-auto px-4 py-8 flex-grow">{checkAuth() ? <Navigate to="/dashboard" /> : <LoginPage />}</div>}
            />
            <Route
              path="/register"
              element={<div className="container mx-auto px-4 py-8 flex-grow">{checkAuth() ? <Navigate to="/dashboard" /> : <RegisterPage />}</div>}
            />

            {/* Participant Routes - Wrapped in Container */}
            <Route element={<div className="container mx-auto px-4 py-8 flex-grow"><OnboardingGuard><Outlet /></OnboardingGuard></div>}>
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route path="/profile" element={<ProfilePage />} />
              <Route path="/activity/:id" element={<ActivityPage />} />
              <Route path="/results/:id" element={<ResultsPage />} />
              <Route path="/questionnaire/:id" element={<QuestionnairePage />} />
              <Route path="/baseline-questionnaire" element={<BaselineRedirect />} />
            </Route>
            {/* Admin Hub - Nested Routes with Sidebar Layout */}
            <Route element={<OnboardingGuard requireAdmin={true}><AdminLayout /></OnboardingGuard>}>
               <Route path="/admin" element={<AdminDashboardPage />} />
               <Route path="/admin/groups" element={<GroupsManagementPage />} />
               <Route path="/admin/groups/:id" element={<GroupDetailPage />} />
               <Route path="/admin/reports" element={<AdminReportsPage />} />
            </Route>

            {/* Fallback */}
            <Route path="*" element={<Navigate to="/" />} />

          </Routes>
        </main>
      </div>
    </Router>
  );
};


export default App;
