import {
    createContext,
    useCallback,
    useContext,
    useEffect,
    useMemo,
    useState,
    type ReactNode,
} from 'react';

import { ApiError } from '../../services/http';
import { getAuthStatus, login as loginRequest, logout as logoutRequest, signup as signupRequest } from './api';
import { clearSessionToken, getSessionToken, setSessionToken } from './storage';
import { buildOfflineAuthStatus, type AuthContextValue, type AuthStatusResponse, type SignupResponse } from './types';

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

function normalizeAuthBootstrapError(error: unknown): AuthStatusResponse {
    if (error instanceof ApiError && error.status === 0) {
        return buildOfflineAuthStatus(error.message);
    }
    if (error instanceof Error) {
        return buildOfflineAuthStatus(error.message);
    }
    return buildOfflineAuthStatus('Unable to determine backend auth status.');
}

export function AuthProvider({ children }: { children: ReactNode }) {
    const [loading, setLoading] = useState(true);
    const [status, setStatus] = useState<AuthStatusResponse | null>(null);

    const refreshStatus = useCallback(async () => {
        try {
            const nextStatus = await getAuthStatus();
            if (!nextStatus.authenticated && getSessionToken()) {
                clearSessionToken();
            }
            setStatus(nextStatus);
        } catch (error) {
            clearSessionToken();
            setStatus(normalizeAuthBootstrapError(error));
        }
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
            } catch (error) {
                clearSessionToken();
                if (active) {
                    setStatus(normalizeAuthBootstrapError(error));
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
            try {
                const nextStatus = await getAuthStatus();
                setStatus(nextStatus);
            } catch (error) {
                setStatus(normalizeAuthBootstrapError(error));
            }
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
