import React from 'react'
import { Database, Zap, Clock } from 'lucide-react'
import type { QueryResponse } from '../types'
import ChunkCard from './ChunkCard'
import ExpansionPanel from './ExpansionPanel'

interface Props {
  response: QueryResponse
}

export default function ComparisonView({ response }: Props) {
  const { strategy_a, strategy_b, expanded_query, expansion_terms, retrieval_time_ms } = response

  // Build a map: chunk_id → rank in Strategy A (for movement indicators in B)
  const rankInA = new Map<number, number>()
  strategy_a?.forEach(r => rankInA.set(r.chunk.id, r.rank))

  const showBoth = strategy_a && strategy_b
  const showA = !!strategy_a
  const showB = !!strategy_b

  return (
    <div className="space-y-5">
      {/* Expansion panel (only when B is active) */}
      {showB && expanded_query && (
        <ExpansionPanel
          originalQuery={response.query}
          expandedQuery={expanded_query}
          expansionTerms={expansion_terms}
        />
      )}

      {/* Results columns */}
      <div className={`grid gap-5 ${showBoth ? 'grid-cols-1 lg:grid-cols-2' : 'grid-cols-1'}`}>
        {/* Strategy A column */}
        {showA && (
          <div className="space-y-3">
            {/* Column header */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Database size={14} className="text-accent-cyan" />
                <span className="text-sm font-medium text-text-primary">Strategy A</span>
                <span className="badge-cyan text-[10px]">Raw Vector Search</span>
              </div>
              <span className="text-[10px] font-mono text-text-muted flex items-center gap-1">
                <Clock size={10} />
                {retrieval_time_ms['A'] ?? 0}ms
              </span>
            </div>

            {/* Pipeline tag */}
            <div className="flex items-center gap-1.5 text-[10px] font-mono text-text-muted">
              <span className="badge-cyan">embed</span>
              <span>→</span>
              <span className="badge-cyan">FAISS</span>
              <span>→</span>
              <span className="badge-cyan">cosine top-k</span>
            </div>

            {/* Results */}
            <div className="space-y-3">
              {strategy_a.map((r, i) => (
                <ChunkCard key={r.chunk.id} result={r} delay={i * 0.08} />
              ))}
            </div>
          </div>
        )}

        {/* Strategy B column */}
        {showB && (
          <div className="space-y-3">
            {/* Column header */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Zap size={14} className="text-accent-violet-glow" />
                <span className="text-sm font-medium text-text-primary">Strategy B</span>
                <span className="badge-violet text-[10px]">AI-Enhanced</span>
              </div>
              <span className="text-[10px] font-mono text-text-muted flex items-center gap-1">
                <Clock size={10} />
                {retrieval_time_ms['B'] ?? 0}ms
              </span>
            </div>

            {/* Pipeline tag */}
            <div className="flex items-center gap-1.5 text-[10px] font-mono text-text-muted flex-wrap">
              <span className="badge-violet">expand</span>
              <span>→</span>
              <span className="badge-violet">FAISS</span>
              <span>+</span>
              <span className="badge-amber">BM25</span>
              <span>→</span>
              <span className="badge-violet">RRF</span>
              <span>→</span>
              <span className="badge-violet">rerank</span>
            </div>

            {/* Results */}
            <div className="space-y-3">
              {strategy_b.map((r, i) => (
                <ChunkCard
                  key={r.chunk.id}
                  result={r}
                  rankInOther={rankInA.get(r.chunk.id)}
                  delay={i * 0.08}
                />
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Score delta summary (only when both are shown) */}
      {showBoth && strategy_a.length > 0 && strategy_b.length > 0 && (
        <div className="card bg-bg-elevated border-border-bright">
          <div className="grid grid-cols-3 gap-4 text-center">
            <div>
              <p className="text-[10px] font-mono text-text-muted mb-1">A Top-1 Score</p>
              <p className="text-lg font-mono text-accent-cyan">
                {strategy_a[0].score.toFixed(4)}
              </p>
            </div>
            <div>
              <p className="text-[10px] font-mono text-text-muted mb-1">Score Δ</p>
              <p className={`text-lg font-mono ${
                strategy_b[0].score >= strategy_a[0].score
                  ? 'text-accent-green'
                  : 'text-accent-red'
              }`}>
                {strategy_b[0].score >= strategy_a[0].score ? '+' : ''}
                {(strategy_b[0].score - strategy_a[0].score).toFixed(4)}
              </p>
            </div>
            <div>
              <p className="text-[10px] font-mono text-text-muted mb-1">B Top-1 Score</p>
              <p className="text-lg font-mono text-accent-violet-glow">
                {strategy_b[0].score.toFixed(4)}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
