import { ApiError, authHeaders } from './client'
import type { Coach, CoachCreated } from './types'

const BASE = '/api/v1'

async function parseError(resp: Response): Promise<never> {
  let detail = resp.statusText
  try {
    const body = await resp.json()
    if (body?.detail) {
      detail = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail)
    }
  } catch {
    // non-JSON body; keep statusText
  }
  throw new ApiError(resp.status, detail)
}

/** The caller's coach (+ messages + trait context); 404 (ApiError) if none. */
export async function getCoach(): Promise<Coach> {
  const resp = await fetch(`${BASE}/coach`, {
    headers: { ...(await authHeaders()) },
  })
  if (!resp.ok) return parseError(resp)
  return (await resp.json()) as Coach
}

/** Claim the profile and create its coach. */
export async function createCoach(profileId: string): Promise<CoachCreated> {
  const resp = await fetch(`${BASE}/coach`, {
    method: 'POST',
    headers: { 'content-type': 'application/json', ...(await authHeaders()) },
    body: JSON.stringify({ profile_id: profileId }),
  })
  if (!resp.ok) return parseError(resp)
  return (await resp.json()) as CoachCreated
}

export interface StreamCallbacks {
  onToken: (chunk: string) => void
  onError?: (detail: string) => void
  signal?: AbortSignal
}

/**
 * Send a message and stream Sol's reply. Uses fetch (not EventSource, which
 * can't POST or attach an auth header) and parses the SSE frames by hand.
 *
 * A non-streamed error (e.g. 503 llm_not_configured) is thrown as an ApiError
 * before any tokens arrive, so the caller can show the inline system note and
 * keep the user's draft.
 */
export async function streamCoachMessage(
  content: string,
  { onToken, onError, signal }: StreamCallbacks,
): Promise<void> {
  const resp = await fetch(`${BASE}/coach/messages`, {
    method: 'POST',
    headers: { 'content-type': 'application/json', ...(await authHeaders()) },
    body: JSON.stringify({ content }),
    signal,
  })
  if (!resp.ok) return parseError(resp)
  if (!resp.body) return

  const reader = resp.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  // SSE frames are separated by a blank line; each frame has "event:" and
  // "data:" lines. We only care about token/error data payloads.
  const flush = (frame: string) => {
    let event = 'message'
    const dataLines: string[] = []
    for (const line of frame.split('\n')) {
      if (line.startsWith('event:')) event = line.slice(6).trim()
      else if (line.startsWith('data:')) dataLines.push(line.slice(5).replace(/^ /, ''))
    }
    const data = dataLines.join('\n')
    if (event === 'token') onToken(data)
    else if (event === 'error') onError?.(data)
  }

  for (;;) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    let idx: number
    while ((idx = buffer.indexOf('\n\n')) !== -1) {
      const frame = buffer.slice(0, idx)
      buffer = buffer.slice(idx + 2)
      if (frame.trim()) flush(frame)
    }
  }
  if (buffer.trim()) flush(buffer)
}
