import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { BookOpen, ChevronDown, Search } from 'lucide-react'
import type { Chunk } from '../types'

interface Props {
  chunks: Chunk[]
  loading: boolean
}

export default function CorpusExplorer({ chunks, loading }: Props) {
  const [open, setOpen] = useState(false)
  const [filter, setFilter] = useState('')
  const [expanded, setExpanded] = useState<number | null>(null)

  const filtered = chunks.filter(c =>
    filter.trim() === '' || c.text.toLowerCase().includes(filter.toLowerCase())
  )

  return (
    <div className="card">
      <button
        onClick={() => setOpen(o => !o)}
        className="flex items-center justify-between w-full text-left"
      >
        <div className="flex items-center gap-2">
          <BookOpen size={14} className="text-accent-cyan" />
          <span className="text-xs font-mono text-text-muted uppercase tracking-widest">
            Corpus Explorer
          </span>
          <span className="badge-cyan text-[10px]">{chunks.length} chunks</span>
        </div>
        <ChevronDown
          size={14}
          className={`text-text-muted transition-transform duration-200 ${open ? 'rotate-180' : ''}`}
        />
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="mt-4 space-y-3">
              {/* Search filter */}
              <div className="relative">
                <Search size={12} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" />
                <input
                  value={filter}
                  onChange={e => setFilter(e.target.value)}
                  placeholder="Filter chunks..."
                  className="w-full bg-bg-primary border border-border rounded-lg pl-8 pr-3 py-2
                             text-xs text-text-primary placeholder-text-muted font-mono
                             focus:outline-none focus:border-accent-violet transition-colors"
                />
              </div>

              {loading && <p className="text-xs text-text-muted">Loading corpus...</p>}

              {/* Chunk list */}
              <div className="space-y-2 max-h-96 overflow-y-auto pr-1">
                {filtered.map((chunk, i) => (
                  <div
                    key={chunk.id}
                    className="bg-bg-primary border border-border rounded-lg overflow-hidden"
                  >
                    <button
                      onClick={() => setExpanded(expanded === chunk.id ? null : chunk.id)}
                      className="w-full flex items-center gap-3 px-3 py-2.5 text-left hover:bg-bg-hover transition-colors"
                    >
                      <span className="text-[10px] font-mono text-accent-violet-glow w-6 flex-shrink-0">
                        #{chunk.id}
                      </span>
                      <p className="text-xs text-text-secondary flex-1 truncate">
                        {chunk.text.slice(0, 80)}…
                      </p>
                      <span className="text-[10px] font-mono text-text-muted flex-shrink-0">
                        {chunk.token_count}w
                      </span>
                      <ChevronDown
                        size={10}
                        className={`text-text-muted flex-shrink-0 transition-transform duration-150
                          ${expanded === chunk.id ? 'rotate-180' : ''}`}
                      />
                    </button>

                    <AnimatePresence>
                      {expanded === chunk.id && (
                        <motion.div
                          initial={{ height: 0 }}
                          animate={{ height: 'auto' }}
                          exit={{ height: 0 }}
                          className="overflow-hidden border-t border-border"
                        >
                          <p className="px-3 py-3 text-xs text-text-secondary leading-relaxed font-sans">
                            {chunk.text}
                          </p>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                ))}

                {filtered.length === 0 && (
                  <p className="text-xs text-text-muted text-center py-4">
                    No chunks match your filter.
                  </p>
                )}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
