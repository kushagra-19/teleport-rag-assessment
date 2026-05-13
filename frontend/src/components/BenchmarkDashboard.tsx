import React from 'react'
import { motion } from 'framer-motion'
import { BarChart2, Play, Loader } from 'lucide-react'
import type { BenchmarkEntry } from '../types'

interface Props {
  results: BenchmarkEntry[]
  loading: boolean
  error: string | null
  onRun: () => void
}

export default function BenchmarkDashboard({ results, loading, error, onRun }: Props) {
  return (
    <div className="card space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <BarChart2 size={14} className="text-accent-cyan" />
          <span className="text-xs font-mono text-text-muted uppercase tracking-widest">
            Benchmark Dashboard
          </span>
        </div>
        <button
          onClick={onRun}
          disabled={loading}
          className="btn-primary text-xs py-1.5 px-3"
        >
          {loading ? (
            <>
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                className="w-3 h-3 border-2 border-white/30 border-t-white rounded-full"
              />
              Running...
            </>
          ) : (
            <>
              <Play size={12} />
              Run All 3 Queries
            </>
          )}
        </button>
      </div>

      {error && (
        <div className="text-xs text-accent-red bg-accent-red/10 border border-accent-red/30 rounded-lg px-3 py-2">
          {error}
        </div>
      )}

      {results.length === 0 && !loading && (
        <div className="text-center py-8 text-text-muted text-sm">
          <BarChart2 size={32} className="mx-auto mb-3 opacity-30" />
          <p>Click "Run All 3 Queries" to compare Strategy A vs B</p>
          <p className="text-xs mt-1 text-text-muted/60">
            Runs 3 preset benchmark queries and shows score comparison
          </p>
        </div>
      )}

      {results.length > 0 && (
        <div className="space-y-4">
          {/* Summary table */}
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-border">
                  <th className="text-left py-2 pr-4 text-text-muted font-mono font-medium">Query</th>
                  <th className="text-right py-2 px-3 text-accent-cyan font-mono font-medium">A Score</th>
                  <th className="text-right py-2 px-3 text-accent-violet-glow font-mono font-medium">B Score</th>
                  <th className="text-right py-2 px-3 text-text-muted font-mono font-medium">Δ</th>
                  <th className="text-right py-2 pl-3 text-text-muted font-mono font-medium">B Latency</th>
                </tr>
              </thead>
              <tbody>
                {results.map((entry, i) => {
                  const scoreA = entry.strategy_a?.[0]?.score ?? 0
                  const scoreB = entry.strategy_b?.[0]?.score ?? 0
                  const delta = scoreB - scoreA
                  return (
                    <motion.tr
                      key={i}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: i * 0.1 }}
                      className="border-b border-border/50 hover:bg-bg-hover transition-colors"
                    >
                      <td className="py-3 pr-4 text-text-secondary max-w-[200px] truncate">
                        {entry.query}
                      </td>
                      <td className="py-3 px-3 text-right font-mono text-accent-cyan">
                        {scoreA.toFixed(4)}
                      </td>
                      <td className="py-3 px-3 text-right font-mono text-accent-violet-glow">
                        {scoreB.toFixed(4)}
                      </td>
                      <td className={`py-3 px-3 text-right font-mono ${delta >= 0 ? 'text-accent-green' : 'text-accent-red'}`}>
                        {delta >= 0 ? '+' : ''}{delta.toFixed(4)}
                      </td>
                      <td className="py-3 pl-3 text-right font-mono text-text-muted">
                        {entry.retrieval_time_ms['B'] ?? 0}ms
                      </td>
                    </motion.tr>
                  )
                })}
              </tbody>
            </table>
          </div>

          {/* Per-query expansion terms */}
          <div className="space-y-3">
            <p className="text-[10px] font-mono text-text-muted uppercase tracking-wider">
              Expansion Terms per Query
            </p>
            {results.map((entry, i) => (
              <div key={i} className="space-y-1.5">
                <p className="text-xs text-text-secondary truncate">{entry.query}</p>
                <div className="flex flex-wrap gap-1.5">
                  {(entry.expansion_terms || []).map(term => (
                    <span key={term} className="badge-violet text-[10px]">+ {term}</span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
