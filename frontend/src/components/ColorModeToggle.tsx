import IconButton from '@mui/material/IconButton';
import Tooltip from '@mui/material/Tooltip';
import Brightness4Icon from '@mui/icons-material/Brightness4';
import Brightness7Icon from '@mui/icons-material/Brightness7';
import type { SxProps, Theme } from '@mui/material/styles';
import { useColorScheme } from '@mui/material/styles';

interface ColorModeToggleProps {
    sx?: SxProps<Theme>;
}

export default function ColorModeToggle({ sx }: ColorModeToggleProps) {
    const { mode, setMode } = useColorScheme();

    if (!mode) return null;

    const nextMode = mode === 'dark' ? 'light' : 'dark';

    return (
        <Tooltip title={`Switch to ${nextMode} mode`}>
            <IconButton
                aria-label={`Switch to ${nextMode} mode`}
                onClick={() => setMode(nextMode)}
                sx={sx}
                color="inherit"
            >
                {mode === 'dark' ? <Brightness7Icon /> : <Brightness4Icon />}
            </IconButton>
        </Tooltip>
    );
}
