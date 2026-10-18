import { Handle, Position } from 'reactflow'

/**
 * Custom pathway node. Three visual states:
 *  - default: quiet teal border
 *  - affected: the node the selected variant perturbs — coral border + glow
 *  - selected (clicked): brighter ring, regardless of affected state
 */
export default function PathwayFlowNode({ data }) {
  const { label, isAffected, isSelected, activity } = data

  const borderColor = isAffected ? '#FF6B6B' : '#1D8A72'
  const glow = isAffected ? '0 0 0 3px rgba(255,107,107,0.15)' : 'none'
  const ringStyle = isSelected ? { boxShadow: '0 0 0 2px #EAF3F1, ' + glow } : { boxShadow: glow }
  const opacity = activity != null ? Math.min(1, Math.max(0.35, activity)) : 1

  return (
    <div
      style={{ borderColor, opacity, ...ringStyle }}
      className="px-4 py-2.5 rounded-lg border-2 bg-ink-panel min-w-[120px] text-center transition-all"
    >
      <Handle type="target" position={Position.Left} style={{ background: '#1E3040', border: 'none' }} />
      <div className="flex items-center justify-center gap-1.5">
        {isAffected && <span className="w-1.5 h-1.5 rounded-full bg-signal-coral" />}
        <span className="font-mono text-xs text-text-primary">{label}</span>
      </div>
      {activity != null && (
        <div className="font-mono text-[10px] text-text-muted mt-0.5">{Math.round(activity * 100)}%</div>
      )}
      <Handle type="source" position={Position.Right} style={{ background: '#1E3040', border: 'none' }} />
    </div>
  )
}
