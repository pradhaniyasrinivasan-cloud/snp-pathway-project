import { Link, useLocation } from 'react-router-dom'

const NAV_LINKS = [
  { to: '/', label: 'Home' },
  { to: '/analyze', label: 'Analyze Variant' },
]

export default function Layout({ children }) {
  const location = useLocation()

  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-ink-border">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2.5 group">
            <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
              <circle cx="11" cy="11" r="9" stroke="#33D6B0" strokeWidth="1.5" />
              <circle cx="11" cy="11" r="2.5" fill="#33D6B0" className="trace-dot" />
            </svg>
            <span className="font-display font-semibold text-[15px] tracking-tight">
              SNPs <span className="text-signal-teal">→</span> Pathways
            </span>
          </Link>

          <nav className="flex items-center gap-1">
            {NAV_LINKS.map((link) => {
              const active = location.pathname === link.to
              return (
                <Link
                  key={link.to}
                  to={link.to}
                  className={`px-3.5 py-1.5 rounded-md text-sm font-medium transition-colors ${
                    active
                      ? 'bg-ink-panel text-signal-teal'
                      : 'text-text-muted hover:text-text-primary'
                  }`}
                >
                  {link.label}
                </Link>
              )
            })}
          </nav>
        </div>
      </header>

      <main className="flex-1">{children}</main>

      <footer className="border-t border-ink-border mt-16">
        <div className="max-w-6xl mx-auto px-6 py-8 text-xs text-text-muted font-mono flex flex-col sm:flex-row justify-between gap-2">
          <span>Academic research demo — computational predictions, not clinical advice.</span>
          <span>Data sources: Ensembl · ClinVar · MyVariant.info · Demo dataset</span>
        </div>
      </footer>
    </div>
  )
}
