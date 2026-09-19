import React from 'react';
import { View } from 'react-native';
import { BannerAd, BannerAdSize } from 'react-native-google-mobile-ads';
import { usePublicSettings } from '../context/PublicSettingsContext';

/**
 * Drop this in anywhere a banner ad should appear (e.g. between sections
 * of a scrollable list). Reads its ad unit ID from the backend (Admin >
 * App Settings) at runtime — no rebuild needed to swap in a real ID,
 * only to change the underlying AdMob App ID itself.
 */
export function AdBanner() {
  const { bannerUnitId } = usePublicSettings();

  return (
    <View style={{ alignItems: 'center', marginVertical: 10 }}>
      <BannerAd
        unitId={bannerUnitId}
        size={BannerAdSize.ANCHORED_ADAPTIVE_BANNER}
        requestOptions={{ requestNonPersonalizedAdsOnly: false }}
      />
    </View>
  );
}
