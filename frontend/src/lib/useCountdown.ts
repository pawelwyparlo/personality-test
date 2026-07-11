import { useEffect, useRef, useState } from 'react'

/**
 * Recreates the reference TimeBar semantics in React: a 30s soft timer driven by
 * requestAnimationFrame against performance.now(), reporting elapsed each frame
 * and firing `onExpire` once when it runs out. Resets cleanly whenever `resetKey`
 * changes (a new item), mirroring the Vue TimeBar's "reset elapsed to 0 on
 * advance" behaviour. `paused` suspends the loop (keeping accumulated time) so
 * e.g. a confirm dialog does not eat the clock.
 *
 * Accumulated elapsed lives in a ref (not state) so it is immune to render
 * batching: on advance the ref is zeroed synchronously in render, before the
 * rAF effect re-runs, which is what prevents a stale ~30s value from making the
 * next item expire instantly.
 *
 * Returns `progress` (0..1) for the thin bar and `remainingMs` for the label.
 */
export function useCountdown(
  durationMs: number,
  resetKey: unknown,
  onExpire: () => void,
  paused = false,
): { progress: number; remainingMs: number } {
  const [, forceTick] = useState(0)
  const elapsedRef = useRef(0)
  const firedRef = useRef(false)
  const prevKeyRef = useRef(resetKey)
  const onExpireRef = useRef(onExpire)
  onExpireRef.current = onExpire

  // Reset synchronously during render when the item changes, so the rAF effect
  // below always starts from a clean elapsed=0 for the new item.
  if (prevKeyRef.current !== resetKey) {
    prevKeyRef.current = resetKey
    elapsedRef.current = 0
    firedRef.current = false
  }

  useEffect(() => {
    if (paused || firedRef.current) return
    let handle = 0
    // Anchor so already-accumulated time (from before a pause) keeps counting.
    const anchor = performance.now() - elapsedRef.current

    const tick = () => {
      elapsedRef.current = performance.now() - anchor
      forceTick((n) => n + 1)
      if (elapsedRef.current >= durationMs) {
        if (!firedRef.current) {
          firedRef.current = true
          onExpireRef.current()
        }
        return
      }
      handle = requestAnimationFrame(tick)
    }
    handle = requestAnimationFrame(tick)

    return () => cancelAnimationFrame(handle)
    // resetKey drives a full restart; paused suspends/resumes the loop.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [durationMs, resetKey, paused])

  const elapsed = Math.min(elapsedRef.current, durationMs)
  const progress = Math.min(elapsed / durationMs, 1)
  const remainingMs = Math.max(durationMs - elapsed, 0)
  return { progress, remainingMs }
}
