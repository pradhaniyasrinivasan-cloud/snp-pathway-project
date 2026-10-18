import { useMemo, useState, useCallback } from 'react'
import ReactFlow, { Background, Controls, MarkerType } from 'reactflow'
import 'reactflow/dist/style.css'
import PathwayFlowNode from './PathwayFlowNode.jsx'
import NodeDetailPanel from './NodeDetailPanel.jsx'
import { usePathway } from '../../hooks/usePathway.js'

const NODE_TYPES = { pathwayNode: PathwayFlowNode }

function buildFlowElements(pathway, affectedNode, selectedNodeKey, activities) {
  const nodes = pathway.nodes.map((n) => ({
    id: n.node_key,
    type: 'pathwayNode',
    position: { x: n.position_x ?? 0, y: n.position_y ?? 0 },
    data: {
      label: n.label,
      isAffected: n.node_key === affectedNode,
      isSelected: n.node_key === selectedNodeKey,
      activity: activities ? activities[n.node_key] : undefined,
    },
    draggable: true,
  }))

  const edges = pathway.edges.map((e) => {
    const isInhibition = e.interaction_type === 'inhibition'
    const color = isInhibition ? '#F2A93B' : '#33D6B0'
    return {
      id: `${e.source}-${e.target}`,
      source: e.source,
      target: e.target,
      animated: e.target === affectedNode,
      style: { stroke: color, strokeWidth: 1.75, strokeDasharray: isInhibition ? '4 4' : undefined },
      markerEnd: { type: MarkerType.ArrowClosed, color },
    }
  })

  return { nodes, edges }
}

export default function PathwayGraph({ pathwayId, affectedNode, activities }) {
  const { pathway, status, error } = usePathway(pathwayId)
  const [selectedNodeKey, setSelectedNodeKey] = useState(null)

  const { nodes, edges } = useMemo(() => {
    if (!pathway) return { nodes: [], edges: [] }
    return buildFlowElements(pathway, affectedNode, selectedNodeKey, activities)
  }, [pathway, affectedNode, selectedNodeKey, activities])

  const handleNodeClick = useCallback((_, node) => {
    setSelectedNodeKey((prev) => (prev === node.id ? null : node.id))
  }, [])

  const selectedNode = pathway?.nodes.find((n) => n.node_key === selectedNodeKey) ?? null

  if (status === 'loading' || status === 'idle') {
    return <div className="text-sm text-text-muted font-mono animate-pulse">Loading pathway…</div>
  }

  if (status === 'error') {
    return (
      <div className="bg-signal-coral/10 border border-signal-coral/30 rounded-xl p-5 text-sm text-signal-coral">
        Couldn't load the pathway graph: {error?.message}
      </div>
    )
  }

  return (
    <div className="relative">
      <div style={{ height: 340 }} className="rounded-lg overflow-hidden border border-ink-border bg-ink">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          nodeTypes={NODE_TYPES}
          onNodeClick={handleNodeClick}
          fitView
          fitViewOptions={{ padding: 0.3 }}
          proOptions={{ hideAttribution: true }}
          minZoom={0.4}
          maxZoom={2}
        >
          <Background color="#1E3040" gap={20} size={1} />
          <Controls showInteractive={false} />
        </ReactFlow>
      </div>

      <NodeDetailPanel
        node={selectedNode}
        isAffected={selectedNode?.node_key === affectedNode}
        onClose={() => setSelectedNodeKey(null)}
      />

      <div className="flex items-center gap-5 mt-3 text-xs text-text-muted font-mono">
        <span className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full border-2 border-signal-tealDim" />
          Unaffected node
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full border-2 border-signal-coral" />
          Affected node
        </span>
        <span className="text-text-muted/60">Click a node for details · drag to rearrange · scroll to zoom</span>
      </div>
    </div>
  )
}
