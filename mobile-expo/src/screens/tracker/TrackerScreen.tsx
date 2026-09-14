import React, { useEffect } from 'react';
import { FlatList, StyleSheet, Text, View } from 'react-native';
import { Picker } from '@react-native-picker/picker';
import { colors, fonts } from '../../theme/colors';
import { useAuth } from '../../context/AuthContext';
import { useTracker } from '../../context/TrackerContext';
import { FeatureGate } from '../../components/FeatureGate';

const STATUSES = ['saved', 'applied', 'interview', 'accepted', 'rejected'];

function statusColor(status: string) {
  switch (status) {
    case 'applied': return colors.blue;
    case 'interview': return colors.amber;
    case 'accepted': return colors.green;
    case 'rejected': return colors.red;
    default: return colors.inkSoft;
  }
}

export default function TrackerScreen() {
  const { user } = useAuth();
  const tracker = useTracker();

  useEffect(() => {
    if (user) tracker.fetch();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user]);

  if (!user) {
    return (
      <View style={{ flex: 1, backgroundColor: colors.bg }}>
        <FeatureGate title="Unlock the Tracker" body="Save scholarships and follow your application status from saved to accepted." />
      </View>
    );
  }

  return (
    <FlatList
      style={{ backgroundColor: colors.bg }}
      contentContainerStyle={{ padding: 20, paddingBottom: 100 }}
      data={tracker.entries}
      keyExtractor={(item) => item.scholarship_id}
      ListHeaderComponent={
        <View>
          <Text style={styles.eyebrow}>Your applications</Text>
          <Text style={styles.heading}>Tracker</Text>
        </View>
      }
      ListEmptyComponent={
        <View style={styles.emptyBox}>
          <Text style={styles.emptyText}>
            Nothing saved yet. Tap the bookmark icon on any scholarship from Home to track it here.
          </Text>
        </View>
      }
      renderItem={({ item }) => (
        <View style={styles.row}>
          <View style={{ flex: 1 }}>
            <Text style={styles.rowTitle}>{item.scholarship.name}</Text>
            <Text style={styles.rowSub}>{item.scholarship.provider} · {item.scholarship.deadline_window}</Text>
          </View>
          <View style={styles.pickerWrap}>
            <Picker
              selectedValue={item.status}
              style={{ color: statusColor(item.status) }}
              onValueChange={(v) => tracker.updateStatus(item.scholarship_id, v as string)}
              mode="dropdown"
            >
              {STATUSES.map((s) => <Picker.Item key={s} label={s[0].toUpperCase() + s.slice(1)} value={s} />)}
            </Picker>
          </View>
        </View>
      )}
    />
  );
}

const styles = StyleSheet.create({
  eyebrow: { fontFamily: fonts.regular, fontSize: 13, color: colors.inkSoft },
  heading: { fontFamily: fonts.extraBold, fontSize: 27, color: colors.ink, marginBottom: 18 },
  emptyBox: { borderWidth: 1, borderColor: colors.line, borderRadius: 12, padding: 16 },
  emptyText: { fontFamily: fonts.regular, fontSize: 13.5, color: colors.inkSoft },
  row: {
    flexDirection: 'row', alignItems: 'center', backgroundColor: colors.card, borderRadius: 14,
    borderWidth: 1, borderColor: colors.line, padding: 14, marginBottom: 12,
  },
  rowTitle: { fontFamily: fonts.extraBold, fontSize: 14.5, color: colors.ink },
  rowSub: { fontFamily: fonts.regular, fontSize: 12, color: colors.inkSoft, marginTop: 2 },
  pickerWrap: { width: 140 },
});
