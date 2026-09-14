import React from 'react';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Ionicons } from '@expo/vector-icons';
import { colors } from '../theme/colors';
import HomeScreen from '../screens/home/HomeScreen';
import MatchScreen from '../screens/match/MatchScreen';
import TrackerScreen from '../screens/tracker/TrackerScreen';
import AdvisorScreen from '../screens/advisor/AdvisorScreen';
import ProfileScreen from '../screens/profile/ProfileScreen';

const Tab = createBottomTabNavigator();

const ICONS: Record<string, keyof typeof Ionicons.glyphMap> = {
  HomeTab: 'home',
  MatchTab: 'flash',
  TrackerTab: 'list',
  AdvisorTab: 'chatbubble',
  ProfileTab: 'person',
};
const ICONS_OUTLINE: Record<string, keyof typeof Ionicons.glyphMap> = {
  HomeTab: 'home-outline',
  MatchTab: 'flash-outline',
  TrackerTab: 'list-outline',
  AdvisorTab: 'chatbubble-outline',
  ProfileTab: 'person-outline',
};

export function MainTabs() {
  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        headerShown: false,
        tabBarActiveTintColor: colors.blue,
        tabBarInactiveTintColor: colors.inkFaint,
        tabBarStyle: { backgroundColor: '#fff', borderTopColor: colors.line },
        tabBarIcon: ({ focused, color, size }) => {
          const name = focused ? ICONS[route.name] : ICONS_OUTLINE[route.name];
          return <Ionicons name={name} size={size} color={color} />;
        },
      })}
    >
      <Tab.Screen name="HomeTab" component={HomeScreen} options={{ title: 'Home' }} />
      <Tab.Screen name="MatchTab" component={MatchScreen} options={{ title: 'Match' }} />
      <Tab.Screen name="TrackerTab" component={TrackerScreen} options={{ title: 'Tracker' }} />
      <Tab.Screen name="AdvisorTab" component={AdvisorScreen} options={{ title: 'Advisor' }} />
      <Tab.Screen name="ProfileTab" component={ProfileScreen} options={{ title: 'Profile' }} />
    </Tab.Navigator>
  );
}
