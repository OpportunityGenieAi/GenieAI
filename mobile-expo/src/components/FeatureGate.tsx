import React from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useNavigation } from '@react-navigation/native';
import { colors, fonts } from '../theme/colors';

export function FeatureGate({ title, body }: { title: string; body: string }) {
  const navigation = useNavigation<any>();
  return (
    <View style={styles.wrap}>
      <View style={styles.iconCircle}>
        <Ionicons name="lock-closed-outline" size={28} color={colors.blue} />
      </View>
      <Text style={styles.title}>{title}</Text>
      <Text style={styles.body}>{body}</Text>
      <Pressable style={styles.primaryBtn} onPress={() => navigation.navigate('Signup')}>
        <Text style={styles.primaryBtnText}>Create a free account</Text>
      </Pressable>
      <Pressable onPress={() => navigation.navigate('Login')}>
        <Text style={styles.linkBtnText}>I already have an account</Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: 30 },
  iconCircle: {
    width: 64, height: 64, borderRadius: 32, backgroundColor: colors.blueTint,
    alignItems: 'center', justifyContent: 'center', marginBottom: 18,
  },
  title: { fontFamily: fonts.extraBold, fontSize: 20, color: colors.ink, marginBottom: 8, textAlign: 'center' },
  body: { fontFamily: fonts.regular, fontSize: 13.5, color: colors.inkSoft, textAlign: 'center', marginBottom: 22, maxWidth: 280 },
  primaryBtn: { backgroundColor: colors.blue, borderRadius: 12, paddingVertical: 13, paddingHorizontal: 28, marginBottom: 10, width: '100%', alignItems: 'center' },
  primaryBtnText: { fontFamily: fonts.bold, fontSize: 14, color: '#fff' },
  linkBtnText: { fontFamily: fonts.bold, fontSize: 13.5, color: colors.blue },
});
