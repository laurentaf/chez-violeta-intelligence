# Constitution — Chez Violeta Intelligence Platform

**Version:** 1.0 | **Status:** Vigente

---

## Princípios

1. **Missão 0 é obrigatória** — Nenhum estágio produtivo começa sem SDD scaffold completo.
2. **Medallion invariante** — Pipeline segue bronze → silver → gold, sem leitura cruzada.
3. **Testabilidade mandatória** — Todo componente tem pre-condição e HARNESS.
4. **Test-first** — Código só após critérios de aceitação definidos.
5. **Idempotência** — Jobs executam N vezes com o mesmo resultado.

## Article I — Missão 0 é Obrigatória
Nenhum estágio produtivo começa antes do SDD scaffold completo.
Stage 0 antecede Stage 1. Gate mecânico: subagent_boot_check.py 6ª dimensão.

## Article II — Medallion as Structural Invariant
Every pipeline follows bronze → silver → gold. No cross-layer reads.

## Article III — Mandatory Testability
Every component has pre-condition, post-condition, HARNESS level.

## Article IV — Test-First Imperative
No code before acceptance criteria and validations defined.

## Article V — Idempotency
Every job executable N times without different results.

## Article VI — Ubiquitous Language
Code names reflect business vocabulary (vendas, estoques, compras, financeiro).

## Article VII — No Cross-Layer Reads
Silver reads from silver. Gold reads from silver.

## Article VIII — Simplicity
Max 3 medallion layers. No speculative features.

## Article IX — Anti-Abstraction
Use tools directly. No unnecessary wrappers.

## Article X — Integration Before Implementation
Contracts before code. HARNESS before production.

## Article XI — PII Safety First
Dados sintéticos ou anonimizados em artefatos públicos.
Nunca expor CPF, nome completo, email ou telefone em dashboards.

## Scope
Projeto de inteligência operacional para a Chez Violeta.
Cobre: star schema dimensional, dashboards de vendas/estoque,
modelo de precificação (elasticidade), previsão de demanda,
pipelines automatizados, e apresentação executiva.

## Non-goals
- Não substitui o sistema ERP/GAVARNIE Oracle
- Não é plataforma de e-commerce
- Não faz integração com marketplaces (Mercado Livre)
- Não é sistema de RH ou folha de pagamento
