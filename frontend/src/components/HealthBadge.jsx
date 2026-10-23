import { useEffect, useState } from 'react'
import { api } from '../api/client.js'

const POLL_MS = 15000

export default function HealthBadge() {
  const [status, setStatus] = useState({ ok: null, env: null })

  useEffect(() => {
    let cancelled = false

    async function check() {
      try {
        const data = await api.health()
        if (!cancelled) setStatus({ ok: data.status === 'ok', env: data.env })
      } catch {
        if (!cancelled) setStatus({ ok: false, env: null })
      }
    }

    check()
    const timer = setInterval(check, POLL_MS)
    return () => {
      cancelled = true
      clearInterval(timer)
    }
  }, [])

  const label = status.ok === null ? 'Comprobando API…' : status.ok ? 'API operativa' : 'API caída'
  const state = status.ok === null ? 'pending' : status.ok ? 'up' : 'down'

  return (
    <span className={`health health-${state}`} title={status.env ? `Entorno: ${status.env}` : undefined}>
      <span className="dot" aria-hidden="true" />
      {label}
    </span>
  )
}
