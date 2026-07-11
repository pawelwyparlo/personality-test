import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router'

import { api } from '../api/client'
import { useRunStore } from '../store/runStore'
import styles from './ScoringPage.module.css'

const CHIPS = ['O', 'C', 'E', 'A', 'N']

type Phase = 'scoring' | 'error'

/**
 * Screen 2c: covers the POST /complete call. On success routes to the report;
 * on failure shows a simple, on-tone retry state (error states are a design gap
 * per the handoff).
 */
export function ScoringPage() {
  const navigate = useNavigate()
  const runId = useRunStore((s) => s.runId)
  const reset = useRunStore((s) => s.reset)
  const [phase, setPhase] = useState<Phase>('scoring')
  const startedRef = useRef(false)

  useEffect(() => {
    if (!runId) {
      navigate('/', { replace: true })
      return
    }
    // StrictMode double-invokes effects in dev; complete exactly once.
    if (startedRef.current) return
    startedRef.current = true
    void run()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  async function run() {
    if (!runId) return
    setPhase('scoring')
    try {
      await api.completeTestRun(runId)
      const id = runId
      reset()
      navigate(`/report/${id}`, { replace: true })
    } catch {
      setPhase('error')
    }
  }

  function retry() {
    startedRef.current = true
    void run()
  }

  if (phase === 'error') {
    return (
      <div className={styles.page}>
        <div className={styles.card}>
          <h1 className={styles.errorTitle}>We couldn&rsquo;t score that run</h1>
          <p className={styles.errorText}>
            Something went wrong reaching the scorer. Your answers are saved — try
            again.
          </p>
          <button className={styles.retry} onClick={retry}>
            Try again
          </button>
          <button
            className={styles.exitLink}
            onClick={() => {
              reset()
              navigate('/', { replace: true })
            }}
          >
            Back to start
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className={styles.page}>
      <div className={styles.card}>
        <div className={styles.spinner} aria-hidden="true" />
        <div>
          <h1 className={styles.title}>Analyzing your responses…</h1>
          <p className={styles.subtitle}>Mapping you across five dimensions</p>
        </div>
        <div className={styles.chips} aria-hidden="true">
          {CHIPS.map((c, i) => (
            <div
              key={c}
              className={styles.chip}
              style={{ animationDelay: `${i * 0.2}s` }}
            >
              {c}
            </div>
          ))}
        </div>
        <div className={styles.bar}>
          <div className={styles.barIndeterminate} />
        </div>
      </div>
    </div>
  )
}
