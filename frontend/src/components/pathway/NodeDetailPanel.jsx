export default function NodeDetailPanel({ node, isAffected, onClose }) {
  if (!node) return null

  return (
    <div className="absolute top-4 right-4 w-64 bg-ink-panel border border-ink-border rounded-xl p-4 shadow-xl">
      <div className="flex items-start justify-between mb-2">
        <div className="font-display font-semibold text-sm">{node.label}</div>
        <button
          onClick={onClose}
          className="text-text-muted hover:text-text-primary text-xs leading-none"
          aria-label="Close"
        >
          ✕
        </button>
      </div>

      <div className="text-[11px] font-mono text-text-muted mb-3">{node.node_key}</div>

      <div className="text-xs text-text-muted mb-1">Baseline activity</div>
      <div className="font-mono text-sm mb-3">{node.baseline_activity.toFixed(2)}</div>

      {isAffected ? (
        <div className="text-xs text-signal-coral bg-signal-coral/10 border border-signal-coral/25 rounded-md px-2.5 py-2 leading-relaxed">
          This is the node directly affected by the selected variant.
        </div>
      ) : (
        <div className="text-xs text-text-muted leading-relaxed">
          Not directly affected by the selected variant, but downstream of it may still shift
          if it sits later in the chain.
        </div>
      )}
    </div>
  )
}
