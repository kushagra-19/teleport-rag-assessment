"""
Technical corpus: 10 paragraphs covering distributed systems and cloud infrastructure.
Topics are chosen to create meaningful retrieval challenges for the benchmark queries.
"""

CORPUS: list[str] = [
    # 0 ── Load Balancing & Peak Traffic ──────────────────────────────────────
    "The platform employs a multi-tier load balancing architecture to handle traffic spikes "
    "and peak load conditions. At the edge, a global Application Load Balancer (ALB) distributes "
    "inbound requests across regional clusters using weighted round-robin with health-check-driven "
    "exclusion. Within each region, an internal Network Load Balancer routes traffic to individual "
    "service pods based on active connection count (least-connections algorithm), preventing any "
    "single instance from becoming a throughput bottleneck. During burst events, the load balancer's "
    "connection draining mechanism ensures graceful handoff of in-flight requests before removing "
    "unhealthy nodes from rotation. Sticky sessions are intentionally avoided to preserve horizontal "
    "scalability. Circuit-level timeouts (5 seconds) are enforced at the ALB to prevent cascading "
    "stalls from slow upstream services during demand surge events.",

    # 1 ── Kubernetes Auto-scaling ─────────────────────────────────────────────
    "Horizontal scalability is implemented through Kubernetes Horizontal Pod Autoscaler (HPA) "
    "combined with a Cluster Autoscaler managing a pre-warmed node pool. The HPA monitors CPU "
    "utilization and custom Prometheus metrics (requests per second, queue depth) and adjusts "
    "replica counts within 60-second windows. When pod demand exceeds available node capacity, "
    "the Cluster Autoscaler provisions additional compute nodes from a pre-warmed pool, reducing "
    "cold-start latency from 4 minutes to 45 seconds. Each microservice is deployed as a stateless "
    "pod, enabling safe horizontal replication without session affinity requirements. Vertical Pod "
    "Autoscaler (VPA) handles memory-bound services that cannot be horizontally replicated. Resource "
    "requests and limits are tuned per service to prevent CPU throttling during concurrent request "
    "surges, ensuring predictable latency under autoscaling events.",

    # 2 ── Multi-layer Caching ─────────────────────────────────────────────────
    "A multi-layer caching architecture reduces database read pressure and improves response "
    "latency across the stack. Session data and authentication tokens are cached in a Redis Cluster "
    "with consistent hashing across six shards, providing sub-millisecond lookups with a 99.9% "
    "cache hit rate. Object-level caching uses Memcached with a cache-aside pattern: on cache miss, "
    "the application fetches from the database, serializes the result, and writes back with a "
    "configurable TTL ranging from 60 to 3600 seconds depending on data volatility. Write-through "
    "caching is applied to high-read, low-write entities such as user profiles and product catalog "
    "entries, eliminating cache invalidation complexity. A cache warming job runs 15 minutes before "
    "anticipated peak periods, pre-populating the top 10,000 hot keys derived from the previous "
    "week's access frequency analytics to prevent cold-cache stampede effects.",

    # 3 ── CDN Edge Caching ────────────────────────────────────────────────────
    "Content delivery is accelerated through a globally distributed CDN with Points of Presence "
    "in 38 regions. Cacheable API responses such as product listings and public content are served "
    "directly from the nearest edge node, reducing origin server load by 73% and cutting average "
    "response latency by 180ms for international users. Cache-Control headers set varying TTLs per "
    "content type: static assets use a one-year TTL with cache-busting fingerprints, API responses "
    "use 60 to 300 seconds, and user-specific data is marked no-store. Edge-side cache invalidation "
    "is triggered programmatically via CDN API on each deployment using tag-based purging to flush "
    "related content groups atomically. Stale-while-revalidate semantics tolerate brief cache "
    "staleness during refresh without increasing perceived user latency.",

    # 4 ── PostgreSQL Read Replicas ────────────────────────────────────────────
    "Database read traffic is distributed across a pool of PostgreSQL read replicas managed by a "
    "PgBouncer connection pooling proxy operating in transaction-pooling mode. Write operations "
    "target the primary instance exclusively, with synchronous streaming replication ensuring at "
    "most one transaction of lag on the hot standby. PgBouncer maintains 20 connections per replica "
    "to serve hundreds of concurrent application threads without connection exhaustion. For analytical "
    "workloads, data is continuously streamed from the primary via Debezium Change Data Capture (CDC) "
    "into a columnar ClickHouse store, decoupling heavy read workloads from the OLTP cluster entirely. "
    "Failover is automated: when the primary becomes unavailable, Patroni promotes the standby within "
    "30 seconds and updates the DNS CNAME, requiring zero application-level configuration changes "
    "to restore full database availability.",

    # 5 ── Database Sharding ───────────────────────────────────────────────────
    "User data is horizontally partitioned across 16 logical shards using consistent hashing on "
    "the user UUID. A shard router service maps each request to the correct shard without exposing "
    "partitioning logic to application code; the routing table is replicated in-memory across all "
    "API nodes via a gossip protocol for sub-millisecond routing decisions. Cross-shard queries "
    "such as aggregations and admin reports are handled by a scatter-gather service that broadcasts "
    "the query to all 16 shards in parallel, collects partial results, and applies final aggregation "
    "and pagination in memory. Shard rebalancing is triggered when any shard exceeds 80% storage "
    "capacity, using virtual node migration to move entire hash ranges rather than individual records, "
    "minimizing I/O impact and rebalancing duration.",

    # 6 ── Circuit Breaker & Resilience ───────────────────────────────────────
    "The circuit breaker pattern prevents cascading failures when downstream services degrade under "
    "load. Each inter-service call is wrapped by a Resilience4j circuit breaker configured with a "
    "sliding window of 20 calls, opening when the error rate exceeds 50% within that window. In the "
    "open state, requests are immediately failed-fast and routed to a fallback handler, typically a "
    "cached response or a graceful degradation payload, rather than waiting for the upstream timeout. "
    "A half-open probe state attempts a single real request every 30 seconds to test recovery; "
    "if successful, the breaker closes and normal traffic resumes. Exponential backoff with jitter "
    "(base 500ms, max 30 seconds, jitter ±20%) is applied to all retry policies to prevent "
    "thundering herd reconvergence after a transient outage.",

    # 7 ── Kafka Async Processing ──────────────────────────────────────────────
    "Long-running and computationally expensive operations are decoupled from the synchronous API "
    "request path using Apache Kafka as the distributed event streaming platform. API handlers "
    "publish events to topic partitions and return a job ID immediately, maintaining consistently "
    "low API response latencies with P99 below 200 milliseconds regardless of background task "
    "complexity. Consumer groups process these events asynchronously with at-least-once delivery "
    "semantics, while idempotency keys on each event prevent duplicate processing on retries. "
    "Dead-letter queues capture events that fail after three retry attempts, preserving them for "
    "manual inspection without blocking healthy consumer progress. Kafka's 7-day retention policy "
    "allows full event replay for disaster recovery, audit trails, or backfilling newly deployed "
    "consumer services.",

    # 8 ── Rate Limiting ───────────────────────────────────────────────────────
    "API access is governed by a token bucket rate limiter implemented at the API Gateway layer "
    "with per-client quota enforcement. Each authenticated client receives a bucket with a "
    "configurable capacity of 1000 tokens and a refill rate of 100 tokens per second, stored in "
    "a Redis sorted set shared across all gateway instances to ensure consistent enforcement. "
    "Clients that exhaust their token bucket receive a 429 Too Many Requests response with a "
    "Retry-After header indicating the millisecond-precise time until quota replenishment. "
    "Adaptive rate limiting automatically reduces quotas for clients exhibiting anomalous traffic "
    "patterns where burst coefficient exceeds five times the baseline, protecting downstream "
    "services from intentional or accidental abuse. Rate limit metrics are exposed to Prometheus, "
    "enabling SRE teams to monitor patterns and adjust quotas dynamically via the admin API.",

    # 9 ── Observability Stack ─────────────────────────────────────────────────
    "The observability stack is built on three complementary pillars: structured logging, "
    "distributed tracing, and time-series metrics. All service logs are emitted as JSON to stdout "
    "and shipped via Fluentbit to an Elasticsearch cluster, enabling full-text search across "
    "billions of log events with Kibana dashboards. Distributed traces are instrumented via the "
    "OpenTelemetry SDK with W3C TraceContext propagation and exported to a Jaeger collector, "
    "providing end-to-end latency breakdowns across microservice boundaries with P50, P95, and P99 "
    "percentiles per span. Time-series metrics following the RED method (Rate, Errors, Duration) "
    "are scraped by Prometheus at 15-second intervals and visualized in Grafana dashboards with "
    "SLO burn-rate alerting. When P99 API latency exceeds 500ms for five consecutive minutes, "
    "PagerDuty alerts are triggered for SLA-compliant incident response.",
]

BENCHMARK_QUERIES: list[str] = [
    "How does the system handle peak load?",
    "What caching strategies improve system performance?",
    "How is the database scaled for high availability and read performance?",
]
