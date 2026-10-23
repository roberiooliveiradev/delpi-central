# SUPPLIER_ENRICHMENT_RETENTION_CLASSIFICATION — GATE-B (S2)

> **Estado: EVIDENCE-DRIVEN.** Classificação das categorias de dados das
> revisões de enriquecimento contra a política LGPD institucional vigente
> (`docs/14-auditoria-lgpd/ropa-registro-tratamento.md`,
> `relatorio-adequacao-lgpd.md`). Não cria política paralela.

## Categorias × enquadramento

| Categoria | Dados armazenados | Finalidade | Enquadramento ROPA | Retenção |
|---|---|---|---|---|
| Review (metadados) | `review_id`, `supplier_code/store`, `actor_subject` (UUID), `source_id/reference/retrieved_at`, versões, status, revision, timestamps | execução do workflow de revisão | §6/§7 — User ID como ator de processo/configuração (execução de contrato / legítimo interesse) | enquanto a revisão estiver ativa; expiração por TTL |
| Proposta por campo | `field_key`, `section_key`, estados, `eligibility_reason`, `source_field`, `source_reference`, `current_value`, `suggested_value` | exibir divergência, gerar draft | dados cadastrais **corporativos/públicos** (registro CNPJ) — não são dados pessoais de pessoa natural | ciclo de vida da revisão |
| Decisão | `decision_id`, `review_id`, `proposal_id`, `actor_subject`, `decision`, `reason_code`, `decided_at`, `revision`, `idempotency_key` | auditabilidade da decisão | §2 — logs de auditoria (User ID, legítimo interesse Art. 7º IX) | alinhada a §2: 2 anos |
| Evento (append-only) | `event_type`, `actor_subject`, `created_at`, metadados mínimos | rastreabilidade | §2 — logs de auditoria | alinhada a §2: 2 anos |

## Minimização aplicada

- `tax_id` **nunca** é persistido em proposta (campo protegido; já conhecido pela identidade da revisão).
- Nenhum payload bruto de provider, nenhum token, nenhum espelho SA2.
- `contact_name` não está no mapeamento v1; `phone`/`email` são canais de contato **empresariais publicados** em registro público — flag residual abaixo.
- `unit_context` permanece `NULL` (sem escopo de unidade comprovado — ver contrato de escopo).
- `review_id`, `actor_subject`, `created_at`, status inicial: server-side; navegador não os define.

## TTL da revisão

`expires_at` = `created_at + ENRICHMENT_REVIEW_TTL_HOURS` (default operacional **24h**). É restrição funcional de vigência do rascunho (proposta B-02 do contrato — pendente de decisão PO para o valor final), **não** política de retenção. Revisão expirada bloqueia decisões (410); o registro permanece para auditoria conforme §2.

## Resíduos (declarados)

1. Endosso formal do DPO sobre esta classificação e inclusão de linha `supplies-api` na ROPA institucional — pendente de governança (não editada unilateralmente).
2. `phone`/`email` corporativos podem coincidir com dados pessoais em casos de MEI/contato pessoal — monitorar; hoje são propostos apenas como exibição/draft, nunca aplicados sem política de fonte confiável (`trusted_source_policy_pending`).
3. Prazo definitivo de anonimização dos UUIDs de ator ao expirar revisões — herda padrão §2 (2 anos); job de anonimização não implementado nesta fatia.

**Verdict: GATE-B = `PASS_WITH_RESIDUAL`** — todas as categorias persistidas enquadram-se em tratamentos institucionais vigentes (§2/§6/§7) ou são dados corporativos públicos; minimização aplicada; endosso formal DPO pendente e registrado.
