import React, { useEffect, useState } from 'react';
import { Linking, Pressable, ScrollView, StyleSheet, Switch, Text, TextInput, View } from 'react-native';
import { Picker } from '@react-native-picker/picker';
import { useNavigation } from '@react-navigation/native';
import { colors, fonts } from '../../theme/colors';
import { useAuth } from '../../context/AuthContext';
import { useProfile } from '../../context/ProfileContext';
import { useTracker } from '../../context/TrackerContext';
import { FeatureGate } from '../../components/FeatureGate';

const LEVELS = ['Undergraduate', "Master's", 'PhD', 'Postdoc'];
const LEADERSHIP = ['None', 'Some', 'Extensive'];
const VOLUNTEERING = ['None', 'Occasional', 'Regular'];

export default function ProfileScreen() {
  const navigation = useNavigation<any>();
  const { user, logout } = useAuth();
  const profile = useProfile();
  const tracker = useTracker();

  const [level, setLevel] = useState("Master's");
  const [field, setField] = useState('');
  const [nationality, setNationality] = useState('');
  const [ielts, setIelts] = useState('');
  const [workYears, setWorkYears] = useState('0');
  const [publications, setPublications] = useState('0');
  const [leadership, setLeadership] = useState('None');
  const [volunteering, setVolunteering] = useState('None');
  const [hasCv, setHasCv] = useState(false);
  const [hasSop, setHasSop] = useState(false);
  const [hasRecs, setHasRecs] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!user) return;
    (async () => {
      await profile.loadAll();
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user]);

  useEffect(() => {
    const ap = profile.academicProfile;
    if (ap) {
      setLevel(ap.level); setField(ap.field); setNationality(ap.nationality);
      setIelts(ap.ielts != null ? String(ap.ielts) : '');
      setWorkYears(String(ap.work_years)); setPublications(String(ap.publications));
      setLeadership(ap.leadership); setVolunteering(ap.volunteering);
      setHasCv(ap.has_cv); setHasSop(ap.has_sop); setHasRecs(ap.has_recommendation_letters);
    }
  }, [profile.academicProfile]);

  if (!user) {
    return (
      <View style={{ flex: 1, backgroundColor: colors.bg }}>
        <FeatureGate title="Create your profile" body="Save your GPA and academic details to power match scores and the AI advisor." />
      </View>
    );
  }

  const saveProfile = async () => {
    setSaving(true);
    try {
      await profile.saveAcademic({
        level, field: field.trim(), nationality: nationality.trim(),
        ielts: ielts ? parseFloat(ielts) : null,
        work_years: parseInt(workYears, 10) || 0,
        publications: parseInt(publications, 10) || 0,
        leadership, volunteering,
        has_cv: hasCv, has_sop: hasSop, has_recommendation_letters: hasRecs,
      });
    } catch {
      // silently ignore for now — could surface a toast
    }
    setSaving(false);
  };

  const doLogout = async () => {
    await logout();
    profile.reset();
    tracker.reset();
  };

  return (
    <ScrollView style={{ backgroundColor: colors.bg }} contentContainerStyle={{ padding: 20, paddingBottom: 100 }}>
      <Text style={styles.eyebrow}>Your account</Text>
      <Text style={styles.heading}>Profile</Text>

      <View style={styles.card}>
        <View style={styles.profileHead}>
          <View style={styles.bigAvatar}><Text style={styles.bigAvatarText}>{user.name.charAt(0).toUpperCase()}</Text></View>
          <View>
            <Text style={styles.userName}>{user.name}</Text>
            <Text style={styles.userEmail}>{user.email}</Text>
          </View>
        </View>
        <View style={{ flexDirection: 'row', gap: 10, marginTop: 14 }}>
          {user.is_admin && (
            <Pressable style={styles.outlineBtn} onPress={() => navigation.navigate('Admin')}>
              <Text style={styles.outlineBtnText}>Admin console</Text>
            </Pressable>
          )}
          <Pressable style={styles.ghostBtn} onPress={doLogout}>
            <Text style={styles.ghostBtnText}>Log out</Text>
          </Pressable>
        </View>
      </View>

      <View style={styles.card}>
        <Text style={styles.cardTitle}>Academic standing</Text>
        <Text style={styles.cardSub}>From the GPA Converter.</Text>
        {profile.gpaProfile ? (
          <>
            <View style={{ flexDirection: 'row', alignItems: 'center', gap: 12, marginTop: 4 }}>
              <Text style={styles.bigGpa}>{profile.gpaProfile.gpa.toFixed(2)}</Text>
              <Text style={styles.gpaMeta}>
                Unified GPA · {profile.gpaProfile.percent.toFixed(0)}% US-equivalent · ECTS {profile.gpaProfile.ects}
              </Text>
            </View>
            <Pressable style={[styles.outlineBtn, { marginTop: 12, alignSelf: 'flex-start' }]} onPress={() => navigation.navigate('GpaConverter')}>
              <Text style={styles.outlineBtnText}>Update my grade</Text>
            </Pressable>
          </>
        ) : (
          <>
            <View style={styles.emptyBox}><Text style={styles.emptyText}>You haven't converted a grade yet.</Text></View>
            <Pressable style={[styles.primaryBtn, { marginTop: 12 }]} onPress={() => navigation.navigate('GpaConverter')}>
              <Text style={styles.primaryBtnText}>Open GPA Converter</Text>
            </Pressable>
          </>
        )}
      </View>

      <View style={styles.card}>
        <Text style={styles.cardTitle}>Your details</Text>
        <Text style={styles.cardSub}>Used to score how well each scholarship fits you.</Text>

        <Text style={styles.label}>Degree level seeking</Text>
        <View style={styles.pickerWrap}>
          <Picker selectedValue={level} onValueChange={(v) => setLevel(v as string)}>
            {LEVELS.map((l) => <Picker.Item key={l} label={l} value={l} />)}
          </Picker>
        </View>

        <Text style={styles.label}>Field of study</Text>
        <TextInput style={styles.input} value={field} onChangeText={setField} placeholder="e.g. Public health" />

        <Text style={styles.label}>Nationality</Text>
        <TextInput style={styles.input} value={nationality} onChangeText={setNationality} placeholder="e.g. Kenya" />

        <View style={{ flexDirection: 'row', gap: 10 }}>
          <View style={{ flex: 1 }}>
            <Text style={styles.label}>IELTS score</Text>
            <TextInput style={styles.input} value={ielts} onChangeText={setIelts} keyboardType="decimal-pad" placeholder="e.g. 7.0" />
          </View>
          <View style={{ flex: 1 }}>
            <Text style={styles.label}>Work years</Text>
            <TextInput style={styles.input} value={workYears} onChangeText={setWorkYears} keyboardType="number-pad" />
          </View>
        </View>

        <Text style={styles.label}>Publications</Text>
        <TextInput style={styles.input} value={publications} onChangeText={setPublications} keyboardType="number-pad" />

        <View style={{ flexDirection: 'row', gap: 10 }}>
          <View style={{ flex: 1 }}>
            <Text style={styles.label}>Leadership</Text>
            <View style={styles.pickerWrap}>
              <Picker selectedValue={leadership} onValueChange={(v) => setLeadership(v as string)}>
                {LEADERSHIP.map((l) => <Picker.Item key={l} label={l} value={l} />)}
              </Picker>
            </View>
          </View>
          <View style={{ flex: 1 }}>
            <Text style={styles.label}>Volunteering</Text>
            <View style={styles.pickerWrap}>
              <Picker selectedValue={volunteering} onValueChange={(v) => setVolunteering(v as string)}>
                {VOLUNTEERING.map((l) => <Picker.Item key={l} label={l} value={l} />)}
              </Picker>
            </View>
          </View>
        </View>

        <View style={styles.switchRow}>
          <Switch value={hasCv} onValueChange={setHasCv} />
          <Text style={styles.switchLabel}>I have a CV/resume ready</Text>
        </View>
        <View style={styles.switchRow}>
          <Switch value={hasSop} onValueChange={setHasSop} />
          <Text style={styles.switchLabel}>I have a Statement of Purpose ready</Text>
        </View>
        <View style={styles.switchRow}>
          <Switch value={hasRecs} onValueChange={setHasRecs} />
          <Text style={styles.switchLabel}>I have reference/recommendation letters ready</Text>
        </View>

        <Pressable style={[styles.primaryBtn, { marginTop: 12 }]} onPress={saveProfile} disabled={saving}>
          <Text style={styles.primaryBtnText}>{saving ? 'Saving…' : 'Save profile'}</Text>
        </Pressable>
      </View>

      <View style={styles.card}>
        <Text style={styles.cardTitle}>Scholarship Readiness Score</Text>
        <Text style={styles.cardSub}>Like a credit score for your scholarship applications.</Text>
        {!profile.readiness ? (
          <View style={styles.emptyBox}><Text style={styles.emptyText}>Save your GPA and details above to see your readiness score.</Text></View>
        ) : (
          <>
            <View style={{ flexDirection: 'row', alignItems: 'baseline', gap: 8, marginBottom: 8 }}>
              <Text style={styles.readinessOverall}>{profile.readiness.overall}</Text>
              <Text style={styles.readinessOutOf}>/ 100</Text>
            </View>
            {profile.readiness.categories.map((c) => (
              <View key={c.label} style={styles.readinessRow}>
                <Text style={styles.readinessLabel}>{c.label}</Text>
                <Text style={styles.readinessStars}>{'★'.repeat(c.stars)}{'☆'.repeat(5 - c.stars)}</Text>
              </View>
            ))}
          </>
        )}
      </View>

      <View style={styles.card}>
        <Text style={styles.cardTitle}>Legal</Text>
        <Pressable
          style={styles.linkRow}
          onPress={() => Linking.openURL('https://opportunitygenie.org/static/privacy-policy.html')}
        >
          <Text style={styles.linkRowText}>Privacy Policy</Text>
        </Pressable>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  eyebrow: { fontFamily: fonts.regular, fontSize: 13, color: colors.inkSoft },
  heading: { fontFamily: fonts.extraBold, fontSize: 27, color: colors.ink, marginBottom: 18 },
  card: { backgroundColor: colors.card, borderRadius: 16, borderWidth: 1, borderColor: colors.line, padding: 20, marginBottom: 14 },
  profileHead: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  bigAvatar: { width: 52, height: 52, borderRadius: 26, backgroundColor: colors.blue, alignItems: 'center', justifyContent: 'center' },
  bigAvatarText: { fontFamily: fonts.extraBold, fontSize: 19, color: '#fff' },
  userName: { fontFamily: fonts.extraBold, fontSize: 16, color: colors.ink },
  userEmail: { fontFamily: fonts.regular, fontSize: 12.5, color: colors.inkSoft },
  outlineBtn: { borderWidth: 1, borderColor: colors.line, borderRadius: 10, paddingVertical: 9, paddingHorizontal: 14 },
  outlineBtnText: { fontFamily: fonts.bold, fontSize: 13, color: colors.ink },
  ghostBtn: { backgroundColor: colors.grayTint, borderRadius: 10, paddingVertical: 9, paddingHorizontal: 14 },
  ghostBtnText: { fontFamily: fonts.bold, fontSize: 13, color: colors.ink },
  cardTitle: { fontFamily: fonts.extraBold, fontSize: 15.5, color: colors.ink, marginBottom: 3 },
  cardSub: { fontFamily: fonts.regular, fontSize: 12.5, color: colors.inkSoft, marginBottom: 12 },
  bigGpa: { fontFamily: fonts.extraBold, fontSize: 28, color: colors.blue },
  gpaMeta: { fontFamily: fonts.regular, fontSize: 12.5, color: colors.inkSoft, flex: 1 },
  emptyBox: { borderWidth: 1, borderColor: colors.line, borderRadius: 10, padding: 14 },
  emptyText: { fontFamily: fonts.regular, fontSize: 13, color: colors.inkSoft },
  primaryBtn: { backgroundColor: colors.blue, borderRadius: 12, paddingVertical: 13, alignItems: 'center' },
  primaryBtnText: { fontFamily: fonts.bold, fontSize: 14, color: '#fff' },
  label: { fontFamily: fonts.bold, fontSize: 12.5, color: colors.inkSoft, marginBottom: 6, marginTop: 10 },
  input: { backgroundColor: colors.grayTint, borderRadius: 10, paddingHorizontal: 13, paddingVertical: 12, fontFamily: fonts.regular, fontSize: 14, color: colors.ink },
  pickerWrap: { backgroundColor: colors.grayTint, borderRadius: 10, overflow: 'hidden' },
  switchRow: { flexDirection: 'row', alignItems: 'center', gap: 10, marginTop: 12 },
  switchLabel: { fontFamily: fonts.regular, fontSize: 13.5, color: colors.ink, flex: 1 },
  readinessOverall: { fontFamily: fonts.extraBold, fontSize: 34, color: colors.blue },
  readinessOutOf: { fontFamily: fonts.regular, fontSize: 12.5, color: colors.inkSoft },
  readinessRow: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 7 },
  readinessLabel: { fontFamily: fonts.regular, fontSize: 13, color: colors.ink },
  readinessStars: { color: colors.blue, letterSpacing: 1 },
  linkRow: { paddingVertical: 10 },
  linkRowText: { fontFamily: fonts.bold, fontSize: 14, color: colors.blue },
});