import type { ReactNode } from 'react';
import Box from '@mui/material/Box';
import Chip from '@mui/material/Chip';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';
import ColorModeToggle from './ColorModeToggle';

interface AuthSplitLayoutProps {
    heroTitle: string;
    heroBody: string;
    heroTags?: string[];
    children: ReactNode;
    footer?: ReactNode;
}

function NeuralMeshSvg() {
    return (
        <Box
            component="svg"
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 420 260"
            role="img"
            aria-hidden="true"
            sx={{ width: '100%', maxWidth: 460, opacity: 0.9 }}
        >
            <defs>
                <linearGradient id="meshStroke" x1="0" y1="0" x2="1" y2="1">
                    <stop offset="0%" stopColor="currentColor" stopOpacity="0.6" />
                    <stop offset="100%" stopColor="currentColor" stopOpacity="0.2" />
                </linearGradient>
            </defs>
            <g fill="none" stroke="url(#meshStroke)" strokeWidth="1.2">
                <path d="M30 210 L120 120 L210 150 L310 60 L390 90" />
                <path d="M40 60 L140 90 L210 30 L300 140 L380 200" />
                <path d="M70 230 L170 190 L240 220 L320 160 L400 180" />
                <path d="M20 130 L130 150 L220 110 L300 190 L390 130" />
            </g>
            <g fill="currentColor">
                <circle cx="120" cy="120" r="6" opacity="0.9" />
                <circle cx="210" cy="150" r="5" opacity="0.7" />
                <circle cx="310" cy="60" r="6" opacity="0.8" />
                <circle cx="140" cy="90" r="4.5" opacity="0.6" />
                <circle cx="210" cy="30" r="5.5" opacity="0.8" />
                <circle cx="300" cy="140" r="6" opacity="0.7" />
                <circle cx="380" cy="200" r="5" opacity="0.6" />
                <circle cx="240" cy="220" r="6" opacity="0.8" />
            </g>
        </Box>
    );
}

export default function AuthSplitLayout({
    heroTitle,
    heroBody,
    heroTags = [],
    children,
    footer,
}: AuthSplitLayoutProps) {
    return (
        <Box
            sx={{
                minHeight: '100dvh',
                display: 'grid',
                gridTemplateColumns: { xs: '1fr', md: '1.1fr 0.9fr' },
                bgcolor: 'background.default',
            }}
        >
            <ColorModeToggle sx={{ position: 'fixed', top: 16, right: 16, zIndex: 1300 }} />
            <Box
                sx={(theme) => ({
                    position: 'relative',
                    overflow: 'hidden',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    p: { xs: 4, md: 8 },
                    color: theme.palette.text.primary,
                    background:
                        theme.palette.mode === 'dark'
                            ? 'radial-gradient(1200px circle at 10% 20%, rgba(92,225,230,0.18), transparent 55%), radial-gradient(900px circle at 80% 10%, rgba(124,255,107,0.15), transparent 50%), linear-gradient(135deg, rgba(8,12,24,0.96), rgba(12,20,36,0.98))'
                            : 'radial-gradient(900px circle at 10% 20%, rgba(0,124,130,0.12), transparent 55%), radial-gradient(800px circle at 80% 10%, rgba(43,103,246,0.12), transparent 50%), linear-gradient(135deg, rgba(244,247,251,0.98), rgba(233,238,248,0.98))',
                })}
            >
                <Box sx={{ maxWidth: 520 }}>
                    <Stack direction="row" spacing={1} sx={{ mb: 2, flexWrap: 'wrap' }}>
                        {heroTags.map((tag) => (
                            <Chip key={tag} label={tag} size="small" variant="outlined" />
                        ))}
                    </Stack>
                    <Typography variant="h3" sx={{ mb: 2 }}>
                        {heroTitle}
                    </Typography>
                    <Typography variant="body1" sx={{ color: 'text.secondary', mb: 4 }}>
                        {heroBody}
                    </Typography>
                    <NeuralMeshSvg />
                </Box>
            </Box>
            <Box
                sx={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    p: { xs: 3, sm: 4, md: 6 },
                    bgcolor: 'background.default',
                }}
            >
                <Box sx={{ width: '100%', maxWidth: 480 }}>
                    {children}
                    {footer && <Box sx={{ mt: 2 }}>{footer}</Box>}
                </Box>
            </Box>
        </Box>
    );
}
