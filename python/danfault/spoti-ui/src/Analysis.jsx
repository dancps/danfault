import { useEffect, useState } from 'react'
import ArtistChart from './ArtistChart'
import BpmHistogram from './BpmHistogram'
import BpmTimeline from './BpmTimeline'

export default function Analysis({ file }) {
  const [state, setState] = useState({ status: 'idle', playlist: null, features: null })

  useEffect(() => {
    if (!file) return
    setState({ status: 'loading', playlist: null, features: null })
    Promise.all([
      fetch(`/api/playlist?file=${encodeURIComponent(file)}`).then(r => r.json()),
      fetch(`/api/audio-features?file=${encodeURIComponent(file)}`).then(r => r.json()),
    ]).then(([playlist, features]) => {
      setState({ status: 'ready', playlist, features })
    }).catch(() => {
      setState({ status: 'error', playlist: null, features: null })
    })
  }, [file])

  if (!file) {
    return (
      <div className="text-sp-muted text-sm text-center py-20">
        ← Pick a playlist in the Library tab.
      </div>
    )
  }

  if (state.status === 'loading') {
    return (
      <div className="text-sp-muted text-sm text-center py-20">
        Fetching audio features…
      </div>
    )
  }

  if (state.status === 'error') {
    return (
      <div className="text-sp-muted text-sm text-center py-20">
        Failed to load playlist data.
      </div>
    )
  }

  const { playlist, features } = state
  const tracks = playlist?.tracks ?? []
  const pl = playlist?.playlist ?? {}

  // Resolve BPM for a track: enriched field → embedded Spotify features → live API features
  const getBpm = t => {
    if (t.bpm != null) return t.bpm
    const f = t.features ?? features?.[t.id]
    return f?.tempo ?? null
  }

  // Artist distribution
  const ac = {}
  tracks.forEach(t =>
    (t.artists ?? []).forEach(a => { ac[a.name] = (ac[a.name] ?? 0) + 1 })
  )
  const artistData = Object.entries(ac)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 25)
    .map(([name, count]) => ({ name, count }))

  // BPM series (original playlist order, skipping tracks without data)
  const bpmData = tracks.reduce((acc, t, i) => {
    const bpm = getBpm(t)
    if (bpm == null) return acc
    acc.push({
      position: i + 1,
      bpm: Math.round(bpm * 10) / 10,
      name: t.name,
      artist: (t.artists ?? []).map(a => a.name).join(', '),
      source: t.bpm_source ?? 'spotify',
    })
    return acc
  }, [])

  return (
    <div>
      <div className="mb-7">
        <h2 className="text-lg font-semibold text-sp-text">{pl.name}</h2>
        <p className="text-sm text-sp-muted mt-1">{pl.total} tracks · {pl.owner}</p>
      </div>

      <div className="flex flex-col gap-5">
        <ChartCard title="Artist Distribution" badge="top 25">
          <ArtistChart data={artistData} />
        </ChartCard>

        <ChartCard title="BPM Distribution">
          <BpmHistogram bpmValues={bpmData.map(d => d.bpm)} />
        </ChartCard>

        <ChartCard title="BPM Over Playlist">
          <BpmTimeline data={bpmData} />
        </ChartCard>
      </div>
    </div>
  )
}

function ChartCard({ title, badge, children }) {
  return (
    <div className="bg-sp-surface rounded-xl p-6">
      <div className="flex items-baseline gap-2 mb-5">
        <h3 className="text-xs font-bold uppercase tracking-widest text-sp-muted">{title}</h3>
        {badge && (
          <span className="text-xs text-sp-green font-medium">{badge}</span>
        )}
      </div>
      {children}
    </div>
  )
}
