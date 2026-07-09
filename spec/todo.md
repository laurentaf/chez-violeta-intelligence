# TODO — Chez Violeta Intelligence Platform

---

## Stage 0 — SDD Scaffold (Missão 0)

- [x] spec/constitution.md
- [x] spec/todo.md (este arquivo)
- [x] spec/adr/_template.md
- [x] spec/adr/README.md
- [x] spec/harness/_template.md
- [x] spec/specs/000-bootstrap/spec.md
- [x] contract.md
- [x] README.md
- [x] spec/design-direction.md

## Stage 1 — Data Model (Star Schema)

- [x] Mapear tabelas fonte → dimensões
- [x] Modelar fato VENDAS
- [x] Modelar fato ESTOQUE_DIARIO
- [x] Modelar fato COMPRAS
- [x] Modelar fato TROCAS
- [x] Modelar dim PRODUTO (SCD tipo 2)
- [x] Modelar dim TEMPO
- [x] Modelar dim LOJA
- [x] Modelar dim FORNECEDOR
- [x] Gerar DDL gold layer
- [x] Documentar modelo dimensional

## Stage 2 — Dashboards & Analytics

- [x] Dashboard de Vendas (receita, ticket médio, sazonalidade)
- [x] Dashboard de Estoque (giro, cobertura, ruptura)
- [x] Modelo de precificação (elasticidade-preço)
- [ ] Relatório de performance por loja/produto

## Stage 2b — Table Relationships & Process Docs

- [x] Validação de integridade referencial (PK/FK entre fatos e dimensões)
- [x] Documentação do processo de entrada de mercadorias (NF + etiquetagem)
- [x] Gerador de vendas sintéticas com sazonalidade (ARIMA + temperatura)

## Stage 2c — Motor de Simulação de Estoque

- [x] Arquitetura completa do motor de simulação (spec)
- [x] simulation_engine.py (classificação de regime, lead time, vendas, alertas)
- [x] simulation_config.json com parâmetros por regime
- [x] Simulação de 30 dias executada
- [x] Outputs: daily_log, stockouts, purchase_alerts, supplier_performance, slow_movers
- [x] Dashboard HTML com gráficos da simulação

## Stage 3 — Advanced Analytics

- [x] Motor de Simulação de Estoque (360 dias, recebimentos, alertas)
- [x] Dashboard do Comprador (alertas, fornecedores, produtos lentos)
- [x] Chatbot de Processos da Loja
- [ ] Pipeline automatizado de atualização

## Stage 4 — Executive Deck

- [ ] Apresentação executiva dos resultados

---

## Completed

- [x] Schema extraído do DMP Oracle (100 tabelas, 13.6M linhas)
- [x] Dados carregados no PostgreSQL (localhost:5433/chez_violeta)
- [x] Pipeline de migração Oracle → PostgreSQL
