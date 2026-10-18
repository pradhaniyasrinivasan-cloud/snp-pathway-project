import { SourceBadge } from '../common/Badge.jsx'

export default function InterpretationCard({ result }) {
  return (
    <div className="bg-ink-panel border border-ink-border rounded-xl p-6">
      <div className="flex items-start justify-between mb-3">
        <h3 className="font-display font-semibold text-base">Biological interpretation</h3>
        <SourceBadge isModelled={result.is_modelled} />
      </div>
      <p className="text-sm text-text-muted leading-relaxed">{result.interpretation}</p>
      <div className="mt-4 pt-4 border-t border-ink-border text-[11px] text-text-muted font-mono">
        Computational prediction from a simplified pathway model — not experimental proof.
      </div>
    </div>
  )
}
