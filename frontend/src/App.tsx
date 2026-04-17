import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Navbar from './components/Navbar';
import LandingPage from './pages/LandingPage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import DashboardPage from './pages/DashboardPage';
import ActivityPage from './pages/ActivityPage';
import AdminDashboardPage from './pages/AdminDashboardPage';
import ProfilePage from './pages/ProfilePage';
import GroupsManagementPage from './pages/GroupsManagementPage';

const App: React.FC = () => {
  // Helper to get fresh auth status
  const checkAuth = () => !!localStorage.getItem('access_token');

  return (
    <Router>
      <div className="min-h-screen flex flex-col">
        <Navbar />
        <main className="flex-grow container mx-auto px-4 py-8">
          <Routes>
            <Route path="/" element={<LandingPage />} />
            
            {/* Guest Only Routes */}
            <Route 
              path="/login" 
              element={checkAuth() ? <Navigate to="/dashboard" /> : <LoginPage />} 
            />
            <Route 
              path="/register" 
              element={checkAuth() ? <Navigate to="/dashboard" /> : <RegisterPage />} 
            />

            {/* Protected Routes */}
            <Route 
              path="/dashboard" 
              element={checkAuth() ? <DashboardPage /> : <Navigate to="/login" />} 
            />
            <Route 
              path="/activity/:id" 
              element={checkAuth() ? <ActivityPage /> : <Navigate to="/login" />} 
            />
            <Route 
              path="/profile" 
              element={checkAuth() ? <ProfilePage /> : <Navigate to="/login" />} 
            />
            <Route 
              path="/admin" 
              element={checkAuth() ? <AdminDashboardPage /> : <Navigate to="/login" />} 
            />
            <Route 
              path="/admin/groups" 
              element={checkAuth() ? <GroupsManagementPage /> : <Navigate to="/login" />} 
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
