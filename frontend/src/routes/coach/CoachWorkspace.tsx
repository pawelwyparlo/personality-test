import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router'

import { ApiError } from '../../api/client'
import { streamCoachMessage } from '../../api/coach'
import type { Coach, CoachMessage } from '../../api/types'
import styles from '../CoachPage.module.css'

const OCEAN = ['O', 'C', 'E', 'A', 'N']

/** "knows: O72 · C84 · E38 · A61 · N29" from the live trait context. */
function knowsLine(percentiles: Record<string, number>): string {
  return (
    'knows: ' +
    OCEAN.filter((l) => l in percentiles)
      .map((l) => `${l}${percentiles[l]}`)
      .join(' · ')
  )
}

/**
 * Screen 2g — Coach workspace. Two-pane: a sidebar (Sol identity + nav, with
 * Check-ins/Goals as disabled "coming soon" and "My report" linking to the
 * latest run's report) and the chat pane (header with the knows-token line, a
 * scrollable thread, a typing indicator while awaiting the first SSE token,
 * progressive streaming, and a composer).
 */
export function CoachWorkspace({ coach }: { coach: Coach }) {
  const [messages, setMessages] = useState<CoachMessage[]>(coach.messages)
  const [draft, setDraft] = useState('')
  const [streaming, setStreaming] = useState(false)
  // The reply text as it streams in, before it lands as a persisted message.
  const [pending, setPending] = useState<string | null>(null)
  const [systemNote, setSystemNote] = useState<string | null>(null)

  const threadRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  const reportRunId = coach.trait_context.run_id

  // Keep the thread pinned to the latest content as it grows / streams.
  useEffect(() => {
    const el = threadRef.current
    if (el) el.scrollTop = el.scrollHeight
  }, [messages, pending])

  async function send() {
    const content = draft.trim()
    if (!content || streaming) return

    // Optimistically show the user's message; keep the draft until we know the
    // send succeeded (a 503 should not lose it).
    const optimistic: CoachMessage = {
      id: `local-${Date.now()}`,
      role: 'user',
      content,
      created_at: new Date().toISOString(),
    }
    setMessages((prev) => [...prev, optimistic])
    setStreaming(true)
    setPending('')
    setSystemNote(null)

    let assembled = ''
    try {
      await streamCoachMessage(content, {
        onToken: (chunk) => {
          assembled += chunk
          setPending(assembled)
        },
        onError: (detail) => {
          setSystemNote(detail || 'Sol ran into a problem. Please try again.')
        },
      })
      setDraft('')
      if (assembled) {
        setMessages((prev) => [
          ...prev,
          {
            id: `coach-${Date.now()}`,
            role: 'coach',
            content: assembled,
            created_at: new Date().toISOString(),
          },
        ])
      }
    } catch (err) {
      // Roll the optimistic user message back and keep the draft.
      setMessages((prev) => prev.filter((m) => m.id !== optimistic.id))
      if (err instanceof ApiError && err.status === 503) {
        setSystemNote('Sol needs an LLM key to reply — see README.')
      } else if (err instanceof ApiError) {
        setSystemNote(err.message)
      } else {
        setSystemNote('Could not reach Sol. Please try again.')
      }
    } finally {
      setPending(null)
      setStreaming(false)
      inputRef.current?.focus()
    }
  }

  function onKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    // Enter sends; Shift+Enter inserts a newline.
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      send()
    }
  }

  return (
    <div className={styles.workspace}>
      {/* Sidebar */}
      <aside className={styles.sidebar}>
        <div className={styles.sidebarHead}>
          <div className={styles.sidebarAvatar} aria-hidden="true">
            ◕
          </div>
          <div>
            <div className={styles.sidebarName}>{coach.name}</div>
            <div className={styles.sidebarStatus}>● your coach</div>
          </div>
        </div>
        <span className={`${styles.navItem} ${styles.navItemActive}`}>
          💬 Chat
        </span>
        <span
          className={`${styles.navItem} ${styles.navItemDisabled}`}
          aria-disabled="true"
        >
          ✓ Check-ins <span className={styles.navSoon}>SOON</span>
        </span>
        <span
          className={`${styles.navItem} ${styles.navItemDisabled}`}
          aria-disabled="true"
        >
          ◎ Goals <span className={styles.navSoon}>SOON</span>
        </span>
        <Link
          to={`/report/${reportRunId}`}
          className={`${styles.navItem} ${styles.navItemLink}`}
        >
          ◇ My report
        </Link>
      </aside>

      {/* Chat */}
      <section className={styles.chat}>
        <header className={styles.chatHeader}>
          <div className={styles.chatTitle}>Chat with {coach.name}</div>
          <div className={styles.knows}>
            {knowsLine(coach.trait_context.percentiles)}
          </div>
        </header>

        <div className={styles.thread} ref={threadRef}>
          {messages.length === 0 && pending === null ? (
            <p className={styles.empty}>
              Say hi to {coach.name}. It already knows your five traits — ask
              about your report, or where to start.
            </p>
          ) : null}

          {messages.map((m) => (
            <div
              key={m.id}
              className={m.role === 'coach' ? styles.bubbleCoach : styles.bubbleUser}
            >
              {m.content}
            </div>
          ))}

          {/* Streaming reply: typing dots until the first token, then text. */}
          {pending !== null ? (
            pending === '' ? (
              <div className={styles.typing} aria-label={`${coach.name} is typing`}>
                <span className={styles.dot} />
                <span className={styles.dot} />
                <span className={styles.dot} />
              </div>
            ) : (
              <div className={styles.bubbleCoach}>{pending}</div>
            )
          ) : null}

          {systemNote ? <div className={styles.systemNote}>{systemNote}</div> : null}
        </div>

        <div className={styles.composer}>
          <div className={styles.composerRow}>
            <textarea
              ref={inputRef}
              className={styles.composerInput}
              placeholder={`Message ${coach.name}…`}
              rows={1}
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              onKeyDown={onKeyDown}
              disabled={streaming}
            />
            <button
              className={styles.send}
              onClick={send}
              disabled={streaming || draft.trim().length === 0}
              aria-label="Send"
            >
              ↑
            </button>
          </div>
        </div>
      </section>
    </div>
  )
}
