import { api } from './client';

export interface GradingSystem {
  id: string;
  label: string;
  input_type: 'percent' | 'number' | 'select';
  min: number;
  max: number;
  options?: string[] | null;
}

export interface GpaProfile {
  gpa: number;
  percent: number;
  ects: string;
  system_id: string;
  system_label: string;
}

export interface AcademicProfile {
  level: string;
  field: string;
  nationality: string;
  ielts: number | null;
  work_years: number;
  publications: number;
  leadership: string;
  volunteering: string;
  has_cv: boolean;
  has_sop: boolean;
  has_recommendation_letters: boolean;
}

export interface ReadinessCategory { label: string; stars: number; }
export interface Readiness { overall: number; categories: ReadinessCategory[]; }

export const ProfileApi = {
  gpaSystems: (): Promise<GradingSystem[]> => api.get('/profile/gpa/systems'),

  convertGpa: (system_id: string, value: string): Promise<{ gpa: number; percent: number; ects: string; percentile_note: string }> =>
    api.post('/profile/gpa/convert', { system_id, value }),

  saveGpa: (system_id: string, value: string): Promise<GpaProfile> =>
    api.post('/profile/gpa', { system_id, value }, { auth: true }),

  getGpa: (): Promise<GpaProfile | null> => api.get('/profile/gpa', { auth: true }),

  saveAcademic: (payload: AcademicProfile): Promise<AcademicProfile> =>
    api.post('/profile/academic', payload, { auth: true }),

  getAcademic: (): Promise<AcademicProfile | null> => api.get('/profile/academic', { auth: true }),

  getReadiness: (): Promise<Readiness | null> => api.get('/profile/readiness', { auth: true }),
};
