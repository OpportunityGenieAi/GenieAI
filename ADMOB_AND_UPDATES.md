# AdMob + App Settings + OTA Updates — what to do with this

## 1. Apply these files

Extract this zip's contents directly into your project, overwriting the
matching files in `backend/` and `mobile-expo/`. Then:

```bash
# backend
cd backend
git add .
git commit -m "Add admin-editable app settings (AdMob, API key overrides)"
git push origin main   # Render redeploys automatically

# mobile-expo
cd ../mobile-expo
npm install   # pulls in react-native-google-mobile-ads and expo-dev-client
git add .
git commit -m "Add real AdMob ads, App Settings admin screen"
git push origin main
```

## 2. The Expo Go limitation — read this before testing

**Expo Go can no longer run this app.** `react-native-google-mobile-ads`
is native code; Expo Go only bundles a fixed set of modules and doesn't
include it. From now on, testing on your phone means installing a
**development build** instead — a real app, built once via EAS, that
behaves like Expo Go but includes your actual native dependencies.

```bash
npm install -g eas-cli
eas login                      # free Expo account, create one if needed
eas build:configure            # first-time setup, creates eas.json

eas build --profile development --platform android
```

This builds in the cloud (10-20 minutes typically) and gives you a link
to download an `.apk` — install that directly on your Android phone
(same "allow unknown sources" prompt as before). For iOS, the same
command with `--platform ios` works but needs an Apple Developer account
even for this development build (Apple requires code signing even for
internal testing).

Once installed, run your dev server as usual:
```bash
npx expo start --dev-client
```
and open the link/QR it gives you from inside your new development build
app (not Expo Go).

## 3. Right now, you're seeing Google's official TEST ads

The App ID in `app.json` and the fallback ad unit IDs in
`PublicSettingsContext.tsx` are Google's published test values — they
always show a real (test-labeled) ad, safely, with no AdMob account
needed yet. This is intentional: it proves the whole pipeline works
before you deal with a real AdMob account.

## 4. Switching to your real AdMob account, when ready

1. Create an AdMob account at admob.google.com, add your app (once it's
   in the Play Store / App Store — AdMob wants a real store listing).
2. AdMob gives you a real **App ID** (`ca-app-pub-XXXX~XXXX`). Put that
   in `app.json`'s plugin config, replacing the test one — this requires
   a new build (`eas build`) since it's baked into the native app.
3. AdMob also gives you **ad unit IDs** for each placement (banner,
   interstitial). These you can set from inside the app itself: log in
   as admin → Profile → Admin console → **App Settings** → paste in the
   real IDs → Save. These take effect immediately, no rebuild needed.

## 5. Publishing updates without app-store resubmission (EAS Update)

Once you have a real build installed (from step 2), most future changes
that are pure JavaScript/React (new screens, bug fixes, most of what
you'll actually change day to day) can be pushed **instantly** to
everyone's phones, skipping app-store review entirely:

```bash
eas update:configure     # one-time setup

eas update --branch production --message "Fixed the scholarship search bug"
```

Everyone with the app installed gets the update the next time they open
it — typically within seconds. This does **not** work for changes that
touch native code (like a new native library, or the AdMob App ID
itself) — those still need a full `eas build` + store resubmission.

## 6. Full store resubmission (native changes, or your first real release)

```bash
eas build --profile production --platform android
eas build --profile production --platform ios
eas submit --platform android
eas submit --platform ios
```

Same accounts as covered in the earlier `DEPLOY.md` (Apple Developer
$99/yr, Google Play Console $25 one-time).
