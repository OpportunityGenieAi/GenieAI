import { API_BASE_URL } from '../config/env';
import { TokenStorage } from './tokenStorage';

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function buildHeaders(auth: boolean): Promise<Record<string, string>> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (auth) {
    const token = await TokenStorage.read();
    if (token) headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}

async function handle(res: Response): Promise<any> {
  const text = await res.text();
  const body = text ? JSON.parse(text) : null;
  if (res.ok) return body;
  const detail = body && body.detail ? String(body.detail) : `Something went wrong (${res.status}).`;
  throw new ApiError(res.status, detail);
}

function toQuery(params?: Record<string, string | undefined>): string {
  if (!params) return '';
  const filtered = Object.entries(params).filter(([, v]) => v !== undefined && v !== '');
  if (filtered.length === 0) return '';
  return '?' + filtered.map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v as string)}`).join('&');
}

export const api = {
  async get(path: string, opts: { auth?: boolean; query?: Record<string, string | undefined> } = {}) {
    const res = await fetch(`${API_BASE_URL}${path}${toQuery(opts.query)}`, {
      headers: await buildHeaders(!!opts.auth),
    });
    return handle(res);
  },
  async post(path: string, body?: any, opts: { auth?: boolean } = {}) {
    const res = await fetch(`${API_BASE_URL}${path}`, {
      method: 'POST',
      headers: await buildHeaders(!!opts.auth),
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
    return handle(res);
  },
  async put(path: string, body?: any, opts: { auth?: boolean } = {}) {
    const res = await fetch(`${API_BASE_URL}${path}`, {
      method: 'PUT',
      headers: await buildHeaders(!!opts.auth),
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
    return handle(res);
  },
  async patch(path: string, body?: any, opts: { auth?: boolean } = {}) {
    const res = await fetch(`${API_BASE_URL}${path}`, {
      method: 'PATCH',
      headers: await buildHeaders(!!opts.auth),
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
    return handle(res);
  },
  async delete(path: string, opts: { auth?: boolean } = {}) {
    const res = await fetch(`${API_BASE_URL}${path}`, {
      method: 'DELETE',
      headers: await buildHeaders(!!opts.auth),
    });
    if (res.status === 204) return null;
    return handle(res);
  },
};
