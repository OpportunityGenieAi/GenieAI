import { api } from './client';
import { Scholarship } from './scholarships';

export interface TrackerEntry {
  scholarship_id: string;
  status: 'saved' | 'applied' | 'interview' | 'accepted' | 'rejected';
  saved_at: string;
  scholarship: Scholarship;
}

export const TrackerApi = {
  list: (): Promise<TrackerEntry[]> => api.get('/tracker', { auth: true }),
  add: (scholarshipId: string): Promise<TrackerEntry> => api.post(`/tracker/${scholarshipId}`, undefined, { auth: true }),
  updateStatus: (scholarshipId: string, status: string): Promise<TrackerEntry> =>
    api.patch(`/tracker/${scholarshipId}`, { status }, { auth: true }),
  remove: (scholarshipId: string): Promise<void> => api.delete(`/tracker/${scholarshipId}`, { auth: true }),
};

export const AdvisorApi = {
  recommend: async (): Promise<string> => {
    const res = await api.post('/advisor/recommend', undefined, { auth: true });
    return res.text;
  },
};
