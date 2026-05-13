import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ChevronDown, Sparkles, ArrowRight } from 'lucide-react'

interface Props {
  originalQuery: string
  expandedQuery: string
  expansionTerms: string[]
}

export default function ExpansionPanel({ originalQuery, expandedQuery, expansionTerms }: Props) {
  const [open, setOpen] = useState(true)

  return (
    <div className="card border-accent-violet/30 bg-bg-surface">
      {/* Header */}
      <button
        onClick={() => setOpen(o => !o)}
        className="flex items-center justify-between w-full text-left group"
      >
        <div className="flex items-center gap-2">
          <Sparkles size={14} className="text-accent-violet-glow" />
          <span className="text-xs font-mono text-accent-violet-glow uppercase tracking-widest">
            AI Query Expansion
          </span>
          <span className="badge-violet text-[10px]">Strategy B</span>
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
            <div className="mt-4 space-y-4">
              {/* Original → Expanded */}
              <div className="grid grid-cols-1 md:grid-cols-[1fr_auto_1fr] gap-3 items-start">
                {/* Original */}
                <div className="space-y-1.5">
                  <p className="text-[10px] font-mono text-text-muted uppercase tracking-wider">
                    Original Query
                  </p>
                  <div className="bg-bg-primary border border-border rounded-lg px-3 py-2.5">
                    <p className="text-sm text-text-secondary font-sans">{originalQuery}</p>
                  </div>
                </div>

                {/* Arrow */}
                <div className="flex items-center justify-center pt-6">
                  <ArrowRight size={16} className="text-accent-violet opacity-60" />
                </div>

                {/* Expanded */}
                <div className="space-y-1.5">
                  <p className="text-[10px] font-mono text-accent-violet-glow uppercase tracking-wider">
                    AI-Expanded Query
                  </p>
                  <div className="bg-accent-violet/5 border border-accent-violet/25 rounded-lg px-3 py-2.5">
                    <p className="text-sm text-text-primary font-sans">{expandedQuery}</p>
                  </div>
                </div>
              </div>

              {/* Expansion terms */}
              {expansionTerms.length > 0 && (
                <div className="space-y-2">
                  <p className="text-[10px] font-mono text-text-muted uppercase tracking-wider">
                    Terms added by expansion
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {expansionTerms.map(term => (
                      <span key={term} className="badge-violet text-xs">
                        + {term}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Explanation */}
              <p className="text-xs text-text-muted leading-relaxed border-t border-border pt-3">
                <span className="text-text-secondary">Why this improves retrieval:</span>{' '}
                The user's vocabulary may not match exact corpus terminology. Expansion bridges this
                gap — "peak load" maps to "traffic spikes, autoscaling, burst events" in the corpus.
                The expanded query is then embedded for semantic search, while the original drives BM25
                for exact-term coverage.
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
