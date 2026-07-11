import { create } from 'zustand'

import type { Item } from '../api/types'

/**
 * Client state for the active Test Run: which run, its items, where we are, and
 * the values committed so far. Server calls (answers/complete) go through
 * TanStack Query; this store just tracks the in-flight run so the Test screen
 * can render without refetching. Cleared when a run ends.
 */
interface RunState {
  runId: string | null
  items: Item[]
  index: number
  /** Committed 1..5 values keyed by item id (mirrors what the server has). */
  values: Record<number, number>

  start: (runId: string, items: Item[]) => void
  commit: (itemId: number, value: number) => void
  next: () => void
  reset: () => void
}

export const useRunStore = create<RunState>((set) => ({
  runId: null,
  items: [],
  index: 0,
  values: {},

  start: (runId, items) => set({ runId, items, index: 0, values: {} }),
  commit: (itemId, value) =>
    set((s) => ({ values: { ...s.values, [itemId]: value } })),
  next: () => set((s) => ({ index: s.index + 1 })),
  reset: () => set({ runId: null, items: [], index: 0, values: {} }),
}))
