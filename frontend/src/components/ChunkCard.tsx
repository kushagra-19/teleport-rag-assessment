import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { ChevronDown, TrendingUp, TrendingDown, Minus } from 'lucide-react'
import type { RetrievalResult } from '../types'

interface Props {
  result: RetrievalResult
  rankInOther?: number | null  // Rank of same chunk in the other strategy (for movement indicator)
  delay?: number
}

const pathColors = {
  faiss: 'badge-cyan',
  bm25: 'badge-amber',
  rrf_fused: 'badge-violet',
} as const

const pathLabels = {
  faiss: 'FAISS',
  bm25: 'BM25',
  rrf_fused: 'RRF Fused',
}

function RankMovement({ currentRank, otherRank }: { currentRank: number; otherRank: number | null | undefined }) {
  if (otherRank == null) {
    return <span className="badge badge-green text-[10px]">NEW</span>
  }
  const diff = otherRank - currentRank
  if (diff > 0) {
    return (
      <span className="flex items-center gap-0.5 text-accent-green text-[10px] font-mono">
        <TrendingUp size={10} />+{diff}
      </span>
    )
  }
  if (diff < 0) {
    return (
      <span className="flex items-center gap-0.5 text-accent-red text-[10px] font-mono">
        <TrendingDown size={10} />{diff}
      </span>
    )
  }
  return (
    <span className="flex items-center gap-0.5 text-text-muted text-[10px] font-mono">
      <Minus size={10} />0
    </span>
  )
}

export default function ChunkCard({ result, rankInOther, delay = 0 }: Props) {
  const [expanded, setExpanded] = useState(false)

  const PREVIEW_LEN = 200
  const needsTruncation = result.chunk.text.length > PREVIEW_LEN
  const displayText = expanded || !needsTruncation
    ? result.chunk.text
    : result.chunk.text.slice(0, PREVIEW_LEN) + '…'

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.3 }}
      className="card-elevated space-y-3 hover:border-border-bright transition-colors duration-200"
    >
      {/* Top row: rank + score + badges */}
      <div className="flex items-center gap-2 flex-wrap">
        {/* Rank badge */}
        <div
          className="flex items-center justify-center w-7 h-7 rounded-lg
                       bg-accent-violet/20 border border-accent-violet/40 text-accent-violet-glow
                       text-xs font-mono font-bold flex-shrink-0"
        >
          #{result.rank}
        </div>

        {/* Score */}
        <div className="flex-1 space-y-1 min-w-[80px]">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-mono text-text-muted">Score</span>
            <span className="text-xs font-mono text-accent-cyan-glow">
              {result.score.toFixed(4)}
            </span>
          </div>
          <div className="score-bar-bg">
            <motion.div
              className="score-bar-fill"
              initial={{ width: 0 }}
              animate={{ width: `${Math.min(result.score * 100, 100)}%` }}
              transition={{ delay: delay + 0.2, duration: 0.6, ease: 'easeOut' }}
            />
          </div>
        </div>

        {/* Retrieval path */}
        <span className={pathColors[result.retrieval_path]}>
          {pathLabels[result.retrieval_path]}
        </span>

        {/* Rank movement (only for Strategy B results) */}
        {result.strategy === 'B' && (
          <RankMovement currentRank={result.rank} otherRank={rankInOther} />
        )}

        {/* Latency */}
        <span className="text-[10px] font-mono text-text-muted ml-auto">
          {result.latency_ms}ms
        </span>
      </div>

      {/* Chunk text */}
      <div className="space-y-2">
        <p className="text-[10px] font-mono text-text-muted uppercase tracking-wider">
          Chunk #{result.chunk.id} · {result.chunk.token_count} tokens
        </p>
        <p className="text-sm text-text-secondary leading-relaxed font-sans">
          {displayText}
        </p>
        {needsTruncation && (
          <button
            onClick={() => setExpanded(e => !e)}
            className="flex items-center gap-1 text-xs text-accent-violet hover:text-accent-violet-glow transition-colors"
          >
            <ChevronDown
              size={12}
              className={`transition-transform duration-200 ${expanded ? 'rotate-180' : ''}`}
            />
            {expanded ? 'Show less' : 'Show full chunk'}
          </button>
        )}
      </div>
    </motion.div>
  )
}
