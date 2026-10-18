import Card from '../common/Card.jsx'

function Field({ label, value, mono = true }) {
  return (
    <div>
      <div className="text-[11px] text-text-muted uppercase tracking-wide mb-1">{label}</div>
      <div className={`text-sm ${mono ? 'font-mono' : ''}`}>{value ?? '—'}</div>
    </div>
  )
}

export default function VariantCard({ variant }) {
  return (
    <Card eyebrow={`Source: ${variant.source}`} title="Variant information">
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-5">
        <Field label="rsID" value={variant.rsid} />
        <Field label="Gene" value={variant.gene_symbol} />
        <Field label="Chromosome" value={variant.chromosome} />
        <Field label="Position" value={variant.position} />
        <Field label="Reference allele" value={variant.ref_allele} />
        <Field label="Alternate allele" value={variant.alt_allele} />
        <Field label="Consequence" value={variant.consequence} mono={false} />
        <Field label="Amino acid change" value={variant.amino_acid_change} />
      </div>
    </Card>
  )
}
