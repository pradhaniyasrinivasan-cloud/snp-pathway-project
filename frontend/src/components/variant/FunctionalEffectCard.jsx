import Card from '../common/Card.jsx'
import { ImpactBadge, SourceBadge } from '../common/Badge.jsx'

function ScoreRow({ label, prediction, score }) {
  if (prediction == null && score == null) {
    return (
      <div className="flex items-center justify-between py-2 border-b border-ink-border last:border-0">
        <span className="text-sm text-text-muted">{label}</span>
        <span className="text-sm font-mono text-text-muted">not available</span>
      </div>
    )
  }
  return (
    <div className="flex items-center justify-between py-2 border-b border-ink-border last:border-0">
      <span className="text-sm text-text-muted">{label}</span>
      <span className="text-sm font-mono">
        {prediction}
        {score != null && <span className="text-text-muted ml-2">({score})</span>}
      </span>
    </div>
  )
}

export default function FunctionalEffectCard({ effect }) {
  return (
    <Card>
      <div className="flex items-start justify-between mb-4">
        <h3 className="font-display font-semibold text-lg">Functional effect</h3>
        <div className="flex flex-col items-end gap-2">
          <ImpactBadge level={effect.impact_level} />
          <SourceBadge isModelled={effect.is_modelled} />
        </div>
      </div>

      <div className="mb-4">
        <ScoreRow label="SIFT" prediction={effect.sift_prediction} score={effect.sift_score} />
        <ScoreRow label="PolyPhen" prediction={effect.polyphen_prediction} score={effect.polyphen_score} />
        <ScoreRow label="ClinVar significance" prediction={effect.clinvar_significance} />
      </div>

      <div className="bg-ink border border-ink-border rounded-lg p-4 text-sm text-text-muted leading-relaxed">
        {effect.note}
      </div>
    </Card>
  )
}
