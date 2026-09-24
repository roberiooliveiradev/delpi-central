# DAVI Wave 005 — Stock Balances Retrieval Correction

**TASK_ID:** `DAVI-WAVE005-STOCK-BALANCES-RETRIEVAL-CORRECTION-001`  
**STATUS (source):** PASS  
**STATUS (live/deploy):** `PENDING_EXTERNAL_ACTION` / `TEST_NOT_RUN`

## Problem

Query: `resumo dos saldos de estoque por depósito`

| Before | Score (local) |
|---|---|
| 1. get_supplies_stock_balances_items | ~0.93 |
| 2. get_product_stock | ~0.904 |
| 3. get_supplies_stock_balances_summary | ~0.84 |

Expected top: `get_supplies_stock_balances_summary`

## Root cause

- Items owned generic alias `estoque por depósito` (contiguous phrase hit).
- Summary aliases did not match contiguous phrases (`saldo`≠`saldos`; `resumo saldos` broken by `dos`).
- Generic ranking algorithm correct; **no algorithm change**.

## Fix

- Allowlist **v12 → v13** (semanticAliases contract change; eligible remains 53).
- Summary: precise resumo/consolidado/total + depósito aliases.
- Items: remove ambiguous `estoque por depósito`; add list/itens/produtos phrases.
- Product stock: add `saldo por filial do produto`, `estoque do código` (product-specific).
- Projection `by_warehouse[].branch` unchanged.

## Decision

`CORRECT_STOCK_BALANCES_SUMMARY_ITEMS_RETRIEVAL`  
previous: `CORRECT_STOCK_BALANCES_BRANCH_GRAIN_PROJECTION`
