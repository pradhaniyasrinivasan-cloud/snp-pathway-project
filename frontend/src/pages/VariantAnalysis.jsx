import { useEffect } from 'react'
import { useParams } from 'react-router-dom'
import VariantInputForm from '../components/variant/VariantInputForm.jsx'
import VariantCard from '../components/variant/VariantCard.jsx'
import ProteinCard from '../components/variant/ProteinCard.jsx'
import FunctionalEffectCard from '../components/variant/FunctionalEffectCard.jsx'
import SimulationPanel from '../components/simulation/SimulationPanel.jsx'
import { useVariant } from '../hooks/useVariant.js'

// Only one pathway exists in the MVP dataset — see README limitations.
// Once multiple pathways are supported, this should come from
// GET /api/variant/{id}/pathways instead of being hardcoded.
const DEFAULT_PATHWAY_ID = 'mapk'

export default function VariantAnalysis() {
  const { variantId } = useParams()
  const { variant, functionalEffect, status, error, run } = useVariant()

  useEffect(() => {
    if (variantId) run(variantId)
  }, [variantId, run])

  return (
    <div className="max-w-6xl mx-auto px-6 py-14">
      <div className="mb-10">
        <div className="text-[11px] font-mono uppercase tracking-wider text-signal-teal mb-1.5">
          Step 1 of 3
        </div>
        <h1 className="font-display font-semibold text-3xl tracking-tight">Analyze a variant</h1>
        <p className="text-text-muted text-sm mt-2 max-w-xl">
          Enter an rsID, or pick one of the demo variants to see the full pipeline run
          without needing a live database lookup.
        </p>
      </div>

      <VariantInputForm onSubmit={run} isLoading={status === 'loading'} />

      <div className="mt-10">
        {status === 'loading' && (
          <div className="text-sm text-text-muted font-mono animate-pulse">Analyzing variant…</div>
        )}

        {status === 'error' && (
          <div className="bg-signal-coral/10 border border-signal-coral/30 rounded-xl p-5 text-sm text-signal-coral">
            {error?.message || 'Something went wrong looking up that variant.'}
          </div>
        )}

        {status === 'success' && variant && (
          <div className="space-y-6">
            <VariantCard variant={variant} />
            <ProteinCard variant={variant} />
            {functionalEffect ? (
              <FunctionalEffectCard effect={functionalEffect} />
            ) : (
              <div className="bg-ink-panel border border-ink-border rounded-xl p-5 text-sm text-text-muted">
                No functional-effect prediction is available for this variant.
              </div>
            )}

            <SimulationPanel variantId={variant.rsid} pathwayId={DEFAULT_PATHWAY_ID} />
          </div>
        )}
      </div>
    </div>
  )
}
