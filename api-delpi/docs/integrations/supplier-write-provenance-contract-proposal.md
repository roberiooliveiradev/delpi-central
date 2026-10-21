# Contrato transversal de proveniência — escrita de fornecedores na api-delpi

> **PROPOSED / TARGET — DOCUMENTAÇÃO, NÃO IMPLEMENTADO.** Proposta arquitetural transversal para **qualquer BFF/consumer** que utilize a api-delpi para POST/PUT de fornecedor SA2. O documento existente [contrato REST Protheus](./protheus-rest-supplier-api-contract.md) continua sendo authority sobre o payload upstream; não se pode acrescentar campos arbitrários à MATA020. Não afirmar runtime ou persistência. Registrar decisão formal/ADR e consumer impact antes de freeze/implementação.

## 1. Invariante central — origem da alteração é dado de negócio

Todo write autorizado, manual ou apoiado em fonte externa, deve ter **proveniência por operação e por campo alterado**, incluindo:
- **de onde veio a informação:** `source_type` = `MANUAL_USER_INPUT`, `GOVERNMENT_API`, `THIRD_PARTY_API`, `INTERNAL_SYSTEM`, `IMPORT`, `AUTOMATION_RULE`, `UNKNOWN_LEGACY` (legacy somente quando não comprovável; não fabricar fonte);
- **qual origem específica**: `source_id` estável e registrado, ex. `serpro_cnpj` **somente se contratado/consultado**, ou `manual_form`, `source_reference` hash/identificador opaco, `source_retrieved_at`, `source_dataset_version` quando disponível;
- **como foi alterado:** `change_mode` = `MANUAL_DIRECT`, `EXTERNAL_SUGGESTION_USER_APPROVED`, `BULK_SUGGESTION_USER_APPROVED`, `AUTOMATED_BY_APPROVED_POLICY`, `SYSTEM_SYNC`, `IMPORT_JOB`; não usar `AUTOMATED` para simples preenchimento/sugestão confirmado pelo usuário;
- **quem aprovou/solicitou e quem executou**: `actor_subject` (identidade resolvida server-side), `initiating_client_id`, `approver_subject` quando aplicável, `on_behalf_of` de automações contratadas, `policy_id/version` para automação;
- `field_key`, antes/depois **segundo política de PII**, `decision_id/review_id`, `correlation_id`, `operation_id`, timestamp e resultado de persistência.

**Regra:** metadados de request não provam write realizado. A trilha só aponta "persistido no ERP" após verificação canônica confiável `CONFIRMED`. `ACKNOWLEDGED`, `UNKNOWN` ou `RECONCILIATION_REQUIRED` não podem aparecer como persistidos.

## 2. Bounded contexts / estrutura

| Owner | Obrigação |
|---|---|
| `supplies-api` | faz consulta/compare, resolve Core effective AuthZ, grava decisões de aceite/recusa e origem das sugestões, envia proveniência aprovada no write |
| **`api-delpi`** | define **contrato canônico de metadados de proveniência para qualquer consumer**; valida origem, actor/client, associa metadados ao tracking de operação e evidência de confirmação; não aceita autodeclaração como prova de identidade |
| `api-delpi` → Protheus MATA020 | envia **somente payload de campos suportados pela integração ERP**; metadata de audit não vai para campos SA2 desconhecidos |
| Core/Keycloak | prova de identidade SSO, scopes e efetive permissions; JWT não é fonte final de grants |
| outros BFFs autorizados | encaminham origem, modalidade, ator e motivação através da mesma versão de contrato; devem passar por AuthZ do próprio produto |

A proveniência **não deve ficar só no frontend ou só na supplies-api**, senão outras APIs que usam api-delpi perderão rastreabilidade. **Source of truth da SA2 continua Protheus**; event/audit store de integração da api-delpi registra histórico da *modificação*, não espelha registro SA2.

## 3. Schema de metadata v1 candidata (envelope / headers a congelar)

Preferir objeto de contexto de escrita separado da lista de campos Protheus. Este exemplo é **candidato**, dependente de versionamento e compatibilidade de todas as rotas:

```json
{
  "supplier_changes": {
    "supplier_name": "Razão social revisada",
    "district": "CENTRO"
  },
  "change_context": {
    "schema_version": "1",
    "initiating_client_id": "supplies-api",
    "change_mode": "EXTERNAL_SUGGESTION_USER_APPROVED",
    "reason_code": "CADASTRAL_REVIEW",
    "review_id": "opaque-review-id",
    "idempotency_key": "opaque-operation-id",
    "field_provenance": [
      {
        "field_key": "supplier_name",
        "source_type": "GOVERNMENT_API",
        "source_id": "approved_registry_provider",
        "source_reference": "opaque-evidence-id",
        "retrieved_at": "2026-10-21T12:00:00Z",
        "decision_id": "opaque-decision-id",
        "decision_mode": "USER_ACCEPTED"
      },
      {
        "field_key": "district",
        "source_type": "MANUAL_USER_INPUT",
        "source_id": "manual_form",
        "decision_mode": "USER_EDITED"
      }
    ]
  }
}
```

**O exemplo acima NÃO é o payload REST vigente.** Antes de implementar, verificar schemas DTO/handlers reais, compatibilidade POST/PUT e mecanismo oficial de metadata (envelope aninhado, cabeçalho assinado, contexto interno), não quebrar rota existente. `actor_subject` e claims/autorização **não podem ser arbitrariamente fornecidos pelo MFE**, devem ser derivados de identidade validada e vinculação S2S. Provider ID é verificável no server-side contra o evento/review; cliente não pode se atribuir livremente origem oficial. `source_id=approved_registry_provider` é placeholder, não prova consulta.

### Regras cross-consumer

1. **Toda escrita nova exige origem explícita**; durante rollout, chamadas legadas sem contexto precisam de política de compatibilidade visível e limitada, com `UNKNOWN_LEGACY` e cliente identificado — **nunca** inventar `MANUAL_USER_INPUT` para chamadas antigas.
2. **Campo a campo obrigatório**: uma operação pode misturar valor da API oficial com correção manual; `change_mode` global não substitui `field_provenance`.
3. A lista de `field_key` deve corresponder **exatamente** a campos efetivamente enviados ao upstream na operação, após allowlist/normalização; metadata para campos protegidos/rejeitados → erro fail-closed.
4. Sugestão recusada → somente evento de decisão no BFF, **sem change provenance de write**. Aceita mas não salva → evento `ACCEPTED_FOR_DRAFT`, **sem marcar ERP confirmed**.
5. Operação executada por automação exige contrato explícito de `policy_id/version`, aprovação, owner e gate; não habilitar por enumerar `AUTOMATED_BY_APPROVED_POLICY`.
6. Atualizações POST de criação e PUT parcial devem poder associar campos ao `operation_id` da `api-delpi`; idempotency e reconciliação sem retries cegos.
7. Evolução compatível com consumidores: negociar `schema_version`, `compatibility_window`, `deprecation`, testes consumer-driven e rollout sem drift.

## 4. Máquina de estados da evidência

```text
CHANGE_REQUESTED (provenance validated, no ERP change asserted)
  -> SENDING -> ACKNOWLEDGED (NOT persistent proof)
  -> CONFIRMED (read-after-write / permitted canonical evidence)
  -> REJECTED | FAILED_PRE_SEND | UNKNOWN | RECONCILIATION_REQUIRED
```

Proveniência da intenção é imutável e vinculada à operação; confirmação anexa `confirmed_at`, método de prova, referência canônica/snapshot redacted ou digests seguros. Mudanças posteriores criam evento novo, nunca sobrescrevem origem de evento anterior. Última alteração por campo = evento `CONFIRMED` mais recente para chave+loja+filial/unidade/field, ordenação confiável; **não** usar `ACKNOWLEDGED` nem tentativa mais nova ainda indeterminada para substituir origem exibida.

Proposta para leitura por outros consumidores (sem implementação): endpoint da api-delpi, sujeito a owner/AuthZ S2S, de **histórico/proveniência da alteração** por fornecedor e campo, paginado e redacted. Não inferir “campo de origem embutido na SA2”: armazenamento de auditoria em integração é suficiente para provenance histórica se cobertura e durabilidade forem garantidas; **se o requisito for metadado materializado dentro do ERP, exige contrato TOTVS distinto** (campos customizados, hooks, ownership e rollback), não supor suporte.

## 5. Modelo lógico de storage na api-delpi (TARGET)

Aproveitar `integration_tracking` existente; inspecionar schema e migrations reais antes de alterar. Se o tracking atual não suporta payload granular de origem, projetar tabelas/eventos de proveniência acoplados à operação:
- `supplier_change_provenance`: `id`, `operation_id` FK, `supplier_code`, `supplier_store`, `company_branch_scope`, `field_key`, `source_type`, `source_id`, `source_reference_digest`, `source_retrieved_at`, `change_mode`, `actor_subject`, `initiating_client_id`, `review_id`, `decision_id`, `confirmed_at`, `confirmation_method`, `status`, timestamps;
- `supplier_change_provenance_events`: append-only, snapshots mínimos sem PII, transições e hashes/HMAC por política;
- referência entre `supplies-api.supplier_enrichment_decisions` e `api-delpi.operation_id`, por contrato HTTP (sem FK interdatabase);
- índices por `supplier_code/store/scope/field_key/confirmed_at`, e retenção por finalidade.

Não duplicar SA2; não guardar payload integral externo ou before/after em plaintext sem aprovação jurídica/retention. HMAC com chave no server-side para evidência, sem prometer valor criptográfico imutável se algoritmo/rotação não forem decididos. Logs comuns não contêm CNPJ, nomes, endereços, JWT ou secret.

**Ambiguidade crítica:** a trilha histórica só será completa a partir do **coverage start** de todos writers de fornecedores. Mudanças diretas pelo Protheus/MATA020 ou outros sistemas fora da api-delpi não terão origem rastreável pela DELPI sem eventos/integração TOTVS própria. Marcar como `SOURCE_UNKNOWN_EXTERNAL_WRITE` quando discrepância for detectada; **não alegar rastreabilidade global de SA2**.

## 6. AuthZ, leitura e minimização

- `api-delpi` identifica consumidor S2S e usuário delegado conforme contrato; não confiar em strings `actor_subject` fornecidas por serviço não autorizado.
- BFF resolve Core effective permissions `capability AND unit_scope AND resource_scope AND business_rule`; endpoints de histórico/proveniência precisam scope explícito e redaction server-side.
- Persistência auditável de quem/como não significa que todo usuário possa ler identidade/PII completa do operador. Definir visibilidade: fonte e modo para usuário de fornecedor autorizado; ator detalhado e diagnóstico somente conforme escopo e finalidade.
- DPO define base legal/retention; dados de contato e representantes podem ser dados pessoais mesmo no contexto PJ; evitar QSA/CPF de sócios no MVP.
- Direito de retificação e retenção/eliminação: política por categoria (reviews efêmeros, decisões, audit legal, integration tracking), documentação de exceções legais e retenção limitada.

## 7. Testes e invariantes do contrato transversal

- POST e PUT por 2 consumers simulados: origem manual e oficial, ambos permitidos se autorizados e campo comprovado.
- Mixed-source field provenance e mismatch de `field_keys` → rejeição.
- `GOVERNMENT_API` sem evidence válida → fail-closed (não aceitar alegação do cliente).
- `AUTOMATED_BY_APPROVED_POLICY` sem policy/gate aprovado → proibido.
- operação ACK/UNKNOWN não aparece como proveniência confirmada.
- operação CONFIRMED com evidence produz timeline e leitura por campo.
- evento/retry idempotente não duplica trilha, não refaz PUT em outcome desconhecido.
- CNPJ/tax_id e identidade protegidos na atualização; campos omitted não geram provenance fictícia.
- 401 sem token, 403 sibling unit/resource, S2S audience/client mismatch, Core fail closed.
- migration forwards/backwards, retenção, redaction/log leakage, consumidor legado com política explícita, regressão de contrato e rollback com states em voo.

## 8. Aprovações / bloqueios

`P-01` decisão de produto: provenance visível por campo ao usuário (fonte, data, modo), histórico, filtro de autoria; **pedido explícito do PO**.
`P-02` arquitetura: schema cross-consumer e owner audit, extension tracking, identidade S2S e ator delegado — `TO_INVENTORY`.
`P-03` TOTVS: cobertura writes fora da api-delpi e viabilidade de incluir origem **no ERP** se requisito literal — `TO_INVENTORY`.
`P-04` jurídico/DPO: retenção por categoria, encryption e acesso/eliminação — `PENDING`.
`P-05` contratos: retrofit dos consumidores existentes, versionamento e compatibilidade — `TO_INVENTORY`.
`P-06` finalização: freeze+ADR+OpenAPI+migration+GO explícito — `NOT_AUTHORIZED`.

**Saída:** `PROVENANCE_CONTRACT=PROPOSED`; `ALL_WRITERS_COVERED=NOT_PROVEN`; `ERP_EMBEDDED_PROVENANCE=NOT_PROVEN`; `IMPLEMENTATION=NOT_AUTHORIZED`.
