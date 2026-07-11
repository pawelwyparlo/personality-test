import { createBrowserRouter } from 'react-router'

import { CoachPage } from './routes/CoachPage'
import { ReportPage } from './routes/ReportPage'
import { ScoringPage } from './routes/ScoringPage'
import { StartPage } from './routes/StartPage'
import { TestPage } from './routes/TestPage'

export const router = createBrowserRouter([
  // Every screen renders its own full-bleed chrome (per the design handoff: a
  // marketing top-nav on Start, a slim test header on Test, a Report/Coach tab
  // bar on Report, and the split coach intro / two-pane workspace on Coach), so
  // there is no shared AppShell.
  { path: '/', element: <StartPage /> },
  { path: '/test', element: <TestPage /> },
  { path: '/test/scoring', element: <ScoringPage /> },
  { path: '/report/:runId', element: <ReportPage /> },
  { path: '/coach', element: <CoachPage /> },
])
