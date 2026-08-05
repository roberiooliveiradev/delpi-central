# 21 — Fase 2B.4 — Anexos CAPEX (frontend)

**Branch:** `feat/planejamento-orcamentario`  
**Data:** 2026-08-05  
**Escopo:** upload multipart, listagem, download autenticado, arquivamento, progresso, erros amigáveis, testes Vitest.  
**Fora:** alterações de backend/migrations; submissão; aprovação; restore; conta contábil; exportações.  
**Commit:** nenhum (conforme brief).

---

## Status

```text
STATUS: CONCLUÍDO COM RESSALVAS
```

Ressalva: smoke autenticado da seção de anexos no portal permanece BLOCKED sem sessão — shell HTTP e `remoteEntry.js` validados; não substituem fluxo autenticado.

---

## 1. Integração no formulário

Seção **Documentos e Anexos** no `CapexInvestmentFormPage`, **fora** do `<form>` do investimento (evita nested forms e isolamento do autosave).

| Estado | Comportamento |
|--------|----------------|
| Sem ID (`persistedId` null) | “Salve o rascunho para adicionar documentos.” |
| Com ID | Listagem + upload |
| Investimento arquivado | Somente leitura (download; sem upload/arquivar) |

Componente: `CapexInvestmentAttachmentsPanel`.

---

## 2. Upload e progresso

- `multipart/form-data` via `httpPostFormWithProgress` / `uploadCapexInvestmentAttachment`
- Campos: arquivo, nome de exibição, tipo, descrição opcional, `idempotency_key` (UUID por tentativa / troca de arquivo)
- Validação client: arquivo, nome, tipo, 25 MB, extensões de `documentUpload.ts` (mesmo contrato do storage)
- Estados: Pronto / Enviando / Processando / Concluído / Erro — barra de progresso com %
- Botão desabilitado durante envio; cancelar limpa o formulário antes do envio
- Sucesso: limpa form, recarrega lista, feedback; não altera campos do investimento

Tipos (valores backend + labels PT):

| Valor | Label |
|-------|--------|
| `quotation` | Orçamento |
| `commercial_proposal` | Proposta comercial |
| `technical_specification` | Especificação técnica |
| `image` | Imagem |
| `justification` | Justificativa |
| `other` | Outro documento |

---

## 3. Listagem

`GET /capex/investments/{id}/attachments` — cards/lista adaptável (`po-doc-list`):

nome, tipo, descrição, nome original, tamanho, data, `created_by`, ações Baixar/Arquivar.

Sem `storage_key` / paths. Arquivados não retornam na listagem padrão da API.

---

## 4. Download

`downloadCapexAttachment` → blob autenticado → `triggerBrowserDownload` com `original_filename`.  
Trata 401/403/404; botão “Baixando…” impede clique duplo.

---

## 5. Arquivamento

Confirmação textual do brief → `POST …/attachments/{id}/archive` → feedback + reload. Sem restore.

---

## 6. Isolamento do autosave

Painel com estado próprio; fora do form principal; não chama `patchForm` / `scheduleAutosave` / `updateCapexInvestment`. Teste de regressão no form page.

---

## 7. Testes

| Arquivo | Cobertura |
|---------|-----------|
| `CapexInvestmentAttachmentsPanel.test.tsx` | seção sem ID, lista, vazio, validação, limite, upload+progresso, MIME/ext/tamanho, download, archive, RO, 401/403, sem storage_key |
| `capexAttachments.test.ts` | labels, validação, erros, idempotency |
| `CapexInvestmentFormPage.test.tsx` | bloqueio pré-ID + isolamento autosave |

Vitest do pacote: **85** passed.

---

## 8. Build e smoke

| Check | Resultado |
|-------|-----------|
| lint (0 errors) / typecheck / Vitest (85) / `vite build` | OK |
| `./infra/scripts/up-dev-sequential.sh --fase mfe --build planejamento-orcamentario` | OK |
| `HEAD …/assets/remoteEntry.js` | **200** |
| Shell rota de investimento | **200** |
| Smoke autenticado anexos | **BLOCKED** (sem sessão) |

---

## 9. Arquivos

- `src/components/CapexInvestmentAttachmentsPanel.tsx` (+ test)
- `src/utils/capexAttachments.ts` (+ test)
- `src/api/budgetPlanningApi.ts`, `src/types/budgetPlanning.ts`
- `src/pages/CapexInvestmentFormPage.tsx` (+ test)
- `src/index.css`
- esta doc

---

## 10. Pendências

- Submissão / aprovação / restore / exportações
- Smoke autenticado no portal
- Frontend de conta contábil (fase futura)

---

## 11. Relatório resumido

UI de anexos CAPEX integrada ao formulário 2B.2, reutilizando o cliente multipart com progresso da Fase 1, isolada do autosave, com testes e build verdes.
