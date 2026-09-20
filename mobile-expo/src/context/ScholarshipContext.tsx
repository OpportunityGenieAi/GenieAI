import React, { createContext, useCallback, useContext, useState } from 'react';
import { Scholarship, ScholarshipsApi } from '../api/scholarships';

interface ScholarshipContextValue {
  items: Scholarship[];
  loading: boolean;
  query: string;
  region: string;
  setQuery: (q: string) => void;
  setRegion: (r: string) => void;
  fetch: (auth: boolean) => Promise<void>;
  sortedByMatch: () => Scholarship[];
}

const ScholarshipContext = createContext<ScholarshipContextValue | undefined>(undefined);

export function ScholarshipProvider({ children }: { children: React.ReactNode }) {
  const [items, setItems] = useState<Scholarship[]>([]);
  const [loading, setLoading] = useState(false);
  const [query, setQuery] = useState('');
  const [region, setRegion] = useState('All');

  const fetchList = useCallback(async (auth: boolean) => {
    setLoading(true);
    try {
      const res = await ScholarshipsApi.list({ q: query, region, auth });
      setItems(res);
    } catch (err) {
  console.log('Scholarship fetch failed:', err);
}
    setLoading(false);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [query, region]);

  const sortedByMatch = useCallback(() => {
    return [...items].sort((a, b) => (b.match_score ?? -1) - (a.match_score ?? -1));
  }, [items]);

  return (
    <ScholarshipContext.Provider value={{ items, loading, query, region, setQuery, setRegion, fetch: fetchList, sortedByMatch }}>
      {children}
    </ScholarshipContext.Provider>
  );
}

export function useScholarships(): ScholarshipContextValue {
  const ctx = useContext(ScholarshipContext);
  if (!ctx) throw new Error('useScholarships must be used within ScholarshipProvider');
  return ctx;
}
