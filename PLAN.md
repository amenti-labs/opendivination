# OpenDivination — Project Plan

> *"The Global Consciousness Project spent 15 years asking whether consciousness influences quantum randomness. OpenDivination inverts the question: what if quantum randomness is a window into meaning? We built the tools to find out."*

---

## What Is This

**OpenDivination** is an open-source oracle SDK that applies genuine quantum entropy to divination systems. It is the first developer toolkit to:

1. Replace PRNG with real QRNG hardware sources in symbol-draw systems
2. Introduce semantic resonance — finding which symbol an entropy burst most *resembles* in embedding space
3. Enable ARV (Associative Remote Viewing) protocol infrastructure
4. Provide a research layer for studying entropy patterns over time

It is **not** a magic app. It is a rigorous, auditable, provenance-stamped system for structured reflection using the most genuinely random signal available to modern hardware.

---

## Positioning

- **For developers:** The first proper OSS primitive for divination software. Drop-in QRNG for any symbol draw. MIT licensed.
- **For researchers:** Reproducible entropy validation, NIST-tested sources, GCP-compatible methodology.
- **For builders:** MCP server out of the box — any LLM agent can call it natively.
- **For consumers:** The underlying engine for a quantum tarot app (future).

**Closest prior art:** Princeton's Global Consciousness Project (network of QRNG nodes since 1998). OpenDivination is the personal/developer equivalent.

**Competition:** 222 tarot repos, 107 divination repos on GitHub. Zero use real QRNG. The space is empty.

---

## Core Concepts

### Oracle Modes

**Mode 1 — Selection Oracle**
Pure QRNG → symbol draw. Replaces `Math.random()` with hardware quantum entropy. Simple, defensible, immediately useful. Every draw comes with a provenance receipt.

**Mode 2 — Resonance Oracle**
Quantum noise features (entropy rate, frequency spectrum, statistical moments) are projected into semantic embedding space. The nearest-neighbor symbol is returned — not randomly selected, but *resonant* with the quantum state.
- Draws on the 2025 GAN paper: "Improving GANs by leveraging quantum noise from real hardware" — direct validation that quantum noise has structure PRNG lacks.
- Your FFT spectral work (remoteview-nextjs) applies directly here.

**Mode 3 — Morphology Oracle**
Characterize the *shape* of the noise burst rather than its value:
- Spikey vs smooth → volatile vs stable
- High freq vs low → urgency vs patience
- Clustering vs uniform → concentrated vs dispersed
Map morphological features directly to card/hexagram attributes. No ML required. Especially powerful for I Ching's changing lines.

**Mode 4 — Waveform Oracle** *(most novel)*
Don't select a symbol. Render raw quantum bytes as a waveform image. Pass to vision LLM:
> *"Read this waveform as an oracle. What does its shape, rhythm, and texture suggest about the question?"*
No corpus needed. The noise IS the message. Completely novel — no prior art.

**Mode 5 — Entropic Timing**
Monitor entropy rate continuously. Alert when entropy exceeds threshold — "the field just opened." Use quantum moments as prompts to act, rather than drawing on demand. Quantum Pomodoro.

**Mode 6 — Quantum Sigil Engine**
1. User writes intention as text
2. Reduce via classic sigil method (remove repeated letters → shape seed)
3. Feed quantum entropy into diffusion model latent space seeded by sigil shape
4. Output: unrepeatable image derived from intention + genuine quantum noise

**Mode 7 — Cross-System Convergence**
Draw simultaneously from Tarot, I Ching, and Runes using the same entropy seed. Highlight when all three systems independently converge on the same theme. Convergence is the signal — not any single system's claim.

**Mode 8 — Temporal Entropy Field** *(for ARV research)*
Persistent entropy monitor across multiple QRNG sources. Record entropy every second. Overlay with ARV session timestamps and outcomes. Over months: do entropy anomalies predict ARV hit sessions? Personal GCP node.

---

## Corpus Library

Each corpus ships as a JSON file with text embeddings pre-computed.

| System | Count | Notes |
|--------|-------|-------|
| Tarot (Rider-Waite) | 78 cards | Major + Minor Arcana |
| I Ching | 64 hexagrams + changing lines | 384 total states |
| Elder Futhark Runes | 24 symbols | |
| Lenormand | 36 cards | Popular in Europe, concrete/predictive |
| Ogham | 20 symbols | Celtic tree alphabet |
| Geomancy | 16 figures | Pure binary, 4 bits each — perfect QRNG fit |
| Numerology | reduction rules | Map entropy stream to 1–9 + master numbers |
| Custom | JSON schema | Anyone can add their own system |

### I Ching Special Handling
I Ching is uniquely suited to QRNG — it's a binary system at its core:
- 6 lines × (yin/yang + changing status) = hexagram + changing lines
- Smooth/clustered noise → few changing lines (stable moment)
- Noisy/spikey → many changing lines (turbulent moment)
- Primary hexagram = present. Secondary (after changes) = future direction.

---

## QRNG Source Architecture

OpenDivination uses **openentropy** as its canonical entropy backend — the modular, hardware-aware entropy SDK already built and tested. This is not a wrapper around a single API — it's a pluggable source registry with runtime fallback.

### openentropy as the Entropy Layer

```
opendivination
    └── @opendivination/core
            └── openentropy (Rust core / Python bindings)
                    ├── hardware sources   ← local devices
                    ├── network QRNG       ← remote APIs
                    └── software fallback  ← CSPRNG, clearly labeled
```

**openentropy** (`~/Repos/openentropy`) already provides:
- `EntropyPool.auto()` — auto-detects available sources at runtime
- `detect_available_sources()` — enumerates what's present
- Conditioning modes: `raw`, `sha256`, `none`
- CLI: `openentropy scan`, `openentropy stream`, `openentropy monitor`
- HTTP server: `openentropy-server` for remote access
- WASM build: browser-compatible entropy via `openentropy-wasm`

**openentropy-embed** (`~/Repos/openentropy-embed`) provides:
- Window-based entropy → embedding pipeline (already built)
- Qwen3-Embedding-0.6B as default local backend
- Source-separation metrics (is QRNG geometrically distinct from PRNG in embedding space?)
- Pre-registration methodology for psi/intention experiments

OpenDivination's Resonance Oracle (Mode 2) plugs directly into this pipeline.

### Source Registry

Sources are registered as plugins. OpenDivination ships with these out of the box:

| ID | Source | Type | Backend |
|----|--------|------|---------|
| `qcicada` | Crypta Labs QCicada USB | Photonic shot noise, NIST SP 800-90B | openentropy hardware |
| `anu` | ANU QRNG API | Photon vacuum fluctuation | openentropy network |
| `qbert` | Qbert (cipherstone.co) | Quantum tunneling | openentropy network |
| `outshift` | Cisco Outshift | DRBG post-processed | outshift-qrng-sdk |
| `blockchain` | Bitcoin block hashes | Deterministic public entropy | openentropy network |
| `os` | `/dev/urandom` | CSPRNG | openentropy software |
| `cpu_jitter` | CPU timing jitter | Hardware timing entropy | openentropy hardware |
| `thermal` | Thermal noise | On-device analog noise | openentropy hardware |

### Source Interface

Every source implements the same interface:

```typescript
interface EntropySource {
  id: string
  type: "hardware" | "network" | "software"
  isQuantum: boolean
  isAvailable(): Promise<boolean>
  getBytes(n: number): Promise<Uint8Array>
  getFeatures(n: number): Promise<EntropyFeatures>  // for Resonance mode
  quality(): Promise<SourceQuality>
}
```

### EntropyFeatures (for Resonance + Morphology modes)

Entropy feature extraction is shared with `openentropy-embed`:

```typescript
interface EntropyFeatures {
  entropyRate: number          // bits per byte
  autocorrelation: number[]    // lag-1 through lag-16
  fftSpectrum: number[]        // frequency domain (FFT, from RV pipeline work)
  momentSkewness: number
  momentKurtosis: number
  burstiness: number           // clustering coefficient
  smoothness: number           // inverse of high-freq power
}
```

These features feed directly into Mode 2 (Resonance) and Mode 3 (Morphology).

### Runtime Fallback Chain

```
1. Try: hardware QRNG (qcicada if connected)
2. Try: network QRNG (anu → qbert → outshift)
3. Try: local hardware entropy (cpu_jitter, thermal)
4. Fallback: os CSPRNG (clearly labeled in provenance receipt)
```

User can override: `opendivination draw tarot --source qcicada`

### Provenance Receipts

Every draw attaches a full source audit:

```json
{
  "id": "draw_abc123",
  "timestamp": "2026-03-12T09:58:00Z",
  "source": {
    "id": "anu",
    "type": "network",
    "isQuantum": true,
    "description": "ANU photon vacuum fluctuation",
    "qualityScore": 0.997
  },
  "raw_entropy_hex": "a3f7...",
  "entropy_bits": 256,
  "features": { "entropyRate": 7.94, "burstiness": 0.12, "..." },
  "mode": "resonance",
  "corpus": "tarot",
  "result": "The Tower",
  "resonance_distance": 0.342,
  "verifiable": true
}
```

---

## Repository Structure

```
opendivination/
├── packages/
│   ├── core/                     # Entropy layer + source registry
│   │   ├── sources/
│   │   │   ├── index.ts          # Source registry + fallback chain
│   │   │   ├── openentropy.ts    # openentropy Python/CLI bridge (primary)
│   │   │   ├── anu.ts            # ANU QRNG API
│   │   │   ├── qbert.ts          # Qbert API
│   │   │   ├── outshift.ts       # Cisco Outshift SDK
│   │   │   ├── blockchain.ts     # Bitcoin block hash entropy
│   │   │   └── csprng.ts         # Software fallback
│   │   ├── features.ts           # EntropyFeatures extraction (FFT, moments, etc.)
│   │   ├── pool.ts               # EntropyPool with auto-detect + fallback
│   │   └── provenance.ts         # Signed draw receipts
│   ├── corpora/                  # All symbol systems + pre-computed embeddings
│   │   ├── tarot.json            # 78 cards, Rider-Waite
│   │   ├── iching.json           # 64 hexagrams + changing lines (384 states)
│   │   ├── runes.json            # 24 Elder Futhark
│   │   ├── lenormand.json        # 36 cards
│   │   ├── ogham.json            # 20 symbols
│   │   ├── geomancy.json         # 16 figures (pure binary)
│   │   ├── numerology.ts         # Reduction rules
│   │   ├── embeddings/           # Pre-computed Qwen3-0.6B vectors (from openentropy-embed)
│   │   └── schema.ts             # Interface for custom corpora
│   ├── oracles/
│   │   ├── selection.ts          # Mode 1: QRNG → weighted draw
│   │   ├── resonance.ts          # Mode 2: entropy features → embedding → nearest neighbor
│   │   ├── morphology.ts         # Mode 3: noise shape → symbol attributes
│   │   ├── waveform.ts           # Mode 4: raw noise → vision LLM reading
│   │   ├── timing.ts             # Mode 5: continuous entropy monitor
│   │   ├── sigil.ts              # Mode 6: intention → quantum sigil image
│   │   ├── convergence.ts        # Mode 7: multi-system cross-draw
│   │   └── arv.ts                # Mode 8: ARV protocol + temporal entropy field
│   ├── llm/                      # Interpreter adapters
│   │   ├── openai.ts
│   │   ├── anthropic.ts
│   │   ├── ollama.ts
│   │   └── zai.ts                # Z.AI / GLM default for scripts
│   ├── api/                      # Self-hostable REST server
│   └── cli/                      # npx opendivination draw tarot --mode resonance --source qcicada
├── research/
│   ├── entropy-validation/       # NIST SP 800-22 tests, chi-squared (openentropy methodology)
│   ├── source-separation/        # openentropy-embed: are sources geometrically distinct?
│   ├── mode-agreement/           # Do Mode 1 + Mode 2 agree more than chance?
│   ├── waveform-readings/        # LLM waveform oracle consistency experiments
│   ├── arv-validation/           # ARV hit rate tracking by oracle mode
│   ├── temporal-field/           # 30-day entropy anomaly log (personal GCP node)
│   └── notebooks/                # Jupyter for reproducible research
├── PLAN.md                       # This file
├── README.md
└── LICENSE                       # MIT
```

---

## Provenance Receipts

Every oracle call returns a signed receipt:

```json
{
  "id": "draw_abc123",
  "timestamp": "2026-03-12T09:48:00Z",
  "source": "anu_qrng",
  "source_type": "photon_vacuum_fluctuation",
  "raw_entropy_hex": "a3f7...",
  "entropy_bits": 256,
  "entropy_quality_score": 0.997,
  "mode": "resonance",
  "corpus": "tarot",
  "result": "The Tower",
  "resonance_distance": 0.342,
  "verifiable": true
}
```

---

## Research Layer

### Experiment 1 — QRNG vs PRNG uniformity
Run 10,000 draws from each source, chi-squared test for uniform distribution across corpus. Prove quantum is unbiased.

### Experiment 2 — Mode agreement
Do Mode 1 (selection) and Mode 2 (resonance) agree more than chance on the same entropy stream? If yes — quantum noise has semantic structure beyond randomness. That's a paper.

### Experiment 3 — Waveform LLM oracle consistency
Same waveform, different LLMs, different prompts. How consistent are the readings? Are certain waveform shapes reliably interpreted similarly?

### Experiment 4 — ARV hit rate by mode
Run 100 ARV trials using Mode 1, then Mode 2. Compare hit rates. If Mode 2 > Mode 1 > chance — suggests semantic resonance is real.

### Experiment 5 — Temporal entropy field
Log entropy continuously for 30 days. Find entropy anomalies. Did anything meaningful happen at those moments? Personal GCP replication.

---

## MCP Server

Ship as a Model Context Protocol server from day one. Any LLM agent (Claude, GPT, Gemini) can call:

```
opendivination.draw(corpus="tarot", mode="resonance", question="...")
opendivination.hexagram(mode="morphology")
opendivination.waveform(question="...")
opendivination.arv.new_session(target_pool="...")
opendivination.entropy.status()
```

Directly competes with (and supersedes) the existing I Ching MCP server (Rust, Jan 2026).

---

## Connection to Existing Work

| OpenDivination Component | Built On |
|---------------------|----------|
| Entropy layer / source registry | `openentropy` (Rust/Python, multi-source, auto-detect) |
| Entropy → embedding pipeline | `openentropy-embed` (Qwen3-0.6B, window-based, already running) |
| Hardware QRNG source | QCicada USB (`qcicada` crate in openentropy) |
| FFT feature extraction | FFT Spectral RV Prompt (`remoteview-nextjs`) |
| Network QRNG sources | `outshift-qrng-sdk`, `qbert` repo |
| Resonance mode concept | `quantum-llama.cpp` (QRNG-seeded latent sampling) |
| ARV protocol | `remoteview-nextjs`, `pear-experiments`, `llm-rv-pipeline` |
| Psi/intention methodology | `openentropy-embed/ENTROPY_EMBEDDING_EXPERIMENT.md` (pre-registered) |
| Waveform oracle | LLM RV Pipeline (LLM as perceptual instrument) |
| GCP-compatible research | `qrng-research`, `openentropy` benchmark methodology |

**openentropy is the keystone.** It already solves the hardest problem: a production-grade, multi-source entropy SDK with hardware QRNG support, statistical validation, and Python bindings. OpenDivination is the oracle layer that sits on top of it.

This is not a new idea — it's the integration layer across everything already built.

---

## Build Order

### v0.1 — Foundation (weekend)
- [ ] `packages/core/sources/openentropy.ts` — bridge to openentropy CLI/Python (primary source)
- [ ] `packages/core/sources/anu.ts`, `qbert.ts` — network QRNG fallbacks
- [ ] `packages/core/pool.ts` — EntropyPool with auto-detect + fallback chain
- [ ] `packages/corpora` — Tarot + I Ching JSON with pre-computed embeddings (reuse openentropy-embed Qwen3 pipeline)
- [ ] `packages/oracles/selection` — Mode 1, clean API
- [ ] Provenance receipts with source metadata
- [ ] CLI: `npx opendivination draw tarot --source auto`
- [ ] README with entropy source docs + validation methodology

### v0.2 — Resonance (1–2 weeks)
- [ ] Entropy feature extraction (FFT, moments, autocorrelation)
- [ ] Pre-computed embeddings for all corpora
- [ ] Mode 2 resonance oracle
- [ ] Research experiment 1 + 2 notebooks

### v0.3 — Oracle Modes (2–4 weeks)
- [ ] Modes 3, 4, 5 (morphology, waveform, timing)
- [ ] LLM adapters (OpenAI, Anthropic, Z.AI/GLM default)
- [ ] MCP server
- [ ] REST API

### v0.4 — ARV + Research (ongoing)
- [ ] Mode 8 ARV protocol
- [ ] Temporal entropy field logger
- [ ] Experiments 3, 4, 5
- [ ] Paper draft

### Consumer App (post-OSS)
- Quantum Tarot app built on top of this SDK
- ASO: "quantum tarot", "AI tarot reading", "daily tarot"
- Monetization: free daily pull, $4.99/mo unlimited + journal

---

## Name

**opendivination** — clean, memorable, googleable, hits both technical and spiritual audiences.

npm: `@opendivination/core`, `@opendivination/corpora`, `@opendivination/oracles`  
GitHub: `ereid7/opendivination`  
Docs: `opendivination.dev` (TBD)

---

*Last updated: 2026-03-12*
