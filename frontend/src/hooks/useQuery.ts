import { useState, useCallback } from 'react'
import type { QueryResponse, SystemInfo, Chunk, BenchmarkEntry, Strategy } from '../types'

const API = ''

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    const err = await res.text()
    throw new Error(err || `HTTP ${res.status}`)
  }
  return res.json()
}

export function useQueryEngine() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<QueryResponse | null>(null)

  const runQuery = useCallback(
    async (query: string, strategy: Strategy, k: number) => {
      setLoading(true)
      setError(null)
      try {
        const data = await apiFetch<QueryResponse>('/query', {
          method: 'POST',
          body: JSON.stringify({ query, strategy, k }),
        })
        setResult(data)
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Query failed')
      } finally {
        setLoading(false)
      }
    },
    []
  )

  return { loading, error, result, runQuery }
}

export function useSystemInfo() {
  const [info, setInfo] = useState<SystemInfo | null>(null)
  const [loading, setLoading] = useState(false)

  const fetchInfo = useCallback(async () => {
    setLoading(true)
    try {
      const data = await apiFetch<SystemInfo>('/system-info')
      setInfo(data)
    } finally {
      setLoading(false)
    }
  }, [])

  return { info, loading, fetchInfo }
}

export function useCorpus() {
  const [chunks, setChunks] = useState<Chunk[]>([])
  const [loading, setLoading] = useState(false)

  const fetchCorpus = useCallback(async () => {
    setLoading(true)
    try {
      const data = await apiFetch<Chunk[]>('/corpus')
      setChunks(data)
    } finally {
      setLoading(false)
    }
  }, [])

  return { chunks, loading, fetchCorpus }
}

export function useBenchmark() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [results, setResults] = useState<BenchmarkEntry[]>([])

  const runBenchmark = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await apiFetch<{ benchmark_queries: BenchmarkEntry[] }>('/benchmark', {
        method: 'POST',
      })
      setResults(data.benchmark_queries)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Benchmark failed')
    } finally {
      setLoading(false)
    }
  }, [])

  return { loading, error, results, runBenchmark }
}
