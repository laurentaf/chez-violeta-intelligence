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

## Article XII — Simulação de Estoque com ARIMA

O motor de simulação de estoque opera em regime dia-a-dia integrando:
- **Vendas simuladas** via modelo ARIMA com sazonalidade semanal e temperatura
- **Lead times** por regime de fornecedor (normal, crítico, sazonal)
- **Regras de reposição** automática: cobertura alvo de 120d, pedido mínimo R$10k
- **Alertas** de ruptura iminente (estoque < 15d de cobertura)
- **Recebimentos** programados com base em pedidos + lead time
- Outputs obrigatórios: daily_log, stockouts, purchase_alerts, supplier_performance, slow_movers

## Article XIII — Dashboard de Compras por Fornecedor

O Dashboard do Comprador (v6) consolida:
- Alertas de reposição por fornecedor (produtos com cobertura < 120d)
- Performance histórica de entregas por fornecedor (atraso > 45d)
- Lista de produtos lentos (slow movers) por loja
- Produtos FORA DE LINHA/INATIVO/SALDO — excluídos de reposição
- Vestuário: compra pessoal por tipo+tamanho, sem fornecedor automático

## Article XIV — Chatbot de Processos da Loja

O chatbot operacional cobre:
- Procedimentos de entrada de mercadorias (NF → etiquetagem → loja)
- Regras de troca e devolução
- Política de precificação e margem
- Consulta de status de pedidos e recebimentos
- Baseado em documento de processos indexado, sem alucinação de procedimentos

## Article XV — Modelo Prophet de Previsão Semanal

O modelo de previsão de demanda semanal usa Facebook Prophet com:
- Tendência não-linear com changepoints
- Sazonalidade semanal e anual
- Efeitos de eventos sazonais (Dia das Mães, Natal, etc.)
- Validação: R² mínimo aceitável de 0.70
- Treinamento automático via `_train_prophet.py`
- Previsões > 0 para todas as categorias de produto

## Article XVI — Regras de Negócio Vinculantes

As regras abaixo são válidas para todos os componentes do sistema:

| Regra | Valor | Aplicação |
|-------|-------|-----------|
| Pedido mínimo por fornecedor | R$ 10.000,00 | Motor de simulação, alertas de compra |
| Cobertura alvo de estoque | 120 dias | Todos os relatórios de cobertura |
| Atraso crítico de fornecedor | > 45 dias | Dashboard, supplier_performance |
| Frequência máxima de pedido | 1 por mês por fornecedor | Motor de simulação |
| Produtos sem reposição | FORA DE LINHA, INATIVO, SALDO | Alertas, dashboard |
| Vestuário | Compra pessoal por tipo+tamanho | Sem fornecedor automático |
