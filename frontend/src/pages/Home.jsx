import { Link } from 'react-router-dom'
import SignalTrace from '../components/common/SignalTrace.jsx'
import Card from '../components/common/Card.jsx'

const WORKFLOW_STEPS = [
  { label: 'DNA variant', detail: 'A single letter of DNA differs from the reference sequence.' },
  { label: 'Gene', detail: 'That change sits inside a gene — the instructions for one protein.' },
  { label: 'Protein', detail: 'The gene\u2019s protein may fold or function slightly differently.' },
  { label: 'Pathway', detail: 'That protein is one link in a chain that relays signals inside the cell.' },
  { label: 'Cell response', detail: 'A change partway down the chain can change the outcome at the end.' },
]

export default function Home() {
  return (
    <div>
      <section className="max-w-6xl mx-auto px-6 pt-16 pb-10">
        <div className="max-w-2xl">
          <div className="text-[11px] font-mono uppercase tracking-wider text-signal-teal mb-4">
            Computational biology · portfolio project
          </div>
          <h1 className="font-display font-semibold text-4xl sm:text-5xl leading-[1.1] tracking-tight">
            A single DNA variant can shift a signal all the way down the chain.
          </h1>
          <p className="mt-5 text-text-muted text-base leading-relaxed">
            This tool takes a genetic variant, predicts how damaging it is to its protein,
            and runs that effect through a computational model of a real cell-signalling
            pathway — so you can see, quantitatively, how one letter of DNA changes what
            a cell does next.
          </p>
          <div className="mt-8 flex items-center gap-4">
            <Link
              to="/analyze"
              className="inline-flex items-center gap-2 bg-signal-teal text-ink font-medium px-5 py-2.5 rounded-lg hover:bg-signal-teal/90 transition-colors"
            >
              Analyze a variant
            </Link>
            <span className="text-xs text-text-muted font-mono">no biology background required</span>
          </div>
        </div>
      </section>

      <section className="max-w-6xl mx-auto px-6 py-8">
        <div className="bg-ink-panel border border-ink-border rounded-xl p-8 sm:p-10">
          <SignalTrace />
        </div>
      </section>

      <section className="max-w-6xl mx-auto px-6 py-14">
        <h2 className="font-display font-semibold text-xl mb-2">How a variant becomes a cellular effect</h2>
        <p className="text-text-muted text-sm mb-8 max-w-xl">
          Five steps, from a single DNA letter to a change in cell behaviour. This is the
          chain the tool actually computes — not a simplification for the homepage.
        </p>
        <div className="grid sm:grid-cols-5 gap-3">
          {WORKFLOW_STEPS.map((step, i) => (
            <div key={step.label} className="relative">
              <Card className="h-full">
                <div className="font-mono text-xs text-signal-teal mb-2">0{i + 1}</div>
                <div className="font-display font-semibold text-sm mb-1.5">{step.label}</div>
                <div className="text-text-muted text-xs leading-relaxed">{step.detail}</div>
              </Card>
            </div>
          ))}
        </div>
      </section>

      <section className="max-w-6xl mx-auto px-6 pb-20">
        <div className="border border-ink-border rounded-xl p-6 bg-ink-panel/40 text-sm text-text-muted leading-relaxed">
          <span className="text-text-primary font-medium">A note on what this tool actually shows: </span>
          every result is labelled as either evidence from a real database (Ensembl, ClinVar,
          MyVariant.info), a prediction from a real tool (SIFT, PolyPhen), or a value from
          our own simplified pathway model. Nothing here is a claim of biological fact —
          it's a computational prediction, clearly marked as such throughout.
        </div>
      </section>
    </div>
  )
}
