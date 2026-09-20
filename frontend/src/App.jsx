import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth, ROLE_HOME_ROUTES } from './context/AuthContext';
import { ProtectedRoute } from './components/auth/ProtectedRoute';
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';
import { CitizenWorkspace } from './pages/CitizenWorkspace';
import { AnalystWorkspace } from './pages/AnalystWorkspace';
import { AuthorityWorkspace } from './pages/AuthorityWorkspace';
import { AdminWorkspace } from './pages/AdminWorkspace';

/**
 * Root Redirect Handler:
 * Dynamically forwards authenticated users to their assigned workspace,
 * or unauthenticated users to /login.
 */
const RootRedirect = () => {
  const { isAuthenticated, role, isLoading } = useAuth();
  
  if (isLoading) {
    return (
      <div className="w-screen h-screen bg-slate-950 flex flex-col items-center justify-center text-slate-100">
        <div className="w-12 h-12 border-2 border-cyan-500/20 border-t-cyan-400 rounded-full animate-spin mb-3" />
        <span className="text-xs font-mono text-slate-400">Resolving workspace privileges...</span>
      </div>
    );
  }
  
  if (!isAuthenticated || !role) {
    return <Navigate to="/login" replace />;
  }
  
  return <Navigate to={ROLE_HOME_ROUTES[role] || '/login'} replace />;
};

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public Auth Routes */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/signup" element={<RegisterPage />} />

          {/* 1. CITIZEN Workspace: Public GIS, Ward Discovery, Grievances, Stations */}
          <Route
            path="/citizen"
            element={
              <ProtectedRoute allowedRoles={['CITIZEN', 'SYSTEM_ADMIN']}>
                <CitizenWorkspace />
              </ProtectedRoute>
            }
          />

          {/* 2. URBAN ANALYST Workspace: 12-Lens GIS Command Center, AI Diagnostics, Scenarios, Comparisons */}
          <Route
            path="/analyst"
            element={
              <ProtectedRoute allowedRoles={['URBAN_ANALYST', 'SYSTEM_ADMIN']}>
                <AnalystWorkspace />
              </ProtectedRoute>
            }
          />

          {/* 3. URBAN AUTHORITY Workspace: Operational Monitoring, Grievance Queues, Municipal Dispatch */}
          <Route
            path="/authority"
            element={
              <ProtectedRoute allowedRoles={['URBAN_AUTHORITY', 'SYSTEM_ADMIN']}>
                <AuthorityWorkspace />
              </ProtectedRoute>
            }
          />

          {/* 4. SYSTEM ADMIN Workspace: User Management, RBAC Matrix, GIS Layer Registry, Audit Logs */}
          <Route
            path="/admin"
            element={
              <ProtectedRoute allowedRoles={['SYSTEM_ADMIN']}>
                <AdminWorkspace />
              </ProtectedRoute>
            }
          />

          {/* Root and Catch-All Fallback Redirects */}
          <Route path="/" element={<RootRedirect />} />
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
