import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
} from 'recharts'

const GREEN = '#1db954'
const MUTED = '#666'
const LABEL = '#b3b3b3'

const tooltipStyle = {
  background: '#1a1a1a',
  border: '1px solid #333',
  borderRadius: 8,
  fontSize: 13,
  color: '#e4e4e4',
}

export default function ArtistChart({ data }) {
  if (!data.length) {
    return <Empty>No artist data.</Empty>
  }

  // Highest count at top → reverse for vertical bar chart
  const reversed = [...data].reverse()
  const height = Math.max(280, reversed.length * 26 + 40)

  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart
        layout="vertical"
        data={reversed}
        margin={{ top: 0, right: 16, bottom: 0, left: 0 }}
      >
        <XAxis
          type="number"
          tick={{ fill: MUTED, fontSize: 11 }}
          axisLine={false}
          tickLine={false}
          allowDecimals={false}
        />
        <YAxis
          type="category"
          dataKey="name"
          width={155}
          tick={{ fill: LABEL, fontSize: 12 }}
          axisLine={false}
          tickLine={false}
        />
        <Tooltip
          cursor={{ fill: '#222' }}
          contentStyle={tooltipStyle}
          labelStyle={{ color: '#e4e4e4', fontWeight: 600 }}
          formatter={v => [v, 'tracks']}
        />
        <Bar dataKey="count" fill={GREEN} radius={[0, 4, 4, 0]} maxBarSize={18} />
      </BarChart>
    </ResponsiveContainer>
  )
}

function Empty({ children }) {
  return (
    <div className="text-sp-muted text-sm text-center py-10">{children}</div>
  )
}
