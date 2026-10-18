import { useState, useCallback } from 'react'
import { fetchVariant, fetchFunctionalEffect } from '../services/api.js'

/**
 * Loads a variant's core info and functional-effect prediction together,
 * since the Variant Analysis page always needs both. Exposes a single
 * `run(variantId)` you can call from a form submit or a demo-picker click.
 */
export function useVariant() {
  const [variant, setVariant] = useState(null)
  const [functionalEffect, setFunctionalEffect] = useState(null)
  const [status, setStatus] = useState('idle') // idle | loading | success | error
  const [error, setError] = useState(null)

  const run = useCallback(async (variantId) => {
    setStatus('loading')
    setError(null)
    setVariant(null)
    setFunctionalEffect(null)

    try {
      const variantData = await fetchVariant(variantId)
      setVariant(variantData)

      if (variantData.has_functional_effect_data) {
        const feData = await fetchFunctionalEffect(variantId)
        setFunctionalEffect(feData)
      }

      setStatus('success')
    } catch (err) {
      setError(err)
      setStatus('error')
    }
  }, [])

  return { variant, functionalEffect, status, error, run }
}
