import Constants from 'expo-constants';

/**
 * API base URL, read from app.json's `expo.extra.apiBaseUrl`, or overridden
 * at build time with an EAS build profile / environment variable.
 *
 * - Physical device with Expo Go: use your computer's LAN IP, not localhost
 *   (e.g. http://192.168.1.23:8000) — the phone can't resolve "localhost"
 *   as your dev machine.
 * - Android emulator: http://10.0.2.2:8000
 * - iOS simulator: http://localhost:8000 works fine.
 */
export const API_BASE_URL: string =
  (Constants.expoConfig?.extra?.apiBaseUrl as string) || 'http://localhost:8000';
