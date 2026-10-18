export default function Card({ title, eyebrow, children, className = '' }) {
  return (
    <div className={`bg-ink-panel border border-ink-border rounded-xl p-6 ${className}`}>
      {eyebrow && (
        <div className="text-[11px] font-mono uppercase tracking-wider text-signal-teal mb-1.5">
          {eyebrow}
        </div>
      )}
      {title && (
        <h3 className="font-display font-semibold text-lg mb-4">{title}</h3>
      )}
      {children}
    </div>
  )
}
