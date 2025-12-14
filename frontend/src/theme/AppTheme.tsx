import * as React from 'react';
import { ThemeProvider } from '@mui/material/styles';
import { theme } from './theme';
import Box from '@mui/material/Box';

interface AppThemeProps {
  children: React.ReactNode;
  disableCustomTheme?: boolean;
}

export default function AppTheme({ children }: AppThemeProps) {
  return (
    <ThemeProvider theme={theme} disableTransitionOnChange>
      <Box
        sx={{
          minHeight: "100vh",
          width: "100vw",
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          bgcolor: "background.default",
          overflowY: "auto",
        }}
      >
        {children}
      </Box>
    </ThemeProvider>
  );
}
