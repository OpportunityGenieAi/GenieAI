import React, { createContext, useCallback, useContext, useState } from 'react';
import { AppUser, AuthApi } from '../api/auth';
import { ApiError } from '../api/client';
import { TokenStorage } from '../api/tokenStorage';

export type LoginResult = 'ok' | 'unverified' | 'error';

interface AuthContextValue {
  user: AppUser | null;
  loading: boolean;
  error: string | null;
  restoreSession: () => Promise<void>;
  login: (email: string, password: string) => Promise<LoginResult>;
  /** Returns true when the confirmation code email has been sent. */
  signup: (params: { name: string; email: string; password: string }) => Promise<boolean>;
  /** Confirms the emailed code and logs the user in. */
  verifyEmail: (email: string, code: string) => Promise<boolean>;
  logout: () => Promise<void>;
  clearError: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AppUser | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const restoreSession = useCallback(async () => {
    setLoading(true);
    const token = await TokenStorage.read();
    if (token) {
      const me = await AuthApi.me();
      setUser(me);
    }
    setLoading(false);
  }, []);

  const login = useCallback(async (email: string, password: string): Promise<LoginResult> => {
    setError(null);
    try {
      const u = await AuthApi.login(email, password);
      setUser(u);
      return 'ok';
    } catch (e: any) {
      // 403 = correct password but email not verified yet
      if (e instanceof ApiError && e.status === 403) return 'unverified';
      setError(e.message || 'Login failed');
      return 'error';
    }
  }, []);

  const signup = useCallback(async (params: { name: string; email: string; password: string }) => {
    setError(null);
    try {
      await AuthApi.signup(params);
      return true;
    } catch (e: any) {
      setError(e.message || 'Signup failed');
      return false;
    }
  }, []);

  const verifyEmail = useCallback(async (email: string, code: string) => {
    setError(null);
    try {
      const u = await AuthApi.verifyEmail(email, code);
      setUser(u);
      return true;
    } catch (e: any) {
      setError(e.message || 'Verification failed');
      return false;
    }
  }, []);

  const logout = useCallback(async () => {
    await AuthApi.logout();
    setUser(null);
  }, []);

  const clearError = useCallback(() => setError(null), []);

  return (
    <AuthContext.Provider value={{ user, loading, error, restoreSession, login, signup, verifyEmail, logout, clearError }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
