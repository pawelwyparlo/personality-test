import { createBrowserRouter } from 'react-router'

import { AppShell } from './components/AppShell'
import { CoachPage } from './routes/CoachPage'
import { ReportPage } from './routes/ReportPage'
import { ScoringPage } from './routes/ScoringPage'
import { StartPage } from './routes/StartPage'
import { TestPage } from './routes/TestPage'

export const router = createBrowserRouter([
  // Start and Test render their own full-bleed chrome (per the design handoff:
  // a marketing top-nav on Start, a slim test header on Test), so they sit
  // outside the shared AppShell.
  { path: '/', element: <StartPage /> },
  { path: '/test', element: <TestPage /> },
  { path: '/test/scoring', element: <ScoringPage /> },
  {
    element: <AppShell />,
    children: [
      { path: '/report/:runId', element: <ReportPage /> },
      { path: '/coach', element: <CoachPage /> },
    ],
  },
])
