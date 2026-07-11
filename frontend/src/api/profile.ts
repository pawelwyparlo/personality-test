import { api } from './client'

const PROFILE_KEY = 'bigfive.profileId'

/** Return the persisted anonymous Profile id, minting one on first visit. */
export async function ensureProfileId(): Promise<string> {
  const existing = localStorage.getItem(PROFILE_KEY)
  if (existing) return existing
  const { id } = await api.createProfile()
  localStorage.setItem(PROFILE_KEY, id)
  return id
}
