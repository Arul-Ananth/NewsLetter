import { BrowserRouter as Router, Navigate, Route, Routes } from 'react-router-dom';
import Box from '@mui/material/Box';
import CircularProgress from '@mui/material/CircularProgress';

import { AuthProvider, useAuth } from './features/auth/AuthProvider';
import SignInPage from './features/auth/pages/SignInPage';
import SignUpPage from './features/auth/pages/SignUpPage';
import { SettingsProvider } from './context/SettingsContext';
import Dashboard from './pages/Dashboard';
import AppTheme from './theme/AppTheme';

function LoadingScreen() {
  return (
    <Box sx={{ minHeight: '100dvh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <CircularProgress />
    </Box>
  );
}

function AppRoutes() {
  const { loading, status } = useAuth();

  if (loading || !status) {
    return <LoadingScreen />;
  }

  const interactiveMode = status.auth_mode === 'interactive';
  const needsLogin = interactiveMode && !status.authenticated;

  return (
    <Routes>
      <Route path="/" element={needsLogin ? <Navigate to="/signin" replace /> : <Dashboard />} />
      <Route
        path="/signin"
        element={interactiveMode && status.authenticated ? <Navigate to="/" replace /> : status.trusted_lan_mode ? <Navigate to="/" replace /> : <SignInPage />}
      />
      <Route
        path="/signup"
        element={interactiveMode && status.authenticated ? <Navigate to="/" replace /> : status.trusted_lan_mode ? <Navigate to="/" replace /> : <SignUpPage />}
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <AppTheme>
      <AuthProvider>
        <SettingsProvider>
          <Router>
            <AppRoutes />
          </Router>
        </SettingsProvider>
      </AuthProvider>
    </AppTheme>
  );
}
