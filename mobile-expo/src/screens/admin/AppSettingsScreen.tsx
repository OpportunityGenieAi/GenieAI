import React, { useEffect, useState } from 'react';
import { ActivityIndicator, Alert, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { Ionicons } from '@expo/vector-icons';
import { colors, fonts } from '../../theme/colors';
import { SettingsApi } from '../../api/settings';

const FIELDS: { key: string; label: string; hint?: string; secret?: boolean }[] = [
  { key: 'admob_banner_unit_id_android', label: 'AdMob banner unit ID — Android', hint: 'From your AdMob account, Ad units section' },
  { key: 'admob_banner_unit_id_ios', label: 'AdMob banner unit ID — iOS' },
  { key: 'admob_interstitial_unit_id_android', label: 'AdMob interstitial unit ID — Android' },
  { key: 'admob_interstitial_unit_id_ios', label: 'AdMob interstitial unit ID — iOS' },
  { key: 'anthropic_api_key_override', label: 'Anthropic API key (override)', hint: 'Leave blank to keep using the server env var', secret: true },
  { key: 'stripe_secret_key_override', label: 'Stripe secret key (override)', hint: 'Leave blank to keep using the server env var', secret: true },
];

export default function AppSettingsScreen() {
  const navigation = useNavigation<any>();
  const [values, setValues] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [savingKey, setSavingKey] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const rows = await SettingsApi.listAll();
        const map: Record<string, string> = {};
        rows.forEach((r) => { map[r.key] = r.value || ''; });
        setValues(map);
      } catch {
        Alert.alert('Could not load settings', 'Try again in a moment.');
      }
      setLoading(false);
    })();
  }, []);

  const save = async (key: string) => {
    setSavingKey(key);
    try {
      await SettingsApi.set(key, values[key] || '');
      Alert.alert('Saved', 'This takes effect immediately for ad unit IDs — for API key overrides, on the next request.');
    } catch {
      Alert.alert('Could not save', 'Try again.');
    }
    setSavingKey(null);
  };

  return (
    <ScrollView style={{ backgroundColor: colors.bg }} contentContainerStyle={{ padding: 20, paddingBottom: 60 }}>
      <Pressable style={styles.backRow} onPress={() => navigation.goBack()}>
        <Ionicons name="chevron-back" size={16} color={colors.inkSoft} />
        <Text style={styles.backText}>Back</Text>
      </Pressable>
      <Text style={styles.heading}>App Settings</Text>
      <Text style={styles.sub}>
        Ad unit IDs update instantly for everyone. API key overrides here take priority over the server's
        own environment variables — leave blank to keep using those.
      </Text>

      {loading ? (
        <ActivityIndicator color={colors.blue} style={{ marginTop: 30 }} />
      ) : (
        FIELDS.map((f) => (
          <View key={f.key} style={styles.card}>
            <Text style={styles.label}>{f.label}</Text>
            {f.hint && <Text style={styles.hint}>{f.hint}</Text>}
            <TextInput
              style={styles.input}
              value={values[f.key] || ''}
              onChangeText={(v) => setValues((prev) => ({ ...prev, [f.key]: v }))}
              secureTextEntry={f.secret}
              autoCapitalize="none"
              placeholder="Not set — using default"
            />
            <Pressable style={styles.saveBtn} onPress={() => save(f.key)} disabled={savingKey === f.key}>
              <Text style={styles.saveBtnText}>{savingKey === f.key ? 'Saving…' : 'Save'}</Text>
            </Pressable>
          </View>
        ))
      )}

      <Text style={styles.footnote}>
        Note: the AdMob App ID itself (as opposed to individual ad unit IDs) is baked into the native
        app build and can't be changed here — updating that needs a new build via EAS.
      </Text>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  backRow: { flexDirection: 'row', alignItems: 'center', gap: 4, marginBottom: 12 },
  backText: { fontFamily: fonts.bold, fontSize: 13, color: colors.inkSoft },
  heading: { fontFamily: fonts.extraBold, fontSize: 24, color: colors.ink, marginBottom: 6 },
  sub: { fontFamily: fonts.regular, fontSize: 13, color: colors.inkSoft, marginBottom: 18, lineHeight: 19 },
  card: { backgroundColor: colors.card, borderRadius: 14, borderWidth: 1, borderColor: colors.line, padding: 16, marginBottom: 12 },
  label: { fontFamily: fonts.bold, fontSize: 13, color: colors.ink, marginBottom: 3 },
  hint: { fontFamily: fonts.regular, fontSize: 11.5, color: colors.inkSoft, marginBottom: 8 },
  input: { backgroundColor: colors.grayTint, borderRadius: 10, paddingHorizontal: 13, paddingVertical: 11, fontFamily: fonts.regular, fontSize: 13.5, color: colors.ink, marginTop: 6 },
  saveBtn: { backgroundColor: colors.blue, borderRadius: 10, paddingVertical: 9, alignItems: 'center', marginTop: 10 },
  saveBtnText: { fontFamily: fonts.bold, fontSize: 13, color: '#fff' },
  footnote: { fontFamily: fonts.regular, fontSize: 11.5, color: colors.inkFaint, marginTop: 8, lineHeight: 17 },
});
