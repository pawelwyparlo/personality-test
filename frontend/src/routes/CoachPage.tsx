import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router'

import { ApiError } from '../api/client'
import { getCoach } from '../api/coach'
import { clerkEnabled } from '../config'
import { CoachIntro } from './coach/CoachIntro'
import { CoachWorkspace } from './coach/CoachWorkspace'
import styles from './CoachPage.module.css'

/**
 * Screens 2f (coach intro) and 2g (coach workspace).
 *
 * Routing rule: fetch the caller's coach. A 404 means "no coach yet" -> intro;
 * a 200 -> workspace. Keyless (no Clerk key) the GET goes out unauthenticated
 * and the backend answers 503 auth_not_configured — which we treat as "no coach"
 * so the intro (with its setup card) still renders. Nothing crashes without keys.
 */
export function CoachPage() {
  const navigate = useNavigate()

  const coachQuery = useQuery({
    queryKey: ['coach'],
    queryFn: getCoach,
    // Only meaningful to fetch when Clerk is configured; keyless we short-circuit
    // to the intro's setup card without a network round-trip.
    enabled: clerkEnabled,
    retry: false,
  })

  // Keyless: go straight to the intro (it shows the setup card).
  if (!clerkEnabled) {
    return (
      <div className={styles.page}>
        <CoachIntro onCreated={() => coachQuery.refetch()} />
      </div>
    )
  }

  if (coachQuery.isLoading) {
    return (
      <div className={styles.page}>
        <div className={styles.center}>
          <div className={styles.spinner} aria-label="Loading" />
        </div>
      </div>
    )
  }

  // A coach exists -> workspace.
  if (coachQuery.data) {
    return (
      <div className={styles.page}>
        <CoachWorkspace coach={coachQuery.data} />
      </div>
    )
  }

  // 404 (no coach) or 503 (auth not configured) -> intro. Any other error also
  // falls through to the intro rather than a dead end.
  const err = coachQuery.error
  const isExpected =
    err instanceof ApiError && (err.status === 404 || err.status === 503)
  if (coachQuery.isError && !isExpected) {
    return (
      <div className={styles.page}>
        <div className={styles.center}>
          <div className={styles.statusCard}>
            <h1 className={styles.statusTitle}>We couldn&rsquo;t load your coach</h1>
            <p className={styles.statusText}>Something went wrong. Try again.</p>
            <button
              className={styles.statusBtn}
              onClick={() => coachQuery.refetch()}
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className={styles.page}>
      <CoachIntro
        onCreated={() => {
          // A fresh coach exists now; refetch flips us into the workspace.
          coachQuery.refetch()
        }}
        onDecline={() => navigate(-1)}
      />
    </div>
  )
}
