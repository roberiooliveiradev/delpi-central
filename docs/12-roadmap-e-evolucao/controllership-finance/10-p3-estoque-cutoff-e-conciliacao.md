# 10 — P3 — Estoque, Cutoff e Conciliação

## State model

```text
PRELIMINARY
→ WAITING_FOR_CUTOFF
→ REVALIDATION_REQUIRED
→ READY_TO_CLOSE
→ STOCK_CLOSED
```

## Cutoff

O sistema mostra sinais de prontidão.

Um humano autorizado confirma o cutoff.

Não inferir cutoff automaticamente apenas porque relatórios parecem estáveis.

## Revalidação

Após cutoff confirmado, disparar automaticamente o núcleo:
- P7;
- Entradas/Saídas;
- H02;
- conciliação tripla.

Também deve existir reprocessamento/revalidação manual para usuário autorizado.

## READY_TO_CLOSE

Requer:
- cutoff confirmado;
- revalidação aplicável;
- divergência operacional zero;
- sources necessários disponíveis.

Não equivale a STOCK_CLOSED.

## Sacramentação

V1 não executa escrita no ERP.

A autoridade permanece no owner autorizado.

E03 confirmará executor/permissões reais.

## STOCK_CLOSED

Target: ler estado canônico do owner/ERP, se existir.

T03 é inventário obrigatório.

Sem fallback manual silencioso.

Se T03 provar ausência/incompatibilidade, registrar EXECUTION_DRIFT.

## Conciliação

```text
Divergência = Entradas/Saídas - P7 - H02
```

Drilldown:
- total;
- grupo;
- item/evidência.

## Freshness

Resultados estruturados devem carregar:
- source;
- fetched/calculated_at;
- competência;
- unidade;
- preliminary/final;
- rule/version.

## Edge cases

- H02 indisponível;
- P7 indisponível;
- cutoff confirmado com source falhando;
- divergência zero pre-cutoff;
- input alterado pós-revalidação;
- estado owner atrasado;
- unidade não aplicável.

## Pendências de implementação

- E02 correção pós-sacramentação;
- E03 executor/permissões;
- T01 bindings;
- T03 estado canônico.
