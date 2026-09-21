import { useCallback, useEffect, useRef, useState } from 'react';
import { InterstitialAd, AdEventType } from 'react-native-google-mobile-ads';
import { usePublicSettings } from '../context/PublicSettingsContext';

let shownThisSession = false;

export function useInterstitialAd() {
  const { adsEnabled, interstitialUnitId } = usePublicSettings();
  const adRef = useRef<InterstitialAd | null>(null);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    if (!adsEnabled) return;

    const ad = InterstitialAd.createForAdRequest(interstitialUnitId, {
      requestNonPersonalizedAdsOnly: false,
    });
    adRef.current = ad;

    const unsubLoaded = ad.addAdEventListener(AdEventType.LOADED, () => setLoaded(true));
    const unsubClosed = ad.addAdEventListener(AdEventType.CLOSED, () => {
      setLoaded(false);
      ad.load();
    });

    ad.load();

    return () => {
      unsubLoaded();
      unsubClosed();
    };
  }, [adsEnabled, interstitialUnitId]);

  const showIfFirstTimeThisSession = useCallback(() => {
    if (!adsEnabled) return false;
    if (shownThisSession) return false;
    if (loaded && adRef.current) {
      shownThisSession = true;
      adRef.current.show();
      return true;
    }
    return false;
  }, [adsEnabled, loaded]);

  return { showIfFirstTimeThisSession, loaded };
}
