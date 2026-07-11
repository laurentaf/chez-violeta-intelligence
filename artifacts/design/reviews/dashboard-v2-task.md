# Dashboard do Comprador Chez Violeta v2 — Resultado

## O que foi criado/atualizado

### `artifacts/design/dashboard-comprador/index.html` (SOBRESCRITO)
Dashboard self-contained de 231 KB com dados embutidos (200 alertas, 178 fornecedores, estoque por loja). Inclui:

1. **KPIs no topo** — Total alertas (7.111), % ALTO/CRÍTICO (99,1%), ruptura antes do pedido (7.066), pior fornecedor (VALENTINA LINGERIE, 50%)
2. **Tabela de Alertas Interativa** — 13 colunas, ordenação por clique no cabeçalho, filtros (Urgência/Categoria/Fornecedor/Risco), destaque vermelho onde NÃO chega antes da ruptura
3. **Gráficos** — Distribuição de risco (rosca), alertas por categoria (barras horizontais), top 10 fornecedores por valor
4. **Seção Risco de Ruptura vs Pedidos** — Cards explicativos (🟢🟡🔴⚫) + tabela com cobertura e risco
5. **Seção Cobertura por Loja** — Estoque por loja para produtos em alerta (1.008 registros)
6. **Seção Performance de Fornecedores** — Tabela ordenável com compliance, nota A-D, coluna de explicação
7. **Design System** — Vinho #7B2D4E, Dourado #C9A84C, Off-white #FAF8F5, Cormorant Garamond + Inter
8. **MOCK banner** no topo
9. **Responsivo** — adapta a mobile

### `artifacts/design/dashboard-comprador/README.md`
Documentação completa com seções, metodologia de risco, design system e instruções de uso.

### `artifacts/design/dashboard-comprador/source.md` (ATUALIZADO)
Design source com frontmatter synthetic + versão 2 melhorias.

### Arquivos auxiliares
- `data.json` — dados extraídos (205 KB)
- `generate_dashboard.py` — gerador do HTML
- `extract_data.py` — extração dos CSVs

## Detalhes Técnicos

- Chart.js 4.4.4 via CDN (requer internet)
- Google Fonts (Cormorant Garamond + Inter) via CDN
- Dados embutidos em variáveis JavaScript no próprio HTML
- Abre em `file:///` sem necessidade de servidor
- Ordenação client-side (JavaScript puro, sem dependências)

## Design Source

Ver `artifacts/design/dashboard-comprador/source.md`
