import {
  LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid,
  ResponsiveContainer, ReferenceLine,
} from 'recharts'

const GREEN = '#1db954'
const MUTED = '#666'
const GRID = '#222'

function CustomTooltip({ active, payload }) {
  if (!active || !payload?.length) return null
  const d = payload[0].payload
  return (
    <div className="bg-sp-surface border border-sp-border rounded-lg px-3 py-2 text-sm shadow-xl">
      <p className="font-semibold text-sp-text leading-tight">{d.name}</p>
      <p className="text-sp-muted text-xs mt-0.5">{d.artist}</p>
      <p className="text-sp-green font-bold mt-1.5">{d.bpm} BPM</p>
      <p className="text-sp-muted text-xs">#{d.position}</p>
    </div>
  )
}

export default function BpmTimeline({ data }) {
  if (!data.length) {
    return (
      <div className="text-sp-muted text-sm text-center py-10">
        No BPM data — audio features unavailable for this playlist.
      </div>
    )
  }

  const bpms = data.map(d => d.bpm)
  const avg = Math.round(bpms.reduce((s, v) => s + v, 0) / bpms.length)

  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={data} margin={{ top: 4, right: 16, bottom: 0, left: 0 }}>
        <CartesianGrid stroke={GRID} strokeDasharray="0" vertical={false} />
        <XAxis
          dataKey="position"
          tick={{ fill: MUTED, fontSize: 11 }}
          axisLine={false}
          tickLine={false}
          label={{ value: 'Track #', position: 'insideBottomRight', offset: -4, fill: MUTED, fontSize: 11 }}
        />
        <YAxis
          tick={{ fill: MUTED, fontSize: 11 }}
          axisLine={false}
          tickLine={false}
          domain={['auto', 'auto']}
          label={{ value: 'BPM', angle: -90, position: 'insideLeft', offset: 12, fill: MUTED, fontSize: 11 }}
        />
        <ReferenceLine
          y={avg}
          stroke="#444"
          strokeDasharray="4 4"
          label={{ value: `avg ${avg}`, position: 'right', fill: MUTED, fontSize: 11 }}
        />
        <Tooltip content={<CustomTooltip />} />
        <Line
          type="monotone"
          dataKey="bpm"
          stroke={GREEN}
          strokeWidth={1.5}
          dot={{ r: 3, fill: GREEN, strokeWidth: 0 }}
          activeDot={{ r: 5, fill: GREEN, strokeWidth: 0 }}
        />
      </LineChart>
    </ResponsiveContainer>
  )
}
