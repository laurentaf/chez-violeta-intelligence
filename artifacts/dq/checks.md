# Chez Violeta — Data Quality Baseline Checks

## Objetivo

Garantir que a camada gold (star schema) mantenha integridade referencial,
consistência de dados e ausência de anomalias antes de ser consumida por
dashboards e modelos preditivos.

---

## Checks Implementados

### DQ-01: PK Uniqueness (BLOCK)
**Tabelas:** Todas as dimensões e fatos
**Descrição:** Nenhuma tabela gold pode ter duplicatas na PK.
**SQL:**
```sql
SELECT 'dim_produto' AS tabela, id_produto, COUNT(*)
FROM gold.dim_produto GROUP BY id_produto HAVING COUNT(*) > 1
UNION ALL
SELECT 'dim_tempo', id_data, COUNT(*)
FROM gold.dim_tempo GROUP BY id_data HAVING COUNT(*) > 1
UNION ALL
SELECT 'dim_loja', id_loja, COUNT(*)
FROM gold.dim_loja GROUP BY id_loja HAVING COUNT(*) > 1
-- ... (replicate for all tables)
```
**Severidade:** BLOCK — se falhar, o pipeline deve abortar.
**Threshold:** 0 duplicatas.

### DQ-02: FK Referential Integrity (BLOCK)
**Tabelas:** Todos os fatos
**Descrição:** Toda FK em fatos deve ter correspondência na dimensão.
**Implementação:** Views `gold.dq_*_sem_*` no schema-gold.sql.
**Severidade:** BLOCK — orphan rows corrompem análises.
**Threshold:** 0 orphans.

### DQ-03: Business Key Uniqueness (BLOCK)
**Tabelas:** dim_loja, dim_fornecedor, dim_cliente, dim_vendedor
**Descrição:** Business keys (códigos do ERP) devem ser únicas.
**SQL:**
```sql
SELECT cod_estabelecimento, COUNT(*)
FROM gold.dim_loja GROUP BY cod_estabelecimento HAVING COUNT(*) > 1
```
**Severidade:** BLOCK
**Threshold:** 0 duplicatas.

### DQ-04: SCD2 No Overlap (BLOCK)
**Tabela:** dim_produto
**Descrição:** Períodos de vigência SCD2 não podem se sobrepor para o mesmo business key.
**SQL:**
```sql
SELECT a.cod_artigo, a.cod_cor, a.cod_tamanho,
       a.dat_inicio_vigencia, a.dat_fim_vigencia,
       b.dat_inicio_vigencia, b.dat_fim_vigencia
FROM gold.dim_produto a
JOIN gold.dim_produto b
  ON a.cod_artigo = b.cod_artigo
 AND a.cod_cor = b.cod_cor
 AND a.cod_tamanho = b.cod_tamanho
 AND a.id_produto <> b.id_produto
 AND a.dat_inicio_vigencia <= COALESCE(b.dat_fim_vigencia, '9999-12-31')
 AND b.dat_inicio_vigencia <= COALESCE(a.dat_fim_vigencia, '9999-12-31')
```
**Severidade:** BLOCK
**Threshold:** 0 overlaps.

### DQ-05: Negative Quantities (WARN)
**Tabelas:** fato_vendas, fato_estoque_diario, fato_compras, fato_trocas
**Descrição:** Quantidades devem ser >= 0. Negativo = possível erro de ETL ou source.
**Implementação:** View `gold.dq_estoque_negativo`.
**Severidade:** WARN — notifica operador, não bloqueia.
**Threshold:** > 1% das linhas com qtd < 0.

### DQ-06: Future-Dated Sales (WARN)
**Tabela:** fato_vendas
**Descrição:** Vendas com data futura são raras e indicam possível erro.
**Implementação:** View `gold.dq_vendas_futuras`.
**Severidade:** WARN
**Threshold:** Qualquer linha futura.

### DQ-07: Negative or Zero Sales (WARN)
**Tabela:** fato_vendas
**Descrição:** Valor líquido negativo ou zero pode indicar venda cancelada não processada.
**SQL:**
```sql
SELECT COUNT(*) as qtd, COUNT(*) * 100.0 / (SELECT COUNT(*) FROM gold.fato_vendas) as pct
FROM gold.fato_vendas WHERE val_venda_liquida <= 0
```
**Severidade:** WARN se > 2%
**Threshold:** 2% das linhas.

### DQ-08: Null FK Ratio (WARN)
**Tabela:** fato_vendas.id_cliente
**Descrição:** Cliente nulo em vendas é aceitável (venda sem cadastro), mas
alta proporção indica problema de integração.
**SQL:**
```sql
SELECT COUNT(*) as total, SUM(CASE WHEN id_cliente IS NULL THEN 1 ELSE 0 END) as sem_cliente,
       AVG(CASE WHEN id_cliente IS NULL THEN 1.0 ELSE 0 END) * 100 as pct_sem_cliente
FROM gold.fato_vendas
```
**Severidade:** WARN se > 30%
**Threshold:** > 30% de nulos.

### DQ-09: Column Existence Check (BLOCK)
**Tabelas:** Todas as gold
**Descrição:** Verificar se todas as colunas esperadas existem no schema.
**Implementação:** Script de boot check.
**Severidade:** BLOCK

### DQ-10: Row Count Trend (WARN)
**Tabelas:** Todas
**Descrição:** Monitorar variação brusca no volume de linhas entre cargas.
**Implementação:** Pipeline step compara row count atual vs. média dos últimos 7 dias.
**Severidade:** WARN se variação > 50%.

---

## Alert Channels

| Severidade | Canal | Ação |
|------------|-------|------|
| BLOCK | n8n → Slack/Email | Pipeline aborta, notificação imediata |
| WARN | n8n → Slack | Pipeline continua, notificação para revisão |

---

## Responsabilidade

- **Owner:** data-architect (Laurent)
- **Manutenção:** A cada alteração no modelo gold ou nas fontes
- **Revisão:** Semanal (junto com o refresh semanal das dimensões)
