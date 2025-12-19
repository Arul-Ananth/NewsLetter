import { extendTheme } from '@mui/material/styles';

export const theme = extendTheme({
    cssVariables: true,
    colorSchemes: {
        light: {
            palette: {
                primary: { main: '#007C82' },
                secondary: { main: '#2B67F6' },
                background: { default: '#F4F7FB', paper: '#FFFFFF' },
                text: { primary: '#0D1B2A', secondary: '#3B4A66' },
            },
        },
        dark: {
            palette: {
                primary: { main: '#5CE1E6' },
                secondary: { main: '#7CFF6B' },
                background: { default: '#0A0F1E', paper: '#11182A' },
                text: { primary: '#E6F0FF', secondary: '#A9B6D0' },
            },
        },
    },
    shape: {
        borderRadius: 14,
    },
    typography: {
        fontFamily: '"IBM Plex Sans", "Space Grotesk", "Roboto", "Arial", sans-serif',
        h1: { fontFamily: '"Space Grotesk", "IBM Plex Sans", sans-serif', fontWeight: 600 },
        h2: { fontFamily: '"Space Grotesk", "IBM Plex Sans", sans-serif', fontWeight: 600 },
        h3: { fontFamily: '"Space Grotesk", "IBM Plex Sans", sans-serif', fontWeight: 600 },
        h4: { fontFamily: '"Space Grotesk", "IBM Plex Sans", sans-serif', fontWeight: 600 },
        h5: { fontFamily: '"Space Grotesk", "IBM Plex Sans", sans-serif', fontWeight: 600 },
        h6: { fontFamily: '"Space Grotesk", "IBM Plex Sans", sans-serif', fontWeight: 600 },
    },
    components: {
        MuiButton: {
            styleOverrides: {
                root: { textTransform: 'none', borderRadius: 12 },
            },
        },
        MuiPaper: {
            styleOverrides: {
                root: {
                    borderRadius: 16,
                },
            },
        },
    },
});
