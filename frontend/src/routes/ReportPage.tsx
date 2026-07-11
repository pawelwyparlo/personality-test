import type { ReactNode } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link, useNavigate, useParams } from 'react-router'

import { api } from '../api/client'
import type { DomainScore } from '../api/types'
import styles from './ReportPage.module.css'

/**
 * Screen 2d — Report, Variant A (narrative + scores).
 *
 * Its own top chrome (Report/Coach tabs + Download PDF), a ~60/40 two-column
 * body: narrative on the left (pull-quote, paragraphs, strengths/watch-outs),
 * the five dimensions with bars + plain-language descriptors on the right, plus
 * the coach CTA. Loading skeleton and graceful in_progress/abandoned/not-found
 * states are handled.
 */

// Plain-language descriptors, one per domain (hard product requirement — copy
// written for non-native speakers). Keyed by domain letter.
const DESCRIPTORS: Record<string, string> = {
  O: 'Curiosity and imagination; enjoying new ideas',
  C: 'Being organized and dependable; planning ahead',
  E: 'Where your energy comes from: people or quiet',
  A: 'Being warm, cooperative, considerate',
  N: 'How strongly you feel stress and worry',
}

// Sidebar presentation order (OCEAN).
const DIMENSION_ORDER = ['O', 'C', 'E', 'A', 'N']

function ReportChrome({
  runId,
  children,
}: {
  runId?: string
  children: ReactNode
}) {
  return (
    <div className={styles.page}>
      <header className={styles.nav}>
        <Link to="/" className={styles.wordmark}>
          Big Five
        </Link>
        <nav className={styles.tabs}>
          <span className={`${styles.tab} ${styles.tabActive}`}>Report</span>
          <Link to="/coach" className={styles.tab}>
            Coach
          </Link>
        </nav>
        <div className={styles.navRight}>
          {runId ? (
            <a
              className={styles.download}
              href={api.reportPdfUrl(runId)}
              // Let the browser handle the attachment download.
            >
              ⇩ Download PDF
            </a>
          ) : null}
        </div>
      </header>
      <main className={styles.body}>{children}</main>
    </div>
  )
}

export function ReportPage() {
  const { runId } = useParams()
  const navigate = useNavigate()

  // First check run status so we can show the right state; then the report.
  const runQuery = useQuery({
    queryKey: ['test-run', runId],
    queryFn: () => api.getTestRun(runId as string),
    enabled: Boolean(runId),
  })

  const completed = runQuery.data?.status === 'completed'
  const reportQuery = useQuery({
    queryKey: ['report', runId],
    queryFn: () => api.getReport(runId as string),
    enabled: Boolean(runId) && completed,
  })

  if (runQuery.isLoading || (completed && reportQuery.isLoading)) {
    return (
      <ReportChrome>
        <ReportSkeleton />
      </ReportChrome>
    )
  }

  if (runQuery.isError || !runQuery.data) {
    return (
      <ReportChrome>
        <div className={styles.status}>
          <p className={styles.statusText}>We couldn&rsquo;t load that run.</p>
          <button className={styles.statusBtn} onClick={() => navigate('/')}>
            Take the test →
          </button>
        </div>
      </ReportChrome>
    )
  }

  if (!completed) {
    const message =
      runQuery.data.status === 'abandoned'
        ? 'This test run was abandoned, so there is no report.'
        : 'This test run is still in progress — finish it to see your report.'
    return (
      <ReportChrome>
        <div className={styles.status}>
          <p className={styles.statusText}>{message}</p>
          <button className={styles.statusBtn} onClick={() => navigate('/')}>
            Start a new test →
          </button>
        </div>
      </ReportChrome>
    )
  }

  if (reportQuery.isError || !reportQuery.data) {
    return (
      <ReportChrome runId={runId}>
        <div className={styles.status}>
          <p className={styles.statusText}>
            We scored your run, but couldn&rsquo;t build the report just now.
          </p>
          <button
            className={styles.statusBtn}
            onClick={() => reportQuery.refetch()}
          >
            Try again
          </button>
        </div>
      </ReportChrome>
    )
  }

  const report = reportQuery.data
  const { narrative } = report
  const byLetter = new Map<string, DomainScore>(
    report.domains.map((d) => [d.domain, d]),
  )
  const dimensions = DIMENSION_ORDER.map((l) => byLetter.get(l)).filter(
    (d): d is DomainScore => Boolean(d),
  )

  return (
    <ReportChrome runId={runId}>
      <div className={styles.grid}>
        {/* Left: narrative */}
        <section className={styles.narrative}>
          <div className={styles.eyebrow}>YOUR PROFILE</div>
          <h1 className={styles.h1}>Who you are</h1>

          {narrative.source === 'textbank' ? (
            <p className={styles.sourceNote}>
              AI narrative unavailable — showing standard descriptions.
            </p>
          ) : null}

          <blockquote className={styles.pullQuote}>
            {narrative.pull_quote}
          </blockquote>

          <div className={styles.paragraphs}>
            {narrative.paragraphs.map((p, i) => (
              <p key={i}>{p}</p>
            ))}
          </div>

          <div className={styles.lists}>
            <div className={styles.listCol}>
              <h2 className={styles.strengthsHead}>✓ Strengths</h2>
              <ul className={styles.list}>
                {narrative.strengths.map((s, i) => (
                  <li key={i}>{s}</li>
                ))}
              </ul>
            </div>
            <div className={styles.listCol}>
              <h2 className={styles.watchHead}>! Watch-outs</h2>
              <ul className={styles.list}>
                {narrative.watch_outs.map((w, i) => (
                  <li key={i}>{w}</li>
                ))}
              </ul>
            </div>
          </div>
        </section>

        {/* Right: dimensions + coach CTA */}
        <aside className={styles.sidebar}>
          <div className={styles.card}>
            <h2 className={styles.cardTitle}>Your five dimensions</h2>
            {dimensions.map((d) => (
              <div key={d.domain} className={styles.dim}>
                <div className={styles.dimHead}>
                  <span className={styles.dimName}>{d.name}</span>
                  <span className={styles.dimScore}>{d.percentile}</span>
                </div>
                <div className={styles.track}>
                  <div
                    className={styles.fill}
                    style={{ width: `${d.percentile}%` }}
                  />
                </div>
                <p className={styles.descriptor}>{DESCRIPTORS[d.domain]}</p>
              </div>
            ))}
          </div>

          <div className={styles.coachCta}>
            <div className={styles.coachAvatar} aria-hidden="true">
              ◕
            </div>
            <h3 className={styles.coachTitle}>Discuss this with a coach</h3>
            <p className={styles.coachText}>
              Get a personal coach that already knows your results.
            </p>
            <Link to="/coach" className={styles.coachBtn}>
              Create my coach
            </Link>
          </div>
        </aside>
      </div>
    </ReportChrome>
  )
}

function ReportSkeleton() {
  return (
    <div className={styles.grid} aria-hidden="true">
      <section className={styles.narrative}>
        <div className={`${styles.skel} ${styles.skelEyebrow}`} />
        <div className={`${styles.skel} ${styles.skelH1}`} />
        <div className={`${styles.skel} ${styles.skelQuote}`} />
        <div className={`${styles.skel} ${styles.skelLine}`} />
        <div className={`${styles.skel} ${styles.skelLine}`} />
        <div className={`${styles.skel} ${styles.skelLineShort}`} />
      </section>
      <aside className={styles.sidebar}>
        <div className={styles.card}>
          {DIMENSION_ORDER.map((l) => (
            <div key={l} className={styles.dim}>
              <div className={`${styles.skel} ${styles.skelBarHead}`} />
              <div className={`${styles.skel} ${styles.skelBar}`} />
            </div>
          ))}
        </div>
      </aside>
    </div>
  )
}
