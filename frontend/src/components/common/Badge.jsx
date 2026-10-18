const IMPACT_STYLES = {
  HIGH: 'bg-signal-coral/15 text-signal-coral border-signal-coral/30',
  MODERATE: 'bg-signal-amber/15 text-signal-amber border-signal-amber/30',
  LOW: 'bg-signal-teal/15 text-signal-teal border-signal-teal/30',
  UNKNOWN: 'bg-text-muted/15 text-text-muted border-text-muted/30',
}

export function ImpactBadge({ level }) {
  const style = IMPACT_STYLES[level] || IMPACT_STYLES.UNKNOWN
  return (
    <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-mono font-medium border ${style}`}>
      {level}
    </span>
  )
}

export function SourceBadge({ isModelled }) {
  return isModelled ? (
    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-mono font-medium border bg-signal-amber/15 text-signal-amber border-signal-amber/30">
      <span className="w-1.5 h-1.5 rounded-full bg-signal-amber" />
      Demo / Modelled Prediction
    </span>
  ) : (
    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-mono font-medium border bg-signal-teal/15 text-signal-teal border-signal-teal/30">
      <span className="w-1.5 h-1.5 rounded-full bg-signal-teal" />
      Real Prediction Data
    </span>
  )
}
