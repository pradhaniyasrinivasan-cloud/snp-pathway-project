import { useState, useMemo } from 'react'
import Card from '../common/Card.jsx'
import PathwayGraph from '../pathway/PathwayGraph.jsx'
import ActivityBarChart from './ActivityBarChart.jsx'
import SimulationSummary from './SimulationSummary.jsx'
import InterpretationCard from './InterpretationCard.jsx'
import { useSimulation } from '../../hooks/useSimulation.js'
import { usePathway } from '../../hooks/usePathway.js'

export default function SimulationPanel({ variantId, pathwayId }) {
  const { result, status, error } = useSimulation(variantId, pathwayId)
  const { pathway } = usePathway(result?.pathway_id ?? pathwayId)
  const [mode, setMode] = useState('variant') // 'normal' | 'variant'

  const nodeLabels = useMemo(() => {
    if (!pathway) return {}
    return Object.fromEntries(pathway.nodes.map((n) => [n.node_key, n.label]))
  }, [pathway])

  if (status === 'loading' || status === 'idle') {
    return <div className="text-sm text-text-muted font-mono animate-pulse">Running simulation…</div>
  }

  if (status === 'error') {
    return (
      <div className="bg-signal-coral/10 border border-signal-coral/30 rounded-xl p-5 text-sm text-signal-coral">
        Couldn't run the simulation: {error?.message}
      </div>
    )
  }

  if (!result) return null

  const activeActivities = mode === 'normal' ? result.normal : result.variant

  return (
    <div className="space-y-6">
      <Card eyebrow="Simulation" title="Normal vs. variant pathway output">
        <SimulationSummary result={result} />
      </Card>

      <Card eyebrow="Signalling pathway" title="MAPK/ERK pathway">
        <div className="flex items-center gap-2 mb-4">
          <span className="text-xs text-text-muted mr-1">Showing:</span>
          {['normal', 'variant'].map((m) => (
            <button
              key={m}
              onClick={() => setMode(m)}
              className={`px-3 py-1.5 rounded-md text-xs font-mono capitalize transition-colors ${
                mode === m
                  ? 'bg-signal-teal text-ink font-medium'
                  : 'bg-ink border border-ink-border text-text-muted hover:text-text-primary'
              }`}
            >
              {m}
            </button>
          ))}
        </div>
        <PathwayGraph
          pathwayId={result.pathway_id}
          affectedNode={result.affected_node}
          activities={activeActivities}
        />
      </Card>

      <Card eyebrow="Comparison" title="Node activity: normal vs. variant">
        <ActivityBarChart normal={result.normal} variant={result.variant} nodeLabels={nodeLabels} />
      </Card>

      <InterpretationCard result={result} />
    </div>
  )
}
