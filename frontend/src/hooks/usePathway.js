import { useState, useEffect } from 'react'
import { fetchPathway } from '../services/api.js'

export function usePathway(pathwayId) {
  const [pathway, setPathway] = useState(null)
  const [status, setStatus] = useState('idle') // idle | loading | success | error
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!pathwayId) return
    let cancelled = false

    setStatus('loading')
    setError(null)

    fetchPathway(pathwayId)
      .then((data) => {
        if (!cancelled) {
          setPathway(data)
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
  }, [pathwayId])

  return { pathway, status, error }
}
