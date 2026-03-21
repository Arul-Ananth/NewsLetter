import { createContext, useContext, useMemo, useState, type ReactNode } from 'react';

interface SettingsContextType {
    apiKey: string;
    setApiKey: (key: string) => void;
    serperKey: string;
    setSerperKey: (key: string) => void;
}

const SettingsContext = createContext<SettingsContextType | undefined>(undefined);

export function useSettings() {
    const context = useContext(SettingsContext);
    if (!context) {
        throw new Error('useSettings must be used within a SettingsProvider');
    }
    return context;
}

function usePersistedSetting(storageKey: string, initialValue = '') {
    const [value, setValue] = useState(() => localStorage.getItem(storageKey) || initialValue);

    const updateValue = (nextValue: string) => {
        setValue(nextValue);
        localStorage.setItem(storageKey, nextValue);
    };

    return [value, updateValue] as const;
}

export function SettingsProvider({ children }: { children: ReactNode }) {
    const [apiKey, setApiKey] = usePersistedSetting('userArgs_apiKey');
    const [serperKey, setSerperKey] = usePersistedSetting('userArgs_serperKey');

    const value = useMemo(
        () => ({
            apiKey,
            setApiKey,
            serperKey,
            setSerperKey,
        }),
        [apiKey, serperKey],
    );

    return <SettingsContext.Provider value={value}>{children}</SettingsContext.Provider>;
}
