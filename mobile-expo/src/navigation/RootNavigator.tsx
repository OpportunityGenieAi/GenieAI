import React from 'react';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { MainTabs } from './MainTabs';
import LoginScreen from '../screens/auth/LoginScreen';
import SignupScreen from '../screens/auth/SignupScreen';
import ForgotPasswordScreen from '../screens/auth/ForgotPasswordScreen';
import VerifyEmailScreen from '../screens/auth/VerifyEmailScreen';
import GpaConverterScreen from '../screens/profile/GpaConverterScreen';
import { AdminScreen, ScholarshipFormScreen } from '../screens/admin/AdminScreen';
import AppSettingsScreen from '../screens/admin/AppSettingsScreen';
import { colors } from '../theme/colors';

const Stack = createNativeStackNavigator();

export function RootNavigator() {
  return (
    <Stack.Navigator screenOptions={{ headerShown: false }}>
      <Stack.Screen name="Main" component={MainTabs} />
      <Stack.Screen
        name="Login" component={LoginScreen}
        options={{ headerShown: true, title: '', headerStyle: { backgroundColor: colors.bg }, headerShadowVisible: false }}
      />
      <Stack.Screen
        name="Signup" component={SignupScreen}
        options={{ headerShown: true, title: '', headerStyle: { backgroundColor: colors.bg }, headerShadowVisible: false }}
      />
      <Stack.Screen
        name="VerifyEmail" component={VerifyEmailScreen}
        options={{ headerShown: true, title: '', headerStyle: { backgroundColor: colors.bg }, headerShadowVisible: false }}
      />
      <Stack.Screen
        name="ForgotPassword" component={ForgotPasswordScreen}
        options={{ headerShown: true, title: '', headerStyle: { backgroundColor: colors.bg }, headerShadowVisible: false }}
      />
      <Stack.Screen name="GpaConverter" component={GpaConverterScreen} />
      <Stack.Screen name="Admin" component={AdminScreen} />
      <Stack.Screen name="AppSettings" component={AppSettingsScreen} />
      <Stack.Screen name="ScholarshipForm" component={ScholarshipFormScreen} />
    </Stack.Navigator>
  );
}
