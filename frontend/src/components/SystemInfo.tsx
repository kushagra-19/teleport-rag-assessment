import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Info, X, Cpu, Database, Layers, Zap } from 'lucide-react'
import type { SystemInfo as SystemInfoType } from '../types'

interface Props {
  info: SystemInfoType | null
  loading: boolean
}

export default function SystemInfo({ info, loading }: Props) {
  const [open, setOpen] = useState(false)

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className="btn-ghost text-xs"
        title="System Info"
      >
        <Info size={14} />
        <span className="hidden sm:inline">System Info</span>
        {info && (
          <span className="badge-green text-[10px]">
            {info.doc_count} docs
          </span>
        )}
      </button>

      <AnimatePresence>
        {open && (
          <>
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setOpen(false)}
              className="fixed inset-0 bg-black/60 z-40"
            />

            {/* Panel */}
            <motion.div
              initial={{ opacity: 0, x: 50 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 50 }}
              className="fixed right-0 top-0 h-full w-80 bg-bg-surface border-l border-border z-50 p-5 space-y-5 overflow-y-auto"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Info size={14} className="text-accent-cyan" />
                  <span className="text-sm font-medium text-text-primary">System Info</span>
                </div>
                <button onClick={() => setOpen(false)} className="btn-ghost p-1">
                  <X size={14} />
                </button>
              </div>

              {loading && (
                <p className="text-sm text-text-muted">Loading...</p>
              )}

              {info && (
                <div className="space-y-4">
                  {/* Index stats */}
                  <div className="space-y-3">
                    <p className="text-[10px] font-mono text-text-muted uppercase tracking-wider">
                      Index
                    </p>
                    <div className="grid grid-cols-2 gap-3">
                      <div className="card-elevated text-center">
                        <p className="text-2xl font-mono text-accent-cyan">{info.doc_count}</p>
                        <p className="text-[10px] text-text-muted mt-0.5">Documents</p>
                      </div>
                      <div className="card-elevated text-center">
                        <p className="text-2xl font-mono text-accent-violet-glow">{info.embedding_dim}</p>
                        <p className="text-[10px] text-text-muted mt-0.5">Embed Dim</p>
                      </div>
                    </div>
                  </div>

                  {/* Models */}
                  <div className="space-y-2">
                    <p className="text-[10px] font-mono text-text-muted uppercase tracking-wider">
                      Models
                    </p>
                    {[
                      { icon: <Cpu size={12} />, label: 'Embedding', value: info.embedding_model.split('→')[1]?.trim() || info.embedding_model },
                      { icon: <Layers size={12} />, label: 'Reranker', value: info.reranker_model },
                      { icon: <Zap size={12} />, label: 'Generative', value: info.generative_model },
                      { icon: <Database size={12} />, label: 'Vector Index', value: info.faiss_index_type },
                    ].map(item => (
                      <div key={item.label} className="flex items-start gap-2 p-2 rounded-lg bg-bg-primary">
                        <span className="text-text-muted mt-0.5 flex-shrink-0">{item.icon}</span>
                        <div className="min-w-0">
                          <p className="text-[10px] text-text-muted">{item.label}</p>
                          <p className="text-xs text-text-secondary font-mono truncate" title={item.value}>
                            {item.value}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Capabilities */}
                  <div className="space-y-2">
                    <p className="text-[10px] font-mono text-text-muted uppercase tracking-wider">
                      Active Capabilities
                    </p>
                    <div className="flex flex-wrap gap-1.5">
                      <span className="badge-green">FAISS Semantic</span>
                      {info.bm25_enabled && <span className="badge-green">BM25 Lexical</span>}
                      <span className="badge-green">RRF Fusion</span>
                      <span className="badge-green">CrossEncoder Rerank</span>
                      <span className="badge-green">Query Expansion</span>
                    </div>
                  </div>

                  {/* Simulated vertex note */}
                  <div className="text-xs text-text-muted bg-bg-primary border border-border rounded-lg p-3 leading-relaxed">
                    <span className="text-accent-violet-glow font-mono">Vertex AI simulation:</span>{' '}
                    textembedding-gecko@003 is simulated via sentence-transformers/all-MiniLM-L6-v2.
                    gemini-pro is mocked with deterministic semantic enrichment.
                  </div>
                </div>
              )}
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  )
}
