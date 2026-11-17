# 166 — Gate B — Saneamento de competências 2026-09/2026-10 e baseline do checklist mensal

Estado: **pacote Gate A preparado; execução destrutiva em produção NÃO realizada.** Este documento é o manifesto técnico cuja aprovação explícita pré-autoriza o Gate B.

## 1. Objetivo

1. O conteúdo da V2 do template `monthly-closing-checklist` (16 itens, revisão 9, estado `REVIEW`, sem vigência publicada) passa a ser o conteúdo da **V1 oficial**, `PUBLISHED`, vigência inicial `2026-01`.
2. A V2 deixa de ser versão operacional concorrente (`INACTIVE`, preservada como histórico).
3. As competências `2026-09` e `2026-10` são excluídas com seus dados exclusivamente dependentes (documentos, versões, arquivos, mensagens e demais linhas por `competence_id`), pela exclusão governada.
4. Demais competências, documentos compartilhados, dados do ERP/TOTVS e registros de outros contextos são preservados. Auditoria (`closing_audit_event`) permanece íntegra (`ON DELETE SET NULL`, V021).

## 2. Ambiente e identificação

| Item | Valor |
|---|---|
| Bounded context | `controllership-finance` |
| BFF | `controllership-finance-api` (`/apps/controllership-finance-api`) |
| MFE | `plugins/controllership-finance` (`/apps/controllership-finance`) |
| Schema | `controllership_finance` (postgres-plugins) |
| Processo | PROC-0072 |
| Permissão exigida | `controllership-finance.manage` (nenhuma permission nova) |

IDs **preliminares** (observação do usuário — revalidar antes de escrever):

- Template `a0e24014-7a04-4e89-a2d7-92054ed7f73d`
- Competência 2026-09 `5daaa8d1-3024-4fdf-9a94-c9c14f87cc96`
- Competência 2026-10 `3745ae2a-0235-46e6-98c8-98aef171ab0d`
- Documentos `de463d86-…` (set) e `b7d8706c-…` (out)

**Fail-closed:** qualquer divergência entre o inventário real e o manifesto aprovado aborta a execução.

## 3. Causa raiz dos bloqueios

- `competence_delete_blocked`: o caminho de exclusão rejeitava **qualquer** dependência — inclusive dados exclusivamente pertencentes à competência (documentos, mensagens, itens de checklist), que são exatamente o que deve sair no saneamento.
- `window_covers_open_competence` / `retroactive_effective_period`: guards **intencionais** do fluxo prospectivo (`apply_document_requirement`) — impedem que uma janela retroativa altere o catálogo sob competências já abertas, porque snapshots são congelados. Não foram removidos; a consolidação do baseline é operação administrativa controlada (script) que verifica ausência de snapshots conflitantes antes de mexer na timeline.

## 4. Componentes entregues (Gate A)

| Componente | Arquivo |
|---|---|
| Exclusão governada com dependentes | `controllership-finance-api/.../persistence/competence_deletion.py` |
| Contrato DELETE + diagnóstico | `.../interface/http/routes/competences_routes.py` |
| Pass-through repository | `.../persistence/closing_checklist_repository.py` |
| Diagnóstico CLARA (conservador) | `.../application/clara/governed_writes.py` |
| MFE: tipos + diálogo `eligible_with_dependents` | `plugins/controllership-finance/src/api/competencesApi.ts`, `.../DeleteCompetenceControl.tsx` |
| Inventário/backup/verify | `controllership-finance-api/scripts/competence_inventory_backup.py` |
| Consolidação V2→V1 | `controllership-finance-api/scripts/consolidate_checklist_baseline.py` |
| Testes PG de cascade | `tests/test_pg_competence_delete_dependents.py` |

Contrato novo (backward-compatible):

- Diagnóstico pode retornar `outcome = "eligible_with_dependents"` + `dependents.exclusive[]` + `dependents.shared_files`.
- `DELETE` aceita `delete_dependents: true` + `expected_dependents: {<tabela>: <count>}` — OCC sobre o inventário; divergência = `competence_delete_conflict`.
- Sem os campos, comportamento anterior intacto (`eligible`/`blocked`).
- `closing_package`, `closing_review_assignment`, `closing_terminal_rejection` e referências compartilhadas continuam `BLOCKING` — inclusive sob o flag. Tabela dependente desconhecida (schema evoluído) = BLOCKING por padrão.

## 5. Procedimento de execução (Gate B)

Ordem obrigatória; cada etapa só avança com evidência da anterior.

```text
E1 inventário      → competence_inventory_backup.py inventory --expect-id …
E2 aprovação       → manifesto (este doc + saída E1) aprovado nominalmente
E3 backup          → backup --output cf-backup-<ts>.json + cópia dos
                     objetos físicos (storage_key em document_files)
E4 restore test    → validar restauração do JSON em schema de homologação
E5 dry-run         → verify --manifest (fingerprint idêntico) + diagnóstico
                     GET /closing/competences/{period}/deletion-eligibility
E6 exclusão 09     → DELETE /closing/competences/2026-09
                     {expected_competence_id, delete_dependents: true,
                      expected_dependents: <manifesto E5>, idempotency_key}
E7 exclusão 10     → idem 2026-10
E8 consolidação    → consolidate_checklist_baseline.py apply
                     --source-version 2 --target-version 1
                     --effective-from 2026-01 --expect-items 16
                     (primeiro --dry-run; depois real)
E9 read-back       → estado final §6 verificado por SELECT direto
```

Exclusão via Portal ou HTTP com `manage`; nunca por SQL manual. Falha de limpeza de storage é reportada como residual/orphan housekeeping — não false-success.

## 6. Estado final esperado (read-back)

```sql
-- V1 oficial
SELECT version, status, effective_from_period
  FROM controllership_finance.checklist_template_version
 WHERE template_id = '<template>' ORDER BY version;
-- V1 PUBLISHED 2026-01 (16 itens) ; V2 INACTIVE

SELECT count(*) FROM controllership_finance.checklist_template_item
 WHERE version_id = '<v1>';  -- = 16, checksum = manifesto E1

SELECT period FROM controllership_finance.monthly_competence
 WHERE period IN ('2026-09','2026-10');  -- vazio

-- zero órfãos
SELECT count(*) FROM controllership_finance.closing_document d
 WHERE NOT EXISTS (SELECT 1 FROM controllership_finance.monthly_competence c
                   WHERE c.competence_id = d.competence_id);

-- auditoria preservada
SELECT event_type FROM controllership_finance.closing_audit_event
 WHERE detail->>'competence_id' IN ('<id09>','<id10>')
 ORDER BY created_at;
-- COMPETENCE_OPENED … COMPETENCE_DELETED
```

## 7. Rollback

- **Antes de E6:** nada a fazer (somente leituras).
- **Depois de E6/E7:** reabertura manual da competência é possível, mas dados exclusivos só retornam via restore do backup E3 (JSON + arquivos físicos). Por isso E4 é pré-requisito.
- **Depois de E8:** UPDATE reversível — V2 volta a `REVIEW`/`PUBLISHED` e V1 a `INACTIVE`/`DRAFT` com os itens originais restaurados do backup de `checklist_template_item` (exportar antes de E8: `SELECT * … WHERE version_id IN (<v1>,<v2>)`). Nenhuma competence_snapshot é tocada, então rollback não corrompe competências.
- **Qualquer ponto:** divergência de manifesto/contagem aborta com rollback integral (transação única por operação).

## 8. Riscos e resíduos

- Objetos físicos de storage ficam fora da transação; falha pós-commit gera residual reportado (orfanato de arquivo), nunca sucesso falso.
- `clara_proposal`/`clara_batch` abertos para o período bloqueiam (checagem por `resource_key`/`payload`/`plan` — sem FK). Janela entre PREPARE CLARA e DELETE é coberta pela revalidação imediata.
- Propostas CLARA criadas após a contagem e sem referência textual ao período/competência poderiam passar — mitigado pela revalidação na transação.
- A seleção de versão vigente na abertura (`PUBLISHED`, maior `effective_from_period <= período`) é global por schema; garantir que nenhum outro template publique versão com vigência sobreposta (invariante atual do domínio: um template de fechamento).
- Schema local de dev está em V017; produção deve estar ≥V021 — confirmar `schema_migrations` em E1.

## 9. Checklist de aprovação

- [ ] Inventário E1 anexado (fingerprint + contagens + IDs reais)
- [ ] Backup E3 gravado e restore E4 validado em homologação
- [ ] Dry-run E5 sem divergências
- [ ] Janela de mudança e operador responsável definidos
- [ ] Rollback §7 revisado
- [ ] Estado final §6 acordado
