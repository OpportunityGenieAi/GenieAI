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
  /** Step 1: creates the account and emails a confirmation code. Does NOT log in. */
  async signup(params: { name: string; email: string; password: string }): Promise<void> {
    await api.post('/auth/signup', params);
  },

  /** Step 2: the user types the emailed code; on success they're logged in. */
  async verifyEmail(email: string, code: string): Promise<AppUser> {
    const res = await api.post('/auth/verify-email', { email, code });
    await TokenStorage.save(res.access_token);
    return res.user;
  },

  async resendCode(email: string): Promise<void> {
    await api.post('/auth/resend-code', { email });
  },

  async login(email: string, password: string): Promise<AppUser> {
    const res = await api.post('/auth/login', { email, password });
    await TokenStorage.save(res.access_token);
    return res.user;
  },

  /** Emails a password-reset code. */
  async forgotPasswordStart(email: string): Promise<void> {
    await api.post('/auth/forgot-password/start', { email });
  },

  async forgotPasswordVerify(email: string, code: string, new_password: string): Promise<void> {
    await api.post('/auth/forgot-password/verify', { email, code, new_password });
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
