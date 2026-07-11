import { createBrowserRouter } from 'react-router'

import { AppShell } from './components/AppShell'
import { CoachPage } from './routes/CoachPage'
import { ReportPage } from './routes/ReportPage'
import { StartPage } from './routes/StartPage'
import { TestPage } from './routes/TestPage'

export const router = createBrowserRouter([
  {
    element: <AppShell />,
    children: [
      { path: '/', element: <StartPage /> },
      { path: '/test', element: <TestPage /> },
      { path: '/report/:runId', element: <ReportPage /> },
      { path: '/coach', element: <CoachPage /> },
    ],
  },
])
