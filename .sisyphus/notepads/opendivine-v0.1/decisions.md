# OpenDivine v0.1 — Architectural Decisions

## [2026-03-12] Core Decisions

### Entropy Source Priority Order
1. openentropy (hardware, optional import)
2. ANU QRNG (network)
3. Qbert (network, requires QBERT_API_KEY)
4. Outshift (network, requires OUTSHIFT_API_KEY)
5. CSPRNG (always available fallback)

### Rejection Sampling (CRITICAL)
- NEVER use `value % N` — modulo bias
- Use rejection sampling: read ceil(log2(N)/8) bytes, reject if >= N * floor(256^k/N)
- `rejection_sample(entropy: bytes, max_value: int) -> tuple[int, int]` returns (index, bytes_consumed)
- `rejection_sample_weighted(entropy: bytes, weights: list[float]) -> tuple[int, int]` for I Ching

### I Ching Probability Models
- YARROW: P(old_yin)=1/16, P(young_yang)=5/16, P(young_yin)=7/16, P(old_yang)=3/16
- THREE_COIN: P(old_yin)=1/8, P(young_yang)=3/8, P(young_yin)=3/8, P(old_yang)=1/8
- UNIFORM: equal probability for all 4 line types

### openentropy Import Guard Pattern
```python
try:
    import openentropy
    _OPENENTROPY_AVAILABLE = True
except ImportError:
    _OPENENTROPY_AVAILABLE = False
```
Reference: `/Users/erai/Repos/Quantum-random-vLLM-sampler/src/qr_sampler/entropy/openentropy.py`

### API Keys (env vars only)
- QBERT_API_KEY
- ANU_API_KEY (optional, free tier exists)
- OUTSHIFT_API_KEY

### Timeout
- 2s timeout on source availability checks (keep CLI fast, <3s total)
