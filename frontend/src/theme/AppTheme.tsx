import * as React from 'react';
import { CssVarsProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { theme } from './theme';

interface AppThemeProps {
  children: React.ReactNode;
  disableCustomTheme?: boolean;
}

export default function AppTheme({ children }: AppThemeProps) {
  return (
    <CssVarsProvider theme={theme} defaultMode="dark">
      <CssBaseline enableColorScheme />
      {children}
    </CssVarsProvider>
  );
}
