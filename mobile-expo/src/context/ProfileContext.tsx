import React, { createContext, useCallback, useContext, useState } from 'react';
import { AcademicProfile, GpaProfile, GradingSystem, ProfileApi, Readiness } from '../api/profile';

interface ProfileContextValue {
  gpaProfile: GpaProfile | null;
  academicProfile: AcademicProfile | null;
  readiness: Readiness | null;
  systems: GradingSystem[];
  loading: boolean;
  isComplete: boolean;
  loadAll: () => Promise<void>;
  saveGpa: (systemId: string, value: string) => Promise<void>;
  saveAcademic: (profile: AcademicProfile) => Promise<void>;
  reset: () => void;
}

const ProfileContext = createContext<ProfileContextValue | undefined>(undefined);

export function ProfileProvider({ children }: { children: React.ReactNode }) {
  const [gpaProfile, setGpaProfile] = useState<GpaProfile | null>(null);
  const [academicProfile, setAcademicProfile] = useState<AcademicProfile | null>(null);
  const [readiness, setReadiness] = useState<Readiness | null>(null);
  const [systems, setSystems] = useState<GradingSystem[]>([]);
  const [loading, setLoading] = useState(false);

  const loadAll = useCallback(async () => {
    setLoading(true);
    try {
      const [sys, gpa, academic, ready] = await Promise.all([
        ProfileApi.gpaSystems(),
        ProfileApi.getGpa(),
        ProfileApi.getAcademic(),
        ProfileApi.getReadiness(),
      ]);
      setSystems(sys);
      setGpaProfile(gpa);
      setAcademicProfile(academic);
      setReadiness(ready);
    } catch {
      // leave prior state on failure
    }
    setLoading(false);
  }, []);

  const saveGpa = useCallback(async (systemId: string, value: string) => {
    const gpa = await ProfileApi.saveGpa(systemId, value);
    setGpaProfile(gpa);
    const ready = await ProfileApi.getReadiness();
    setReadiness(ready);
  }, []);

  const saveAcademic = useCallback(async (profile: AcademicProfile) => {
    const saved = await ProfileApi.saveAcademic(profile);
    setAcademicProfile(saved);
    const ready = await ProfileApi.getReadiness();
    setReadiness(ready);
  }, []);

  const reset = useCallback(() => {
    setGpaProfile(null);
    setAcademicProfile(null);
    setReadiness(null);
  }, []);

  const isComplete = !!gpaProfile && !!academicProfile;

  return (
    <ProfileContext.Provider value={{ gpaProfile, academicProfile, readiness, systems, loading, isComplete, loadAll, saveGpa, saveAcademic, reset }}>
      {children}
    </ProfileContext.Provider>
  );
}

export function useProfile(): ProfileContextValue {
  const ctx = useContext(ProfileContext);
  if (!ctx) throw new Error('useProfile must be used within ProfileProvider');
  return ctx;
}
