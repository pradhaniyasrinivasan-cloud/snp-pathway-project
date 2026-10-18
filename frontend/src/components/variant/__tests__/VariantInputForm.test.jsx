import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import VariantInputForm from '../VariantInputForm.jsx'

vi.mock('../../../services/api.js', () => ({
  fetchDemoVariants: vi.fn(() =>
    Promise.resolve([
      { variant_id: 'demo-001', gene_symbol: 'BRAF', amino_acid_change: 'V600E', impact_level: 'HIGH' },
      { variant_id: 'demo-004', gene_symbol: 'MAP2K1', amino_acid_change: 'L115L', impact_level: 'LOW' },
    ])
  ),
}))

describe('VariantInputForm', () => {
  it('submits a manually entered rsID', async () => {
    const user = userEvent.setup()
    const onSubmit = vi.fn()
    render(<VariantInputForm onSubmit={onSubmit} isLoading={false} />)

    const input = screen.getByPlaceholderText('rs113488022')
    await user.type(input, 'rs113488022')
    await user.click(screen.getByRole('button', { name: /analyze/i }))

    expect(onSubmit).toHaveBeenCalledWith('rs113488022')
  })

  it('does not submit an empty rsID', async () => {
    const user = userEvent.setup()
    const onSubmit = vi.fn()
    render(<VariantInputForm onSubmit={onSubmit} isLoading={false} />)

    const button = screen.getByRole('button', { name: /analyze/i })
    expect(button).toBeDisabled()
    await user.click(button)
    expect(onSubmit).not.toHaveBeenCalled()
  })

  it('loads and displays demo variants, and submits on click', async () => {
    const user = userEvent.setup()
    const onSubmit = vi.fn()
    render(<VariantInputForm onSubmit={onSubmit} isLoading={false} />)

    await waitFor(() => expect(screen.getByText('BRAF')).toBeInTheDocument())
    expect(screen.getByText('MAP2K1')).toBeInTheDocument()

    await user.click(screen.getByText('BRAF').closest('button'))
    expect(onSubmit).toHaveBeenCalledWith('demo-001')
  })
})
