# Changelog

## [Unreleased]

### Added
- Motor de simulação de estoque 360d
- Dashboard do comprador v6 (fornecedores + vestuário)
- Chatbot de processos da loja
- Modelo Prophet de previsão semanal (R²=0.726)
- Regressão OLS inicial (substituída pelo Prophet)

### Fixed
- Bug de recebimentos nunca processados (tagging days)
- Dados de vendas corrigidos: fato_vendas → fato_estoque_diario.qtd_venda (10k → 676k registros)
- Dashboard: corrigido rendering com \r\r\n

### Changed
- Definição de atraso de fornecedor: >45 dias (antes qualquer atraso)
- Classificação de produtos: status FORA DE LINHA/INATIVO/SALDO não são repostos
- Cobertura alvo: 120d (antes 90d)
- Compra: por fornecedor, max 1 pedido/mês, mínimo R$10k
- Vestuário: sem fornecedor, compra pessoal por tipo+tamanho
