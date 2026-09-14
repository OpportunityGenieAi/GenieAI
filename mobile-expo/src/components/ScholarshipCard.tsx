import React from 'react';
import { Linking, Pressable, StyleSheet, Text, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, fonts } from '../theme/colors';
import { Scholarship } from '../api/scholarships';

function matchColor(tier?: string | null): string {
  if (tier === 'green') return colors.green;
  if (tier === 'yellow') return colors.amber;
  if (tier === 'red') return colors.red;
  return colors.blue;
}

export function ScholarshipCard({
  scholarship, isBookmarked, showMatch, onToggleBookmark,
}: {
  scholarship: Scholarship;
  isBookmarked?: boolean;
  showMatch?: boolean;
  onToggleBookmark?: () => void;
}) {
  return (
    <View style={styles.card}>
      <View style={styles.topRow}>
        <View style={{ flex: 1 }}>
          <Text style={styles.title}>{scholarship.name}</Text>
          <Text style={styles.provider}>{scholarship.provider}</Text>
        </View>
        <View style={{ alignItems: 'flex-end', gap: 8 }}>
          {showMatch && scholarship.match_score != null && (
            <Text style={[styles.matchPct, { color: matchColor(scholarship.match_tier) }]}>
              {scholarship.match_score}%
            </Text>
          )}
          <Pressable
            onPress={onToggleBookmark}
            style={[styles.bookmarkBtn, isBookmarked && { backgroundColor: colors.blue, borderColor: colors.blue }]}
          >
            <Ionicons name={isBookmarked ? 'bookmark' : 'bookmark-outline'} size={15} color={isBookmarked ? '#fff' : colors.inkSoft} />
          </Pressable>
        </View>
      </View>

      <Text style={styles.blurb}>{scholarship.blurb}</Text>

      <View style={styles.metaRow}>
        <View style={styles.metaItem}>
          <Ionicons name="location-outline" size={13} color={colors.inkSoft} />
          <Text style={styles.metaText}>{scholarship.country}</Text>
        </View>
        <View style={styles.metaItem}>
          <Ionicons name="cash-outline" size={13} color={colors.inkSoft} />
          <Text style={styles.metaText}>{scholarship.funding}</Text>
        </View>
        <View style={styles.metaItem}>
          <Ionicons name="time-outline" size={13} color={colors.inkSoft} />
          <Text style={styles.metaText}>{scholarship.deadline_window}</Text>
        </View>
      </View>

      {scholarship.tags?.length > 0 && (
        <View style={styles.tagRow}>
          {scholarship.tags.map((t) => (
            <View key={t} style={styles.tag}>
              <Text style={styles.tagText}>{t}</Text>
            </View>
          ))}
        </View>
      )}

      <Pressable style={styles.applyBtn} onPress={() => Linking.openURL(scholarship.official_link)}>
        <Text style={styles.applyBtnText}>Apply on official site</Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.card, borderRadius: 16, borderWidth: 1, borderColor: colors.line,
    padding: 18, marginBottom: 14,
  },
  topRow: { flexDirection: 'row', alignItems: 'flex-start', gap: 10 },
  title: { fontFamily: fonts.extraBold, fontSize: 16.5, color: colors.ink, marginBottom: 2 },
  provider: { fontFamily: fonts.regular, fontSize: 12.5, color: colors.inkSoft },
  matchPct: { fontFamily: fonts.extraBold, fontSize: 17 },
  bookmarkBtn: {
    width: 30, height: 30, borderRadius: 15, borderWidth: 1, borderColor: colors.line,
    backgroundColor: '#fff', alignItems: 'center', justifyContent: 'center',
  },
  blurb: { fontFamily: fonts.regular, fontSize: 13.5, color: colors.inkSoft, marginTop: 8, marginBottom: 12, lineHeight: 20 },
  metaRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 14, marginBottom: 12 },
  metaItem: { flexDirection: 'row', alignItems: 'center', gap: 5 },
  metaText: { fontFamily: fonts.regular, fontSize: 12.5, color: colors.inkSoft },
  tagRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 7, marginBottom: 12 },
  tag: { backgroundColor: colors.blueTint, borderRadius: 20, paddingHorizontal: 11, paddingVertical: 4 },
  tagText: { fontFamily: fonts.bold, fontSize: 11.5, color: colors.blue },
  applyBtn: { backgroundColor: colors.blue, borderRadius: 10, paddingVertical: 11, alignItems: 'center' },
  applyBtnText: { fontFamily: fonts.bold, fontSize: 13.5, color: '#fff' },
});
