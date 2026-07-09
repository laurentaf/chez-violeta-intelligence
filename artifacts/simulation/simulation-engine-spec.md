# Motor de Simulação de Estoque — Chez Violeta

## Spec de Arquitetura v1.0

**Data:** 2026-07-08
**Autor:** Orchestrator (Qwen 3.7 Plus) → Executor: DeepSeek V4 Flash
**Status:** READY para implementação

---

## 1. Visão Geral

Motor de simulação dia-a-dia que parte do estoque real atual, gera vendas sintéticas
com sazonalidade (ARIMA), simula recebimento de mercadorias com lead time variável,
e gera alertas de compra inteligentes.

### Arquitetura de alto nível

```
┌─────────────────────────────────────────────────────────────────┐
│                    SIMULATION ENGINE                             │
│                                                                  │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐  │
│  │  DIA 1   │───>│  DIA 2   │───>│  DIA 3   │───>│  DIA N   │  │
│  └────┬─────┘    └────┬─────┘    └────┬─────┘    └────┬─────┘  │
│       │               │               │               │         │
│  ┌────▼───────────────▼───────────────▼───────────────▼────┐   │
│  │              DAILY CYCLE (por dia simulado)               │   │
│  │                                                           │   │
│  │  1. Gerar vendas do dia (ARIMA + temperatura)            │   │
│  │  2. Abater do estoque                                    │   │
│  │  3. Verificar recebimentos pendentes (lead time)         │   │
│  │  4. Se lead time expirou → entrada NF → etiquetagem      │   │
│  │  5. Verificar ponto de reabastecimento                   │   │
│  │  6. Se abaixo do ponto → gerar alerta de compra          │   │
│  │  7. Registrar estado do dia                              │   │
│  └───────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    OUTPUTS                                  │  │
│  │  • Log diário (CSV): dia, categoria, vendas, estoque,     │  │
│  │    compras, alertas                                         │  │
│  │  • Relatório de rupturas (produtos zerados)               │  │
│  │  • Relatório de fornecedores (lead time real vs prometido)│  │
│  │  • Relatório de produtos lentos (sugestão de desconto)    │  │
│  │  • Dashboard HTML com gráficos da simulação               │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Regimes de Produto

Classificação baseada na análise dos dados reais (35K SKUs, 10M+ registros estoque):

### 2.1 Básico / Commodity
**Categorias:** UNDERWARE (BASICO, MEIA, SHAPEWARE, MATERNITY), FITNESS (BASICO)
**Características:**
- Alta repetição de compra (mesmo SKU comprado 10+ vezes)
- Produto contínuo (coleção "CONTINUO" ou "SEMI-CONTINUO")
- Demanda previsível, sazonalidade leve
- **Cobertura alvo: 90 dias** (poder de negociação de preço)
- **Reabastecimento:** Lote econômico, pedido a cada 30-45 dias
- **Lead time:** 15-30 dias (fornecedores nacionais)

### 2.2 Moda / Fashion
**Categorias:** VESTUARIO (CASUAL, JOVEM, WORK), BIJU/JOIAS
**Características:**
- Compra única por SKU (7907 SKUs de VESTUARIO CASUAL com 1 compra)
- Produto sazonal (coleções VERAO/INVERNO)
- Demanda volátil, tendência de moda
- **Cobertura alvo: 7-14 dias** (compra semanal)
- **Reabastecimento:** Não repõe SKU, compra nova coleção
- **Lead time:** 30-60 dias (antecipação de coleção)

### 2.3 Sazonal / Personalizado
**Categorias:** MODA PRAIA (FASHION), LINHA NOITE (INDEFINIDA)
**Características:**
- Mista: alguns SKUs com alta repetição (básicos), outros única
- Coleção anual (VERAO), recompra possível se sell-through > 70%
- Demanda fortemente sazonal (MODA PRAIA vende 3x mais no verão)
- **Cobertura alvo: 180-365 dias** (coleção anual)
- **Reabastecimento:** Recompra se vendendo bem; desconto se lento
- **Lead time:** 60-90 dias (produção sob encomenda)

---

## 3. Parâmetros de Simulação

### 3.1 Estado Inicial
```python
# Extraído de gold.fato_estoque_diario (último dia disponível)
initial_stock = {
    # id_produto -> {qtd_estoque, categoria, linha, colecao, fornecedor, custo}
}
```

### 3.2 Parâmetros por regime
```python
REGIME_PARAMS = {
    "commodity": {
        "coverage_days": 90,
        "reorder_point_days": 30,  # pede quando tem 30 dias de cobertura
        "lead_time_days": 20,      # prazo médio do fornecedor
        "lead_time_std": 5,        # desvio do lead time
        "safety_stock_days": 10,   # estoque de segurança
        "min_order_qty": 50,       # quantidade mínima de pedido
        "order_multiple": 12,      # pedido em múltiplos de 12 (dúzia)
    },
    "fashion": {
        "coverage_days": 14,
        "reorder_point_days": 7,
        "lead_time_days": 45,
        "lead_time_std": 15,
        "safety_stock_days": 3,
        "min_order_qty": 10,
        "order_multiple": 6,
        "no_reorder": True,  # não repõe, compra nova coleção
    },
    "seasonal": {
        "coverage_days": 180,
        "reorder_point_days": 60,
        "lead_time_days": 75,
        "lead_time_std": 20,
        "safety_stock_days": 15,
        "min_order_qty": 24,
        "order_multiple": 12,
        "reorder_if_sell_through": 0.70,  # repõe se vendeu 70%+
    },
}
```

### 3.3 Modelo de vendas (ARIMA)
```python
# Por categoria, extraído do sales-generator.py já construído
sales_model = {
    "UNDERWARE": {
        "base_daily": 5.2,        # peças/dia base
        "seasonality": {1: 1.1, 2: 1.0, 3: 1.0, 4: 1.0, 5: 1.1, 6: 1.2,
                        7: 1.3, 8: 1.2, 9: 1.1, 10: 1.0, 11: 1.0, 12: 1.3},
        "day_of_week": {0: 0.7, 1: 0.8, 2: 0.9, 3: 1.0, 4: 1.1, 5: 1.2, 6: 1.3},
        "temperature_sensitivity": 0.02,  # +2% vendas por +1°C
    },
    "MODA_PRAIA": {
        "base_daily": 2.1,
        "seasonality": {1: 1.8, 2: 2.0, 3: 1.5, 4: 1.0, 5: 0.7, 6: 0.5,
                        7: 0.5, 8: 0.6, 9: 0.8, 10: 1.0, 11: 1.2, 12: 1.5},
        "day_of_week": {0: 0.6, 1: 0.7, 2: 0.8, 3: 0.9, 4: 1.0, 5: 1.3, 6: 1.7},
        "temperature_sensitivity": 0.05,  # +5% vendas por +1°C (alta sensibilidade)
    },
    # ... demais categorias
}
```

### 3.4 Modelo de lead time (fornecedor)
```python
# Extraído de gold.fato_compras (análise de pedidos reais)
supplier_lead_time = {
    # cod_fornecedor -> {mean_days, std_days, compliance_rate}
    "FOR001": {"mean": 18, "std": 4, "compliance": 0.85},
    "FOR002": {"mean": 35, "std": 10, "compliance": 0.70},
    # ...
}
```

---

## 4. Ciclo Diário (Pseudocódigo)

```python
def simulate_day(day: date, state: SimulationState) -> DayResult:
    """Simula um dia completo de operação."""
    
    result = DayResult(day=day)
    
    # ── 1. Gerar vendas do dia ──────────────────────────────────
    for produto in state.active_products:
        if state.stock[produto.id] <= 0:
            result.stockouts.append(produto)
            continue
        
        # Calcular demanda esperada
        regime = classify_regime(produto)
        params = sales_model[produto.categoria]
        
        base = params["base_daily"]
        seasonal_factor = params["seasonality"][day.month]
        dow_factor = params["day_of_week"][day.weekday()]
        temp_factor = 1 + (state.temperature[day] - 25) * params["temperature_sensitivity"]
        
        expected_demand = base * seasonal_factor * dow_factor * temp_factor
        
        # Gerar vendas reais (Poisson distribution)
        actual_sales = np.random.poisson(expected_demand)
        actual_sales = min(actual_sales, state.stock[produto.id])  # limitado pelo estoque
        
        if actual_sales > 0:
            state.stock[produto.id] -= actual_sales
            result.sales.append(Sale(produto, actual_sales, day))
    
    # ── 2. Verificar recebimentos pendentes ─────────────────────
    for pending in state.pending_receipts:
        if day >= pending.expected_date:
            # Simular atraso (lead time real pode variar)
            supplier = pending.supplier
            delay = np.random.normal(0, supplier_lead_time[supplier]["std"])
            actual_arrival = pending.expected_date + timedelta(days=max(0, delay))
            
            if actual_arrival <= day:
                # Mercadoria chegou! Processo de entrada
                receipt = process_goods_receipt(pending, day)
                state.stock[pending.produto] += receipt.quantity
                result.receipts.append(receipt)
                
                # Registrar compliance do fornecedor
                on_time = (actual_arrival == pending.expected_date)
                record_supplier_compliance(supplier, on_time)
    
    # ── 3. Verificar ponto de reabastecimento ───────────────────
    for produto in state.active_products:
        regime = classify_regime(produto)
        params = REGIME_PARAMS[regime]
        
        if params.get("no_reorder"):
            continue  # Moda não repõe
        
        # Calcular dias de cobertura
        daily_demand = calculate_velocity(produto, state)
        if daily_demand == 0:
            continue
        
        coverage_days = state.stock[produto.id] / daily_demand
        
        # Verificar se já tem pedido ativo
        has_active_order = any(
            p.produto == produto.id and p.status == "pending"
            for p in state.pending_receipts
        )
        
        if coverage_days <= params["reorder_point_days"] and not has_active_order:
            # Gerar alerta de compra
            alert = generate_purchase_alert(
                produto=produto,
                coverage_days=coverage_days,
                target_coverage=params["coverage_days"],
                daily_demand=daily_demand,
                lead_time=params["lead_time_days"],
            )
            result.alerts.append(alert)
            
            # Criar pedido pendente
            order_qty = calculate_order_quantity(alert)
            state.pending_receipts.append(PendingReceipt(
                produto=produto.id,
                supplier=produto.fornecedor,
                quantity=order_qty,
                expected_date=day + timedelta(days=params["lead_time_days"]),
                order_date=day,
            ))
    
    # ── 4. Verificar produtos lentos ────────────────────────────
    for produto in state.slow_movers:
        days_without_sale = (day - produto.last_sale_date).days
        if days_without_sale > 60 and state.stock[produto.id] > 0:
            result.slow_mover_alerts.append(SlowMoverAlert(
                produto=produto,
                days_without_sale=days_without_sale,
                stock=state.stock[produto.id],
                suggested_discount=calculate_discount(produto),
            ))
    
    # ── 5. Registrar estado ─────────────────────────────────────
    result.snapshot = {
        "total_stock": sum(state.stock.values()),
        "total_sales": sum(s.qty for s in result.sales),
        "stockouts": len(result.stockouts),
        "alerts": len(result.alerts),
        "receipts": len(result.receipts),
    }
    
    return result
```

---

## 5. Classificação de Regime

```python
def classify_regime(produto: Produto) -> str:
    """Classifica produto em commodity, fashion ou seasonal."""
    
    # Regra 1: Coleção CONTINUO ou SEMI-CONTINUO → commodity
    if produto.colecao in ("CONTINUO", "SEMI-CONTINUO"):
        return "commodity"
    
    # Regra 2: VESTUARIO com coleção sazonal → fashion
    if produto.categoria == "VESTUARIO" and produto.colecao in ("VERAO*", "INVERNO*"):
        return "fashion"
    
    # Regra 3: MODA PRAIA → seasonal (com exceções)
    if produto.categoria == "MODA PRAIA":
        if produto.linha == "BASICO":
            return "commodity"  # básicos de praia são commodity
        return "seasonal"
    
    # Regra 4: LINHA NOITE → seasonal
    if produto.categoria == "LINHA NOITE":
        if produto.linha == "BASICO":
            return "commodity"
        return "seasonal"
    
    # Regra 5: FITNESS → commodity
    if produto.categoria == "FITNESS":
        return "commodity"
    
    # Default: fashion
    return "fashion"
```

---

## 6. Detecção de Substitutos

```python
def find_substitutes(produto: Produto, all_products: list) -> list:
    """Encontra produtos substitutos para um produto em ruptura."""
    
    substitutes = []
    
    for p in all_products:
        if p.id == produto.id:
            continue
        
        # Mesmo categoria + mesma linha + preço similar (±20%)
        if (p.categoria == produto.categoria and 
            p.linha == produto.linha and
            abs(p.preco - produto.preco) / produto.preco < 0.20):
            substitutes.append(p)
    
    # Ordenar por similaridade de preço
    substitutes.sort(key=lambda p: abs(p.preco - produto.preco))
    
    return substitutes[:5]  # Top 5 substitutos
```

---

## 7. Alertas de Compra

```python
def generate_purchase_alert(
    produto: Produto,
    coverage_days: float,
    target_coverage: int,
    daily_demand: float,
    lead_time: int,
) -> PurchaseAlert:
    
    # Calcular quantidade necessária
    days_to_cover = target_coverage - coverage_days + lead_time
    qty_needed = int(days_to_cover * daily_demand)
    
    # Arredondar para múltiplo do regime
    regime = classify_regime(produto)
    multiple = REGIME_PARAMS[regime]["order_multiple"]
    qty_ordered = math.ceil(qty_needed / multiple) * multiple
    
    # Calcular urgência
    if coverage_days <= 7:
        urgency = "CRITICAL"
    elif coverage_days <= 14:
        urgency = "HIGH"
    elif coverage_days <= 30:
        urgency = "MEDIUM"
    else:
        urgency = "LOW"
    
    return PurchaseAlert(
        produto=produto,
        supplier=produto.fornecedor,
        quantity=qty_ordered,
        urgency=urgency,
        coverage_days=coverage_days,
        target_coverage=target_coverage,
        estimated_cost=qty_ordered * produto.custo,
    )
```

---

## 8. Relatório de Fornecedores

```python
def generate_supplier_report(simulation_results: list) -> dict:
    """Gera relatório de performance de fornecedores."""
    
    report = {}
    
    for day_result in simulation_results:
        for receipt in day_result.receipts:
            supplier = receipt.supplier
            
            if supplier not in report:
                report[supplier] = {
                    "total_orders": 0,
                    "on_time_deliveries": 0,
                    "late_deliveries": 0,
                    "avg_delay_days": 0,
                    "compliance_rate": 0,
                }
            
            report[supplier]["total_orders"] += 1
            
            if receipt.on_time:
                report[supplier]["on_time_deliveries"] += 1
            else:
                report[supplier]["late_deliveries"] += 1
                report[supplier]["avg_delay_days"] += receipt.delay_days
    
    # Calcular métricas finais
    for supplier, data in report.items():
        if data["total_orders"] > 0:
            data["compliance_rate"] = data["on_time_deliveries"] / data["total_orders"]
            data["avg_delay_days"] /= max(1, data["late_deliveries"])
    
    return report
```

---

## 9. Outputs

### 9.1 Arquivos gerados
```
artifacts/simulation/
├── simulation_engine.py          # Motor principal
├── simulation_config.json        # Parâmetros configuráveis
├── output/
│   ├── daily_log.csv             # Log diário completo
│   ├── stockouts.csv             # Produtos em ruptura
│   ├── purchase_alerts.csv       # Alertas de compra
│   ├── supplier_performance.csv  # Performance de fornecedores
│   ├── slow_movers.csv           # Produtos lentos
│   └── summary.json              # Resumo da simulação
└── dashboard/
    └── simulation_dashboard.html # Dashboard visual
```

### 9.2 daily_log.csv
```csv
date,category,line,collection,total_stock,total_sales,stockouts,receipts,alerts
2026-07-09,UNDERWARE,BASICO,CONTINUO,1523,45,0,0,0
2026-07-09,MODA_PRAIA,FASHION,VERAO-2020,234,12,2,0,1
...
```

### 9.3 Dashboard HTML
- Gráfico de estoque total ao longo dos dias
- Gráfico de vendas diárias por categoria
- Heatmap de rupturas por categoria/dia
- Tabela de alertas de compra pendentes
- Gráfico de compliance de fornecedores

---

## 10. Instruções para o Executor (DeepSeek V4 Flash)

### Passo a passo de implementação

1. **Criar `simulation_engine.py`** com:
   - Classe `SimulationState` (estoque, pedidos pendentes, alertas)
   - Classe `SimulationEngine` (método `run(days: int)`)
   - Função `classify_regime()` (Seção 5)
   - Função `simulate_day()` (Seção 4)
   - Função `find_substitutes()` (Seção 6)
   - Função `generate_purchase_alert()` (Seção 7)

2. **Criar `simulation_config.json`** com:
   - Parâmetros por regime (Seção 3.2)
   - Modelo de vendas por categoria (Seção 3.3)
   - Lead time por fornecedor (Seção 3.4)

3. **Extrair dados iniciais do DuckDB**:
   - Estoque atual: `SELECT * FROM gold.fato_estoque_diario WHERE id_data = (SELECT MAX(id_data) FROM gold.fato_estoque_diario)`
   - Produtos: `SELECT * FROM gold.dim_produto WHERE dat_fim_vigencia IS NULL`
   - Fornecedores: `SELECT * FROM gold.dim_fornecedor`
   - Histórico de compras (para lead time): `SELECT id_fornecedor, id_data_pedido, num_pedido FROM gold.fato_compras`

4. **Gerar outputs** (Seção 9):
   - CSVs em `artifacts/simulation/output/`
   - Dashboard HTML em `artifacts/simulation/dashboard/`

5. **Validar**:
   - Rodar simulação de 30 dias
   - Verificar que há rupturas (realista)
   - Verificar que há alertas de compra
   - Verificar que há recebimentos após lead time

### Constraints técnicas
- Python 3.11+ (já disponível no workspace)
- Bibliotecas: `pandas`, `numpy`, `duckdb`, `matplotlib` (para dashboard)
- NÃO usar `statsmodels` (ARIMA já está no `sales-generator.py` — reutilizar)
- Caminho do DuckDB: `F:/projects/chez-violeta-intelligence/artifacts/data/chez_gold.duckdb`
- Output path: `F:/projects/chez-violeta-intelligence/artifacts/simulation/`

### Checklist de entrega
- [ ] `simulation_engine.py` funcional
- [ ] `simulation_config.json` com parâmetros
- [ ] `output/daily_log.csv` com 30 dias de simulação
- [ ] `output/stockouts.csv` com rupturas
- [ ] `output/purchase_alerts.csv` com alertas
- [ ] `output/supplier_performance.csv` com compliance
- [ ] `output/slow_movers.csv` com produtos lentos
- [ ] `dashboard/simulation_dashboard.html` visual
- [ ] `README.md` explicando como rodar

---

## 11. Extensões Futuras (fora do escopo v1)

- Integração com n8n para alertas reais (email/Slack)
- Dashboard interativo (Streamlit/Dash)
- Otimização de lote econômico (EOQ)
- Previsão de demanda com ML (Prophet/LSTM)
- Simulação multi-loja (transferências entre lojas)
- Cenários "what-if" (ex: e se aumentar preço 10%?)

---

## 12. Referências

- `artifacts/data/dimensional-model.md` — Schema do star schema
- `artifacts/data/sales-generator.py` — ARIMA já implementado
- `artifacts/data/simulation-data-profile.json` — Perfil de dados extraído
- `artifacts/design/processo-entrada-mercadorias.md` — Processo de recebimento
- `artifacts/data/referential-integrity-report.md` — Validação de FKs
