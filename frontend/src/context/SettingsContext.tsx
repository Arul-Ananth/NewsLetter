import React, { createContext, useContext, useState, useEffect, type ReactNode } from 'react';

interface SettingsContextType {
    isDesktop: boolean;
    useCloud: boolean;
    setUseCloud: (useCloud: boolean) => void;
    isLocalMode: boolean; // Derived: isDesktop && !useCloud
    apiKey: string;
    setApiKey: (key: string) => void;
    serperKey: string;
    setSerperKey: (key: string) => void;
}

const SettingsContext = createContext<SettingsContextType | undefined>(undefined);

export const useSettings = () => {
    const context = useContext(SettingsContext);
    if (!context) {
        throw new Error('useSettings must be used within a SettingsProvider');
    }
    return context;
};

interface SettingsProviderProps {
    children: ReactNode;
}

export const SettingsProvider: React.FC<SettingsProviderProps> = ({ children }) => {
    // 1. Detect Desktop Environment (Tauri)
    // @ts-ignore
    const isDesktop = typeof window !== 'undefined' && window.__TAURI__ !== undefined;

    console.log("[Settings] Environment Detection:", { isDesktop, userAgent: window.navigator.userAgent });

    // 2. Preferences
    const [useCloud, setUseCloudState] = useState(() => {
        return localStorage.getItem('useCloud') === 'true';
    });

    const [apiKey, setApiKeyState] = useState(() => {
        return localStorage.getItem('userArgs_apiKey') || '';
    });

    // NEW: Serper Key
    const [serperKey, setSerperKeyState] = useState(() => {
        return localStorage.getItem('userArgs_serperKey') || '';
    });

    const setUseCloud = (val: boolean) => {
        setUseCloudState(val);
        localStorage.setItem('useCloud', String(val));
    };

    const setApiKey = (val: string) => {
        setApiKeyState(val);
        localStorage.setItem('userArgs_apiKey', val);
    };

    const setSerperKey = (val: string) => {
        setSerperKeyState(val);
        localStorage.setItem('userArgs_serperKey', val);
    };

    // 3. Derived Mode
    // Local Mode = We are on Desktop AND user hasn't opted into Cloud
    const isLocalMode = isDesktop && !useCloud;

    console.log("[Settings] Mode:", { isLocalMode, isDesktop, useCloud });

    // Sync mode to localStorage for api.ts (static access) to read if needed
    useEffect(() => {
        localStorage.setItem('isLocalMode', String(isLocalMode));
    }, [isLocalMode]);

    const value = {
        isDesktop,
        useCloud,
        setUseCloud,
        isLocalMode,
        apiKey,
        setApiKey,
        serperKey,

        setSerperKey, // Uses the wrapper function defined above
    };

    return (
        <SettingsContext.Provider value={value}>
            {children}
        </SettingsContext.Provider>
    );
};
