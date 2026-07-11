import { createBrowserRouter } from 'react-router'

import { AppShell } from './components/AppShell'
import { CoachPage } from './routes/CoachPage'
import { ReportPage } from './routes/ReportPage'
import { ScoringPage } from './routes/ScoringPage'
import { StartPage } from './routes/StartPage'
import { TestPage } from './routes/TestPage'

export const router = createBrowserRouter([
  // Start, Test, and Report render their own full-bleed chrome (per the design
  // handoff: a marketing top-nav on Start, a slim test header on Test, and a
  // Report/Coach tab bar with a Download-PDF action on Report), so they sit
  // outside the shared AppShell.
  { path: '/', element: <StartPage /> },
  { path: '/test', element: <TestPage /> },
  { path: '/test/scoring', element: <ScoringPage /> },
  { path: '/report/:runId', element: <ReportPage /> },
  {
    element: <AppShell />,
    children: [{ path: '/coach', element: <CoachPage /> }],
  },
])
