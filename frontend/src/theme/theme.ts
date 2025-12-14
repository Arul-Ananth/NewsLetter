import { createTheme } from '@mui/material/styles';

export const theme = createTheme({
    cssVariables: true,


    colorSchemes: {
        light: {
            palette: {
                primary: { main: '#1976d2' },
                background: { default: '#f5f5f5', paper: '#ffffff' },
            },
        },
        dark: {
            palette: {
                primary: { main: '#90caf9' },
                secondary: { main: '#f48fb1' },
                background: { default: '#0a1929', paper: '#102035' },
            },
        },
    },
    typography: {
        fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
        h6: { fontWeight: 600 },
    },
    components: {

        MuiButton: {
            styleOverrides: {
                root: { textTransform: 'none' },
            },
        },
    },

});