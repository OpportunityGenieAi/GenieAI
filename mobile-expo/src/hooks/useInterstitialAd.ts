import { useCallback, useEffect, useRef, useState } from 'react';
import { InterstitialAd, AdEventType } from 'react-native-google-mobile-ads';
import { usePublicSettings } from '../context/PublicSettingsContext';

// Module-level (not per-component) so it's shared across the whole app —
// an interstitial should show at most once per app session, not once per screen.
let shownThisSession = false;

export function useInterstitialAd() {
  const { interstitialUnitId } = usePublicSettings();
  const adRef = useRef<InterstitialAd | null>(null);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    const ad = InterstitialAd.createForAdRequest(interstitialUnitId, {
      requestNonPersonalizedAdsOnly: false,
    });
    adRef.current = ad;

    const unsubLoaded = ad.addAdEventListener(AdEventType.LOADED, () => setLoaded(true));
    const unsubClosed = ad.addAdEventListener(AdEventType.CLOSED, () => {
      setLoaded(false);
      ad.load(); // preload the next one
    });

    ad.load();

    return () => {
      unsubLoaded();
      unsubClosed();
    };
  }, [interstitialUnitId]);

  const showIfFirstTimeThisSession = useCallback(() => {
    if (shownThisSession) return false;
    if (loaded && adRef.current) {
      shownThisSession = true;
      adRef.current.show();
      return true;
    }
    return false;
  }, [loaded]);

  return { showIfFirstTimeThisSession, loaded };
}
