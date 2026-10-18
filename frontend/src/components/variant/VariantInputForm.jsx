import { useEffect, useState } from 'react'
import { fetchDemoVariants } from '../../services/api.js'

export default function VariantInputForm({ onSubmit, isLoading }) {
  const [rsidInput, setRsidInput] = useState('')
  const [demoVariants, setDemoVariants] = useState([])
  const [demoError, setDemoError] = useState(false)

  useEffect(() => {
    fetchDemoVariants()
      .then(setDemoVariants)
      .catch(() => setDemoError(true))
  }, [])

  function handleSubmit(e) {
    e.preventDefault()
    const trimmed = rsidInput.trim()
    if (trimmed) onSubmit(trimmed)
  }

  return (
    <div className="grid md:grid-cols-2 gap-6">
      <div className="bg-ink-panel border border-ink-border rounded-xl p-6">
        <div className="text-[11px] font-mono uppercase tracking-wider text-signal-teal mb-1.5">
          Option 1
        </div>
        <h3 className="font-display font-semibold text-base mb-4">Enter an rsID</h3>
        <form onSubmit={handleSubmit} className="flex gap-2">
          <input
            type="text"
            value={rsidInput}
            onChange={(e) => setRsidInput(e.target.value)}
            placeholder="rs113488022"
            className="flex-1 bg-ink border border-ink-border rounded-lg px-3.5 py-2.5 text-sm font-mono placeholder:text-text-muted/60 focus:border-signal-teal outline-none"
          />
          <button
            type="submit"
            disabled={isLoading || !rsidInput.trim()}
            className="bg-signal-teal text-ink font-medium text-sm px-4 py-2.5 rounded-lg hover:bg-signal-teal/90 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            Analyze
          </button>
        </form>
        <p className="text-xs text-text-muted mt-3 leading-relaxed">
          Looked up live where possible, with an automatic fallback to demo data if the
          live lookup fails or the variant isn't found.
        </p>
      </div>

      <div className="bg-ink-panel border border-ink-border rounded-xl p-6">
        <div className="text-[11px] font-mono uppercase tracking-wider text-signal-amber mb-1.5">
          Option 2
        </div>
        <h3 className="font-display font-semibold text-base mb-4">Pick a demo variant</h3>

        {demoError && (
          <p className="text-sm text-signal-coral">Couldn't load demo variants from the API.</p>
        )}

        {!demoError && demoVariants.length === 0 && (
          <p className="text-sm text-text-muted">Loading demo variants…</p>
        )}

        <div className="space-y-2">
          {demoVariants.map((v) => (
            <button
              key={v.variant_id}
              onClick={() => onSubmit(v.variant_id)}
              disabled={isLoading}
              className="w-full flex items-center justify-between text-left bg-ink border border-ink-border rounded-lg px-3.5 py-2.5 hover:border-signal-teal/50 disabled:opacity-40 transition-colors"
            >
              <div>
                <span className="font-mono text-sm text-text-primary">{v.gene_symbol}</span>
                {v.amino_acid_change && (
                  <span className="font-mono text-xs text-text-muted ml-2">{v.amino_acid_change}</span>
                )}
              </div>
              <span
                className={`text-[10px] font-mono px-2 py-0.5 rounded-full border ${
                  v.impact_level === 'HIGH'
                    ? 'text-signal-coral border-signal-coral/30'
                    : v.impact_level === 'MODERATE'
                    ? 'text-signal-amber border-signal-amber/30'
                    : 'text-signal-teal border-signal-teal/30'
                }`}
              >
                {v.impact_level}
              </span>
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
