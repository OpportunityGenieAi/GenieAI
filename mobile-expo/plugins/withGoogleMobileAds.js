const { withAndroidManifest, withInfoPlist } = require('@expo/config-plugins');

function withGoogleMobileAdsAndroid(config, { androidAppId }) {
  return withAndroidManifest(config, (config) => {
    const mainApplication = config.modResults.manifest.application[0];
    if (!mainApplication['meta-data']) {
      mainApplication['meta-data'] = [];
    }
    mainApplication['meta-data'] = mainApplication['meta-data'].filter(
      (item) => item.$['android:name'] !== 'com.google.android.gms.ads.APPLICATION_ID'
    );
    mainApplication['meta-data'].push({
      $: {
        'android:name': 'com.google.android.gms.ads.APPLICATION_ID',
        'android:value': androidAppId,
      },
    });
    return config;
  });
}

function withGoogleMobileAdsIOS(config, { iosAppId }) {
  return withInfoPlist(config, (config) => {
    config.modResults.GADApplicationIdentifier = iosAppId;
    return config;
  });
}

module.exports = function withGoogleMobileAds(config, { androidAppId, iosAppId } = {}) {
  if (androidAppId) {
    config = withGoogleMobileAdsAndroid(config, { androidAppId });
  }
  if (iosAppId) {
    config = withGoogleMobileAdsIOS(config, { iosAppId });
  }
  return config;
};
