# REPORT.md

## Phase 1: Serving Configuration & Architectural Rationale

To meet the production-grade metrics of P95 Latency < 5s and 10+ RPS, we deployed the following optimization configurations for 1× H100 (80GB) and the Qwen3-30B-A3B MoE model:

* `--tensor-parallel-size 1`: Setting this to 1 avoids the significant inter-GPU communication latency overhead, since a single H100 GPU has sufficient VRAM to fit the active parameters of Qwen3-30B along with its KV cache.
* `--gpu-memory-utilization 0.90`: Reserves 90% of the VRAM for the vLLM memory pool, leaving 10% for the CUDA context and runtime allocations, maximizing the number of PagedAttention blocks available.
* `--max-model-len 4096`: Overrides the model's default 262K context window to lock it to the maximum business requirement (3K prompt + short output), releasing significant VRAM back to the KV cache pool.
* `--enable-chunked-prefill true` & `--max-num-batched-tokens 4096`: Enables chunked prefill, splitting large prompts into manageable chunks to batch them with ongoing decoding tokens, smoothing out P95 latency spikes during high-concurrency prefill phases.
* `--enable-prefix-caching`: Multi-turn `verify -> revise` retries submit identical database schemas (~3K tokens). Enabling prefix caching allows second- and third-turn prompts to hit the cache at O(1) time, cutting prefill latency to near zero.
* `--max-num-seqs 256`: Increases concurrent request processing capability to 256, ensuring concurrent incoming requests do not stack up in the vLLM waiting queue during peak 10+ RPS load.

---

## Phase 2: Observability Dashboard Configuration

To ensure serving health visibility, we built a Grafana dashboard (`infra/grafana/provisioning/dashboards/serving.json`) powered by Prometheus metrics scraped from vLLM:

1. **Latency Metrics**:
   * **P95 Request Latency**: `histogram_quantile(0.95, sum(rate(vllm:e2e_request_latency_seconds_bucket[5m])) by (le))` maps directly to our end-to-end SLO.
   * **P95 TTFT (Prefill)**: `histogram_quantile(0.95, sum(rate(vllm:time_to_first_token_seconds_bucket[5m])) by (le))` isolates prompt processing bottlenecking.
   * **P95 ITL (Decode)**: `histogram_quantile(0.95, sum(rate(vllm:inter_token_latency_seconds_bucket[5m])) by (le))` tracks output token generation speed.

2. **Throughput Metrics**:
   * **Generated Tokens/Sec**: `rate(vllm:generation_tokens_total[1m])` measures generation density.
   * **Requests Running vs. Waiting**: `vllm:num_requests_running` and `vllm:num_requests_waiting` measure model saturation.

3. **KV Cache Metrics**:
   * **GPU Cache Usage**: `vllm:gpu_cache_usage_perc` tracks remaining capacity before cache eviction/preemption triggers.

---

## Phase 3 & 4: Agent Design & Observability Tracing

### Agent Design (Phase 3)
We implemented a self-consistency loop in `agent/graph.py` and prompts in `agent/prompts.py`:
1. `generate_sql` converts an English question to SQL.
2. `execute` runs the query against the database.
3. `verify` validates the output rows or execution error for plausibility, outputting `{ok: bool, issue: str}`.
4. `revise` (if `ok` is false) takes the prior SQL, query result, and verifier issue to patch the SQL, looping back to execution (capped at 3 iterations).

### Langfuse Observability Issues (Phase 4 - UNFINISHED)
> [!WARNING]
> **We could not complete Phase 4 (Agent Observability Tracing)** due to SDK and environment issues.
> The local Langfuse container stack and the Python SDK threw initialization and runtime exceptions (such as `'Langfuse' object has no attribute 'trace'`) and experienced connection timeouts.
> Consequently:
> - No agent traces were successfully captured or visualised in Langfuse.
> - We could not produce `screenshots/langfuse_trace.png` or `screenshots/langfuse_tags.png`.
> - The Langfuse CallbackHandler had to be disabled (`_lf_handler = None`) in `agent/server.py` to prevent client initialization failures from blocking or hanging the agent execution.
> - **No observability conclusions could be drawn from agent trace waterfalls.**

---

## Phase 5: Baseline Evaluation Results

We ran the evaluation set of 30 curated questions against our baseline agent using `evals/run_eval.py`. The execution accuracy results are:

* **Total Questions**: 30
* **Mean Iterations per Request**: 1.6
* **Pass Rate by Iteration**:
  * **Iteration 1 (Raw Gen / iter_0)**: **30.0%** (9/30 correct)
  * **Iteration 2 (First Rev / iter_1)**: **36.7%** (11/30 correct)
  * **Iteration 3 (Second Rev / iter_2)**: **36.7%** (11/30 correct)

### Commentary & Example Case
The verifier successfully corrected logic/execution issues on **2 queries** (a 22.2% relative accuracy boost):
* **Success Case**: In `formula_1`, the question was *"What is the coordinates location of the circuits for Australian grand prix?"*. The initial query missed `DISTINCT`, returning duplicate coordinates. The verifier caught this, stating that only one unique coordinate pair should be returned for a single circuit. The revise node successfully injected `SELECT DISTINCT c.lat, c.lng...` on the next turn, passing validation.
* **Failure Case**: In `toxicology`, the agent failed on `m.toxicity` (column did not exist). The model cannot self-heal deep schema misunderstandings without schema correction hints in the verifier's feedback loop.

---

## Phase 6: Hitting the SLO & Tuning (UNFINISHED)

Our target SLO is: **P95 end-to-end agent latency < 5 seconds at 10+ RPS over a 5-minute window.**

### Tuning Blind and Unfinished Status
> [!WARNING]
> **We could not complete Phase 6 (SLO Tuning & Iteration)**. 
> Because we could not get Langfuse to work, we had to proceed "blind" without any agent-level trace waterfalls. More critically, we encountered server-side execution hangs during baseline testing and concurrent test execution:
> - The baseline load test at 10 RPS resulted in a performance collapse, with a P95 latency of **97.0 seconds**, **67 HTTP 500 errors**, and **351 client disconnections/timeouts**.
> - The diagnostic analysis points to thread pool starvation because of the synchronous FastAPI server (`def answer`) and synchronous graph nodes (`llm().invoke`).
> - We attempted to refactor both the FastAPI server and the LangGraph nodes to be asynchronous (using `async def` and `ainvoke`). However, due to port timeouts and hanging connections in the runtime environment, we were unable to successfully run or verify the post-tuning load test at 10 RPS.
> - As a result, **we did not hit the platform SLO and could not collect final post-tuning latency metrics or post-tuning evaluation numbers (eval_after_tuning.json)**.
> - No final conclusions can be drawn regarding post-tuning concurrent capacity or latency improvements.

---

## Phase 7: Verdict & Recommendations

### Agent Value Analysis
The agent's self-correcting loop improves execution accuracy from **30.0% to 36.7%** (a 6.7% absolute gain). However, it averages 1.6 iterations per question, increasing token consumption and inference cost by ~1.6x. If prefix caching works correctly, it should minimize the latency penalty of these extra iterations, but under concurrent load we could not verify this behavior due to server hangs.

### What We Would Do With More Time
1. **Resolve Asynchronous Connection Hangs**: Debug the underlying issues causing connection hangs after switching to async, ensuring clean async I/O between the agent and the vLLM engine.
2. **Dynamic Prompt Schema Pruning**: Retrieve only the top-K relevant tables/columns (using BM25 or embeddings) instead of sending the full schema (~3K tokens). This would cut prefill sizes by ~70%, reducing VRAM and prefill overhead.
3. **Schema-Aware Error Diagnostics**: Enhance the `verify` node to query table structures (`PRAGMA table_info`) on SQL failure, providing the `revise` node with the actual column names to accelerate correction.