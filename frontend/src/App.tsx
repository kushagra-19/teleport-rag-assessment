import React, { useEffect } from 'react'
import { motion } from 'framer-motion'
import { Activity } from 'lucide-react'

import QueryPanel from './components/QueryPanel'
import ComparisonView from './components/ComparisonView'
import BenchmarkDashboard from './components/BenchmarkDashboard'
import SystemInfo from './components/SystemInfo'
import CorpusExplorer from './components/CorpusExplorer'

import {
  useQueryEngine,
  useSystemInfo,
  useCorpus,
  useBenchmark,
} from './hooks/useQuery'
import type { Strategy } from './types'

export default function App() {
  const { loading: queryLoading, error: queryError, result, runQuery } = useQueryEngine()
  const { info, loading: infoLoading, fetchInfo } = useSystemInfo()
  const { chunks, loading: corpusLoading, fetchCorpus } = useCorpus()
  const { loading: benchLoading, error: benchError, results: benchResults, runBenchmark } = useBenchmark()

  useEffect(() => {
    fetchInfo()
    fetchCorpus()
  }, [])

  const handleQuery = (query: string, strategy: Strategy, k: number) => {
    runQuery(query, strategy, k)
  }

  return (
    <div className="min-h-screen bg-bg-primary text-text-primary">
      {/* Top bar */}
      <header className="sticky top-0 z-30 bg-bg-primary/80 backdrop-blur border-b border-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-3">
            {/* Logo mark */}
            <div className="relative w-7 h-7">
              <div className="absolute inset-0 bg-accent-violet/30 rounded-lg blur-sm" />
              <div className="relative w-7 h-7 bg-bg-elevated border border-accent-violet/50 rounded-lg flex items-center justify-center">
                <Activity size={14} className="text-accent-violet-glow" />
              </div>
            </div>
            <div>
              <h1 className="text-sm font-semibold text-text-primary tracking-tight">
                RAG Intelligence Engine
              </h1>
              <p className="text-[10px] text-text-muted font-mono hidden sm:block">
                Semantic Retrieval · Strategy A vs B · GCP Vertex AI Simulation
              </p>
            </div>
          </div>

          {/* Right side */}
          <div className="flex items-center gap-2">
            {info && (
              <div className="hidden md:flex items-center gap-3 text-[10px] font-mono text-text-muted">
                <span className="flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-accent-green animate-pulse-slow" />
                  {info.doc_count} docs indexed
                </span>
                <span className="text-border">|</span>
                <span>{info.embedding_dim}d embeddings</span>
              </div>
            )}
            <SystemInfo info={info} loading={infoLoading} />
          </div>
        </div>
      </header>

      {/* Main */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-6 space-y-5">
        {/* Query panel */}
        <QueryPanel onSubmit={handleQuery} loading={queryLoading} />

        {/* Error */}
        {queryError && (
          <div className="text-xs text-accent-red bg-accent-red/10 border border-accent-red/30 rounded-lg px-4 py-3">
            {queryError}
          </div>
        )}

        {/* Results */}
        {result && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
          >
            {/* Query echo */}
            <div className="flex items-center gap-2 mb-4">
              <span className="text-[10px] font-mono text-text-muted uppercase tracking-wider">
                Results for:
              </span>
              <span className="text-sm text-text-secondary">"{result.query}"</span>
            </div>
            <ComparisonView response={result} />
          </motion.div>
        )}

        {/* Empty state */}
        {!result && !queryLoading && (
          <div className="card-elevated text-center py-16 space-y-3">
            <div className="w-12 h-12 rounded-xl bg-accent-violet/10 border border-accent-violet/20
                           flex items-center justify-center mx-auto">
              <Activity size={20} className="text-accent-violet/60" />
            </div>
            <p className="text-sm text-text-secondary">Enter a query to see Strategy A vs B comparison</p>
            <p className="text-xs text-text-muted max-w-md mx-auto">
              Use "Compare Both" to see the strategies side-by-side, including query expansion,
              retrieval scores, and ranking differences.
            </p>
          </div>
        )}

        {/* Benchmark dashboard */}
        <BenchmarkDashboard
          results={benchResults}
          loading={benchLoading}
          error={benchError}
          onRun={runBenchmark}
        />

        {/* Corpus explorer */}
        <CorpusExplorer chunks={chunks} loading={corpusLoading} />
      </main>

      {/* Footer */}
      <footer className="border-t border-border mt-12 py-4">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 flex items-center justify-between text-[10px] font-mono text-text-muted">
          <span>RAG Intelligence Engine · Senior GenAI Assessment</span>
          <span>sentence-transformers · FAISS · BM25 · CrossEncoder · RRF</span>
        </div>
      </footer>
    </div>
  )
}
