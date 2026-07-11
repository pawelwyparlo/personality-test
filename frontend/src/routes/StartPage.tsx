import { useState } from 'react'
import { useNavigate } from 'react-router'

import { api } from '../api/client'
import { ensureProfileId } from '../api/profile'
import { TEST_MODE } from '../config'
import { useRunStore } from '../store/runStore'
import styles from './StartPage.module.css'

type Sex = 'male' | 'female' | ''

export function StartPage() {
  const navigate = useNavigate()
  const start = useRunStore((s) => s.start)

  // Test mode prefills demographics so a run can begin in one click.
  const [age, setAge] = useState<string>(TEST_MODE ? '30' : '')
  const [sex, setSex] = useState<Sex>(TEST_MODE ? 'male' : '')
  const [starting, setStarting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const ageNum = Number(age)
  const ageValid = Number.isInteger(ageNum) && ageNum >= 13 && ageNum <= 120
  const demographicsValid = ageValid && sex !== ''

  async function handleStart() {
    if (!demographicsValid || starting) return
    setStarting(true)
    setError(null)
    try {
      const profileId = await ensureProfileId()
      const [{ id: runId }, formData] = await Promise.all([
        api.createTestRun({ profile_id: profileId, form: 'full', age: ageNum, sex }),
        api.getFormItems('full'),
      ])
      start(runId, formData.items)
      navigate('/test')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not start the test.')
      setStarting(false)
    }
  }

  return (
    <div className={styles.page}>
      <nav className={styles.nav}>
        <span className={styles.wordmark}>Big Five</span>
        <span className={styles.navLink}>How it works</span>
        <span className={styles.navLink}>The science</span>
        <div className={styles.navRight}>
          <span>Sign in</span>
          <span className={styles.avatar} aria-hidden="true" />
        </div>
      </nav>

      <div className={styles.hero}>
        <div className={styles.eyebrow}>SCIENCE-BACKED · BIG FIVE / IPIP-NEO</div>
        <h1 className={styles.h1}>
          Discover the five traits that shape how you think &amp; act
        </h1>
        <p className={styles.subcopy}>
          Answer honestly and quickly — a soft 30-second timer keeps you on
          instinct. Then get a plain-language report and, if you like, a coach
          who knows your results.
        </p>

        <div className={styles.pickLabel}>Pick your length</div>
        <div className={styles.cards}>
          {/* Quick is disabled until PR6 (ADR-0004): coming soon, not selectable. */}
          <div
            className={`${styles.card} ${styles.cardDisabled}`}
            aria-disabled="true"
          >
            <span className={`${styles.badge} ${styles.badgeMuted}`}>
              Coming soon
            </span>
            <div className={styles.cardHead}>
              <span className={styles.cardTitle}>Quick</span>
              <span className={styles.cardMeta}>~10 min</span>
            </div>
            <div className={styles.cardCount}>60 statements</div>
            <div className={styles.cardRule} />
            <div className={styles.cardDesc}>
              Solid five-trait scores. Great for a first read.
            </div>
          </div>

          <div
            className={`${styles.card} ${styles.cardSelected}`}
            aria-pressed="true"
          >
            <span className={styles.badge}>Recommended</span>
            <div className={styles.cardHead}>
              <span className={styles.cardTitle}>Full</span>
              <span className={styles.cardMeta}>~20 min</span>
            </div>
            <div className={styles.cardCount}>120 statements</div>
            <div className={`${styles.cardRule} ${styles.cardRuleTint}`} />
            <div className={styles.cardDesc}>
              Adds facet-level nuance and a richer report + coach.
            </div>
          </div>
        </div>

        <div className={styles.demographics}>
          <div className={styles.demoRow}>
            <label className={styles.field}>
              <span className={styles.fieldLabel}>Age</span>
              <input
                className={styles.input}
                type="number"
                inputMode="numeric"
                min={13}
                max={120}
                value={age}
                onChange={(e) => setAge(e.target.value)}
                placeholder="e.g. 30"
                required
              />
            </label>
            <label className={styles.field}>
              <span className={styles.fieldLabel}>Sex</span>
              <select
                className={styles.select}
                value={sex}
                onChange={(e) => setSex(e.target.value as Sex)}
                required
              >
                <option value="">Select…</option>
                <option value="male">Male</option>
                <option value="female">Female</option>
              </select>
            </label>
          </div>
          <div className={styles.demoHint}>
            Used to compare you against people like you.
          </div>
        </div>

        <button
          className={styles.cta}
          onClick={handleStart}
          disabled={!demographicsValid || starting}
        >
          {starting ? 'Starting…' : 'Start the Full test →'}
        </button>
        {error && <div className={styles.error}>{error}</div>}
        {TEST_MODE && (
          <div className={styles.testModeHint}>
            ⚡ test mode — demographics prefilled
          </div>
        )}

        <div className={styles.steps}>
          <div className={styles.step}>
            <div className={styles.stepNum}>①</div>
            <div className={styles.stepText}>Rate statements on a slider</div>
          </div>
          <div className={styles.step}>
            <div className={styles.stepNum}>②</div>
            <div className={styles.stepText}>Get your five-trait report</div>
          </div>
          <div className={styles.step}>
            <div className={styles.stepNum}>③</div>
            <div className={styles.stepText}>Spin up a personal coach</div>
          </div>
        </div>
      </div>
    </div>
  )
}
