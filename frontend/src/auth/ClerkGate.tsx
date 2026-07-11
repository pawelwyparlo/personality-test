import { useEffect } from 'react'
import { ClerkProvider, useAuth } from '@clerk/clerk-react'
import type { ReactNode } from 'react'

import { setTokenGetter } from '../api/client'
import { CLERK_PUBLISHABLE_KEY, clerkEnabled } from '../config'

/**
 * Registers Clerk's session-token getter with the API client so coach requests
 * carry an Authorization header. getToken is a hook, so this bridge lives inside
 * ClerkProvider and pushes the getter into the module-level client.
 */
function TokenBridge() {
  const { getToken } = useAuth()
  useEffect(() => {
    setTokenGetter(() => getToken())
    return () => setTokenGetter(null)
  }, [getToken])
  return null
}

/**
 * Mounts ClerkProvider ONLY when a publishable key is configured (ADR-0002).
 * Keyless, it renders children untouched — no Clerk code runs, nothing crashes,
 * and the coach intro shows its setup notice instead of a sign-in CTA.
 */
export function ClerkGate({ children }: { children: ReactNode }) {
  if (!clerkEnabled) return <>{children}</>
  return (
    <ClerkProvider publishableKey={CLERK_PUBLISHABLE_KEY}>
      <TokenBridge />
      {children}
    </ClerkProvider>
  )
}
