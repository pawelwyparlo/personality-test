import { useParams } from 'react-router'

import { Placeholder } from '../components/Placeholder'

export function ReportPage() {
  const { runId } = useParams()
  return (
    <Placeholder title="Report">
      <p>The report for test run {runId} renders here in a later PR.</p>
    </Placeholder>
  )
}
