import { SignedIn, SignedOut, SignInButton } from '@clerk/clerk-react'

import styles from '../CoachPage.module.css'

/**
 * The Clerk-aware CTA on the coach intro (2f). Rendered only when Clerk is
 * configured (its parent gates on ``clerkEnabled``), so these Clerk components
 * always have a provider above them.
 *
 * - SignedOut -> "Create my coach" opens Clerk sign-in (modal).
 * - SignedIn  -> "Create my coach" claims the profile + creates the coach.
 */
export function CoachIntroCta({
  creating,
  onCreate,
}: {
  creating: boolean
  onCreate: () => void
}) {
  return (
    <>
      <SignedOut>
        <SignInButton mode="modal">
          <button className={styles.ctaPrimary}>Create my coach →</button>
        </SignInButton>
      </SignedOut>
      <SignedIn>
        <button
          className={styles.ctaPrimary}
          onClick={onCreate}
          disabled={creating}
        >
          {creating ? 'Creating…' : 'Create my coach →'}
        </button>
      </SignedIn>
    </>
  )
}
