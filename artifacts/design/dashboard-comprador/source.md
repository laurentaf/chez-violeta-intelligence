---
synthetic: true
kind: dashboard
label: "mock, not for production"
granted_by: project_yaml
granted_at: 2026-07-08T10:00:00Z
reason: "dados da simulação output-360d-v2 previamente executada (seed=42, 360 dias)"
---

# Fonte de Design — Dashboard do Comprador Chez Violeta v2 (corrigido)

**DESIGN.md de referência:** O presente dashboard segue o design system
Chez Violeta definido no brief do projeto:

- **Paleta:** Vinho #7B2D4E, Dourado #C9A84C, Off-white #FAF8F5
- **Tipografia:** Cormorant Garamond (headings), Inter/System (body)
- **Projeto:** chez-violeta-intelligence
- **Needs:** dashboard
- **Capabilities:** ladesign
- **Data policy:** `synthetic: true` (dados de simulação de 360 dias)

## Fonte de dados

DuckDB gold layer (`chez_gold.duckdb`) + Prophet forecast CSV:
- `gold.dim_produto` — 15.469 produtos ativos com estoque
- `gold.fato_estoque_diario` — 632 dias de histórico (2018-03 ~ 2019-11)
- `prophet_forecast_future.csv` — Previsão Prophet 120d por categoria

## Versão 2 — Correções (2026-07-13)

vs versão anterior (`generate.py` original):

1. ✅ **VESTUARIO corrigido**: Produtos de `des_categoria = 'VESTUARIO'` vão SEMPRE para a aba de vestuário, mesmo que tenham `cod_fornecedor` preenchido. Antes, todos os 17.886 VESTUARIO iam para fornecedor (todos têm código).
2. ✅ **Velocidade diária corrigida**: Agora usa `total_vendas / 632` (todos os dias do período), não `total_vendas / dias_com_venda`. Ex: um SKU que vendeu 30 un em 8 dias: antes previa 450 un (30/8×120), agora prevê 6 un (30/632×120).
3. ✅ **Custo zero corrigido**: Fallback para custo médio da categoria quando `val_custo_inicial = 0` ou NULL. Médias: VESTUARIO R$28,98, UNDERWARE R$10,33, LINHA NOITE R$23,44, MODA PRAIA R$24,33, EROTICA R$11,20, ACESSORIOS R$3,58.
4. ✅ **Previsão proporcional**: Cada SKU recebe share da previsão total da categoria pelo Prophet 120d: `share = vel_sku / sum(vel_categoria) * prophet_yhat_categoria`. Categorias sem Prophet (FITNESS, BIJU, EROTICA, ACESSORIOS) usam fallback `vel × 120`.

## Artefatos

- `dashboard-comprador/index.html` — Dashboard self-contained (110 KB)
- `dashboard-comprador/source.md` — Este arquivo (fonte de design)
- `dashboard-comprador/generate.py` — Gerador do HTML (DuckDB + Prophet)

## Dados embutidos

- 20 fornecedores mais urgentes (com 3.058 grupos de SKU)
- 30 tipos de vestuário mais urgentes (5.006 SKU agregados)
- Previsão Prophet 120d por categoria: UNDERWARE (36.810), VESTUARIO (17.997), MODA PRAIA (14.040), LINHA NOITE (7.837), OUTROS (524)

## Notas Técnicas

- Geração: `uv run python artifacts/design/dashboard-comprador/generate.py`
- DuckDB: `artifacts/data/chez_gold.duckdb`
- Prophet: `artifacts/data/prophet_forecast_future.csv`
- Navegador: Chrome, Firefox, Edge (moderno)
- Abertura local: `file:///F:/projects/chez-violeta-intelligence/artifacts/design/dashboard-comprador/index.html`
