import React, { useEffect, useState } from 'react';
import { ActivityIndicator, StyleSheet, Text, View } from 'react-native';
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
import { AuthProvider, useAuth } from './src/context/AuthContext';
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
    return (
      <View style={styles.splash}>
        <Text style={styles.splashText}>OpportunityGenie AI</Text>
        <ActivityIndicator color={colors.blue} style={{ marginTop: 16 }} />
      </View>
    );
  }
  return <>{children}</>;
}

export default function App() {
  const [fontsLoaded] = useFonts({
    Inter_400Regular, Inter_500Medium, Inter_600SemiBold, Inter_700Bold, Inter_800ExtraBold,
  });

  if (!fontsLoaded) {
    return (
      <View style={styles.splash}>
        <ActivityIndicator color={colors.blue} />
      </View>
    );
  }

  return (
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
          </TrackerProvider>
        </ScholarshipProvider>
      </ProfileProvider>
    </AuthProvider>
  );
}

const styles = StyleSheet.create({
  splash: { flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.bg },
  splashText: { fontFamily: fonts.extraBold, fontSize: 18, color: colors.ink },
});
