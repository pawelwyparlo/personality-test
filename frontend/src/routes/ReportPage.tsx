import { useQuery } from '@tanstack/react-query'
import { Link, useParams } from 'react-router'

import { api } from '../api/client'
import styles from './ReportPage.module.css'

/**
 * Placeholder report (the real 2d narrative report is PR4). Shows the five
 * domain percentiles as plain bars for a completed run, and handles the
 * in_progress / abandoned / error cases gracefully.
 */
export function ReportPage() {
  const { runId } = useParams()
  const { data, isLoading, isError } = useQuery({
    queryKey: ['test-run', runId],
    queryFn: () => api.getTestRun(runId as string),
    enabled: Boolean(runId),
  })

  if (isLoading) {
    return (
      <div className={styles.wrap}>
        <p className={styles.note}>Loading your report…</p>
      </div>
    )
  }

  if (isError || !data) {
    return (
      <div className={styles.wrap}>
        <div className={styles.status}>
          <p className={styles.statusText}>We couldn&rsquo;t load that run.</p>
          <Link className={styles.link} to="/">
            Take the test →
          </Link>
        </div>
      </div>
    )
  }

  if (data.status !== 'completed' || !data.scores) {
    const message =
      data.status === 'abandoned'
        ? 'This test run was abandoned, so there is no report.'
        : 'This test run is still in progress — finish it to see your report.'
    return (
      <div className={styles.wrap}>
        <div className={styles.status}>
          <p className={styles.statusText}>{message}</p>
          <Link className={styles.link} to="/">
            Start a new test →
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className={styles.wrap}>
      <div className={styles.eyebrow}>YOUR PROFILE</div>
      <h1 className={styles.h1}>Your five dimensions</h1>
      <p className={styles.note}>
        A plain-language report with strengths and watch-outs arrives soon. For
        now, here are your percentile scores.
      </p>
      <div className={styles.card}>
        <h2 className={styles.cardTitle}>Domain percentiles</h2>
        {data.scores.domains.map((d) => (
          <div key={d.domain} className={styles.bar}>
            <div className={styles.barHead}>
              <span className={styles.barName}>{d.name}</span>
              <span className={styles.barScore}>{d.percentile}</span>
            </div>
            <div className={styles.barTrack}>
              <div
                className={styles.barFill}
                style={{ width: `${d.percentile}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
