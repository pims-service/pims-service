import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';

interface OnboardingGuardProps {
  children: React.ReactNode;
  requireAdmin?: boolean;
}

const OnboardingGuard: React.FC<OnboardingGuardProps> = ({ children, requireAdmin = false }) => {
  const location = useLocation();
  
  // Get fresh auth status from localStorage
  const isAuthenticated = !!localStorage.getItem('access_token');
  const userRole = localStorage.getItem('user_role');
  const hasCompletedBaseline = localStorage.getItem('has_completed_baseline') === 'true';

  if (!isAuthenticated) {
    // Redirect to login but save the current location they were trying to access
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Admin Exception: Admins can bypass baseline requirements for management
  if (userRole === 'Admin') {
    return <>{children}</>;
  }

  if (requireAdmin && userRole !== 'Admin') {
    return <Navigate to="/dashboard" replace />;
  }

  // Participant Redirection Logic
  if (!hasCompletedBaseline) {
    // allow access to /baseline-questionnaire AND active questionnaire IDs
    const isAllowedPath = location.pathname === '/baseline-questionnaire' || 
                         location.pathname.startsWith('/questionnaire/');
                         
    if (!isAllowedPath) {
      return <Navigate to="/baseline-questionnaire" replace />;
    }
  } else {
    // If they HAVE finished the baseline, they shouldn't be on the onboarding page anymore
    if (location.pathname === '/baseline-questionnaire') {
      return <Navigate to="/dashboard" replace />;
    }
  }

  return <>{children}</>;
};

export default OnboardingGuard;
