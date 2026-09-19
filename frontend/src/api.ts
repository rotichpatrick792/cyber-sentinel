import type { Health, PredictResponse } from './types';

const API_BASE = 'http://127.0.0.1:8000';

async function request<T>(path: string, init?: RequestInit): Promise<T> {
    const res = await fetch(`${API_BASE}${path}`, {
        headers: { 'Content-Type': 'application/json' },
        ...init,
    });
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
