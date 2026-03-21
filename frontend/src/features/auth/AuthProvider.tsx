import {
    createContext,
    useCallback,
    useContext,
    useEffect,
    useMemo,
    useState,
    type ReactNode,
} from 'react';

import { getAuthStatus, login as loginRequest, logout as logoutRequest, signup as signupRequest } from './api';
import { clearSessionToken, getSessionToken, setSessionToken } from './storage';
import type { AuthContextValue, AuthStatusResponse, SignupResponse } from './types';

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
    const [loading, setLoading] = useState(true);
    const [status, setStatus] = useState<AuthStatusResponse | null>(null);

    const refreshStatus = useCallback(async () => {
        const nextStatus = await getAuthStatus();
        if (!nextStatus.authenticated && getSessionToken()) {
            clearSessionToken();
        }
        setStatus(nextStatus);
    }, []);

    useEffect(() => {
        let active = true;
        (async () => {
            try {
                const nextStatus = await getAuthStatus();
                if (!nextStatus.authenticated && getSessionToken()) {
                    clearSessionToken();
                }
                if (active) {
                    setStatus(nextStatus);
                }
            } finally {
                if (active) {
                    setLoading(false);
                }
            }
        })();
        return () => {
            active = false;
        };
    }, []);

    const login = useCallback(async (email: string, password: string) => {
        const nextStatus = await loginRequest(email, password);
        if (nextStatus.session_token) {
            setSessionToken(nextStatus.session_token);
        } else {
            clearSessionToken();
        }
        const refreshed = await getAuthStatus();
        setStatus(refreshed);
        return refreshed;
    }, []);

    const signup = useCallback(async (fullName: string, email: string, password: string): Promise<SignupResponse> => {
        return signupRequest(fullName, email, password);
    }, []);

    const logout = useCallback(async () => {
        try {
            await logoutRequest();
        } finally {
            clearSessionToken();
            const nextStatus = await getAuthStatus();
            setStatus(nextStatus);
        }
    }, []);

    const value = useMemo<AuthContextValue>(
        () => ({
            loading,
            status,
            refreshStatus,
            login,
            signup,
            logout,
        }),
        [loading, status, refreshStatus, login, signup, logout],
    );

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
}
