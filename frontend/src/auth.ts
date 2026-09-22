// Simple token storage. Kept in localStorage so a page refresh keeps
// the user logged in. Cleared on logout or on 401 from the API.

const TOKEN_KEY = 'cybersentinel_token';

export function getToken(): string | null {
    return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
    localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
    localStorage.removeItem(TOKEN_KEY);
}

export function isLoggedIn(): boolean {
    return getToken() !== null;
}
