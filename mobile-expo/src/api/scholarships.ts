import { api } from './client';

export interface Scholarship {
  id: string;
  name: string;
  provider: string;
  country: string;
  level: string;
  field: string;
  funding: string;
  deadline_window: string;
  official_link: string;
  tags: string[];
  blurb: string;
  match_score?: number | null;
  match_tier?: 'green' | 'yellow' | 'red' | null;
}

export const ScholarshipsApi = {
  async list(params: { q?: string; region?: string; auth?: boolean } = {}): Promise<Scholarship[]> {
    return api.get('/scholarships', {
      auth: !!params.auth,
      query: { q: params.q, region: params.region && params.region !== 'All' ? params.region : undefined },
    });
  },

  async create(payload: Omit<Scholarship, 'id' | 'match_score' | 'match_tier'>): Promise<Scholarship> {
    return api.post('/scholarships', payload, { auth: true });
  },

  async update(id: string, payload: Omit<Scholarship, 'id' | 'match_score' | 'match_tier'>): Promise<Scholarship> {
    return api.put(`/scholarships/${id}`, payload, { auth: true });
  },

  async remove(id: string): Promise<void> {
    await api.delete(`/scholarships/${id}`, { auth: true });
  },
};
