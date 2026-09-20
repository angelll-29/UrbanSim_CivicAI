import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth, ROLE_HOME_ROUTES } from '../../context/AuthContext';
import { ShieldAlert } from 'lucide-react';

export const ProtectedRoute = ({ children, allowedRoles = [] }) => {
  const { user, isAuthenticated, isLoading, hasRole } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="w-screen h-screen bg-[#07090e] flex flex-col items-center justify-center select-none text-slate-100">
        <div className="relative flex items-center justify-center mb-4">
          <div className="w-14 h-14 rounded-full border-2 border-cyan-500/20 border-t-cyan-400 animate-spin"></div>
          <div className="absolute w-7 h-7 rounded-full bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center">
            <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse"></span>
          </div>
        </div>
        <span className="text-xs font-mono text-slate-400">Verifying session credentials...</span>
      </div>
    );
  }

  // 1. Unauthenticated users -> Redirect to /login
  if (!isAuthenticated || !user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // 2. Role Check: If user does not have permission for this route
  if (allowedRoles.length > 0 && !hasRole(allowedRoles)) {
    const userHomeRoute = ROLE_HOME_ROUTES[user.role] || '/login';
    return (
      <Navigate 
        to={userHomeRoute} 
        state={{ unauthorizedAttempt: location.pathname, requiredRoles: allowedRoles }} 
        replace 
      />
    );
  }

  return children;
};
