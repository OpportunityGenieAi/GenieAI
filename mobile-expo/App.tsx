import React, { useEffect, useState } from 'react';
import { ActivityIndicator, StyleSheet, View } from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { StatusBar } from 'expo-status-bar';
import {
  useFonts,
  Inter_400Regular,
  Inter_500Medium,
  Inter_600SemiBold,
  Inter_700Bold,
  Inter_800ExtraBold,
} from '@expo-google-fonts/inter';

import { colors, fonts } from './src/theme/colors';
import { AnimatedSplashScreen } from './src/components/AnimatedSplashScreen';
import { AuthProvider, useAuth } from './src/context/AuthContext';
import { PublicSettingsProvider } from './src/context/PublicSettingsContext';
import { ProfileProvider } from './src/context/ProfileContext';
import { ScholarshipProvider } from './src/context/ScholarshipContext';
import { TrackerProvider } from './src/context/TrackerContext';
import { RootNavigator } from './src/navigation/RootNavigator';

function SessionGate({ children }: { children: React.ReactNode }) {
  const { restoreSession, loading } = useAuth();
  useEffect(() => {
    restoreSession();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (loading) {
    return <View style={styles.splash} />;
  }
  return <>{children}</>;
}

export default function App() {
  const [fontsLoaded] = useFonts({
    Inter_400Regular, Inter_500Medium, Inter_600SemiBold, Inter_700Bold, Inter_800ExtraBold,
  });
  const [introFinished, setIntroFinished] = useState(false);

  if (!fontsLoaded) {
    return (
      <View style={styles.splash}>
        <ActivityIndicator color={colors.blue} />
      </View>
    );
  }

  return (
    <PublicSettingsProvider>
    <AuthProvider>
      <ProfileProvider>
        <ScholarshipProvider>
          <TrackerProvider>
            <SessionGate>
              <NavigationContainer>
                <StatusBar style="dark" />
                <RootNavigator />
              </NavigationContainer>
            </SessionGate>
            {!introFinished && <AnimatedSplashScreen onFinish={() => setIntroFinished(true)} />}
          </TrackerProvider>
        </ScholarshipProvider>
      </ProfileProvider>
    </AuthProvider>
    </PublicSettingsProvider>
  );
}

const styles = StyleSheet.create({
  splash: { flex: 1, backgroundColor: colors.bg },
});
