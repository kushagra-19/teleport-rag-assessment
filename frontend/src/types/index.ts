export interface Chunk {
  id: number
  text: string
  source: string
  token_count: number
}

export interface RetrievalResult {
  chunk: Chunk
  score: number
  rank: number
  strategy: 'A' | 'B'
  expanded_query: string | null
  expansion_terms: string[]
  retrieval_path: 'faiss' | 'bm25' | 'rrf_fused'
  latency_ms: number
}

export interface QueryResponse {
  query: string
  strategy_a: RetrievalResult[] | null
  strategy_b: RetrievalResult[] | null
  expanded_query: string | null
  expansion_terms: string[]
  retrieval_time_ms: Record<string, number>
}

export interface SystemInfo {
  doc_count: number
  embedding_dim: number
  embedding_model: string
  faiss_index_type: string
  bm25_enabled: boolean
  reranker_model: string
  generative_model: string
}

export interface BenchmarkEntry {
  query: string
  strategy_a: RetrievalResult[]
  strategy_b: RetrievalResult[]
  expanded_query: string | null
  expansion_terms: string[]
  retrieval_time_ms: Record<string, number>
}

export type Strategy = 'A' | 'B' | 'both'
export type RetrievalPath = 'faiss' | 'bm25' | 'rrf_fused'
