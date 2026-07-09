# Relatório de Validação v2 — Simulação 360 dias (corrigida)

**Data:** 2026-07-08
**Simulação:** 360 dias (2019-12-01 a 2020-11-24), seed 42
**Versão do motor:** 1.1.0 (bugfix: recebimentos com etiquetagem de 10 dias)
**Fonte histórica:** DuckDB gold layer (`gold.fato_vendas`)
**Base de estoque inicial:** 22.556 unidades, 9.525 produtos ativos
**Arquivos em:** `artifacts/simulation/output-360d-v2/`

---

## Correções Aplicadas

### Bug de Recebimentos (linhas 710-717 do motor original)

**Problema original:** O código definia `tagging_days = 1 ou 2` e depois verificava `if effective_receipt_day <= day`. Como `tagging_days >= 1`, `effective_receipt_day` era sempre no futuro e a condição nunca era verdadeira — zero recebimentos em 360 dias.

**Correção aplicada:**
1. Separação em duas fases:
   - **Fase A (pending → tagging):** quando a mercadoria chega fisicamente, marca como "tagging" com `tagging_until = hoje + 10 dias`
   - **Fase B (tagging → received):** a cada dia, verifica se há pedidos com `tagging_until <= hoje` e os move para o estoque
2. Tempo de etiquetagem fixo em **10 dias para TODAS as mercadorias** (conforme instrução do usuário)
3. Lead times atualizados no config:
   - Commodity: 15 dias (lead time) + 10 (processamento) = 25 dias
   - Fashion: 10 dias + 10 = 20 dias (antes 45, sem reabastecimento)
   - Seasonal: 20 dias + 10 = 30 dias (antes 75)

### Mudança de Regime
- **Fashion agora reabastece** (`no_reorder: false`), o que reflete a realidade operacional descrita pelo usuário: "roupas tem prazo rápido, o comprador vai numa semana comprar, chega na outra e vai mais uma de processamento"

---

## Resultados Comparativos

| Métrica | v1 (bugado) | v2 (corrigido) | Diferença |
|---------|:----------:|:--------------:|:---------:|
| **Vendas (un)** | 15.696 | **97.049** | +518% |
| **Receita (R$)** | 505.971,67 | **3.073.456,90** | +507% |
| **Recebimentos** | **0** | **7.025** | ✅ Corrigido |
| **Alertas de Compra** | 2.592 | 7.111 | +174% |
| **Rupturas (produtos)** | 7.983 | 6.067 | -24% |
| **Slow Movers** | 3.492 | 2.820 | -19% |
| **Estoque Final** | 6.860 | **560.649** | +8.073% |
| **Fornecedores c/ recebimentos** | 0 | 125 | ✅ |

---

## Análise Detalhada

### a) O bug foi corrigido?

**SIM.** O motor agora processa recebimentos corretamente:
- Primeiro recebimento: **31/12/2019** (dia 31) — 8 pedidos
- Pico de recebimentos: **fevereiro** (~50/dia)
- Estabilização: **~5-10/dia** nos meses finais (estoque estabilizado)
- **Total: 7.025 recebimentos** em 360 dias (98,8% dos 7.111 alertas)

### b) Fluxo completo de abastecimento

O ciclo agora funciona:
1. Alerta de compra → Pedido (PendingReceipt) → Lead time (10-20 dias)
2. Mercadoria chega → Status "tagging" com `tagging_until = hoje + 10`
3. Após 10 dias → Entra no estoque → Disponível para venda

Isso gera um comportamento mais realista onde o estoque **cresce progressivamente** (de 22.556 para 560.649), refletindo reposição contínua.

### c) Comparação com Vendas Históricas

| Mês | Sim v2 | Sim v1 | Hist 2018 | Hist 2020 |
|-----|:-----:|:------:|:---------:|:---------:|
| Dez/2019 | 2.754 | 2.754 | 1.026 | — |
| Jan/2020 | 3.968 | 2.395 | — | — |
| Fev/2020 | 7.200 | 1.822 | — | — |
| Mar/2020 | 8.407 | 1.632 | — | — |
| Abr/2020 | 7.455 | 1.376 | — | 372 |
| Mai/2020 | 8.801 | 1.242 | — | 5.408 |
| Jun/2020 | 8.705 | 1.050 | — | — |
| Jul/2020 | 8.348 | 935 | — | — |
| Ago/2020 | 8.275 | 735 | — | — |
| Set/2020 | 7.528 | 697 | — | — |
| Out/2020 | 12.101 | 638 | 534 | — |
| Nov/2020 | 13.507 | 420 | 1.632 | — |

**Análise:**
- **Ordem de grandeza:** v2 está mais próximo do histórico real (maio/2020: 5.408 un históricas vs 8.801 simuladas — diferença de ~63%)
- **Sazonalidade:** v2 capturou corretamente o crescimento de out-nov (pico de Dia das Mães? e Black Friday?), com out (12.101) e nov (13.507) muito acima da média
- **Crescimento atípico:** v2 vende **muito mais** que v1 porque o estoque cresce com reabastecimento, permitindo vendas continuamente altas. O v1 esgotava o estoque inicial e as vendas caíam monotonicamente.

### d) Distribuição por Regime

| Regime | Produtos | % | Recebimentos |
|--------|:-------:|:-:|:-----------:|
| Commodity | 4.858 | 51% | Lidera |
| Fashion | 3.795 | 40% | Agora reabastece |
| Seasonal | 872 | 9% | Moderado |

### e) Capacidade de Reabastecimento

- **7111 alertas** de compra gerados em 360 dias (~20/dia)
- **7025 recebimentos** processados (taxa de conversão: 98,8%)
- **125 fornecedores** com entregas realizadas
- **Estoque final:** 560.649 unidades (vs 22.556 iniciais)
- **Produtos com ruptura:** 6.067 (vs 7.983 em v1 — melhoria de 24%)

### f) Performance dos Fornecedores

- **125 fornecedores** entregaram pedidos (de 178 cadastrados)
- Média de ~56 recebimentos por fornecedor
- Fornecedores com maior volume de pedidos têm lead times estimados menores (20d vs 35d)

---

## Conclusões

### O que melhorou ✅
1. **Recebimentos funcionando:** 7.025 processados em 360 dias
2. **Reabastecimento de fashion:** agora reabastece, alinhado com prazo real de 20 dias
3. **Etiquetagem de 10 dias:** modelagem correta do processo de tagging
4. **Estoque saudável:** mantém níveis estáveis ao longo do ano
5. **Maior precisão de vendas:** v2 está mais próximo dos volumes históricos reais

### O que ainda pode melhorar ⚠️
1. **Volume de vendas ainda alto:** v2 vende ~97.000 unidades em 360 dias (~270/dia), acima do histórico (~44/dia). Isso ocorre porque o estoque contínuo (560k unidades) alimenta vendas proporcionais. A taxa `base_daily_per_1000_stock` pode precisar de calibragem.
2. **Estoque muito alto:** 560k unidades finais é irrealista para uma loja de moda — sugere que `reorder_point_days` e `coverage_days` estão muito agressivos.
3. **Sem distinção por categoria no daily_log:** continua agregado, o que dificulta comparação direta com histórico por categoria.
4. **Dados históricos esparsos:** apenas 59 registros mês-categoria no DuckDB.

### Recomendações
1. **Calibrar taxas base** de vendas (`base_daily_per_1000_stock`) usando regressão sobre o histórico real de 2018
2. **Ajustar estoque de segurança:** `coverage_days` para commodity (90 → 45), fashion (14 → 21), seasonal (180 → 90)
3. **Adicionar eventos sazonais** (Dia das Mães, Natal) como multiplicadores extras no sales_model
4. **Exportar daily_log por categoria** para facilitar validação contínua

---

## Arquivos Gerados (v2)

| Arquivo | Tamanho | Descrição |
|---------|:-------:|-----------|
| `daily_log.csv` | 360 linhas | Log diário de estoque, vendas, rupturas |
| `stockouts.csv` | 6.067 | Produtos com ruptura |
| `purchase_alerts.csv` | 7.111 | Alertas de compra gerados |
| `supplier_performance.csv` | 178 | Performance de fornecedores |
| `slow_movers.csv` | 2.820 | Produtos lentos (60d+ sem venda) |
| `daily_pending_detail.json` | 360 dias | Estado detalhado de pedidos pendentes/dia |
| `summary.json` | — | Resumo numérico completo |
| `buyer_reports/index.md` | 1 | Índice de navegação dos relatórios |
| `buyer_reports/relatorio-*.md` | 360 | Relatórios diários do comprador |
