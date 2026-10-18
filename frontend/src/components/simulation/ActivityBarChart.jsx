import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts'

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-ink-panel border border-ink-border rounded-lg px-3 py-2 text-xs font-mono">
      <div className="text-text-primary mb-1">{label}</div>
      {payload.map((p) => (
        <div key={p.dataKey} style={{ color: p.color }}>
          {p.name}: {p.value.toFixed(3)}
        </div>
      ))}
    </div>
  )
}

export default function ActivityBarChart({ normal, variant, nodeLabels }) {
  const nodeKeys = Object.keys(normal)
  const data = nodeKeys.map((key) => ({
    key,
    label: nodeLabels?.[key] || key,
    Normal: normal[key],
    Variant: variant[key],
  }))

  return (
    <div style={{ width: '100%', height: 260 }}>
      <ResponsiveContainer>
        <BarChart data={data} margin={{ top: 8, right: 8, left: -12, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1E3040" vertical={false} />
          <XAxis
            dataKey="label"
            tick={{ fill: '#7E93A0', fontSize: 11, fontFamily: 'IBM Plex Mono, monospace' }}
            axisLine={{ stroke: '#1E3040' }}
            tickLine={false}
          />
          <YAxis
            tick={{ fill: '#7E93A0', fontSize: 11, fontFamily: 'IBM Plex Mono, monospace' }}
            axisLine={{ stroke: '#1E3040' }}
            tickLine={false}
          />
          <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.03)' }} />
          <Legend
            wrapperStyle={{ fontSize: 12, fontFamily: 'IBM Plex Mono, monospace', color: '#7E93A0' }}
          />
          <Bar dataKey="Normal" fill="#1D8A72" radius={[3, 3, 0, 0]} />
          <Bar dataKey="Variant" fill="#FF6B6B" radius={[3, 3, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
