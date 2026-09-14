import React, { useState } from 'react';
import { ActivityIndicator, Pressable, StyleSheet, Text, TextInput, View } from 'react-native';
import { colors, fonts } from '../../theme/colors';
import { AuthApi } from '../../api/auth';

export default function ForgotPasswordScreen() {
  const [step, setStep] = useState(1);
  const [email, setEmail] = useState('');
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);

  const startReset = async () => {
    setBusy(true); setError(null);
    try {
      const q = await AuthApi.forgotPasswordStart(email.trim());
      setQuestion(q);
      setStep(2);
    } catch (e: any) {
      setError(e.message || 'Something went wrong.');
    }
    setBusy(false);
  };

  const completeReset = async () => {
    setBusy(true); setError(null);
    try {
      await AuthApi.forgotPasswordVerify(email.trim(), answer, newPassword);
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
      {done ? (
        <View style={styles.successBox}>
          <Text style={styles.successText}>Password updated — log in with your new password.</Text>
        </View>
      ) : step === 1 ? (
        <>
          <Text style={styles.label}>Email</Text>
          <TextInput style={styles.input} value={email} onChangeText={setEmail} autoCapitalize="none" keyboardType="email-address" />
          <Pressable style={styles.primaryBtn} onPress={startReset} disabled={busy}>
            {busy ? <ActivityIndicator color="#fff" /> : <Text style={styles.primaryBtnText}>Continue</Text>}
          </Pressable>
        </>
      ) : (
        <>
          <Text style={styles.sub}>{question}</Text>
          <Text style={styles.label}>Answer</Text>
          <TextInput style={styles.input} value={answer} onChangeText={setAnswer} />
          <Text style={styles.label}>New password</Text>
          <TextInput style={styles.input} value={newPassword} onChangeText={setNewPassword} secureTextEntry />
          <Pressable style={styles.primaryBtn} onPress={completeReset} disabled={busy}>
            {busy ? <ActivityIndicator color="#fff" /> : <Text style={styles.primaryBtnText}>Reset password</Text>}
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
  successBox: { backgroundColor: colors.greenTint, borderRadius: 10, padding: 12 },
  successText: { fontFamily: fonts.regular, color: colors.green, fontSize: 12.5 },
  label: { fontFamily: fonts.bold, fontSize: 12.5, color: colors.inkSoft, marginBottom: 6, marginTop: 8 },
  input: { backgroundColor: colors.grayTint, borderRadius: 10, paddingHorizontal: 13, paddingVertical: 12, fontFamily: fonts.regular, fontSize: 14, color: colors.ink },
  primaryBtn: { backgroundColor: colors.blue, borderRadius: 12, paddingVertical: 14, alignItems: 'center', marginTop: 20 },
  primaryBtnText: { fontFamily: fonts.bold, fontSize: 14, color: '#fff' },
});
