import { useEffect, useState } from 'react'

export default function Library({ onAnalyse, selectedFile }) {
  const [playlists, setPlaylists] = useState(null)

  useEffect(() => {
    fetch('/api/playlists')
      .then(r => r.json())
      .then(setPlaylists)
      .catch(() => setPlaylists([]))
  }, [])

  if (playlists === null) {
    return <Placeholder>Loading…</Placeholder>
  }

  if (!playlists.length) {
    return (
      <Placeholder>
        <p>No exported playlists found.</p>
        <p className="mt-3">
          <code className="bg-sp-surface2 text-sp-sub px-2 py-1 rounded text-xs">
            spoti playlist-export "my playlist"
          </code>
        </p>
      </Placeholder>
    )
  }

  return (
    <div className="grid gap-4" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))' }}>
      {playlists.map(p => (
        <PlaylistCard
          key={p.file}
          playlist={p}
          selected={selectedFile === p.file}
          onAnalyse={() => onAnalyse(p.file)}
        />
      ))}
    </div>
  )
}

function PlaylistCard({ playlist, selected, onAnalyse }) {
  return (
    <div
      className={[
        'bg-sp-surface rounded-xl p-5 flex flex-col border-2 transition-all duration-150',
        selected ? 'border-sp-green' : 'border-transparent hover:bg-sp-surface2',
      ].join(' ')}
    >
      <div
        className="font-semibold text-sm truncate mb-1 text-sp-text"
        title={playlist.name}
      >
        {playlist.name}
      </div>
      <div className="text-xs text-sp-muted flex-1 mb-4">
        {playlist.total} tracks · {playlist.owner}
      </div>
      <button
        onClick={onAnalyse}
        className="w-full bg-sp-green text-black text-xs font-bold rounded-full py-2 hover:bg-sp-greenhov transition-colors duration-150"
      >
        Analyse →
      </button>
    </div>
  )
}

function Placeholder({ children }) {
  return (
    <div className="text-sp-muted text-sm text-center py-20 leading-relaxed">
      {children}
    </div>
  )
}
