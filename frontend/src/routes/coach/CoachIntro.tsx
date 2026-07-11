import { useState } from 'react'
import { Link, useNavigate } from 'react-router'

import { ApiError } from '../../api/client'
import { createCoach } from '../../api/coach'
import { ensureProfileId } from '../../api/profile'
import { clerkEnabled } from '../../config'
import styles from '../CoachPage.module.css'
import { CoachIntroCta } from './CoachIntroCta'

/**
 * Screen 2f — Coach intro. Split screen: left pitch + CTA, right avatar + a
 * sample first chat (copy verbatim from the design handoff).
 *
 * The left CTA varies by config:
 *  - keyless -> an on-tone setup card pointing at the README (no Clerk rendered);
 *  - with Clerk -> a sign-in / create-coach CTA (see CoachIntroCta).
 */
export function CoachIntro({
  onCreated,
  onDecline,
}: {
  onCreated: () => void
  onDecline?: () => void
}) {
  const navigate = useNavigate()
  const [creating, setCreating] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [needsTest, setNeedsTest] = useState(false)

  // Shared by the Clerk CTA: claim the profile and create the coach.
  async function handleCreate() {
    if (creating) return
    setCreating(true)
    setError(null)
    setNeedsTest(false)
    try {
      const profileId = await ensureProfileId()
      await createCoach(profileId)
      onCreated()
    } catch (err) {
      if (err instanceof ApiError && err.status === 409 && /completed test run/i.test(err.message)) {
        setNeedsTest(true)
      } else if (err instanceof ApiError) {
        setError(err.message)
      } else {
        setError('Could not create your coach. Please try again.')
      }
      setCreating(false)
    }
  }

  return (
    <div className={styles.intro}>
      <div className={styles.introLeft}>
        <div className={styles.eyebrow}>YOUR PERSONAL COACH</div>
        <h1 className={styles.introH1}>A coach who actually knows you</h1>
        <p className={styles.introSub}>
          Built from your results — not a generic chatbot. It remembers your
          traits and picks up where you left off.
        </p>

        <div className={styles.features}>
          <div className={styles.feature}>
            <span className={styles.featureIcon}>☑</span>
            <span className={styles.featureText}>Daily &amp; weekly check-ins</span>
          </div>
          <div className={styles.feature}>
            <span className={styles.featureIcon}>◎</span>
            <span className={styles.featureText}>Goals that fit your traits</span>
          </div>
          <div className={styles.feature}>
            <span className={styles.featureIcon}>✎</span>
            <span className={styles.featureText}>Dig into your report, anytime</span>
          </div>
        </div>

        {needsTest ? (
          <div className={styles.setupCard}>
            <p className={styles.setupTitle}>Take the test first</p>
            <p className={styles.setupText}>
              Your coach is built from your results, so you need one completed
              test run before we can create it.
            </p>
            <button
              className={styles.ctaPrimary}
              style={{ marginTop: 14 }}
              onClick={() => navigate('/')}
            >
              Take the test →
            </button>
          </div>
        ) : clerkEnabled ? (
          <CoachIntroCta creating={creating} onCreate={handleCreate} />
        ) : (
          <div className={styles.setupCard}>
            <p className={styles.setupTitle}>
              Coach requires sign-in to be configured
            </p>
            <p className={styles.setupText}>
              Add your Clerk keys (<code>VITE_CLERK_PUBLISHABLE_KEY</code> and{' '}
              <code>CLERK_SECRET_KEY</code>) to <code>.env</code> — see the
              README — to enable the coach. Everything else works without keys.
            </p>
          </div>
        )}

        {error ? <p className={styles.ctaError}>{error}</p> : null}

        <Link
          to="/"
          className={styles.ctaLink}
          onClick={(e) => {
            if (onDecline) {
              e.preventDefault()
              onDecline()
            }
          }}
        >
          Not now — just download my report
        </Link>
      </div>

      <div className={styles.introRight}>
        <div className={styles.introAvatar} aria-hidden="true">
          ◕
        </div>
        <div className={styles.sampleChat}>
          <div className={styles.bubbleCoach}>
            Your Conscientiousness is high (84). Want to channel that into a goal
            this week?
          </div>
          <div className={styles.bubbleUser}>Yes — let&rsquo;s do it.</div>
        </div>
        <div className={styles.sampleCaption}>↑ sample of a first chat</div>
      </div>
    </div>
  )
}
