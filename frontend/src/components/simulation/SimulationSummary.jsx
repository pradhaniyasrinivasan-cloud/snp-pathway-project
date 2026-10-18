export default function SimulationSummary({ result }) {
  const { pathway_output_normal, pathway_output_variant, percent_change } = result
  const isIncrease = percent_change > 0
  const isNegligible = Math.abs(percent_change) < 1

  const changeColor = isNegligible
    ? 'text-text-muted'
    : isIncrease
    ? 'text-signal-coral'
    : 'text-signal-teal'

  return (
    <div className="grid grid-cols-3 gap-4">
      <div className="bg-ink border border-ink-border rounded-lg px-4 py-3.5">
        <div className="text-[11px] text-text-muted uppercase tracking-wide mb-1.5">
          Normal output
        </div>
        <div className="font-mono text-2xl font-medium">{pathway_output_normal.toFixed(3)}</div>
      </div>

      <div className="bg-ink border border-ink-border rounded-lg px-4 py-3.5">
        <div className="text-[11px] text-text-muted uppercase tracking-wide mb-1.5">
          Variant output
        </div>
        <div className="font-mono text-2xl font-medium">{pathway_output_variant.toFixed(3)}</div>
      </div>

      <div className="bg-ink border border-ink-border rounded-lg px-4 py-3.5">
        <div className="text-[11px] text-text-muted uppercase tracking-wide mb-1.5">
          Change
        </div>
        <div className={`font-mono text-2xl font-medium ${changeColor}`}>
          {isNegligible ? '≈0%' : `${isIncrease ? '+' : ''}${percent_change}%`}
        </div>
      </div>
    </div>
  )
}
