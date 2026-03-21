const AUTH_SESSION_STORAGE_KEY = 'aerobrief_session_token';

export function getSessionToken(): string | null {
    return sessionStorage.getItem(AUTH_SESSION_STORAGE_KEY);
}

export function setSessionToken(token: string): void {
    sessionStorage.setItem(AUTH_SESSION_STORAGE_KEY, token);
}

export function clearSessionToken(): void {
    sessionStorage.removeItem(AUTH_SESSION_STORAGE_KEY);
}
