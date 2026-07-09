"""
ETL Gold Layer — Chez Violeta
===============================
Connects DuckDB to PostgreSQL, creates gold schema tables,
and loads data from PostgreSQL into DuckDB gold layer.

Usage:
    uv run python artifacts/data/etl_gold.py

Environment:
    PG_HOST=localhost  PG_PORT=5433  PG_DB=chez_violeta
    PG_USER=postgres   PG_PASSWORD=postgres
    (defaults as above if not set)
"""

import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import duckdb

# ─── Config ───────────────────────────────────────────────────────────────────

CHILD_REPO = Path(__file__).resolve().parent.parent.parent  # chez-violeta-intelligence/
SCHEMA_SQL = CHILD_REPO / "artifacts" / "data" / "schema-gold.sql"
GOLDD_DB   = CHILD_REPO / "artifacts" / "data" / "chez_gold.duckdb"
LOG_PATH   = CHILD_REPO / "artifacts" / "data" / "etl-gold-log.md"

PG_CONFIG = {
    "host":     os.environ.get("PG_HOST", "localhost"),
    "port":     os.environ.get("PG_PORT", "5433"),
    "dbname":   os.environ.get("PG_DB", "chez_violeta"),
    "user":     os.environ.get("PG_USER", "postgres"),
    "password": os.environ.get("PG_PASSWORD", "postgres"),
}

def pg_attach_str() -> str:
    return (f"host={PG_CONFIG['host']} port={PG_CONFIG['port']} "
            f"dbname={PG_CONFIG['dbname']} user={PG_CONFIG['user']} "
            f"password={PG_CONFIG['password']}")


# ─── Helpers ──────────────────────────────────────────────────────────────────

_log_lines: list[str] = []

def log(msg: str, detail: str = "") -> None:
    ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
    line = f"| {ts} | {msg}"
    if detail:
        line += f" | {detail}"
    _log_lines.append(line)
    print(f"[{ts}] {msg}", flush=True)


def run_sql(con: duckdb.DuckDBPyConnection, label: str, sql: str) -> list:
    """Execute SQL with timing and basic error handling."""
    t0 = time.perf_counter()
    try:
        result = con.execute(sql).fetchall() if sql.strip().upper().startswith("SELECT") else con.execute(sql)
        elapsed = time.perf_counter() - t0
        log(f"{label} OK", f"{elapsed:.1f}s")
        return result if result else []
    except Exception as e:
        elapsed = time.perf_counter() - t0
        log(f"{label} ERROR", f"{elapsed:.1f}s — {e}")
        print(f"  SQL: {sql[:200]}...", file=sys.stderr)
        raise


def row_count(con: duckdb.DuckDBPyConnection, schema: str, table: str) -> int:
    try:
        r = con.execute(f"SELECT COUNT(*) FROM {schema}.{table}").fetchone()
        return r[0] if r else 0
    except Exception:
        return -1


# ─── Step 1: Create DuckDB + Schema ───────────────────────────────────────────

def step1_create_database() -> duckdb.DuckDBPyConnection:
    log("Step 1", "Creating DuckDB database + gold schema")

    # Remove old DB for fresh start
    if GOLDD_DB.exists():
        GOLDD_DB.unlink()
        log("  Cleanup", "Removed existing chez_gold.duckdb")

    con = duckdb.connect(str(GOLDD_DB))

    # Install/load postgres scanner extension
    con.execute("INSTALL postgres")
    con.execute("LOAD postgres")
    log("  Extensions", "postgres scanner installed & loaded")

    # Create gold schema
    con.execute("CREATE SCHEMA IF NOT EXISTS gold")
    log("  Schema", "gold schema created")

    return con


# ─── Step 2: Execute DDL ──────────────────────────────────────────────────────

def step2_execute_ddl(con: duckdb.DuckDBPyConnection) -> None:
    log("Step 2", "Executing DDL from schema-gold.sql")

    raw_sql = SCHEMA_SQL.read_text(encoding="utf-8")

    # Remove COMMENT ON statements (DuckDB does not support them)
    clean_lines = []
    for line in raw_sql.splitlines():
        stripped = line.strip().upper()
        if stripped.startswith("COMMENT ON"):
            log("  Skipping COMMENT", line.strip()[:80])
            continue
        # Remove COMMENT ON that may be inline (unlikely but safe)
        if re.search(r'COMMENT ON (TABLE|COLUMN)\s', line, re.IGNORECASE):
            continue
        clean_lines.append(line)

    cleaned_sql = "\n".join(clean_lines)

    # Split by semicolons and execute each statement
    statements = re.split(r";\s*", cleaned_sql)
    stmt_count = 0
    for stmt in statements:
        stmt = stmt.strip()
        if not stmt:
            continue
        # Get a short label from the statement
        label_match = re.match(r"(CREATE|DROP|ALTER)\s+(\w+\s+)*(\w+)", stmt, re.IGNORECASE)
        label = label_match.group(0).strip() if label_match else stmt[:50]
        run_sql(con, f"  DDL: {label}", stmt)
        stmt_count += 1

    log("  DDL Complete", f"{stmt_count} statements executed")
    log("  Tables created", ", ".join(
        r[0] for r in con.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema='gold'"
        ).fetchall()
    ))


# ─── Step 3: Attach PostgreSQL ────────────────────────────────────────────────

def step3_attach_pg(con: duckdb.DuckDBPyConnection) -> None:
    log("Step 3", "Attaching PostgreSQL")
    run_sql(con, "  ATTACH PostgreSQL", f"ATTACH '{pg_attach_str()}' AS pg (TYPE POSTGRES)")
    tbl_count = con.execute(
        "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE'"
    ).fetchone()[0]
    log("  PostgreSQL tables found", str(tbl_count))


# ─── Step 4: Load Dimensions ──────────────────────────────────────────────────

def step4_load_dimensions(con: duckdb.DuckDBPyConnection) -> None:
    log("Step 4", "Loading dimensions")

    # Insert "Unknown" placeholder records for FK integrity
    # These are used when a FK lookup fails (COALESCE to -1)
    log("  0 Unknown placeholders", "Inserting N/A records for FK integrity")
    try:
        con.execute("INSERT INTO gold.dim_tempo (id_data, dat_dia) VALUES (19000101, '1900-01-01')")
    except Exception:
        pass  # may already exist
    try:
        con.execute("INSERT INTO gold.dim_produto (id_produto, cod_artigo, cod_cor, cod_tamanho, "
                     "des_artigo, des_produto, dat_inicio_vigencia, flg_ativo) "
                     "VALUES (-1, 'N/A', 'N/A', 'N/A', 'Desconhecido', 'Desconhecido', '1900-01-01', FALSE)")
    except Exception:
        pass
    try:
        con.execute("INSERT INTO gold.dim_loja (id_loja, cod_estabelecimento, des_estabelecimento) "
                     "VALUES (-1, 'N/A', 'Loja Desconhecida')")
    except Exception:
        pass
    try:
        con.execute("INSERT INTO gold.dim_fornecedor (id_fornecedor, cod_fornecedor) "
                     "VALUES (-1, 'N/A')")
    except Exception:
        pass

    # 4.1 dim_tempo ────────────────────────────────────────────────────────
    log("  4.1 dim_tempo", "Loading from datas table")
    # Note: id_ano_mes is stored as 'YYYY-MM' string, so we compute it
    # id_ano_sem and num_sem have '0' as missing value marker
    run_sql(con, "  dim_tempo INSERT", """
        INSERT INTO gold.dim_tempo (id_data, dat_dia, num_dia_semana, des_dia_semana,
            num_dia_mes, num_mes_ano, des_mes_ano, num_ano, id_ano_mes, num_semana,
            id_ano_sem, flg_feriado)
        SELECT
            CAST(STRFTIME(CAST(SPLIT_PART(dat_dia, ' ', 1) AS DATE), '%Y%m%d') AS INTEGER),
            CAST(SPLIT_PART(dat_dia, ' ', 1) AS DATE),
            CAST(NULLIF(num_dia_semana, '') AS INTEGER),
            des_dia_semana,
            CAST(NULLIF(num_dia_mes, '') AS INTEGER),
            CAST(NULLIF(num_mes_ano, '') AS INTEGER),
            des_mes_ano,
            CAST(NULLIF(num_ano, '') AS INTEGER),
            CAST(NULLIF(num_ano, '') AS INTEGER) * 100 + CAST(NULLIF(num_mes_ano, '') AS INTEGER),
            NULLIF(CAST(NULLIF(num_sem, '') AS INTEGER), 0),
            NULLIF(CAST(NULLIF(id_ano_sem, '') AS INTEGER), 0),
            CASE WHEN ind_feriado IN ('S','1','TRUE','true','t') THEN TRUE ELSE FALSE END
        FROM pg.public.datas
    """)
    log(f"  dim_tempo rows: {row_count(con, 'gold', 'dim_tempo')}")

    # 4.2 dim_produto SCD2 (initial full load) ─────────────────────────────
    log("  4.2 dim_produto", "Loading from artigos_modelos + artigos_variantes + lookups (SCD2 initial)")
    run_sql(con, "  dim_produto INSERT", """
        INSERT INTO gold.dim_produto (
            cod_artigo, cod_cor, cod_tamanho, cod_barra, cod_fornecedor,
            des_artigo, des_cor, des_tamanho, des_produto, des_categoria,
            des_linha, des_modelagem, des_material, des_colecao, des_status,
            des_grade, des_publico, des_estilo, cod_ncm, val_custo_inicial,
            dat_cadastramento,
            dat_inicio_vigencia, dat_fim_vigencia, flg_ativo, dc_hash
        )
        SELECT
            am.cod_artigo,
            av.cod_cor,
            av.cod_tamanho,
            av.cod_barra,
            am.cod_fornecedor,
            am.des_artigo,
            c.des_cor,
            t.des_tamanho,
            p.des_produto,
            cat.des_categoria,
            l.des_linha,
            m.des_modelagem,
            mat.des_material,
            col.des_colecao,
            s.des_status,
            g.des_grade,
            am.des_publico,
            am.des_estilo,
            am.cod_ncm,
            CAST(NULLIF(am.val_custo_inicial, '') AS DECIMAL(12,2)),
            CAST(NULLIF(am.dat_cadastramento, '') AS DATE),
            CAST(NULLIF(am.dat_cadastramento, '') AS DATE),  -- dat_inicio_vigencia
            NULL,                                              -- current version
            TRUE,
            MD5(CONCAT(COALESCE(am.des_artigo,''), COALESCE(p.des_produto,''),
                       COALESCE(cat.des_categoria,''), COALESCE(l.des_linha,''),
                       COALESCE(m.des_modelagem,''), COALESCE(mat.des_material,''),
                       COALESCE(col.des_colecao,''), COALESCE(s.des_status,''),
                       COALESCE(g.des_grade,''), COALESCE(am.des_publico,''),
                       COALESCE(am.des_estilo,'')))
        FROM pg.public.artigos_modelos am
        JOIN pg.public.artigos_variantes av ON am.cod_artigo = av.cod_artigo
        LEFT JOIN pg.public.atrv_cores c ON av.at_cod_cor = c.cod_cor
        LEFT JOIN pg.public.atrv_tamanhos t ON av.at_cod_tamanho = t.cod_tamanho
        LEFT JOIN pg.public.atr_produtos p ON am.at_cod_produto = p.cod_produto
        LEFT JOIN pg.public.atr_categorias cat ON am.at_cod_categoria = cat.cod_categoria
        LEFT JOIN pg.public.atr_linhas l ON am.at_cod_linha = l.cod_linha
        LEFT JOIN pg.public.atr_modelagens m ON am.at_cod_modelagem = m.cod_modelagem
        LEFT JOIN pg.public.atr_materiais mat ON am.at_cod_material = mat.cod_material
        LEFT JOIN pg.public.atr_grades g ON am.at_cod_grade = g.cod_grade
        LEFT JOIN pg.public.atrv_colecoes col ON av.at_cod_colecao = col.cod_colecao
        LEFT JOIN pg.public.atr_status s ON av.at_cod_status = s.cod_status
    """)
    log(f"  dim_produto rows: {row_count(con, 'gold', 'dim_produto')}")

    # 4.3 dim_loja ─────────────────────────────────────────────────────────
    log("  4.3 dim_loja", "Loading from estabelecimentos (PII-safe: no CNPJ)")
    run_sql(con, "  dim_loja INSERT", """
        INSERT INTO gold.dim_loja (cod_estabelecimento, des_estabelecimento,
            nom_razao_social, nom_municipio, cod_uf)
        SELECT DISTINCT
            cod_estabelecimento,
            des_estabelecimento,
            nom_razao_social,
            nom_municipio,
            cod_uf
        FROM pg.public.estabelecimentos
    """)
    log(f"  dim_loja rows: {row_count(con, 'gold', 'dim_loja')}")

    # 4.4 dim_fornecedor ───────────────────────────────────────────────────
    log("  4.4 dim_fornecedor", "Loading from fornecedores")
    run_sql(con, "  dim_fornecedor INSERT", """
        INSERT INTO gold.dim_fornecedor (cod_fornecedor, cod_ncm, sts_compra)
        SELECT DISTINCT
            cod_fornecedor,
            NULLIF(cod_ncm, ''),
            NULLIF(sts_compra, '')
        FROM pg.public.fornecedores
    """)
    log(f"  dim_fornecedor rows: {row_count(con, 'gold', 'dim_fornecedor')}")

    # 4.5 dim_cliente ──────────────────────────────────────────────────────
    log("  4.5 dim_cliente", "Loading from clientes (PII-safe: no nome, email, phone)")
    run_sql(con, "  dim_cliente INSERT", """
        INSERT INTO gold.dim_cliente (codigo_cliente, sexo, idade,
            dat_cadastramento, tip_cliente, flg_whatsapp, flg_email_valido)
        SELECT DISTINCT
            codigo_cliente,
            NULLIF(sexo, ''),
            CAST(NULLIF(idade, '') AS INTEGER),
            CAST(NULLIF(dat_cadastramento, '') AS DATE),
            NULLIF(tip_cliente, ''),
            CASE WHEN flg_whatsapp IN ('S','1','TRUE','true','t') THEN TRUE ELSE FALSE END,
            CASE WHEN flg_email_valido IN ('S','1','TRUE','true','t') THEN TRUE ELSE FALSE END
        FROM pg.public.clientes
        WHERE codigo_cliente IS NOT NULL AND codigo_cliente != ''
    """)
    log(f"  dim_cliente rows: {row_count(con, 'gold', 'dim_cliente')}")

    # 4.6 dim_vendedor ─────────────────────────────────────────────────────
    log("  4.6 dim_vendedor", "Loading from rh_funcs (id_cargo FK not found in rh_funcs)")
    run_sql(con, "  dim_vendedor INSERT", """
        INSERT INTO gold.dim_vendedor (cod_vendedor, nom_funcionaria,
            des_cargo, dat_inicio_trabalho, flg_alocado_cd)
        SELECT
            f.id_func,
            NULLIF(f.nom_funcionaria, ''),
            NULL,  -- des_cargo: rh_funcs has no id_cargo FK to rh_cargos
            CAST(NULLIF(f.dat_inicio_trabalho, '') AS DATE),
            CASE WHEN f.flg_alocado_cd IN ('S','1','TRUE','true','t') THEN TRUE ELSE FALSE END
        FROM pg.public.rh_funcs f
    """)
    log(f"  dim_vendedor rows: {row_count(con, 'gold', 'dim_vendedor')}")


# ─── Step 5: Load Fact Tables ─────────────────────────────────────────────────

def step5_load_facts(con: duckdb.DuckDBPyConnection) -> None:
    log("Step 5", "Loading fact tables")

    # 5.1 fato_vendas ──────────────────────────────────────────────────────
    log("  5.1 fato_vendas", "Loading from vendas_cupons + brax_itens_cupons")
    run_sql(con, "  fato_vendas INSERT", """
        INSERT INTO gold.fato_vendas (
            id_data, id_loja, id_produto, id_cliente, id_vendedor,
            num_ticket, num_item,
            qtd_pecas, val_venda_cadastro, val_desconto,
            val_venda_liquida, val_custo, val_pagamento
        )
        SELECT
            CAST(STRFTIME(CAST(SPLIT_PART(vc.dat_venda, ' ', 1) AS DATE), '%Y%m%d') AS INTEGER) AS id_data,
            COALESCE(dl.id_loja, -1),
            COALESCE(dp.id_produto, -1),
            dc.id_cliente,
            dv.id_vendedor,
            vc.num_ticket,
            bi.num_item,
            CAST(NULLIF(bi.qtd_pecas, '') AS INTEGER),
            CAST(NULLIF(bi.val_venda_liquida, '') AS DECIMAL(12,2)),
            CAST(NULLIF(bi.val_desconto, '') AS DECIMAL(12,2)),
            CAST(NULLIF(bi.val_venda_liquida, '') AS DECIMAL(12,2)),
            CAST(NULLIF(vc.val_venda_custo, '') AS DECIMAL(12,2)),
            CAST(NULLIF(vc.val_pagamento, '') AS DECIMAL(12,2))
        FROM pg.public.brax_itens_cupons bi
        JOIN pg.public.vendas_cupons vc
            ON bi.cod_estabelecimento = vc.cod_estabelecimento
           AND bi.num_ticket = vc.num_ticket
        LEFT JOIN gold.dim_loja dl ON vc.cod_estabelecimento = dl.cod_estabelecimento
        LEFT JOIN gold.dim_produto dp
            ON bi.cod_artigo = dp.cod_artigo
           AND bi.cod_cor = dp.cod_cor
           AND bi.cod_tamanho = dp.cod_tamanho
           AND dp.flg_ativo = TRUE
        LEFT JOIN gold.dim_cliente dc ON vc.cod_cliente = dc.codigo_cliente
        LEFT JOIN gold.dim_vendedor dv ON vc.cod_vendedor = dv.cod_vendedor
    """)
    log(f"  fato_vendas rows: {row_count(con, 'gold', 'fato_vendas')}")

    # 5.2 fato_estoque_diario ──────────────────────────────────────────────
    log("  5.2 fato_estoque_diario", "Loading from estoques_diarios (10.1M rows)")
    # Drop unique index for initial load (source has duplicates on same SKU+store+day)
    # Will re-create after load
    run_sql(con, "  fato_estoque_diario DROP INDEX", """
        DROP INDEX IF EXISTS gold.uq_fato_estoque_diario
    """)
    run_sql(con, "  fato_estoque_diario INSERT", """
        INSERT INTO gold.fato_estoque_diario (
            id_data, id_loja, id_produto,
            qtd_estoque, qtd_estoque_inicial, qtd_venda,
            qtd_entrada_nota, qtd_troca, qtd_transf_entrada,
            qtd_transf_saida, qtd_ajuste_positivo, qtd_ajuste_negativo,
            qtd_inventario
        )
        SELECT
            CAST(STRFTIME(CAST(SPLIT_PART(ed.dat_dia, ' ', 1) AS DATE), '%Y%m%d') AS INTEGER) AS id_data,
            COALESCE(dl.id_loja, -1),
            COALESCE(dp.id_produto, -1),
            CAST(NULLIF(ed.qtd_estoque, '') AS INTEGER),
            CAST(NULLIF(ed.qtd_estoque_inicial, '') AS INTEGER),
            CAST(NULLIF(ed.qtd_venda, '') AS INTEGER),
            CAST(NULLIF(ed.qtd_entrada_nota, '') AS INTEGER),
            CAST(NULLIF(ed.qtd_troca, '') AS INTEGER),
            CAST(NULLIF(ed.qtd_transf_entrada, '') AS INTEGER),
            CAST(NULLIF(ed.qtd_transf_saida, '') AS INTEGER),
            CAST(NULLIF(ed.qtd_ajuste_positivo, '') AS INTEGER),
            CAST(NULLIF(ed.qtd_ajuste_negativo, '') AS INTEGER),
            CAST(NULLIF(ed.qtd_inventario, '') AS INTEGER)
        FROM pg.public.estoques_diarios ed
        LEFT JOIN gold.dim_loja dl ON ed.cod_estabelecimento = dl.cod_estabelecimento
        LEFT JOIN gold.dim_produto dp
            ON ed.cod_artigo = dp.cod_artigo
           AND ed.cod_cor = dp.cod_cor
           AND ed.cod_tamanho = dp.cod_tamanho
           AND dp.flg_ativo = TRUE
    """)
    # Note: unique index uq_fato_estoque_diario NOT re-created because the raw
    # source has genuine duplicates on (data, loja, produto). For incremental
    # refresh, use DELETE+INSERT by dat_dia instead of the unique index pattern.
    # A deduplication pass (aggregate/SELECT DISTINCT) is needed before re-creating.
    log("  fato_estoque_diario SKIP unique index re-creation",
        "source has genuine duplicates; dedup needed before re-creating")
    log(f"  fato_estoque_diario rows: {row_count(con, 'gold', 'fato_estoque_diario')}")

    # 5.3 fato_compras ─────────────────────────────────────────────────────
    log("  5.3 fato_compras", "Loading from compras + compras_modelos + compras_variantes")
    run_sql(con, "  fato_compras INSERT", """
        INSERT INTO gold.fato_compras (
            id_data_pedido, id_loja, id_fornecedor, id_produto,
            num_pedido, cod_tipo_pedido,
            qtd_pecas, val_bruto, val_desconto, val_liquido, val_imposto
        )
        SELECT
            COALESCE(dt.id_data, 19000101) AS id_data_pedido,
            COALESCE(dl.id_loja, -1),
            COALESCE(df.id_fornecedor, -1),
            COALESCE(dp.id_produto, -1),
            c.num_pedido,
            c.cod_tipo_pedido,
            CAST(NULLIF(cv.qtd_pecas, '') AS INTEGER),
            CAST(NULLIF(cv.val_uni_bruto, '') AS DECIMAL(12,2)),
            CAST(NULLIF(c.val_desconto, '') AS DECIMAL(12,2)),
            CAST(NULLIF(cv.val_uni_bruto, '') AS DECIMAL(12,2)),
            CAST(NULLIF(c.val_imposto, '') AS DECIMAL(12,2))
        FROM pg.public.compras c
        JOIN pg.public.compras_modelos cm ON c.num_pedido = cm.num_pedido
        JOIN pg.public.compras_variantes cv
            ON cm.num_pedido = cv.num_pedido
           AND cm.cod_artigo = cv.cod_artigo
        LEFT JOIN gold.dim_tempo dt
            ON dt.id_data = CAST(STRFTIME(CAST(SPLIT_PART(c.dat_pedido, ' ', 1) AS DATE), '%Y%m%d') AS INTEGER)
        LEFT JOIN gold.dim_loja dl ON c.cod_estabelecimento = dl.cod_estabelecimento
        LEFT JOIN gold.dim_fornecedor df ON c.cod_fornecedor = df.cod_fornecedor
        LEFT JOIN gold.dim_produto dp
            ON cv.cod_artigo = dp.cod_artigo
           AND cv.cod_cor = dp.cod_cor
           AND cv.cod_tamanho = dp.cod_tamanho
           AND dp.flg_ativo = TRUE
    """)
    log(f"  fato_compras rows: {row_count(con, 'gold', 'fato_compras')}")

    # 5.4 fato_trocas ─────────────────────────────────────────────────────
    log("  5.4 fato_trocas", "Loading from trocas + trocas_itens_devolvidos + trocas_itens_substitutos")

    # Create temp table for unified trocas items (UNION ALL devolvidos + substitutos)
    run_sql(con, "  fato_trocas INSERT (devolvidos)", """
        INSERT INTO gold.fato_trocas (
            id_data, id_loja, id_produto_devolvido, id_produto_substituto,
            tip_troca, qtd_pecas, val_venda_liquida, val_venda_cadastro,
            val_desconto, flg_defeito
        )
        SELECT
            CAST(STRFTIME(CAST(SPLIT_PART(t.dat_troca, ' ', 1) AS DATE), '%Y%m%d') AS INTEGER) AS id_data,

            COALESCE(dl.id_loja, -1),
            COALESCE(dp.id_produto, -1) AS id_produto_devolvido,
            NULL AS id_produto_substituto,
            'DEVOLVIDO' AS tip_troca,
            CAST(NULLIF(ti.qtd_pecas, '') AS INTEGER),
            CAST(NULLIF(ti.val_venda_liquida, '') AS DECIMAL(12,2)),
            CAST(NULLIF(ti.val_venda_cadastro, '') AS DECIMAL(12,2)),
            CAST(NULLIF(ti.val_desconto, '') AS DECIMAL(12,2)),
            CASE WHEN ti.flg_defeito IN ('S','1','TRUE','true','t') THEN TRUE ELSE FALSE END
        FROM pg.public.trocas t
        JOIN pg.public.trocas_itens_devolvidos ti
            ON t.cod_estabelecimento = ti.cod_estabelecimento
           AND t.dat_troca = ti.dat_troca
        LEFT JOIN gold.dim_loja dl ON t.cod_estabelecimento = dl.cod_estabelecimento
        LEFT JOIN gold.dim_produto dp
            ON ti.cod_artigo = dp.cod_artigo
           AND ti.cod_cor = dp.cod_cor
           AND ti.cod_tamanho = dp.cod_tamanho
           AND dp.flg_ativo = TRUE
    """)

    run_sql(con, "  fato_trocas INSERT (substitutos)", """
        INSERT INTO gold.fato_trocas (
            id_data, id_loja, id_produto_devolvido, id_produto_substituto,
            tip_troca, qtd_pecas, val_venda_liquida, val_venda_cadastro,
            val_desconto
        )
        SELECT
            COALESCE(dt.id_data, 19000101) AS id_data,
            COALESCE(dl.id_loja, -1),
            -1 AS id_produto_devolvido,  -- unknown returned product (NOT NULL constraint)
            COALESCE(dp.id_produto, -1) AS id_produto_substituto,
            'SUBSTITUTO' AS tip_troca,
            CAST(NULLIF(ti.qtd_pecas, '') AS INTEGER),
            CAST(NULLIF(ti.val_venda_liquida, '') AS DECIMAL(12,2)),
            CAST(NULLIF(ti.val_venda_cadastro, '') AS DECIMAL(12,2)),
            CAST(NULLIF(ti.val_desconto, '') AS DECIMAL(12,2))
        FROM pg.public.trocas t
        JOIN pg.public.trocas_itens_substitutos ti
            ON t.cod_estabelecimento = ti.cod_estabelecimento
           AND t.dat_troca = ti.dat_troca
        LEFT JOIN gold.dim_tempo dt
            ON dt.id_data = CAST(STRFTIME(CAST(SPLIT_PART(t.dat_troca, ' ', 1) AS DATE), '%Y%m%d') AS INTEGER)
        LEFT JOIN gold.dim_loja dl ON t.cod_estabelecimento = dl.cod_estabelecimento
        LEFT JOIN gold.dim_produto dp
            ON ti.cod_artigo = dp.cod_artigo
           AND ti.cod_cor = dp.cod_cor
           AND ti.cod_tamanho = dp.cod_tamanho
           AND dp.flg_ativo = TRUE
    """)

    log(f"  fato_trocas rows: {row_count(con, 'gold', 'fato_trocas')}")


# ─── Step 6: DQ Views ─────────────────────────────────────────────────────────

def step6_create_dq_views(con: duckdb.DuckDBPyConnection) -> None:
    log("Step 6", "Creating DQ monitoring views")
    run_sql(con, "  dq_vendas_sem_produto", """
        CREATE OR REPLACE VIEW gold.dq_vendas_sem_produto AS
        SELECT fv.*
        FROM gold.fato_vendas fv
        LEFT JOIN gold.dim_produto dp ON fv.id_produto = dp.id_produto
        WHERE dp.id_produto IS NULL
    """)
    run_sql(con, "  dq_estoque_sem_produto", """
        CREATE OR REPLACE VIEW gold.dq_estoque_sem_produto AS
        SELECT fe.*
        FROM gold.fato_estoque_diario fe
        LEFT JOIN gold.dim_produto dp ON fe.id_produto = dp.id_produto
        WHERE dp.id_produto IS NULL
    """)
    run_sql(con, "  dq_estoque_negativo", """
        CREATE OR REPLACE VIEW gold.dq_estoque_negativo AS
        SELECT id_data, id_loja, id_produto, qtd_estoque
        FROM gold.fato_estoque_diario
        WHERE qtd_estoque < 0
    """)
    run_sql(con, "  dq_vendas_futuras", """
        CREATE OR REPLACE VIEW gold.dq_vendas_futuras AS
        SELECT fv.*, td.dat_dia
        FROM gold.fato_vendas fv
        JOIN gold.dim_tempo td ON fv.id_data = td.id_data
        WHERE td.dat_dia > CURRENT_DATE
    """)
    log("  DQ views created", "4 views")


# ─── Step 7: Summary ──────────────────────────────────────────────────────────

def step7_summary(con: duckdb.DuckDBPyConnection) -> dict:
    log("Step 7", "Summary & validation")

    tables = [
        "gold.dim_tempo",
        "gold.dim_produto",
        "gold.dim_loja",
        "gold.dim_fornecedor",
        "gold.dim_cliente",
        "gold.dim_vendedor",
        "gold.fato_vendas",
        "gold.fato_estoque_diario",
        "gold.fato_compras",
        "gold.fato_trocas",
    ]

    summary = {}
    for table in tables:
        try:
            cnt = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        except Exception:
            cnt = -1
        summary[table] = cnt
        log(f"  {table}", f"{cnt:,} rows")

    return summary


# ─── Write Log ────────────────────────────────────────────────────────────────

def write_log(summary: dict, success: bool) -> None:
    """Write ETL log to markdown file."""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    total_rows = sum(v for v in summary.values() if isinstance(v, int) and v >= 0)

    lines = [
        "# ETL Gold Layer — Carga Log",
        "",
        f"**Date:** {ts}",
        f"**Source:** PostgreSQL {PG_CONFIG['host']}:{PG_CONFIG['port']}/{PG_CONFIG['dbname']}",
        f"**Target:** DuckDB {GOLDD_DB.name}",
        f"**Status:** {'SUCCESS' if success else 'FAILED'}",
        "",
        "## Summary",
        "",
        "| Table | Rows Loaded |",
        "|-------|-------------|",
    ]
    for tbl, cnt in summary.items():
        lbl = tbl.replace("gold.", "")
        cnt_str = f"{cnt:,}" if isinstance(cnt, int) and cnt >= 0 else "ERROR"
        lines.append(f"| {lbl} | {cnt_str} |")
    lines.append(f"| **Total** | **{total_rows:,}** |")
    lines.append("")
    lines.append("## Step Log")
    lines.append("")
    lines.append("| Time | Step | Detail |")
    lines.append("|------|------|--------|")
    lines.extend(_log_lines)
    lines.append("")
    lines.append("## Notes")
    lines.append("")
    lines.append("- All data loaded via DuckDB postgres scanner extension")
    lines.append(f"- DuckDB version: {duckdb.__version__}")
    lines.append("- PII columns excluded: dim_cliente (nome, email, celular, telefone), dim_loja (CNPJ)")
    lines.append("- All source columns stored as TEXT in PostgreSQL; CAST to appropriate type on load")
    lines.append("- dim_produto uses SCD2: initial full load, dat_inicio_vigencia = dat_cadastramento")
    lines.append("- Dimensions loaded before facts for FK integrity")
    lines.append("- DQ views created for monitoring: orphan checks, negative inventory, future-dated sales")
    lines.append("")

    LOG_PATH.write_text("\n".join(lines), encoding="utf-8")
    log("Log written", str(LOG_PATH))


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    t_start = time.perf_counter()
    success = False
    summary = {}

    try:
        con = step1_create_database()
        step2_execute_ddl(con)
        step3_attach_pg(con)
        step4_load_dimensions(con)
        step5_load_facts(con)
        step6_create_dq_views(con)
        summary = step7_summary(con)
        con.close()
        success = True

        elapsed = time.perf_counter() - t_start
        log("ETL Complete", f"Total time: {elapsed:.1f}s")
        print(f"\n{'='*60}")
        print(f"  ETL Gold Layer: {'SUCCESS' if success else 'FAILED'}")
        print(f"  Total time: {elapsed:.1f}s")
        print(f"  Database: {GOLDD_DB}")
        print(f"{'='*60}")

    except Exception as e:
        log("FATAL", str(e))
        print(f"\nFATAL ERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()

    finally:
        write_log(summary, success)

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
