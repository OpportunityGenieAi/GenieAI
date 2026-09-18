import React, { useEffect, useRef } from 'react';
import { Animated, Easing, Image, StyleSheet, Text, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, fonts } from '../theme/colors';

/**
 * Plays a short entrance animation on app launch:
 * - the genie logo fades and scales in at the center
 * - a graduation cap icon flies in from the left (the genie's left hand)
 * - a certificate/$ icon flies in from the right (the genie's right hand)
 * - everything settles, holds briefly, then fades out to reveal the app
 *
 * Calls onFinish() once the animation completes.
 */
export function AnimatedSplashScreen({ onFinish }: { onFinish: () => void }) {
  const logoScale = useRef(new Animated.Value(0.6)).current;
  const logoOpacity = useRef(new Animated.Value(0)).current;
  const capTranslate = useRef(new Animated.Value(-90)).current;
  const capOpacity = useRef(new Animated.Value(0)).current;
  const certTranslate = useRef(new Animated.Value(90)).current;
  const certOpacity = useRef(new Animated.Value(0)).current;
  const glowOpacity = useRef(new Animated.Value(0)).current;
  const containerOpacity = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    Animated.sequence([
      // Logo appears first
      Animated.parallel([
        Animated.timing(logoOpacity, { toValue: 1, duration: 450, useNativeDriver: true }),
        Animated.spring(logoScale, { toValue: 1, friction: 5, tension: 60, useNativeDriver: true }),
      ]),
      // Cap and certificate fly in from either side, as if into the genie's hands
      Animated.parallel([
        Animated.spring(capTranslate, { toValue: 0, friction: 6, tension: 50, useNativeDriver: true }),
        Animated.timing(capOpacity, { toValue: 1, duration: 350, useNativeDriver: true }),
        Animated.spring(certTranslate, { toValue: 0, friction: 6, tension: 50, useNativeDriver: true }),
        Animated.timing(certOpacity, { toValue: 1, duration: 350, useNativeDriver: true }),
        Animated.timing(glowOpacity, { toValue: 1, duration: 500, useNativeDriver: true }),
      ]),
      // Hold for a beat so it reads clearly
      Animated.delay(500),
      // Fade the whole splash out
      Animated.timing(containerOpacity, { toValue: 0, duration: 350, easing: Easing.in(Easing.ease), useNativeDriver: true }),
    ]).start(() => onFinish());
  }, []);

  return (
    <Animated.View style={[styles.container, { opacity: containerOpacity }]}>
      <Animated.View style={[styles.glow, { opacity: glowOpacity }]} />

      <View style={styles.stage}>
        <Animated.View style={[styles.sideIcon, styles.leftIcon, { opacity: capOpacity, transform: [{ translateX: capTranslate }] }]}>
          <Ionicons name="school" size={30} color={colors.blue} />
        </Animated.View>

        <Animated.Image
          source={require('../../assets/splash.png')}
          style={[styles.logo, { opacity: logoOpacity, transform: [{ scale: logoScale }] }]}
          resizeMode="contain"
        />

        <Animated.View style={[styles.sideIcon, styles.rightIcon, { opacity: certOpacity, transform: [{ translateX: certTranslate }] }]}>
          <Ionicons name="ribbon" size={30} color={colors.gold} />
        </Animated.View>
      </View>

      <Animated.Text style={[styles.title, { opacity: logoOpacity }]}>
        Opportunity<Text style={{ color: colors.blue }}>Genie</Text> AI
      </Animated.Text>
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  container: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: colors.bg,
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 999,
  },
  glow: {
    position: 'absolute',
    width: 260,
    height: 260,
    borderRadius: 130,
    backgroundColor: colors.blueTint,
  },
  stage: {
    width: 220,
    height: 220,
    alignItems: 'center',
    justifyContent: 'center',
  },
  logo: {
    width: 180,
    height: 180,
  },
  sideIcon: {
    position: 'absolute',
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: '#fff',
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#000',
    shadowOpacity: 0.12,
    shadowRadius: 6,
    shadowOffset: { width: 0, height: 2 },
    elevation: 3,
  },
  leftIcon: {
    left: -6,
    bottom: 30,
  },
  rightIcon: {
    right: -6,
    bottom: 30,
  },
  title: {
    marginTop: 22,
    fontFamily: fonts.extraBold,
    fontSize: 19,
    color: colors.ink,
  },
});
