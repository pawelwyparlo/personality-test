import { useCallback, useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router'

import { api } from '../api/client'
import { Slider } from '../components/Slider'
import { TEST_MODE } from '../config'
import { NEUTRAL_PERCENT, percentToValue } from '../lib/slider'
import { useCountdown } from '../lib/useCountdown'
import { useRunStore } from '../store/runStore'
import styles from './TestPage.module.css'

const TIMER_MS = 30_000

function formatRemaining(ms: number): string {
  const total = Math.ceil(ms / 1000)
  const m = Math.floor(total / 60)
  const s = total % 60
  return `${m}:${s.toString().padStart(2, '0')}`
}

export function TestPage() {
  const navigate = useNavigate()
  const runId = useRunStore((s) => s.runId)
  const items = useRunStore((s) => s.items)
  const index = useRunStore((s) => s.index)
  const commit = useRunStore((s) => s.commit)
  const next = useRunStore((s) => s.next)

  const [percent, setPercent] = useState(NEUTRAL_PERCENT)
  const [showExit, setShowExit] = useState(false)
  const [busy, setBusy] = useState(false)
  const [autofilling, setAutofilling] = useState(false)

  // Guards a single commit per item across the expiry-vs-click race: each item
  // may be committed exactly once (ADR-0001). A Set — never cleared on advance —
  // so a stale expiry from the previous item can't re-commit it after the
  // per-item reset (that ordering produced duplicate POSTs and server 409s).
  const committedItemsRef = useRef<Set<number>>(new Set())

  const item = items[index]
  const total = items.length

  // No active run (e.g. deep-link / refresh): send the user back to Start.
  useEffect(() => {
    if (!runId || total === 0) navigate('/', { replace: true })
  }, [runId, total, navigate])

  // Fresh slider (centered Neutral) for each new item.
  useEffect(() => {
    setPercent(NEUTRAL_PERCENT)
  }, [index])

  const advance = useCallback(
    async (value: number) => {
      if (!runId || !item) return
      // One commit per item — expiry and click can both fire.
      if (committedItemsRef.current.has(item.id)) return
      committedItemsRef.current.add(item.id)
      setBusy(true)
      try {
        await api.submitAnswer({ runId, item_id: item.id, value })
        commit(item.id, value)
        if (index + 1 >= total) {
          navigate('/test/scoring')
        } else {
          next()
        }
      } catch {
        // Allow a retry on failure by clearing the guard.
        committedItemsRef.current.delete(item.id)
      } finally {
        setBusy(false)
      }
    },
    [runId, item, index, total, commit, next, navigate],
  )

  const onExpire = useCallback(() => {
    // Commit the slider as it stands (untouched = Neutral).
    void advance(percentToValue(percent))
  }, [advance, percent])

  const { progress: timerProgress, remainingMs } = useCountdown(
    TIMER_MS,
    index,
    onExpire,
    showExit, // pause the soft timer while the exit dialog is open
  )

  // Keyboard 1..5 jumps to that stop; Enter / → commits.
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (showExit) return
      if (e.key >= '1' && e.key <= '5') {
        setPercent((Number(e.key) - 1) * 25)
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [showExit])

  async function handleAutofill() {
    if (!runId) return
    setAutofilling(true)
    // Answer every REMAINING item with a random 1..5 through the normal path,
    // then complete and route to the report.
    try {
      for (let i = index; i < total; i++) {
        const it = items[i]
        const value = Math.floor(Math.random() * 5) + 1
        await api.submitAnswer({ runId, item_id: it.id, value })
        commit(it.id, value)
      }
      navigate('/test/scoring')
    } catch {
      setAutofilling(false)
    }
  }

  function confirmExit() {
    setShowExit(false)
    if (runId) void api.abandonTestRun(runId).catch(() => {})
    navigate('/', { replace: true })
  }

  if (!item) {
    return (
      <div className={styles.page}>
        <div className={styles.center}>Loading…</div>
      </div>
    )
  }

  const progressPct = ((index + (busy ? 1 : 0)) / total) * 100

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <span className={styles.wordmark}>Big Five</span>
        <div className={styles.progressArea}>
          <div className={styles.progressMeta}>
            <span>
              Question {index + 1} of {total}
            </span>
            <span>⏱ {formatRemaining(remainingMs)} left</span>
          </div>
          <div className={styles.progressBar}>
            <div
              className={styles.progressFill}
              style={{ width: `${progressPct}%` }}
            />
          </div>
          <div className={styles.timerBar}>
            <div
              className={styles.timerFill}
              style={{ width: `${(1 - timerProgress) * 100}%` }}
            />
          </div>
        </div>
        <button className={styles.exit} onClick={() => setShowExit(true)}>
          Exit test
        </button>
      </header>

      <div className={styles.body}>
        <div className={styles.prompt}>How accurately does this describe you?</div>
        <p className={styles.statement}>&ldquo;{item.text}&rdquo;</p>

        <Slider percent={percent} onChange={setPercent} />

        <div className={styles.actions}>
          <button
            className={styles.next}
            onClick={() => advance(percentToValue(percent))}
            disabled={busy}
          >
            Next →
          </button>
        </div>
        <div className={styles.helper}>
          Tip: hit 1–5 on your keyboard · auto-advances when the timer runs out
        </div>

        {TEST_MODE && (
          <button
            className={styles.autofill}
            onClick={handleAutofill}
            disabled={autofilling}
          >
            {autofilling ? 'Filling…' : '⚡ Autofill & finish'}
          </button>
        )}
      </div>

      {showExit && (
        <div className={styles.dialogBackdrop} role="dialog" aria-modal="true">
          <div className={styles.dialog}>
            <h2 className={styles.dialogTitle}>Exit the test?</h2>
            <p className={styles.dialogText}>
              Your progress will be discarded — there&rsquo;s no resuming a run.
            </p>
            <div className={styles.dialogActions}>
              <button
                className={styles.dialogCancel}
                onClick={() => setShowExit(false)}
              >
                Keep going
              </button>
              <button className={styles.dialogConfirm} onClick={confirmExit}>
                Exit test
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
