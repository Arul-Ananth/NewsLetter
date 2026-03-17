import { jwtDecode } from "jwt-decode";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

// --- Interfaces ---
export interface NewsletterResponse {
    topic: string;
    content: string;
    bill: {
        deducted: number;
        remaining: number;
    };
}

export interface Memory {
    id: string;
    document: string;
    metadata: any;
}

export interface LoginResponse {
    access_token: string;
    token_type: string;
}

export interface SignupResponse {
    message: string;
    user_id: number;
}

// --- Token Management ---
const getAuthHeaders = () => {
    const token = localStorage.getItem('access_token');
    return {
        'Content-Type': 'application/json',
        'Authorization': token ? `Bearer ${token}` : ''
    };
};

export const api = {
    // Helper to extract 'user_id' from the JWT Token
    getCurrentUserId: (): string | null => {
        const token = localStorage.getItem('access_token');
        const isLocalMode = localStorage.getItem('isLocalMode') === 'true';

        if (!token) {
            return isLocalMode ? "0" : null;
        }
        try {
            const decoded: any = jwtDecode(token);
            return decoded.user_id ? decoded.user_id.toString() : null;
        } catch (e) {
            console.error("Failed to decode token", e);
            return null;
        }
    },

    // --- Auth ---

    signup: async (fullName: string, email: string, password: string): Promise<SignupResponse> => {
        const response = await fetch(`${API_BASE_URL}/auth/signup`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                full_name: fullName,
                email: email,
                password: password
            }),
        });

        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || 'Signup failed');
        return data;
    },

    login: async (email: string, password: string): Promise<LoginResponse> => {
        const response = await fetch(`${API_BASE_URL}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password }),
        });

        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || 'Login failed');

        // Save Token Automatically
        localStorage.setItem('access_token', data.access_token);
        return data;
    },

    // NEW: Social Login Handler
    // This typically redirects the browser to your backend's OAuth route
    socialLogin: (provider: 'google' | 'facebook' | 'apple') => {
        // Example: Redirect to FastAPI endpoint like /auth/google
        // Since we don't have the backend running for this specific demo, we log it.
        // In production: window.location.href = `${API_BASE_URL}/auth/${provider}`;
        console.log(`Initiating ${provider} login flow...`);
        alert(`Redirecting to ${API_BASE_URL}/auth/${provider} \n(Requires Backend OAuth Implementation)`);
    },

    logout: () => {
        localStorage.removeItem('access_token');
        window.location.href = '/signin';
    },

    isAuthenticated: () => {
        return !!localStorage.getItem('access_token');
    },

    // --- Secure Features ---

    generateBriefing: async (topic: string, apiKeys?: { serper?: string, openai?: string }): Promise<NewsletterResponse> => {
        const userId = api.getCurrentUserId();
        if (!userId) throw new Error("User not logged in");

        const response = await fetch(`${API_BASE_URL}/news/generate`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({
                topic,
                user_id: userId,
                serper_api_key: apiKeys?.serper,
                openai_api_key: apiKeys?.openai
            }),
        });

        if (response.status === 401) api.logout();
        if (response.status === 402) throw new Error("Insufficient Credits. Please Top Up.");

        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || 'Generation failed');
        return data;
    },

    sendFeedback: async (originalTopic: string, feedbackText: string, sentiment: string): Promise<void> => {
        const response = await fetch(`${API_BASE_URL}/news/feedback`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({
                original_topic: originalTopic,
                feedback_text: feedbackText,
                sentiment: sentiment
            }),
        });
        if (!response.ok) {
            const data = await response.json().catch(() => ({}));
            throw new Error(data.detail || 'Feedback submission failed');
        }
    },

    getProfile: async (): Promise<Memory[]> => {
        const userId = api.getCurrentUserId();
        if (!userId) throw new Error("User not logged in");

        const response = await fetch(`${API_BASE_URL}/news/profile/${userId}`, {
            headers: getAuthHeaders()
        });

        if (response.status === 401) api.logout();

        const data = await response.json();
        const items = data.memories || data;

        if (!Array.isArray(items)) return [];

        return items.map((item: any, index: number) => {
            const meta = item.payload || item.metadata || {};
            const doc = item.payload?.document || item.document || item;
            const fallbackId = `${meta.topic || 'memory'}-${index}`;

            return {
                id: String(item.id || item.payload?.id || item.metadata?.id || fallbackId),
                document: doc,
                metadata: meta
            };
        });
    }
};
