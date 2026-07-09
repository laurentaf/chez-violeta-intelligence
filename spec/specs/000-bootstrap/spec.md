# SPEC-000: Bootstrap — Chez Violeta Intelligence Platform

**Status:** ACEITO
**Version:** 1.0
**Authors:** Laurent (data engineer)
**Owner:** Laurent

---

## 1. Executive Summary
Platform to unify Chez Violeta operations data (sales, inventory, purchases, finance, HR) into a single analytical data warehouse with dashboards, pricing models, and demand forecasting.

## 2. Context
Dados extraídos de Oracle DMP (sistema GAVARNIE, 2020) para PostgreSQL.
100 tabelas de negócio, 13.6 milhões de registros.
Schema completo mapeado incluindo PII (NOME_CLIENTE, EMAIL, CNPJ).

## 3. Decisão Inicial
**Arquitetura: Medallion (bronze → silver → gold) com DuckDB.**
- Bronze: carga direta do PostgreSQL (COPY)
- Silver: limpeza, tipagem, joins, qualidade
- Gold: star schema dimensional (fatos + dimensões)

## 4. Critérios de Pronto
- [ ] Star schema modelado e documentado
- [ ] Gold layer queryável no DuckDB
- [ ] Pelo menos 1 dashboard funcional (vendas)
- [ ] Pipeline reproduzível do zero
- [ ] DQ checks implementados (nulls, duplicatas, ranges)

## 5. Sources
| Table | Rows | Description |
|-------|-----:|-------------|
| VENDAS_CUPONS | 528,953 | Cabeçalho de vendas |
| VENDAS_ITENS_CUPONS | 0 | Itens de venda (vazio — usar BRAX_ITENS) |
| BRAX_ITENS_CUPONS | 8,940 | Itens de venda (sistema legado) |
| ESTOQUES_DIARIOS | 9,509,410 | Estoque diário por SKU |
| ARTIGOS_MODELOS | 5,435 | Catálogo de produtos |
| ARTIGOS_VARIANTES | 35,588 | SKUs (cor + tamanho) |
| CLIENTES | 1,097 | Clientes |
| COMPRAS | 2,950 | Pedidos de compra |
| FORNECEDORES | 188 | Fornecedores |
| FI_EXTRATO_BANCARIO | 47,842 | Extrato bancário |

## 6. Destination
Gold layer (star schema) em DuckDB.

## 7. Refresh Strategy
Modo: delete-insert (full refresh por enquanto; futuro: incremental com watermark).
