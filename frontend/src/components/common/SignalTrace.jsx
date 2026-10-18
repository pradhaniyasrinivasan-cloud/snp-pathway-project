/**
 * The signature visual for this project: a signal trace that runs flat
 * and steady, then is visibly perturbed at the point a variant enters
 * the pathway, then continues downstream at an altered level. It's a
 * literal rendering of what the whole app computes -- not decoration.
 */
export default function SignalTrace() {
  const nodeLabels = ['Growth Factor', 'Receptor', 'RAS', 'RAF', 'MEK', 'ERK', 'Response']
  const nodeX = [40, 190, 340, 490, 640, 790, 940]

  return (
    <div className="w-full overflow-hidden">
      <svg
        viewBox="0 0 1000 220"
        className="w-full h-auto"
        role="img"
        aria-label="Diagram showing a signal trace running steady through Growth Factor, Receptor, and RAS, then sharply perturbed at RAF, continuing at an altered level through MEK, ERK, and the cellular response."
      >
        <defs>
          <linearGradient id="traceFade" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="#33D6B0" stopOpacity="0.9" />
            <stop offset="42%" stopColor="#33D6B0" stopOpacity="0.9" />
            <stop offset="46%" stopColor="#FF6B6B" stopOpacity="1" />
            <stop offset="100%" stopColor="#FF6B6B" stopOpacity="0.9" />
          </linearGradient>
        </defs>

        {/* baseline grid */}
        <line x1="0" y1="110" x2="1000" y2="110" stroke="#1E3040" strokeWidth="1" strokeDasharray="2 6" />

        {/* the perturbation marker */}
        <line x1="490" y1="20" x2="490" y2="200" stroke="#FF6B6B" strokeWidth="1" strokeDasharray="3 4" opacity="0.5" />
        <text x="498" y="34" fill="#FF6B6B" fontSize="11" fontFamily="IBM Plex Mono, monospace">
          variant introduced
        </text>

        {/* the trace itself: steady, then perturbed */}
        <path
          d="M 20,112
             C 80,108 130,116 190,110
             C 250,104 300,114 340,110
             C 390,106 440,112 490,110
             C 520,60 560,44 640,50
             C 700,54 740,42 790,46
             C 850,50 900,40 980,44"
          fill="none"
          stroke="url(#traceFade)"
          strokeWidth="2.5"
          strokeLinecap="round"
        />

        {/* traveling pulse dot along the trace */}
        <circle r="4" fill="#EAF3F1" className="trace-dot">
          <animateMotion
            dur="6s"
            repeatCount="indefinite"
            path="M 20,112
                  C 80,108 130,116 190,110
                  C 250,104 300,114 340,110
                  C 390,106 440,112 490,110
                  C 520,60 560,44 640,50
                  C 700,54 740,42 790,46
                  C 850,50 900,40 980,44"
          />
        </circle>

        {/* node ticks + labels */}
        {nodeX.map((x, i) => (
          <g key={nodeLabels[i]}>
            <circle
              cx={x}
              cy={i <= 3 ? 110 : 48}
              r="3"
              fill={i <= 2 ? '#33D6B0' : i === 3 ? '#FF6B6B' : '#FF6B6B'}
            />
            <text
              x={x}
              y="196"
              fill="#7E93A0"
              fontSize="11"
              fontFamily="IBM Plex Mono, monospace"
              textAnchor="middle"
            >
              {nodeLabels[i]}
            </text>
          </g>
        ))}
      </svg>
    </div>
  )
}
