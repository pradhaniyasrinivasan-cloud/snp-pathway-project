import Card from '../common/Card.jsx'

export default function ProteinCard({ variant }) {
  if (!variant.protein_name) return null

  return (
    <Card eyebrow="Affected protein" title={variant.protein_name}>
      <p className="text-sm text-text-muted leading-relaxed">
        {variant.protein_description || 'No plain-language description available for this protein yet.'}
      </p>
    </Card>
  )
}
