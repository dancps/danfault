import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
} from 'recharts'

const GREEN = '#1db954'
const MUTED = '#666'

const tooltipStyle = {
  background: '#1a1a1a',
  border: '1px solid #333',
  borderRadius: 8,
  fontSize: 13,
  color: '#e4e4e4',
}

function buildBins(values, numBins = 20) {
  if (!values.length) return []
  const min = Math.floor(Math.min(...values))
  const max = Math.ceil(Math.max(...values))
  const step = Math.max(1, Math.ceil((max - min) / numBins))
  const bins = []
  for (let lo = min; lo < max; lo += step) {
    const hi = lo + step
    const count = values.filter(v => v >= lo && v < hi).length
    if (count > 0) bins.push({ label: `${lo}–${hi}`, lo, count })
  }
  return bins
}

export default function BpmHistogram({ bpmValues }) {
  const bins = buildBins(bpmValues)

  if (!bins.length) {
    return (
      <div className="text-sp-muted text-sm text-center py-10">
        No BPM data — audio features unavailable for this playlist.
      </div>
    )
  }

  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={bins} margin={{ top: 0, right: 16, bottom: 0, left: 0 }}>
        <XAxis
          dataKey="label"
          tick={{ fill: MUTED, fontSize: 11 }}
          axisLine={false}
          tickLine={false}
          interval="preserveStartEnd"
        />
        <YAxis
          tick={{ fill: MUTED, fontSize: 11 }}
          axisLine={false}
          tickLine={false}
          allowDecimals={false}
        />
        <Tooltip
          cursor={{ fill: '#222' }}
          contentStyle={tooltipStyle}
          labelStyle={{ color: '#e4e4e4', fontWeight: 600 }}
          formatter={v => [v, 'tracks']}
        />
        <Bar dataKey="count" fill={GREEN} radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  )
}
