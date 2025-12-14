import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import AppTheme from './theme/AppTheme'; // Global Theme Wrapper
import { SettingsProvider } from './context/SettingsContext';

import Dashboard from './pages/DashBoard';
import SignIn from "./pages/SignIn";
import Box from "@mui/material/Box";

import SignUp from "./pages/SignUp";

export default function App() {
  return (
    <AppTheme>
      <SettingsProvider>
        <Router>
          <Routes>
            <Route path="/" element={
              <Box sx={{ width: "100%", height: "100%", display: "flex", justifyContent: "center", alignItems: "center" }}>
                <Dashboard />
              </Box>
            } />

            <Route path="/signin" element={<SignIn />} />
            <Route path="/signup" element={<SignUp />} />
          </Routes>
        </Router>
      </SettingsProvider>
    </AppTheme>
  );
}