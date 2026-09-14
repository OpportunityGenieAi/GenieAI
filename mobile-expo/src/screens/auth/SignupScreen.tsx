import React, { useState } from 'react';
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { Picker } from '@react-native-picker/picker';
import { colors, fonts } from '../../theme/colors';
import { useAuth } from '../../context/AuthContext';

const QUESTIONS = [
  'What city were you born in?',
  "What was your first school's name?",
  'What is your favourite subject?',
];

export default function SignupScreen() {
  const navigation = useNavigation<any>();
  const { signup, error } = useAuth();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [securityQuestion, setSecurityQuestion] = useState(QUESTIONS[0]);
  const [securityAnswer, setSecurityAnswer] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);

  const submit = async () => {
    setLocalError(null);
    if (!name.trim() || !email.includes('@') || password.length < 6 || !securityAnswer.trim()) {
      setLocalError('Fill in every field (password needs 6+ characters).');
      return;
    }
    if (password !== confirm) {
      setLocalError("Passwords don't match.");
      return;
    }
    setSubmitting(true);
    const ok = await signup({ name: name.trim(), email: email.trim(), password, securityQuestion, securityAnswer });
    setSubmitting(false);
    if (ok) navigation.goBack();
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={{ padding: 20 }}>
      <Text style={styles.heading}>Create your account</Text>
      <Text style={styles.sub}>Free — takes under a minute.</Text>
      {(localError || error) && (
        <View style={styles.errorBox}><Text style={styles.errorText}>{localError || error}</Text></View>
      )}

      <Text style={styles.label}>Full name</Text>
      <TextInput style={styles.input} value={name} onChangeText={setName} />
      <Text style={styles.label}>Email</Text>
      <TextInput style={styles.input} value={email} onChangeText={setEmail} autoCapitalize="none" keyboardType="email-address" />
      <View style={{ flexDirection: 'row', gap: 10 }}>
        <View style={{ flex: 1 }}>
          <Text style={styles.label}>Password</Text>
          <TextInput style={styles.input} value={password} onChangeText={setPassword} secureTextEntry />
        </View>
        <View style={{ flex: 1 }}>
          <Text style={styles.label}>Confirm</Text>
          <TextInput style={styles.input} value={confirm} onChangeText={setConfirm} secureTextEntry />
        </View>
      </View>

      <Text style={styles.label}>Security question</Text>
      <View style={styles.pickerWrap}>
        <Picker selectedValue={securityQuestion} onValueChange={setSecurityQuestion}>
          {QUESTIONS.map((q) => <Picker.Item key={q} label={q} value={q} />)}
        </Picker>
      </View>
      <Text style={styles.label}>Answer</Text>
      <TextInput style={styles.input} value={securityAnswer} onChangeText={setSecurityAnswer} />
      <Text style={styles.hint}>You'll need this to reset your password.</Text>

      <Pressable style={styles.primaryBtn} onPress={submit} disabled={submitting}>
        {submitting ? <ActivityIndicator color="#fff" /> : <Text style={styles.primaryBtnText}>Create account</Text>}
      </Pressable>

      <Pressable style={{ marginTop: 16, alignItems: 'center' }} onPress={() => navigation.replace('Login')}>
        <Text style={styles.linkText}>Already registered? Log in</Text>
      </Pressable>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg },
  heading: { fontFamily: fonts.extraBold, fontSize: 21, color: colors.ink, marginBottom: 4 },
  sub: { fontFamily: fonts.regular, fontSize: 13, color: colors.inkSoft, marginBottom: 20 },
  errorBox: { backgroundColor: colors.redTint, borderRadius: 10, padding: 12, marginBottom: 14 },
  errorText: { fontFamily: fonts.regular, color: colors.red, fontSize: 12.5 },
  label: { fontFamily: fonts.bold, fontSize: 12.5, color: colors.inkSoft, marginBottom: 6, marginTop: 12 },
  input: { backgroundColor: colors.grayTint, borderRadius: 10, paddingHorizontal: 13, paddingVertical: 12, fontFamily: fonts.regular, fontSize: 14, color: colors.ink },
  pickerWrap: { backgroundColor: colors.grayTint, borderRadius: 10, overflow: 'hidden' },
  hint: { fontFamily: fonts.regular, fontSize: 11.5, color: colors.inkSoft, marginTop: 5 },
  primaryBtn: { backgroundColor: colors.blue, borderRadius: 12, paddingVertical: 14, alignItems: 'center', marginTop: 20 },
  primaryBtnText: { fontFamily: fonts.bold, fontSize: 14, color: '#fff' },
  linkText: { fontFamily: fonts.bold, fontSize: 13, color: colors.blue },
});
