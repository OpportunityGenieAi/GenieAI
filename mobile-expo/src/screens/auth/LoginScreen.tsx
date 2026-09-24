import React, { useState } from 'react';
import { ActivityIndicator, Linking, Pressable, StyleSheet, Text, TextInput, View } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { colors, fonts } from '../../theme/colors';
import { useAuth } from '../../context/AuthContext';

export default function LoginScreen() {
  const navigation = useNavigation<any>();
  const { login, error } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const submit = async () => {
    if (!email.includes('@') || !password) return;
    setSubmitting(true);
    const result = await login(email.trim(), password);
    setSubmitting(false);
    if (result === 'ok') navigation.goBack();
    // Password was right but the email isn't confirmed yet: send a fresh code.
    if (result === 'unverified') navigation.replace('VerifyEmail', { email: email.trim(), autoResend: true });
  };

  return (
    <View style={styles.container}>
      <Text style={styles.heading}>Welcome back</Text>
      <Text style={styles.sub}>Log in to see your scholarship matches.</Text>
      {error && (
        <View style={styles.errorBox}><Text style={styles.errorText}>{error}</Text></View>
      )}
      <Text style={styles.label}>Email</Text>
      <TextInput style={styles.input} value={email} onChangeText={setEmail} autoCapitalize="none" keyboardType="email-address" />
      <Text style={styles.label}>Password</Text>
      <TextInput style={styles.input} value={password} onChangeText={setPassword} secureTextEntry />

      <Pressable style={styles.primaryBtn} onPress={submit} disabled={submitting}>
        {submitting ? <ActivityIndicator color="#fff" /> : <Text style={styles.primaryBtnText}>Log in</Text>}
      </Pressable>

      <Pressable style={{ marginTop: 16, alignItems: 'center' }} onPress={() => navigation.navigate('ForgotPassword')}>
        <Text style={styles.linkText}>Forgot your password?</Text>
      </Pressable>
      <Pressable style={{ marginTop: 10, alignItems: 'center' }} onPress={() => navigation.replace('Signup')}>
        <Text style={styles.linkText}>New here? Create an account</Text>
      </Pressable>
      <Pressable
        style={{ marginTop: 20, alignItems: 'center' }}
        onPress={() => Linking.openURL('https://opportunitygenie.org/static/privacy-policy.html')}
      >
        <Text style={styles.footerLinkText}>Privacy Policy</Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg, padding: 20 },
  heading: { fontFamily: fonts.extraBold, fontSize: 21, color: colors.ink, marginBottom: 4 },
  sub: { fontFamily: fonts.regular, fontSize: 13, color: colors.inkSoft, marginBottom: 20 },
  errorBox: { backgroundColor: colors.redTint, borderRadius: 10, padding: 12, marginBottom: 14 },
  errorText: { fontFamily: fonts.regular, color: colors.red, fontSize: 12.5 },
  label: { fontFamily: fonts.bold, fontSize: 12.5, color: colors.inkSoft, marginBottom: 6, marginTop: 12 },
  input: { backgroundColor: colors.grayTint, borderRadius: 10, paddingHorizontal: 13, paddingVertical: 12, fontFamily: fonts.regular, fontSize: 14, color: colors.ink },
  primaryBtn: { backgroundColor: colors.blue, borderRadius: 12, paddingVertical: 14, alignItems: 'center', marginTop: 20 },
  primaryBtnText: { fontFamily: fonts.bold, fontSize: 14, color: '#fff' },
  linkText: { fontFamily: fonts.bold, fontSize: 13, color: colors.blue },
  footerLinkText: { fontFamily: fonts.regular, fontSize: 12, color: colors.inkSoft, textDecorationLine: 'underline' },
});