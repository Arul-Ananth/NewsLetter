
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import AppTheme from './theme/AppTheme'; // Global Theme Wrapper
import { SettingsProvider } from './context/SettingsContext';

import Dashboard from './pages/DashBoard';
import SignIn from "./pages/SignIn";

import SignUp from "./pages/SignUp";

export default function App() {
  return (
    <AppTheme>
      <SettingsProvider>
        <Router>
          <Routes>
            <Route path="/" element={<Dashboard />} />

            <Route path="/signin" element={<SignIn />} />
            <Route path="/signup" element={<SignUp />} />
          </Routes>
        </Router>
      </SettingsProvider>
    </AppTheme>
  );
}
