import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import VariantAnalysis from '../VariantAnalysis.jsx'
import * as api from '../../services/api.js'

vi.mock('../../services/api.js')

function renderAtVariant(variantId) {
  return render(
    <MemoryRouter initialEntries={[`/analyze/${variantId}`]}>
      <Routes>
        <Route path="/analyze/:variantId" element={<VariantAnalysis />} />
      </Routes>
    </MemoryRouter>
  )
}

const MOCK_VARIANT = {
  rsid: 'rs113488022',
  chromosome: '7',
  position: 140753336,
  ref_allele: 'A',
  alt_allele: 'T',
  gene_symbol: 'BRAF',
  consequence: 'missense_variant',
  amino_acid_change: 'V600E',
  source: 'demo',
  has_functional_effect_data: true,
  protein_name: 'Serine/threonine-protein kinase B-raf',
  protein_description: 'This protein relays growth signals inside the cell.',
}

const MOCK_FUNCTIONAL_EFFECT = {
  rsid: 'rs113488022',
  sift_prediction: 'deleterious',
  sift_score: 0.0,
  polyphen_prediction: 'probably_damaging',
  polyphen_score: 0.97,
  clinvar_significance: 'Pathogenic',
  impact_level: 'HIGH',
  perturbation_factor: 1.8,
  perturbation_direction: 'activating',
  affected_node: 'RAF',
  is_modelled: false,
  note: 'Well-characterized variant.',
  source: 'demo',
}

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

describe('VariantAnalysis page', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    api.fetchDemoVariants.mockResolvedValue([])
    api.fetchPathway.mockResolvedValue(MOCK_PATHWAY)
  })

  it('shows a loading state while fetching', async () => {
    api.fetchVariant.mockImplementation(() => new Promise(() => {})) // never resolves
    renderAtVariant('demo-001')
    expect(screen.getByText(/analyzing variant/i)).toBeInTheDocument()
  })

  it('renders variant, protein, and functional-effect data on success', async () => {
    api.fetchVariant.mockResolvedValue(MOCK_VARIANT)
    api.fetchFunctionalEffect.mockResolvedValue(MOCK_FUNCTIONAL_EFFECT)
    api.runSimulation.mockResolvedValue(MOCK_SIMULATION)

    renderAtVariant('demo-001')

    await waitFor(() => expect(screen.getByText('rs113488022')).toBeInTheDocument())
    expect(screen.getByText('BRAF')).toBeInTheDocument()
    expect(screen.getByText('Serine/threonine-protein kinase B-raf')).toBeInTheDocument()
    expect(screen.getByText('HIGH')).toBeInTheDocument()
  })

  it('shows an error message when the lookup fails', async () => {
    api.fetchVariant.mockRejectedValue(new Error("No variant data found for 'rs00000000'."))

    renderAtVariant('rs00000000')

    await waitFor(() =>
      expect(screen.getByText(/no variant data found/i)).toBeInTheDocument()
    )
  })
})
