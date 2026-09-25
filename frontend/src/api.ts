import { clearToken, getToken } from './auth';
import type { FlowsRecentResponse, Health, PredictResponse } from './types';

const API_BASE = 'http://127.0.0.1:8000';

async function request<T>(path: string, init?: RequestInit): Promise<T> {
    const token = getToken();
    const headers: Record<string, string> = {
        'Content-Type': 'application/json',
    };
    if (token) {
        headers.Authorization = `Bearer ${token}`;
    }

    const res = await fetch(`${API_BASE}${path}`, {
        ...init,
        headers: { ...headers, ...(init?.headers as Record<string, string>) },
    });

    if (res.status === 401) {
        // Token expired or invalid — clear it so the app shows the login screen.
        clearToken();
        window.location.reload();
        throw new Error('Unauthorized');
    }

    if (!res.ok) {
        const text = await res.text();
        throw new Error(`HTTP ${res.status}: ${text.slice(0, 200)}`);
    }
    return res.json() as Promise<T>;
}

export function fetchHealth(): Promise<Health> {
    return request<Health>('/health');
}

export function predict(features: Record<string, number>): Promise<PredictResponse> {
    return request<PredictResponse>('/api/v1/predict', {
        method: 'POST',
        body: JSON.stringify({ features }),
    });
}

export function fetchRecentFlows(limit = 50): Promise<FlowsRecentResponse> {
    return request<FlowsRecentResponse>(`/api/v1/flows/recent?limit=${limit}`);
}

export async function login(username: string, password: string): Promise<string> {
    const res = await fetch(`${API_BASE}/api/v1/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
    });
    if (!res.ok) {
        const text = await res.text();
        throw new Error(text.slice(0, 200));
    }
    const data = (await res.json()) as { access_token: string };
    return data.access_token;
}
export async function register(
    username: string,
    email: string,
    password: string,
): Promise<void> {
    const res = await fetch(`${API_BASE}/api/v1/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, email, password }),
    });
    if (!res.ok) {
        const text = await res.text();
        throw new Error(text.slice(0, 200));
    }
}
