import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import PathwayGraph from '../PathwayGraph.jsx'
import * as api from '../../../services/api.js'

vi.mock('../../../services/api.js')

const MOCK_PATHWAY = {
  pathway_id: 'mapk',
  name: 'MAPK/ERK Signalling Pathway (simplified)',
  description: 'test',
  terminal_node: 'CellularResponse',
  nodes: [
    { node_key: 'GrowthFactor', label: 'Growth Factor', baseline_activity: 1.0, position_x: 0, position_y: 150 },
    { node_key: 'RAF', label: 'RAF', baseline_activity: 1.0, position_x: 600, position_y: 150 },
    { node_key: 'CellularResponse', label: 'Cellular Response', baseline_activity: 1.0, position_x: 1200, position_y: 150 },
  ],
  edges: [
    { source: 'GrowthFactor', target: 'RAF', weight: 0.9, interaction_type: 'activation' },
    { source: 'RAF', target: 'CellularResponse', weight: 0.9, interaction_type: 'activation' },
  ],
}

describe('PathwayGraph', () => {
  beforeEach(() => {
    vi.resetAllMocks()
  })

  it('shows a loading state before the pathway loads', () => {
    api.fetchPathway.mockImplementation(() => new Promise(() => {}))
    render(<PathwayGraph pathwayId="mapk" affectedNode="RAF" />)
    expect(screen.getByText(/loading pathway/i)).toBeInTheDocument()
  })

  it('renders all node labels once loaded', async () => {
    api.fetchPathway.mockResolvedValue(MOCK_PATHWAY)
    render(<PathwayGraph pathwayId="mapk" affectedNode="RAF" />)

    await waitFor(() => expect(screen.getByText('RAF')).toBeInTheDocument())
    expect(screen.getByText('Growth Factor')).toBeInTheDocument()
    expect(screen.getByText('Cellular Response')).toBeInTheDocument()
  })

  it('shows an error state if the pathway fails to load', async () => {
    api.fetchPathway.mockRejectedValue(new Error("No pathway found with id 'mapk'."))
    render(<PathwayGraph pathwayId="mapk" affectedNode="RAF" />)

    await waitFor(() =>
      expect(screen.getByText(/couldn't load the pathway graph/i)).toBeInTheDocument()
    )
  })
})
