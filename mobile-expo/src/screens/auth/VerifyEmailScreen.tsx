import React, { useEffect, useState } from 'react';
import { ActivityIndicator, Pressable, StyleSheet, Text, TextInput, View } from 'react-native';
import { useNavigation, useRoute } from '@react-navigation/native';
import { colors, fonts } from '../../theme/colors';
import { AuthApi } from '../../api/auth';
import { useAuth } from '../../context/AuthContext';

export default function VerifyEmailScreen() {
  const navigation = useNavigation<any>();
  const route = useRoute<any>();
  const { email, autoResend } = route.params as { email: string; autoResend?: boolean };
  const { verifyEmail, error } = useAuth();
  const [code, setCode] = useState('');
  const [busy, setBusy] = useState(false);
  const [info, setInfo] = useState<string | null>(null);
  const [resendError, setResendError] = useState<string | null>(null);

  const resend = async () => {
    setResendError(null); setInfo(null);
    try {
      await AuthApi.resendCode(email);
      setInfo('A new code is on its way. Check your inbox and spam folder.');
    } catch (e: any) {
      setResendError(e.message || 'Could not resend the code.');
    }
  };

  // Coming from a login attempt with an unconfirmed email: send a fresh code.
  useEffect(() => { if (autoResend) resend(); }, []);

  const submit = async () => {
    if (code.trim().length < 6) return;
    setBusy(true);
    const ok = await verifyEmail(email, code.trim());
    setBusy(false);
    if (ok) navigation.goBack();
  };

  const shownError = resendError || error;

  return (
    <View style={styles.container}>
      <Text style={styles.heading}>Check your email</Text>
      <Text style={styles.sub}>We sent a confirmation code to {email}. Enter it below to activate your account.</Text>
      {shownError && <View style={styles.errorBox}><Text style={styles.errorText}>{shownError}</Text></View>}
      {info && <View style={styles.infoBox}><Text style={styles.infoText}>{info}</Text></View>}

      <Text style={styles.label}>Confirmation code</Text>
      <TextInput
        style={[styles.input, styles.codeInput]}
        value={code}
        onChangeText={(t) => setCode(t.replace(/\D/g, ''))}
        keyboardType="number-pad"
        maxLength={10}
        autoFocus
      />

      <Pressable style={styles.primaryBtn} onPress={submit} disabled={busy}>
        {busy ? <ActivityIndicator color="#fff" /> : <Text style={styles.primaryBtnText}>Confirm email</Text>}
      </Pressable>
      <Pressable style={{ marginTop: 16, alignItems: 'center' }} onPress={resend}>
        <Text style={styles.linkText}>Didn't get it? Resend code</Text>
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
  infoBox: { backgroundColor: colors.greenTint, borderRadius: 10, padding: 12, marginBottom: 14 },
  infoText: { fontFamily: fonts.regular, color: colors.green, fontSize: 12.5 },
  label: { fontFamily: fonts.bold, fontSize: 12.5, color: colors.inkSoft, marginBottom: 6, marginTop: 8 },
  input: { backgroundColor: colors.grayTint, borderRadius: 10, paddingHorizontal: 13, paddingVertical: 12, fontFamily: fonts.regular, fontSize: 14, color: colors.ink },
  codeInput: { fontSize: 22, letterSpacing: 6, textAlign: 'center' },
  primaryBtn: { backgroundColor: colors.blue, borderRadius: 12, paddingVertical: 14, alignItems: 'center', marginTop: 20 },
  primaryBtnText: { fontFamily: fonts.bold, fontSize: 14, color: '#fff' },
  linkText: { fontFamily: fonts.bold, fontSize: 13, color: colors.blue },
});
