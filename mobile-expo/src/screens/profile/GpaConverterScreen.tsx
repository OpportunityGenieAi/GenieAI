import React, { useEffect, useState } from 'react';
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { Picker } from '@react-native-picker/picker';
import { useNavigation } from '@react-navigation/native';
import { Ionicons } from '@expo/vector-icons';
import { colors, fonts } from '../../theme/colors';
import { useProfile } from '../../context/ProfileContext';
import { ProfileApi } from '../../api/profile';

export default function GpaConverterScreen() {
  const navigation = useNavigation<any>();
  const profile = useProfile();
  const [systemId, setSystemId] = useState<string>('');
  const [value, setValue] = useState('');
  const [result, setResult] = useState<{ gpa: number; percent: number; ects: string; percentile_note: string } | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      if (profile.systems.length === 0) await profile.loadAll();
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (profile.systems.length > 0 && !systemId) setSystemId(profile.systems[0].id);
  }, [profile.systems, systemId]);

  const system = profile.systems.find((s) => s.id === systemId);

  const convert = async () => {
    if (!systemId || !value.trim()) return;
    setBusy(true); setError(null);
    try {
      const res = await ProfileApi.convertGpa(systemId, value.trim());
      setResult(res);
    } catch {
      setError('Enter a valid value for this grading system.');
    }
    setBusy(false);
  };

  const save = async () => {
    if (!systemId || !value.trim()) return;
    setBusy(true);
    try {
      await profile.saveGpa(systemId, value.trim());
    } catch {
      setError('Could not save — try again.');
    }
    setBusy(false);
  };

  return (
    <ScrollView style={{ backgroundColor: colors.bg }} contentContainerStyle={{ padding: 20, paddingBottom: 60 }}>
      <Pressable style={styles.backRow} onPress={() => navigation.goBack()}>
        <Ionicons name="chevron-back" size={16} color={colors.inkSoft} />
        <Text style={styles.backText}>Back</Text>
      </Pressable>

      <Text style={styles.eyebrow}>Flagship feature</Text>
      <Text style={styles.heading}>GPA Converter</Text>

      <View style={styles.card}>
        <Text style={styles.cardTitle}>Enter your grade</Text>
        {profile.systems.length === 0 ? (
          <ActivityIndicator color={colors.blue} style={{ marginVertical: 10 }} />
        ) : (
          <>
            <Text style={styles.label}>Your grading system</Text>
            <View style={styles.pickerWrap}>
              <Picker selectedValue={systemId} onValueChange={(v) => { setSystemId(v as string); setValue(''); setResult(null); }}>
                {profile.systems.map((s) => <Picker.Item key={s.id} label={s.label} value={s.id} />)}
              </Picker>
            </View>

            <Text style={styles.label}>Your grade</Text>
            {system?.input_type === 'select' ? (
              <View style={styles.pickerWrap}>
                <Picker selectedValue={value} onValueChange={(v) => setValue(v as string)}>
                  <Picker.Item label="Select…" value="" />
                  {(system.options || []).map((o) => <Picker.Item key={o} label={o} value={o} />)}
                </Picker>
              </View>
            ) : (
              <>
                <TextInput style={styles.input} value={value} onChangeText={setValue} keyboardType="decimal-pad" />
                {system && <Text style={styles.hint}>Scale: {system.min}–{system.max}</Text>}
              </>
            )}

            <Pressable style={styles.primaryBtn} onPress={convert} disabled={busy}>
              {busy ? <ActivityIndicator color="#fff" /> : <Text style={styles.primaryBtnText}>Convert</Text>}
            </Pressable>
          </>
        )}
      </View>

      {error && <Text style={styles.errorText}>{error}</Text>}

      {result && (
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Your unified profile</Text>
          <Text style={styles.bigGpa}>{result.gpa.toFixed(2)}</Text>
          <Text style={styles.gpaLabel}>Unified GPA out of 4.0</Text>
          <View style={styles.resultRow}>
            <Text style={styles.resultLabel}>US-equivalent percentage</Text>
            <Text style={styles.resultValue}>{result.percent}%</Text>
          </View>
          <View style={styles.resultRow}>
            <Text style={styles.resultLabel}>ECTS grade</Text>
            <Text style={styles.resultValue}>{result.ects}</Text>
          </View>
          <View style={styles.noteBox}><Text style={styles.noteText}>{result.percentile_note}</Text></View>
          <Pressable style={styles.primaryBtn} onPress={save} disabled={busy}>
            <Text style={styles.primaryBtnText}>Save to my profile</Text>
          </Pressable>
          <Text style={styles.disclaimer}>These figures are estimates for planning purposes and don't replace an official credential evaluation.</Text>
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  backRow: { flexDirection: 'row', alignItems: 'center', gap: 4, marginBottom: 12 },
  backText: { fontFamily: fonts.bold, fontSize: 13, color: colors.inkSoft },
  eyebrow: { fontFamily: fonts.regular, fontSize: 13, color: colors.inkSoft },
  heading: { fontFamily: fonts.extraBold, fontSize: 27, color: colors.ink, marginBottom: 18 },
  card: { backgroundColor: colors.card, borderRadius: 16, borderWidth: 1, borderColor: colors.line, padding: 20, marginBottom: 14 },
  cardTitle: { fontFamily: fonts.extraBold, fontSize: 15.5, color: colors.ink, marginBottom: 14 },
  label: { fontFamily: fonts.bold, fontSize: 12.5, color: colors.inkSoft, marginBottom: 6, marginTop: 10 },
  pickerWrap: { backgroundColor: colors.grayTint, borderRadius: 10, overflow: 'hidden' },
  input: { backgroundColor: colors.grayTint, borderRadius: 10, paddingHorizontal: 13, paddingVertical: 12, fontFamily: fonts.regular, fontSize: 14, color: colors.ink },
  hint: { fontFamily: fonts.regular, fontSize: 11.5, color: colors.inkSoft, marginTop: 5 },
  primaryBtn: { backgroundColor: colors.blue, borderRadius: 12, paddingVertical: 13, alignItems: 'center', marginTop: 16 },
  primaryBtnText: { fontFamily: fonts.bold, fontSize: 14, color: '#fff' },
  errorText: { fontFamily: fonts.regular, fontSize: 12.5, color: colors.red, marginBottom: 10 },
  bigGpa: { fontFamily: fonts.extraBold, fontSize: 36, color: colors.blue },
  gpaLabel: { fontFamily: fonts.regular, fontSize: 12.5, color: colors.inkSoft, marginBottom: 10 },
  resultRow: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 8 },
  resultLabel: { fontFamily: fonts.regular, fontSize: 13, color: colors.ink },
  resultValue: { fontFamily: fonts.bold, fontSize: 13, color: colors.ink },
  noteBox: { borderWidth: 1, borderColor: colors.line, borderRadius: 10, padding: 12, marginTop: 6, marginBottom: 4 },
  noteText: { fontFamily: fonts.regular, fontSize: 12.5, color: colors.inkSoft },
  disclaimer: { fontFamily: fonts.regular, fontSize: 11, color: colors.inkFaint, marginTop: 10 },
});
