import React, { useState, KeyboardEvent } from 'react'
import { motion } from 'framer-motion'
import { Search, Zap, Database, GitCompare } from 'lucide-react'
import type { Strategy } from '../types'

const SUGGESTED = [
  'How does the system handle peak load?',
  'What caching strategies improve system performance?',
  'How is the database scaled for high availability and read performance?',
]

interface Props {
  onSubmit: (query: string, strategy: Strategy, k: number) => void
  loading: boolean
}

const strategyOptions: { value: Strategy; label: string; icon: React.ReactNode; desc: string }[] = [
  {
    value: 'A',
    label: 'Strategy A',
    icon: <Database size={14} />,
    desc: 'Raw Vector Search',
  },
  {
    value: 'B',
    label: 'Strategy B',
    icon: <Zap size={14} />,
    desc: 'AI-Enhanced',
  },
  {
    value: 'both',
    label: 'Compare Both',
    icon: <GitCompare size={14} />,
    desc: 'Side-by-side',
  },
]

export default function QueryPanel({ onSubmit, loading }: Props) {
  const [query, setQuery] = useState('')
  const [strategy, setStrategy] = useState<Strategy>('both')
  const [k, setK] = useState(3)

  const handleSubmit = () => {
    if (query.trim().length < 3 || loading) return
    onSubmit(query.trim(), strategy, k)
  }

  const handleKey = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  return (
    <div className="card space-y-5">
      {/* Header */}
      <div className="flex items-center gap-2">
        <div className="w-2 h-2 rounded-full bg-accent-violet animate-pulse-slow" />
        <span className="text-xs font-mono text-text-muted uppercase tracking-widest">
          Query Interface
        </span>
      </div>

      {/* Textarea */}
      <div className="relative">
        <textarea
          value={query}
          onChange={e => setQuery(e.target.value)}
          onKeyDown={handleKey}
          placeholder="Ask a question about the system architecture..."
          rows={3}
          className="w-full bg-bg-primary border border-border rounded-lg px-4 py-3
                     text-text-primary placeholder-text-muted font-sans text-sm resize-none
                     focus:outline-none focus:border-accent-violet focus:ring-1 focus:ring-accent-violet/30
                     transition-all duration-200"
        />
        <span className="absolute bottom-3 right-3 text-xs text-text-muted font-mono">
          {query.length}/500
        </span>
      </div>

      {/* Suggested queries */}
      <div className="space-y-2">
        <p className="text-xs text-text-muted">Quick queries:</p>
        <div className="flex flex-wrap gap-2">
          {SUGGESTED.map(q => (
            <button
              key={q}
              onClick={() => setQuery(q)}
              className="text-xs px-3 py-1.5 bg-bg-primary border border-border rounded-full
                         text-text-secondary hover:text-text-primary hover:border-accent-violet/50
                         transition-all duration-150"
            >
              {q.length > 45 ? q.slice(0, 42) + '…' : q}
            </button>
          ))}
        </div>
      </div>

      {/* Controls row */}
      <div className="flex flex-wrap items-center gap-3">
        {/* Strategy selector */}
        <div className="flex gap-1 p-1 bg-bg-primary rounded-lg border border-border">
          {strategyOptions.map(opt => (
            <button
              key={opt.value}
              onClick={() => setStrategy(opt.value)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium
                          transition-all duration-200 border
                          ${strategy === opt.value ? 'tab-active' : 'tab-inactive'}`}
            >
              {opt.icon}
              <span>{opt.label}</span>
            </button>
          ))}
        </div>

        {/* Top-K */}
        <div className="flex items-center gap-2 text-xs text-text-secondary">
          <span className="font-mono">Top-K:</span>
          <select
            value={k}
            onChange={e => setK(Number(e.target.value))}
            className="bg-bg-primary border border-border rounded-md px-2 py-1.5 text-text-primary
                       font-mono focus:outline-none focus:border-accent-violet transition-colors"
          >
            {[1, 2, 3, 5, 7, 10].map(n => (
              <option key={n} value={n}>{n}</option>
            ))}
          </select>
        </div>

        {/* Submit */}
        <motion.button
          whileTap={{ scale: 0.97 }}
          onClick={handleSubmit}
          disabled={query.trim().length < 3 || loading}
          className="btn-primary ml-auto"
        >
          {loading ? (
            <>
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full"
              />
              <span>Retrieving...</span>
            </>
          ) : (
            <>
              <Search size={14} />
              <span>Search</span>
            </>
          )}
        </motion.button>
      </div>

      {/* Active strategy description */}
      <p className="text-xs text-text-muted border-t border-border pt-3">
        {strategyOptions.find(o => o.value === strategy)?.desc}
        {strategy === 'A' && ' — embeds query directly → FAISS cosine similarity → top-k chunks'}
        {strategy === 'B' && ' — expands query via AI → FAISS + BM25 → RRF fusion → CrossEncoder rerank'}
        {strategy === 'both' && ' — run both strategies simultaneously and compare results side-by-side'}
      </p>
    </div>
  )
}
