import React, { createContext, useCallback, useContext, useState } from 'react';
import { TrackerApi, TrackerEntry } from '../api/tracker';

interface TrackerContextValue {
  entries: TrackerEntry[];
  loading: boolean;
  isTracked: (scholarshipId: string) => boolean;
  fetch: () => Promise<void>;
  toggle: (scholarshipId: string) => Promise<void>;
  updateStatus: (scholarshipId: string, status: string) => Promise<void>;
  reset: () => void;
}

const TrackerContext = createContext<TrackerContextValue | undefined>(undefined);

export function TrackerProvider({ children }: { children: React.ReactNode }) {
  const [entries, setEntries] = useState<TrackerEntry[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchEntries = useCallback(async () => {
    setLoading(true);
    try {
      setEntries(await TrackerApi.list());
    } catch {
      // keep prior state
    }
    setLoading(false);
  }, []);

  const isTracked = useCallback((scholarshipId: string) => entries.some((e) => e.scholarship_id === scholarshipId), [entries]);

  const toggle = useCallback(async (scholarshipId: string) => {
    if (entries.some((e) => e.scholarship_id === scholarshipId)) {
      await TrackerApi.remove(scholarshipId);
    } else {
      await TrackerApi.add(scholarshipId);
    }
    await fetchEntries();
  }, [entries, fetchEntries]);

  const updateStatus = useCallback(async (scholarshipId: string, status: string) => {
    await TrackerApi.updateStatus(scholarshipId, status);
    await fetchEntries();
  }, [fetchEntries]);

  const reset = useCallback(() => setEntries([]), []);

  return (
    <TrackerContext.Provider value={{ entries, loading, isTracked, fetch: fetchEntries, toggle, updateStatus, reset }}>
      {children}
    </TrackerContext.Provider>
  );
}

export function useTracker(): TrackerContextValue {
  const ctx = useContext(TrackerContext);
  if (!ctx) throw new Error('useTracker must be used within TrackerProvider');
  return ctx;
}
