#!/usr/bin/env bash
#
# Start vLLM with optimized configuration for Qwen3-30B-A3B on 1x H100.
# Reference: https://docs.vllm.ai/en/latest/serving/openai_compatible_server.html

set -euo pipefail

MODEL="Qwen/Qwen3-30B-A3B-Instruct-2507"

export VLLM_USE_V1=0

exec uv run python -m vllm.entrypoints.openai.api_server \
    --model "$MODEL" \
    --host 0.0.0.0 \
    --port 8000 \
    --tensor-parallel-size 1 \
    --gpu-memory-utilization 0.90 \
    --max-model-len 4096 \
    --max-num-seqs 256 \
    --enable-chunked-prefill true \
    --max-num-batched-tokens 4096 \
    --enable-prefix-caching \
    --kv-cache-dtype auto