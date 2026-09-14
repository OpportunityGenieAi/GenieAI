import React, { createContext, useCallback, useContext, useState } from 'react';
import { AppUser, AuthApi } from '../api/auth';
import { TokenStorage } from '../api/tokenStorage';

interface AuthContextValue {
  user: AppUser | null;
  loading: boolean;
  error: string | null;
  restoreSession: () => Promise<void>;
  login: (email: string, password: string) => Promise<boolean>;
  signup: (params: { name: string; email: string; password: string; securityQuestion: string; securityAnswer: string }) => Promise<boolean>;
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

  const login = useCallback(async (email: string, password: string) => {
    setError(null);
    try {
      const u = await AuthApi.login(email, password);
      setUser(u);
      return true;
    } catch (e: any) {
      setError(e.message || 'Login failed');
      return false;
    }
  }, []);

  const signup = useCallback(async (params: { name: string; email: string; password: string; securityQuestion: string; securityAnswer: string }) => {
    setError(null);
    try {
      const u = await AuthApi.signup({
        name: params.name,
        email: params.email,
        password: params.password,
        security_question: params.securityQuestion,
        security_answer: params.securityAnswer,
      });
      setUser(u);
      return true;
    } catch (e: any) {
      setError(e.message || 'Signup failed');
      return false;
    }
  }, []);

  const logout = useCallback(async () => {
    await AuthApi.logout();
    setUser(null);
  }, []);

  const clearError = useCallback(() => setError(null), []);

  return (
    <AuthContext.Provider value={{ user, loading, error, restoreSession, login, signup, logout, clearError }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
