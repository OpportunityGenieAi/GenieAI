import React, { useEffect } from 'react';
import { FlatList, StyleSheet, Text, View } from 'react-native';
import { colors, fonts } from '../../theme/colors';
import { useAuth } from '../../context/AuthContext';
import { useProfile } from '../../context/ProfileContext';
import { useScholarships } from '../../context/ScholarshipContext';
import { useTracker } from '../../context/TrackerContext';
import { ScholarshipCard } from '../../components/ScholarshipCard';
import { FeatureGate } from '../../components/FeatureGate';

export default function MatchScreen() {
  const { user } = useAuth();
  const profile = useProfile();
  const scholarships = useScholarships();
  const tracker = useTracker();

  useEffect(() => {
    if (user) scholarships.fetch(true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user]);

  if (!user) {
    return (
      <View style={{ flex: 1, backgroundColor: colors.bg }}>
        <FeatureGate
          title="Unlock Match scores"
          body="See a live match percentage on every scholarship, based on your real GPA and profile."
        />
      </View>
    );
  }

  if (!profile.isComplete) {
    return (
      <View style={styles.container}>
        <Text style={styles.heading}>Best Matches</Text>
        <View style={styles.emptyBox}>
          <Text style={styles.emptyText}>
            Complete your profile (GPA + academic details) on the Profile tab to see match scores here.
          </Text>
        </View>
      </View>
    );
  }

  return (
    <FlatList
      style={{ backgroundColor: colors.bg }}
      contentContainerStyle={{ padding: 20, paddingBottom: 100 }}
      data={scholarships.sortedByMatch()}
      keyExtractor={(item) => item.id}
      ListHeaderComponent={
        <View>
          <Text style={styles.heading}>Best Matches</Text>
          <Text style={styles.sub}>Ranked by fit to your saved profile</Text>
        </View>
      }
      renderItem={({ item }) => (
        <ScholarshipCard
          scholarship={item}
          showMatch
          isBookmarked={tracker.isTracked(item.id)}
          onToggleBookmark={() => tracker.toggle(item.id)}
        />
      )}
    />
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg, padding: 20 },
  heading: { fontFamily: fonts.extraBold, fontSize: 27, color: colors.ink, marginBottom: 4 },
  sub: { fontFamily: fonts.regular, fontSize: 13, color: colors.inkSoft, marginBottom: 16 },
  emptyBox: { borderWidth: 1, borderColor: colors.line, borderRadius: 12, padding: 16, marginTop: 6 },
  emptyText: { fontFamily: fonts.regular, fontSize: 13.5, color: colors.inkSoft },
});
