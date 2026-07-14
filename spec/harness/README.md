# Harness — Chez Violeta

## Componentes e verificações

### Motor de Simulação
- `python simulation_engine.py --days 30` — Simulação básica
- Verificar: recebimentos > 0, alertas > 0, estoque final > inicial

### Dashboard
- Abrir `index.html` no navegador
- Verificar: KPIs carregam, abas funcionam, fornecedores aparecem

### Prophet
- `python _train_prophet.py` — Re-treinar modelo
- Verificar: R² > 0.7, previsão > 0 para todas categorias

### ETL Gold Layer
- `python etl_gold.py` — Recarregar dados do PostgreSQL
- Verificar: row counts nas tabelas gold

## Convenções

- Todo harness deve especificar: comando, critério de sucesso, tolerância
- Nível 1 (cada execução): sum() com ±0.5% de tolerância
- Nível 2 (semanal): sum() por grupo com ±1.0%
- Nível 3 (mensal): amostra visual
- Resultados: OK → prosseguir | ALERT → investigar | CRITICAL → bloquear
