import { useState, useEffect } from 'react'
import { runSimulation } from '../services/api.js'

export function useSimulation(variantId, pathwayId) {
  const [result, setResult] = useState(null)
  const [status, setStatus] = useState('idle') // idle | loading | success | error
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!variantId) return
    let cancelled = false

    setStatus('loading')
    setError(null)

    runSimulation({ variantId, pathwayId })
      .then((data) => {
        if (!cancelled) {
          setResult(data)
          setStatus('success')
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err)
          setStatus('error')
        }
      })

    return () => {
      cancelled = true
    }
  }, [variantId, pathwayId])

  return { result, status, error }
}
