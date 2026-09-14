import * as SecureStore from 'expo-secure-store';

const TOKEN_KEY = 'og_access_token';

export const TokenStorage = {
  async save(token: string): Promise<void> {
    await SecureStore.setItemAsync(TOKEN_KEY, token);
  },
  async read(): Promise<string | null> {
    return SecureStore.getItemAsync(TOKEN_KEY);
  },
  async clear(): Promise<void> {
    await SecureStore.deleteItemAsync(TOKEN_KEY);
  },
};
