import { useState } from 'react'
import Library from './Library'
import Analysis from './Analysis'

const TABS = ['library', 'analysis']

export default function App() {
  const [tab, setTab] = useState('library')
  const [selectedFile, setSelectedFile] = useState(null)

  function handleAnalyse(file) {
    setSelectedFile(file)
    setTab('analysis')
  }

  return (
    <div className="min-h-screen flex flex-col bg-sp-black text-sp-text font-sans">
      {/* Header */}
      <header className="bg-black border-b border-sp-border px-7 py-4 flex items-center gap-3 flex-shrink-0">
        <span className="text-sp-green font-bold text-base tracking-tight select-none">⬤ Spoti</span>
        <span className="text-sp-muted text-xs">Dashboard</span>
      </header>

      {/* Tab bar */}
      <nav className="bg-sp-surface border-b border-sp-border px-6 flex flex-shrink-0">
        {TABS.map(t => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={[
              'px-5 py-3 text-sm capitalize border-b-2 transition-colors duration-150 outline-none',
              tab === t
                ? 'text-sp-text border-sp-green'
                : 'text-sp-muted border-transparent hover:text-sp-sub',
            ].join(' ')}
          >
            {t}
          </button>
        ))}
      </nav>

      {/* Content */}
      <main className="flex-1 w-full max-w-5xl mx-auto px-7 py-7">
        {tab === 'library' && (
          <Library onAnalyse={handleAnalyse} selectedFile={selectedFile} />
        )}
        {tab === 'analysis' && (
          <Analysis file={selectedFile} />
        )}
      </main>
    </div>
  )
}
