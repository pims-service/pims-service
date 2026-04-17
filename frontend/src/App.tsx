import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Navbar from './components/Navbar';
import LandingPage from './pages/LandingPage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import DashboardPage from './pages/DashboardPage';
import ActivityPage from './pages/ActivityPage';
import AdminDashboardPage from './pages/AdminDashboardPage';
import GroupsManagementPage from './pages/GroupsManagementPage';
import ProfilePage from './pages/ProfilePage';
import QuestionnairePage from './pages/QuestionnairePage';
import OnboardingGuard from './components/Auth/OnboardingGuard';
import BaselineRedirect from './components/Auth/BaselineRedirect';

const App: React.FC = () => {
  // Helper to get fresh auth status
  const checkAuth = () => !!localStorage.getItem('access_token');

  return (
    <Router>
      <div className="min-h-screen flex flex-col">
        <Navbar />
        <main className="flex-grow container mx-auto px-4 py-8">
          <Routes>
            <Route
              path="/"
              element={checkAuth() ? <Navigate to="/dashboard" replace /> : <LandingPage />}
            />

            {/* Guest Only Routes */}
            <Route
              path="/login"
              element={checkAuth() ? <Navigate to="/dashboard" /> : <LoginPage />}
            />
            <Route
              path="/register"
              element={checkAuth() ? <Navigate to="/dashboard" /> : <RegisterPage />}
            />

            {/* Protected Routes - Wrapping with OnboardingGuard */}
            <Route
              path="/dashboard"
              element={<OnboardingGuard><DashboardPage /></OnboardingGuard>}
            />
            <Route
              path="/activity/:id"
              element={<OnboardingGuard><ActivityPage /></OnboardingGuard>}
            />
            <Route
              path="/profile"
              element={<OnboardingGuard><ProfilePage /></OnboardingGuard>}
            />
            <Route
              path="/admin"
              element={<OnboardingGuard requireAdmin={true}><AdminDashboardPage /></OnboardingGuard>}
            />
            <Route
              path="/admin/groups"
              element={<OnboardingGuard requireAdmin={true}><GroupsManagementPage /></OnboardingGuard>}
            />
            <Route
              path="/questionnaire/:id"
              element={<OnboardingGuard><QuestionnairePage /></OnboardingGuard>}
            />

            {/* Dedicated Baseline Entry Point */}
            <Route
              path="/baseline-questionnaire"
              element={<OnboardingGuard><BaselineRedirect /></OnboardingGuard>}
            />

            {/* Fallback */}
            <Route path="*" element={<Navigate to="/" />} />

          </Routes>
        </main>
      </div>
    </Router>
  );
};


export default App;
