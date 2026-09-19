import React, { useEffect, useState } from 'react';
import { Alert, Pressable, ScrollView, StyleSheet, Text, TextInput, View, ActivityIndicator } from 'react-native';
import { Picker } from '@react-native-picker/picker';
import { useNavigation, useRoute } from '@react-navigation/native';
import { Ionicons } from '@expo/vector-icons';
import { colors, fonts } from '../../theme/colors';
import { Scholarship, ScholarshipsApi } from '../../api/scholarships';

export function AdminScreen() {
  const navigation = useNavigation<any>();
  const [items, setItems] = useState<Scholarship[]>([]);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    setItems(await ScholarshipsApi.list({ auth: true }));
    setLoading(false);
  };

  useEffect(() => {
    load();
    const unsub = navigation.addListener('focus', load);
    return unsub;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const confirmDelete = (s: Scholarship) => {
    Alert.alert('Remove this listing?', `This removes "${s.name}" for every visitor.`, [
      { text: 'Cancel', style: 'cancel' },
      { text: 'Delete', style: 'destructive', onPress: async () => { await ScholarshipsApi.remove(s.id); load(); } },
    ]);
  };

  return (
    <ScrollView style={{ backgroundColor: colors.bg }} contentContainerStyle={{ padding: 20, paddingBottom: 60 }}>
      <Pressable style={styles.backRow} onPress={() => navigation.goBack()}>
        <Ionicons name="chevron-back" size={16} color={colors.inkSoft} />
        <Text style={styles.backText}>Back</Text>
      </Pressable>
      <Text style={styles.heading}>Admin</Text>
      <Text style={styles.sub}>Changes appear for every visitor immediately.</Text>

      <Pressable style={styles.primaryBtn} onPress={() => navigation.navigate('ScholarshipForm', {})}>
        <Text style={styles.primaryBtnText}>+ Add scholarship</Text>
      </Pressable>
      <Pressable style={styles.outlineBtnFull} onPress={() => navigation.navigate('AppSettings')}>
        <Text style={styles.outlineBtnFullText}>App Settings (AdMob, API keys)</Text>
      </Pressable>

      {loading ? <ActivityIndicator color={colors.blue} style={{ marginVertical: 20 }} /> : items.map((s) => (
        <View key={s.id} style={styles.row}>
          <View style={{ flex: 1 }}>
            <Text style={styles.rowTitle}>{s.name}</Text>
            <Text style={styles.rowSub}>{s.country} · {s.level} · {s.funding}</Text>
          </View>
          <Pressable onPress={() => navigation.navigate('ScholarshipForm', { scholarship: s })} style={styles.iconBtn}>
            <Ionicons name="create-outline" size={19} color={colors.ink} />
          </Pressable>
          <Pressable onPress={() => confirmDelete(s)} style={styles.iconBtn}>
            <Ionicons name="trash-outline" size={19} color={colors.red} />
          </Pressable>
        </View>
      ))}

      <Text style={styles.footnote}>
        For production, keep this data on the real backend (already the case here) behind role-based admin accounts and audit logging.
      </Text>
    </ScrollView>
  );
}

export function ScholarshipFormScreen() {
  const navigation = useNavigation<any>();
  const route = useRoute<any>();
  const existing: Scholarship | undefined = route.params?.scholarship;

  const [name, setName] = useState(existing?.name || '');
  const [provider, setProvider] = useState(existing?.provider || '');
  const [country, setCountry] = useState(existing?.country || '');
  const [level, setLevel] = useState(existing?.level || '');
  const [field, setField] = useState(existing?.field || 'All fields');
  const [funding, setFunding] = useState(existing?.funding || 'Fully-funded');
  const [deadline, setDeadline] = useState(existing?.deadline_window || '');
  const [link, setLink] = useState(existing?.official_link || '');
  const [tags, setTags] = useState((existing?.tags || []).join(', '));
  const [blurb, setBlurb] = useState(existing?.blurb || '');
  const [saving, setSaving] = useState(false);

  const save = async () => {
    if (!name.trim() || !provider.trim() || !country.trim() || !level.trim() || !deadline.trim() || !link.trim() || !blurb.trim()) {
      Alert.alert('Missing fields', 'Please fill in every required field.');
      return;
    }
    setSaving(true);
    const payload = {
      name: name.trim(), provider: provider.trim(), country: country.trim(), level: level.trim(),
      field: field.trim() || 'All fields', funding, deadline_window: deadline.trim(), official_link: link.trim(),
      tags: tags.split(',').map((t) => t.trim()).filter(Boolean), blurb: blurb.trim(),
    };
    try {
      if (existing) await ScholarshipsApi.update(existing.id, payload);
      else await ScholarshipsApi.create(payload);
      navigation.goBack();
    } catch {
      Alert.alert('Could not save', 'Check the fields and try again.');
    }
    setSaving(false);
  };

  return (
    <ScrollView style={{ backgroundColor: colors.bg }} contentContainerStyle={{ padding: 20, paddingBottom: 60 }}>
      <Pressable style={styles.backRow} onPress={() => navigation.goBack()}>
        <Ionicons name="chevron-back" size={16} color={colors.inkSoft} />
        <Text style={styles.backText}>Back</Text>
      </Pressable>
      <Text style={styles.heading}>{existing ? 'Edit scholarship' : 'Add scholarship'}</Text>

      <Text style={styles.label}>Scholarship name</Text>
      <TextInput style={styles.input} value={name} onChangeText={setName} />
      <Text style={styles.label}>Provider / organization</Text>
      <TextInput style={styles.input} value={provider} onChangeText={setProvider} />
      <Text style={styles.label}>Country / region</Text>
      <TextInput style={styles.input} value={country} onChangeText={setCountry} />
      <Text style={styles.label}>Degree level</Text>
      <TextInput style={styles.input} value={level} onChangeText={setLevel} />
      <Text style={styles.label}>Field of study</Text>
      <TextInput style={styles.input} value={field} onChangeText={setField} />
      <Text style={styles.label}>Funding type</Text>
      <View style={styles.pickerWrap}>
        <Picker selectedValue={funding} onValueChange={(v) => setFunding(v as string)}>
          {['Fully-funded', 'Partial', 'Partial grant'].map((f) => <Picker.Item key={f} label={f} value={f} />)}
        </Picker>
      </View>
      <Text style={styles.label}>Deadline window</Text>
      <TextInput style={styles.input} value={deadline} onChangeText={setDeadline} />
      <Text style={styles.label}>Official application link</Text>
      <TextInput style={styles.input} value={link} onChangeText={setLink} autoCapitalize="none" keyboardType="url" />
      <Text style={styles.label}>Tags (comma separated)</Text>
      <TextInput style={styles.input} value={tags} onChangeText={setTags} />
      <Text style={styles.label}>Short description</Text>
      <TextInput style={[styles.input, { height: 80 }]} value={blurb} onChangeText={setBlurb} multiline />

      <Pressable style={[styles.primaryBtn, { marginTop: 20 }]} onPress={save} disabled={saving}>
        <Text style={styles.primaryBtnText}>{saving ? 'Saving…' : (existing ? 'Save changes' : 'Add scholarship')}</Text>
      </Pressable>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  backRow: { flexDirection: 'row', alignItems: 'center', gap: 4, marginBottom: 12 },
  backText: { fontFamily: fonts.bold, fontSize: 13, color: colors.inkSoft },
  heading: { fontFamily: fonts.extraBold, fontSize: 27, color: colors.ink, marginBottom: 4 },
  sub: { fontFamily: fonts.regular, fontSize: 13, color: colors.inkSoft, marginBottom: 16 },
  primaryBtn: { backgroundColor: colors.blue, borderRadius: 12, paddingVertical: 13, alignItems: 'center', marginBottom: 16 },
  primaryBtnText: { fontFamily: fonts.bold, fontSize: 14, color: '#fff' },
  outlineBtnFull: { borderWidth: 1, borderColor: colors.line, borderRadius: 12, paddingVertical: 12, alignItems: 'center', marginBottom: 16 },
  outlineBtnFullText: { fontFamily: fonts.bold, fontSize: 13.5, color: colors.ink },
  row: {
    flexDirection: 'row', alignItems: 'center', backgroundColor: colors.card, borderWidth: 1, borderColor: colors.line,
    borderRadius: 12, padding: 14, marginBottom: 10, gap: 6,
  },
  rowTitle: { fontFamily: fonts.extraBold, fontSize: 14, color: colors.ink },
  rowSub: { fontFamily: fonts.regular, fontSize: 12, color: colors.inkSoft, marginTop: 2 },
  iconBtn: { padding: 6 },
  footnote: { fontFamily: fonts.regular, fontSize: 11.5, color: colors.inkFaint, marginTop: 10 },
  label: { fontFamily: fonts.bold, fontSize: 12.5, color: colors.inkSoft, marginBottom: 6, marginTop: 12 },
  input: { backgroundColor: colors.grayTint, borderRadius: 10, paddingHorizontal: 13, paddingVertical: 12, fontFamily: fonts.regular, fontSize: 14, color: colors.ink },
  pickerWrap: { backgroundColor: colors.grayTint, borderRadius: 10, overflow: 'hidden' },
});
