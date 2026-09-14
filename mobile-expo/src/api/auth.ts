import { api } from './client';
import { TokenStorage } from './tokenStorage';

export interface AppUser {
  id: string;
  name: string;
  email: string;
  is_admin: boolean;
  subscription_tier: string;
  preferred_locale: string;
}

export const AuthApi = {
  async signup(params: {
    name: string; email: string; password: string;
    security_question: string; security_answer: string;
  }): Promise<AppUser> {
    const res = await api.post('/auth/signup', params);
    await TokenStorage.save(res.access_token);
    return res.user;
  },

  async login(email: string, password: string): Promise<AppUser> {
    const res = await api.post('/auth/login', { email, password });
    await TokenStorage.save(res.access_token);
    return res.user;
  },

  async forgotPasswordStart(email: string): Promise<string> {
    const res = await api.post('/auth/forgot-password/start', { email });
    return res.security_question;
  },

  async forgotPasswordVerify(email: string, security_answer: string, new_password: string): Promise<void> {
    await api.post('/auth/forgot-password/verify', { email, security_answer, new_password });
  },

  async me(): Promise<AppUser | null> {
    try {
      return await api.get('/auth/me', { auth: true });
    } catch {
      return null;
    }
  },

  async logout(): Promise<void> {
    await TokenStorage.clear();
  },
};
