export interface AuthStatusResponse {
    message: string;
    user_id?: number;
    trusted_lan_mode: boolean;
    auth_mode: string;
    authenticated: boolean;
    provider?: string | null;
    requires_login: boolean;
    session_token?: string | null;
}

export interface SignupResponse {
    message: string;
    user_id: number;
    auth_provider: string;
}

export interface AuthContextValue {
    loading: boolean;
    status: AuthStatusResponse | null;
    refreshStatus: () => Promise<void>;
    login: (email: string, password: string) => Promise<AuthStatusResponse>;
    signup: (fullName: string, email: string, password: string) => Promise<SignupResponse>;
    logout: () => Promise<void>;
}

export function buildOfflineAuthStatus(message: string): AuthStatusResponse {
    return {
        message,
        trusted_lan_mode: false,
        auth_mode: 'offline',
        authenticated: false,
        provider: null,
        requires_login: false,
        session_token: null,
    };
}
