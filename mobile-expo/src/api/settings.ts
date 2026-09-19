import { api } from './client';

export interface AppSettingItem {
  key: string;
  value: string | null;
}

export const SettingsApi = {
  // No auth needed — used before login to configure ads
  getPublic: (): Promise<AppSettingItem[]> => api.get('/settings/public'),

  // Admin-only
  listAll: (): Promise<AppSettingItem[]> => api.get('/settings', { auth: true }),
  set: (key: string, value: string): Promise<AppSettingItem> =>
    api.put(`/settings/${key}`, { value }, { auth: true }),
};
