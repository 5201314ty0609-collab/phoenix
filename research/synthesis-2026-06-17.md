# 鲤鱼 Deep Research Synthesis — 2026-06-17

Three parallel deep research agents surveyed 100+ GitHub projects across 13 sub-domains. This report cross-references findings and produces a single prioritized absorption plan.

**Research Agents**: afc66 (knowledge graphs, RAG, meta-prompting, memory, multi-agent comm) + a3cad (observability, debugging, prompt optimization, evaluation, safety) + a83fc (AI testing, QA automation, code verification)

---

## Cross-Domain Consensus Patterns

Seven architectural patterns emerged independently across all three research domains:

### 1. MCP-Native is Universal
Every single project across all three reports ships as an MCP server. MCP has won as the interoperability layer — not just for tools but for memory, observability, testing, and coordination.

### 2. Hybrid Retrieval (FTS5 + Vector + Graph) via RRF
Knowledge MCP, OMEGA, AgenticMemory, Centralaizer, code-context-graph, and Tessera all converge on three-pillar storage: full-text (SQLite FTS5), semantic vectors (sqlite-vec, ONNX), and graph relationships, fused via Reciprocal Rank Fusion. This is the consensus architecture for 2025-2026.

### 3. Mutation Testing is Mandatory for AI-Generated Code
a83fc's strongest finding, corroborated by SWE-ABS (ACL 2026): ~20% of "passing" AI patches are semantically incorrect. Tautest, Veritas, Plumbline, DAE, and Qodo CI independently converged on mutation testing as the mandatory verification layer. Coverage alone creates dangerous false confidence.

### 4. Hooks Over Prompts for Enforcement
a3cad's agent-comm and CROSS enforce coordination at the tool-use layer (PreToolUse hooks), not LLM discretion. This mirrors 鲤鱼's own enforcement hierarchy (Levels 5-7) and validates the architectural direction.

### 5. SQLite + FTS5 is Universal Local Storage
Across all three domains, every local-first tool uses SQLite+FTS5 as the base, extended with sqlite-vec for vectors. 鲤鱼's `knowledge-base.db` is already on the right path — it just needs the vector and graph layers.

### 6. Auto-Capture + Forgetting for Agent Memory
OMEGA (95.4% LongMemEval), AgenticMemory (16 query types), and Centralaizer (4 memory types) converge on automated fact extraction with Ebbinghaus/ACT-R decay, replacing manual logging. 鲤鱼's MEMORY.md + reflections.jsonl need this upgrade.

### 7. Token Efficiency as the Primary Metric
CodeBurn, CodeSeek (60-900x savings), Canopy (85-91% reduction), and TokenTrimmer all measure success by token reduction. 鲤鱼's CLAUDE.md is already flagged as potential bloat — cost attribution per rule is needed.

---

## Cross-Domain Top Picks

Projects that deliver value across multiple research domains:

### 1. Mutation Testing Layer (Tautest + Veritas)
- **Domains**: a83fc (testing) + a3cad (evaluation)
- **Why cross-domain**: Closes the single biggest gap identified across ALL three reports — AI-generated code that passes tests but is semantically wrong
- **鲤鱼 impact**: Every TDD cycle gains a mandatory verification gate. Surviving mutants fed back to agents for test hardening.

### 2. Langfuse (26,400 stars, MIT)
- **Domains**: a3cad (observability) + afc66 (multi-agent coordination)
- **Why cross-domain**: Maps all 7 Metacog senses to quantified traces. OpenTelemetry-native means framework-agnostic. 10B+ observations/month, 19 of Fortune 50.
- **鲤鱼 impact**: O2 → token pressure events. Chronos → timing spans. Nociception → error scores. Echo → repetition detection. Creates a queryable audit trail of Metacog internal state.

### 3. DSPy (34,000 stars, Stanford, MIT)
- **Domains**: a3cad (prompt optimization) + afc66 (meta-prompting)
- **Why cross-domain**: Could auto-optimize 鲤鱼's rule engine. Treats each ECC rule as a DSPy Signature with automated Bayesian optimization. 300+ contributors.
- **鲤鱼 impact**: When a framework drops from validated to observed, DSPy searches for the prompt variant that restores effectiveness.

### 4. OMEGA + AgenticMemory
- **Domains**: afc66 (memory) + a3cad (evaluation — LongMemEval benchmark)
- **Why cross-domain**: SQLite+FTS5+ONNX architecture identical to 鲤鱼's knowledge base. OMEGA scores 95.4% on LongMemEval. AgenticMemory adds causal reasoning + drift detection.
- **鲤鱼 impact**: Auto-capture replaces manual MEMORY.md logging. Ebbinghaus decay prevents infinite growth. Drift detection enhances 鲤鱼's self-correction.

### 5. Kintsugi + CROSS
- **Domains**: a3cad (safety) + afc66 (hooks-over-prompts pattern)
- **Why cross-domain**: Deterministic bash safety using real AST parsing (brush-parser, pure Rust). Catches hidden destructive commands inside `$(...)` that prompt-level guards miss.
- **鲤鱼 impact**: Implements 鲤鱼's danger/caution/safe classification at the kernel level, not the prompt level.

### 6. GNAP (Git-Native Agent Protocol)
- **Domains**: afc66 (multi-agent communication) + aligns with 鲤鱼's existing coordination
- **Why cross-domain**: Formalizes 鲤鱼's lock file + heartbeat + completion log pattern into a structured `.gnap/` directory. `git log` as audit trail. Zero infrastructure.
- **鲤鱼 impact**: Makes 鲤鱼's coordination patterns discoverable and usable by other agent frameworks.

### 7. Midscene.js (13,600 stars, ByteDance, MIT)
- **Domains**: a83fc (E2E testing)
- **Why cross-domain**: Vision-driven UI testing. Natural language assertions. Drop-in for Playwright. 80% token reduction vs DOM-based. Supports Web + Android + iOS + Desktop.
- **鲤鱼 impact**: Survives UI redesigns that break selector-based tests. Tests readable by non-developers.

### 8. Browser-Use (98,000 stars, YC-backed)
- **Domains**: a83fc (agentic testing)
- **Why cross-domain**: Dominant open-source AI browser agent. Domain skills system that extracts reusable patterns and learns across runs.
- **鲤鱼 impact**: Complex E2E flows without brittle selectors. Skills compound over time.

---

## Recommended Absorption Order

### P0 — Immediate (this week, low effort, high impact)

| # | Project | Effort | 鲤鱼 Mapping | What It Does |
|---|---------|--------|-----------------|--------------|
| 1 | **Tautest** | Low | TDD workflow gate | Mutation testing on `git diff` lines. Surviving mutants → AI-ready fix prompts. Closes the "weak test" gap. |
| 2 | **Kintsugi** | Low | Security baseline (Level 6-7 hook) | AST-level bash parsing before execution. Catches `$(...)` hidden commands. Reversible by default. |
| 3 | **CodeBurn** | Low | O2 Vitality sense | Token cost per rule/agent/session. Identifies CLAUDE.md bloat. Health grade (A-F). |

### P1 — This Sprint (1-2 weeks, medium effort)

| # | Project | Effort | 鲤鱼 Mapping | What It Does |
|---|---------|--------|-----------------|--------------|
| 4 | **Langfuse** | Medium | All 7 Metacog senses | OTel-native tracing. Quantified audit trail of O2, Chronos, Nociception, Echo, Drift, Spatial, Vestibular. |
| 5 | **Hybrid Retrieval** | Medium | knowledge-base.py | Add sqlite-vec + graph edges to existing SQLite+FTS5. RRF fusion. Adopt Knowledge MCP's three-pillar pattern. |
| 6 | **Midscene.js** | Low-Medium | Web testing rules | Drop-in for Playwright. Vision-driven assertions. Visual regression. Natural language test authoring. |

### P2 — Next Sprint (2-4 weeks, higher effort)

| # | Project | Effort | 鲤鱼 Mapping | What It Does |
|---|---------|--------|-----------------|--------------|
| 7 | **OMEGA-style Memory** | Medium | MEMORY.md + reflections.jsonl | Auto-capture facts/decisions/errors. Ebbinghaus decay with TTL. Checkpoint/resume. Cross-agent shared memory. |
| 8 | **DSPy Rule Optimization** | Medium | evolve.py + rules/ | Treat each ECC rule as DSPy Signature. Bayesian optimization over prompt variants. Auto-generate hardened rules from framework descriptions. |
| 9 | **GNAP Coordination** | Low-Medium | Lock files + heartbeats + completion logs | Formalize as `.gnap/` directory: Agents, Tasks, Runs, Messages. `git log` as audit trail. |
| 10 | **EvalMonkey** | Medium | Self-evolution engine | 28 chaos injection profiles. Production Reliability Score. Tests whether Metacog senses survive adversarial conditions. |
| 11 | **Veritas** | Medium | Pre-commit quality gate | Mutation + property testing + fuzzing. AI-ready repair prompts. Deterministic-by-default with optional LLM hook. |

### Watch List — Evaluate, Don't Absorb Yet

| # | Project | Reason to Wait |
|---|---------|----------------|
| 12 | **Browser-Use** (98k stars) | Heavyweight. Evaluate for complex flows Midscene.js can't handle. |
| 13 | **guard0/g0** (46 stars, 1,180+ rules) | High rule coverage but low community validation. Wait for 200+ stars. |
| 14 | **TextGrad** (Nature 2025) | Research-quality. Philosophical alignment with 鲤鱼's gradient-based evolution but needs production hardening. |
| 15 | **CROSS + agent-comm** | Evaluate whether 鲤鱼's existing hooks (Levels 5-7) already cover these patterns. |
| 16 | **Promptomatix** (Salesforce) | Promising zero-config approach but DSPy is more battle-tested (34k vs ~100 stars). |
| 17 | **AgentWatch** | Cascade detection is valuable but TypeScript-only. Wait for Python bindings or reimplement the DAG-walking algorithm. |
| 18 | **Polis Protocol** | Multi-armed bandit routing is elegant but 鲤鱼's agent selection is currently simpler. Absorb GNAP first. |

---

## New Capabilities 鲤鱼 Would Gain

| Capability | Current State | After P0 | After P1 | After P2 |
|-----------|--------------|----------|----------|----------|
| **Test quality assurance** | Coverage % only | Mutation score on changed lines | — | Adversarial verification + chaos |
| **Bash safety** | Prompt-level warnings | AST-level deterministic gate | — | — |
| **Cost attribution** | None | Per-rule token cost + health grade | — | — |
| **Agent observability** | Metacog in-memory only | — | Quantified 7-sense audit trail | Cascade detection across agents |
| **Knowledge retrieval** | FTS5 text search only | — | FTS5+vector+graph hybrid RRF | LLM-inferred semantic edges |
| **Persistent memory** | Manual MEMORY.md | — | — | Auto-capture + decay + cross-agent |
| **Prompt optimization** | Manual CLAUDE.md editing | — | — | DSPy Bayesian optimization + A/B metrics |
| **Multi-agent coordination** | Custom lock files | — | — | Formalized GNAP protocol + audit trail |
| **Resilience testing** | None | — | — | Chaos injection + reliability scoring |
| **E2E testing** | Playwright selectors | — | Vision-driven natural language | Agentic goal-mode testing |
| **Code verification** | None beyond tests | — | — | Mutation + property + fuzz pipeline |

---

## Critical Insight: The Mutation Testing Mandate

The single most important finding across all three reports is the independent convergence on mutation testing as the mandatory verification layer for AI-generated code:

- **SWE-ABS** (Feb 2026): ~20% of "solving" SWE-bench patches were semantically incorrect due to weak tests
- **SWE-Mutation** (ACL 2026): RDR drops from 71% → 40% under agentic mutants
- **Tautest**: Purpose-built for AI-written tests; surviving mutants → AI-ready fix prompts
- **Veritas**: Adversarial verification with mutation + property + fuzzing pipeline
- **Plumbline**: Gate engine enforces plan-state before commit
- **DAE**: Differential mutation testing as Checkpoint 8 "Hardening"
- **Qodo CI**: Chaos verification step that mutates source to confirm tests catch bugs

**For 鲤鱼's TDD workflow, this means: test generation MUST be followed by mutation verification before any task is marked complete.** Coverage metrics alone are insufficient and create false confidence worse than no tests.

---

## Architectural Principle: MCP-Native Everything

Every project across all three domains converges on MCP as the universal interface. For 鲤鱼, this means:

1. Memory → MCP server (OMEGA pattern)
2. Observability → MCP tools (Langfuse pattern)
3. Testing → MCP tools (Midscene.js, UniAuto pattern)
4. Safety → MCP gateway (Kintsugi pattern)
5. Coordination → MCP tools (agent-comm pattern)

鲤鱼 should adopt an **MCP-first plugin architecture** so that any of these tools can be swapped in/out without architectural changes.

---

## Sources

Full source tables are in the individual agent reports:
- afc66: `/Users/holyty/.claude/projects/-Users-holyty/0f337237-0ccf-4544-9f9a-441536e22ded/subagents/agent-afc66ab092555fd46.jsonl`
- a3cad: `/Users/holyty/.claude/projects/-Users-holyty/0f337237-0ccf-4544-9f9a-441536e22ded/subagents/agent-a3cad02b2851c0edf.jsonl`
- a83fc: `/Users/holyty/.claude/projects/-Users-holyty/0f337237-0ccf-4544-9f9a-441536e22ded/subagents/agent-a83fc2b1f4d4a16c8.jsonl`

Key source projects referenced in synthesis:
- [Tautest](https://dev.to/canblmz/i-built-tautest) — Mutation testing for AI-written tests
- [Kintsugi](https://github.com/arrowassassin/kintsugi) — Deterministic bash safety gate
- [CodeBurn](https://github.com/coder/codeburn) — Token cost tracking
- [Langfuse](https://github.com/langfuse/langfuse) — OpenTelemetry-native agent tracing
- [Midscene.js](https://github.com/web-infra-dev/midscene) — Vision-driven UI testing
- [OMEGA](https://github.com/IAAR-Shanghai/Awesome-AI-Memory) — LongMemEval 95.4% memory system
- [DSPy](https://github.com/stanfordnlp/dspy) — Programmatic prompt optimization
- [GNAP](https://github.com/farol-team/gnap) — Git-Native Agent Protocol
- [EvalMonkey](https://github.com/Corbell-AI/evalmonkey) — Chaos engineering for AI agents
- [Veritas](https://github.com/Jacobious52/veritas) — Adversarial verification for AI code
- [Knowledge MCP](https://github.com/PaulTheSecond/knowledgebase-mcp) — Hybrid FTS5+vec+graph RRF
- [Browser-Use](https://github.com/browser-use/browser-use) — AI browser agent (98k stars)
