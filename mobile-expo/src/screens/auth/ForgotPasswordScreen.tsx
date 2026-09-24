import React, { useState } from 'react';
import { ActivityIndicator, Pressable, StyleSheet, Text, TextInput, View } from 'react-native';
import { colors, fonts } from '../../theme/colors';
import { AuthApi } from '../../api/auth';

export default function ForgotPasswordScreen() {
  const [step, setStep] = useState(1);
  const [email, setEmail] = useState('');
  const [code, setCode] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);
  const [done, setDone] = useState(false);

  const sendCode = async () => {
    if (!email.includes('@')) { setError('Enter a valid email.'); return; }
    setBusy(true); setError(null); setInfo(null);
    try {
      await AuthApi.forgotPasswordStart(email.trim());
      setStep(2);
      setInfo('If an account exists for that email, a reset code is on its way.');
    } catch (e: any) {
      setError(e.message || 'Something went wrong.');
    }
    setBusy(false);
  };

  const completeReset = async () => {
    if (code.trim().length < 6 || newPassword.length < 6) {
      setError('Enter the code from your email and a new password (6+ characters).');
      return;
    }
    setBusy(true); setError(null);
    try {
      await AuthApi.forgotPasswordVerify(email.trim(), code.trim(), newPassword);
      setDone(true);
    } catch (e: any) {
      setError(e.message || 'Something went wrong.');
    }
    setBusy(false);
  };

  return (
    <View style={styles.container}>
      <Text style={styles.heading}>Reset your password</Text>
      {error && <View style={styles.errorBox}><Text style={styles.errorText}>{error}</Text></View>}
      {info && !done && <View style={styles.successBox}><Text style={styles.successText}>{info}</Text></View>}
      {done ? (
        <View style={styles.successBox}>
          <Text style={styles.successText}>Password updated — log in with your new password.</Text>
        </View>
      ) : step === 1 ? (
        <>
          <Text style={styles.sub}>Enter your account email and we'll send you a reset code.</Text>
          <Text style={styles.label}>Email</Text>
          <TextInput style={styles.input} value={email} onChangeText={setEmail} autoCapitalize="none" keyboardType="email-address" />
          <Pressable style={styles.primaryBtn} onPress={sendCode} disabled={busy}>
            {busy ? <ActivityIndicator color="#fff" /> : <Text style={styles.primaryBtnText}>Send reset code</Text>}
          </Pressable>
        </>
      ) : (
        <>
          <Text style={styles.label}>Code from your email</Text>
          <TextInput
            style={[styles.input, styles.codeInput]}
            value={code}
            onChangeText={(t) => setCode(t.replace(/\D/g, ''))}
            keyboardType="number-pad"
            maxLength={10}
          />
          <Text style={styles.label}>New password</Text>
          <TextInput style={styles.input} value={newPassword} onChangeText={setNewPassword} secureTextEntry />
          <Pressable style={styles.primaryBtn} onPress={completeReset} disabled={busy}>
            {busy ? <ActivityIndicator color="#fff" /> : <Text style={styles.primaryBtnText}>Reset password</Text>}
          </Pressable>
          <Pressable style={{ marginTop: 16, alignItems: 'center' }} onPress={sendCode} disabled={busy}>
            <Text style={styles.linkText}>Didn't get it? Send a new code</Text>
          </Pressable>
        </>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg, padding: 20 },
  heading: { fontFamily: fonts.extraBold, fontSize: 21, color: colors.ink, marginBottom: 20 },
  sub: { fontFamily: fonts.regular, fontSize: 13, color: colors.inkSoft, marginBottom: 8 },
  errorBox: { backgroundColor: colors.redTint, borderRadius: 10, padding: 12, marginBottom: 14 },
  errorText: { fontFamily: fonts.regular, color: colors.red, fontSize: 12.5 },
  successBox: { backgroundColor: colors.greenTint, borderRadius: 10, padding: 12, marginBottom: 14 },
  successText: { fontFamily: fonts.regular, color: colors.green, fontSize: 12.5 },
  label: { fontFamily: fonts.bold, fontSize: 12.5, color: colors.inkSoft, marginBottom: 6, marginTop: 8 },
  input: { backgroundColor: colors.grayTint, borderRadius: 10, paddingHorizontal: 13, paddingVertical: 12, fontFamily: fonts.regular, fontSize: 14, color: colors.ink },
  codeInput: { fontSize: 22, letterSpacing: 6, textAlign: 'center' },
  primaryBtn: { backgroundColor: colors.blue, borderRadius: 12, paddingVertical: 14, alignItems: 'center', marginTop: 20 },
  primaryBtnText: { fontFamily: fonts.bold, fontSize: 14, color: '#fff' },
  linkText: { fontFamily: fonts.bold, fontSize: 13, color: colors.blue },
});
