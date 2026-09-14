import React, { useState } from 'react';
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { colors, fonts } from '../../theme/colors';
import { useAuth } from '../../context/AuthContext';
import { useProfile } from '../../context/ProfileContext';
import { AdvisorApi } from '../../api/tracker';
import { FeatureGate } from '../../components/FeatureGate';

export default function AdvisorScreen() {
  const { user } = useAuth();
  const profile = useProfile();
  const [loading, setLoading] = useState(false);
  const [text, setText] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  if (!user) {
    return (
      <View style={{ flex: 1, backgroundColor: colors.bg }}>
        <FeatureGate title="Unlock the AI Advisor" body="Get a personalized, honest read on your competitiveness and concrete next steps." />
      </View>
    );
  }

  const ask = async () => {
    setLoading(true); setError(null); setText(null);
    try {
      const result = await AdvisorApi.recommend();
      setText(result);
    } catch {
      setError("Couldn't reach the AI advisor just now — try again in a moment.");
    }
    setLoading(false);
  };

  return (
    <ScrollView style={{ backgroundColor: colors.bg }} contentContainerStyle={{ padding: 20, paddingBottom: 100 }}>
      <Text style={styles.eyebrow}>Ask anything</Text>
      <Text style={styles.heading}>AI Advisor</Text>

      <View style={styles.card}>
        <Text style={styles.cardTitle}>Personalized recommendations</Text>
        <Text style={styles.cardSub}>A short, honest read on your competitiveness and what would move the needle most.</Text>

        {!profile.isComplete ? (
          <View style={styles.emptyBox}>
            <Text style={styles.emptyText}>Complete your profile first — the advisor needs your GPA and academic details.</Text>
          </View>
        ) : (
          <>
            <Pressable style={styles.primaryBtn} onPress={ask} disabled={loading}>
              {loading ? <ActivityIndicator color="#fff" /> : <Text style={styles.primaryBtnText}>Get my recommendations</Text>}
            </Pressable>
            {error && <Text style={styles.errorText}>{error}</Text>}
            {text && (
              <View style={styles.aiPanel}>
                <Text style={styles.aiText}>{text}</Text>
              </View>
            )}
          </>
        )}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  eyebrow: { fontFamily: fonts.regular, fontSize: 13, color: colors.inkSoft },
  heading: { fontFamily: fonts.extraBold, fontSize: 27, color: colors.ink, marginBottom: 18 },
  card: { backgroundColor: colors.card, borderRadius: 16, borderWidth: 1, borderColor: colors.line, padding: 20 },
  cardTitle: { fontFamily: fonts.extraBold, fontSize: 15.5, color: colors.ink, marginBottom: 3 },
  cardSub: { fontFamily: fonts.regular, fontSize: 12.5, color: colors.inkSoft, marginBottom: 14 },
  emptyBox: { borderWidth: 1, borderColor: colors.line, borderRadius: 10, padding: 14 },
  emptyText: { fontFamily: fonts.regular, fontSize: 13, color: colors.inkSoft },
  primaryBtn: { backgroundColor: colors.blue, borderRadius: 12, paddingVertical: 13, alignItems: 'center' },
  primaryBtnText: { fontFamily: fonts.bold, fontSize: 14, color: '#fff' },
  errorText: { fontFamily: fonts.regular, fontSize: 12.5, color: colors.red, marginTop: 10 },
  aiPanel: { backgroundColor: colors.blueTint, borderRadius: 12, padding: 16, marginTop: 14 },
  aiText: { fontFamily: fonts.regular, fontSize: 13.5, color: colors.blueDark, lineHeight: 20 },
});
