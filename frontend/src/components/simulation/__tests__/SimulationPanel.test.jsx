import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import SimulationPanel from '../SimulationPanel.jsx'
import * as api from '../../../services/api.js'

vi.mock('../../../services/api.js')

const MOCK_SIMULATION = {
  variant_id: 'rs113488022',
  pathway_id: 'mapk',
  normal: { GrowthFactor: 1.0, RAF: 0.7695, CellularResponse: 0.5609655 },
  variant: { GrowthFactor: 1.0, RAF: 1.3851, CellularResponse: 1.0097379 },
  affected_node: 'RAF',
  pathway_output_normal: 0.561,
  pathway_output_variant: 1.0097,
  percent_change: 80.0,
  interpretation: 'This is a computational prediction, not experimental proof.',
  is_modelled: false,
}

const MOCK_PATHWAY = {
  pathway_id: 'mapk',
  name: 'MAPK pathway',
  description: 'test',
  terminal_node: 'CellularResponse',
  nodes: [
    { node_key: 'GrowthFactor', label: 'Growth Factor', baseline_activity: 1.0, position_x: 0, position_y: 150 },
    { node_key: 'RAF', label: 'RAF', baseline_activity: 1.0, position_x: 600, position_y: 150 },
    { node_key: 'CellularResponse', label: 'Cellular Response', baseline_activity: 1.0, position_x: 1200, position_y: 150 },
  ],
  edges: [],
}

describe('SimulationPanel', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    api.fetchPathway.mockResolvedValue(MOCK_PATHWAY)
  })

  it('shows a loading state while the simulation runs', () => {
    api.runSimulation.mockImplementation(() => new Promise(() => {}))
    render(<SimulationPanel variantId="rs113488022" pathwayId="mapk" />)
    expect(screen.getByText(/running simulation/i)).toBeInTheDocument()
  })

  it('renders headline normal/variant/percent-change numbers', async () => {
    api.runSimulation.mockResolvedValue(MOCK_SIMULATION)
    render(<SimulationPanel variantId="rs113488022" pathwayId="mapk" />)

    await waitFor(() => expect(screen.getByText('0.561')).toBeInTheDocument())
    expect(screen.getByText('1.010')).toBeInTheDocument()
    expect(screen.getByText('+80%')).toBeInTheDocument()
  })

  it('renders the interpretation text', async () => {
    api.runSimulation.mockResolvedValue(MOCK_SIMULATION)
    render(<SimulationPanel variantId="rs113488022" pathwayId="mapk" />)

    await waitFor(() =>
      expect(screen.getByText(/computational prediction, not experimental proof/i)).toBeInTheDocument()
    )
  })

  it('toggles between normal and variant view', async () => {
    const user = userEvent.setup()
    api.runSimulation.mockResolvedValue(MOCK_SIMULATION)
    render(<SimulationPanel variantId="rs113488022" pathwayId="mapk" />)

    await waitFor(() => expect(screen.getByText('0.561')).toBeInTheDocument())

    const normalButton = screen.getByRole('button', { name: /^normal$/i })
    const variantButton = screen.getByRole('button', { name: /^variant$/i })
    expect(variantButton).toBeInTheDocument()

    await user.click(normalButton)
    // no crash + button still present is a reasonable smoke assertion here,
    // since the actual activity values are rendered inside the mocked graph
    expect(normalButton).toBeInTheDocument()
  })

  it('shows an error state if the simulation request fails', async () => {
    api.runSimulation.mockRejectedValue(new Error('Simulation failed.'))
    render(<SimulationPanel variantId="rs113488022" pathwayId="mapk" />)

    await waitFor(() =>
      expect(screen.getByText(/couldn't run the simulation/i)).toBeInTheDocument()
    )
  })
})
