import type {
  AnswerCreate,
  FormItems,
  ProfileCreated,
  Report,
  ScoreResult,
  TestRunCreated,
  TestRunStatus,
} from './types'

const BASE = '/api/v1'

export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
    this.name = 'ApiError'
  }
}

/**
 * A getter for the current Clerk session token, registered by the app once
 * Clerk mounts (getToken is a hook, so it can't be called from a plain module).
 * Keyless, this stays null and the coach endpoints go out unauthenticated —
 * the backend answers 503 auth_not_configured, which the UI handles.
 */
type TokenGetter = () => Promise<string | null>
let tokenGetter: TokenGetter | null = null

export function setTokenGetter(getter: TokenGetter | null): void {
  tokenGetter = getter
}

/** Authorization header with the Clerk session token, if one is available. */
export async function authHeaders(): Promise<Record<string, string>> {
  if (!tokenGetter) return {}
  const token = await tokenGetter()
  return token ? { authorization: `Bearer ${token}` } : {}
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const resp = await fetch(`${BASE}${path}`, {
    headers: { 'content-type': 'application/json' },
    ...init,
  })
  if (!resp.ok) {
    let detail = resp.statusText
    try {
      const body = await resp.json()
      if (body?.detail) detail = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail)
    } catch {
      // non-JSON error body; keep statusText
    }
    throw new ApiError(resp.status, detail)
  }
  if (resp.status === 204) return undefined as T
  return (await resp.json()) as T
}

export interface AnswerCreateArgs extends AnswerCreate {
  runId: string
}

export const api = {
  createProfile: () => request<ProfileCreated>('/profiles', { method: 'POST' }),

  getFormItems: (form: string) =>
    request<FormItems>(`/forms/${form}/items`),

  createTestRun: (body: {
    profile_id: string
    form: string
    age: number
    sex: string
  }) => request<TestRunCreated>('/test-runs', { method: 'POST', body: JSON.stringify(body) }),

  submitAnswer: ({ runId, item_id, value }: AnswerCreateArgs) =>
    request<void>(`/test-runs/${runId}/answers`, {
      method: 'POST',
      body: JSON.stringify({ item_id, value }),
    }),

  completeTestRun: (runId: string) =>
    request<ScoreResult>(`/test-runs/${runId}/complete`, { method: 'POST' }),

  abandonTestRun: (runId: string) =>
    request<{ id: string; status: string }>(`/test-runs/${runId}/abandon`, {
      method: 'POST',
    }),

  getTestRun: (runId: string) => request<TestRunStatus>(`/test-runs/${runId}`),

  getReport: (runId: string) => request<Report>(`/reports/${runId}`),

  /** Absolute URL for the PDF download endpoint (used as an <a href>). */
  reportPdfUrl: (runId: string) => `${BASE}/reports/${runId}/pdf`,
}
