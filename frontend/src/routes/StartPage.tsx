import { Link } from 'react-router'

import { Placeholder } from '../components/Placeholder'

export function StartPage() {
  return (
    <Placeholder title="Discover your Big Five">
      <p>
        Take an IPIP-NEO personality test with a soft per-item timer and a
        continuous slider, then read a plain-language report of your five traits.
      </p>
      <p>
        <Link to="/test">Start the test →</Link>
      </p>
    </Placeholder>
  )
}
