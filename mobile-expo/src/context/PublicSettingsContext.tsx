import React, { createContext, useCallback, useContext, useEffect, useState } from 'react';
import { Platform } from 'react-native';
import { SettingsApi } from '../api/settings';

const TEST_BANNER_UNIT_ID = Platform.select({
  ios: 'ca-app-pub-3940256099942544/2934735716',
  android: 'ca-app-pub-3940256099942544/6300978111',
  default: 'ca-app-pub-3940256099942544/6300978111',
})!;

const TEST_INTERSTITIAL_UNIT_ID = Platform.select({
  ios: 'ca-app-pub-3940256099942544/4411468910',
  android: 'ca-app-pub-3940256099942544/1033173712',
  default: 'ca-app-pub-3940256099942544/1033173712',
})!;

interface PublicSettingsValue {
  adsEnabled: boolean;
  bannerUnitId: string;
  interstitialUnitId: string;
  usingTestAds: boolean;
}

const PublicSettingsContext = createContext<PublicSettingsValue>({
  adsEnabled: false,
  bannerUnitId: TEST_BANNER_UNIT_ID,
  interstitialUnitId: TEST_INTERSTITIAL_UNIT_ID,
  usingTestAds: true,
});

export function PublicSettingsProvider({ children }: { children: React.ReactNode }) {
  const [value, setValue] = useState<PublicSettingsValue>({
    adsEnabled: false,
    bannerUnitId: TEST_BANNER_UNIT_ID,
    interstitialUnitId: TEST_INTERSTITIAL_UNIT_ID,
    usingTestAds: true,
  });

  const load = useCallback(async () => {
    try {
      const rows = await SettingsApi.getPublic();
      const map: Record<string, string> = {};
      rows.forEach((r) => { if (r.value) map[r.key] = r.value; });

      const bannerKey = Platform.OS === 'ios' ? 'admob_banner_unit_id_ios' : 'admob_banner_unit_id_android';
      const interstitialKey = Platform.OS === 'ios' ? 'admob_interstitial_unit_id_ios' : 'admob_interstitial_unit_id_android';

      const bannerUnitId = map[bannerKey] || TEST_BANNER_UNIT_ID;
      const interstitialUnitId = map[interstitialKey] || TEST_INTERSTITIAL_UNIT_ID;

      setValue({
        adsEnabled: map['ads_enabled'] === 'true',
        bannerUnitId,
        interstitialUnitId,
        usingTestAds: bannerUnitId === TEST_BANNER_UNIT_ID,
      });
    } catch {
      // keep ads-disabled defaults on failure
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  return <PublicSettingsContext.Provider value={value}>{children}</PublicSettingsContext.Provider>;
}

export function usePublicSettings() {
  return useContext(PublicSettingsContext);
}
