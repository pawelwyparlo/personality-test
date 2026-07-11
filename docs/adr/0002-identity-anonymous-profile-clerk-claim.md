# Identity: anonymous Profile, claimed by a Clerk Account at Coach creation

The test and report work fully anonymously (a server-issued Profile ID held in the browser), but
creating the Coach — the persistent half of the product — requires signing in with Clerk, which
claims the Profile. All domain data is keyed by `profile_id`; Clerk contributes only the
`account → profile` claim and session verification (JWT checked in FastAPI). We chose the hosted
SaaS (over self-hosted fastapi-users/Keycloak) for its drop-in React components and speed, accepting
that sign-in requires internet and user credentials live with Clerk. Keeping the funnel top
anonymous preserves the design's frictionless start screen while giving the coach durable identity.

## Consequences

- Two identity states exist (anonymous vs claimed) but only the coach flow branches on it.
- The app is no longer fully offline-capable once a user reaches the coach gate.
- Future "sync my anonymous history" = claiming a Profile; no data migration needed.
