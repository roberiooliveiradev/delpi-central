# Carga-Máquina — Regras de Sequenciamento por Centro de Trabalho

> Estado: **Etapa 1 implementada — fundação administrativa**.
> Base factual: `main` @ `1ed9df25b` + worktree local (pendente de commit).
> Iniciativa nova — sem relação com as Etapas E1–E4 de seleção múltipla
> (`MACHINE-LOAD-MULTI-SELECTION-E1.md`).

## 1. Objetivo e escopo

O PCP poderá cadastrar **perfis de sequenciamento** — listas ordenadas de
critérios tipados — e vinculá-los a `(filial, centro de trabalho)`. Etapas
futuras farão o motor consumir o perfil vinculado do CT ao resequenciar.

**Esta etapa entrega:** domínio (critérios/validações), persistência
(V018), serviço de aplicação com concorrência otimista e auditoria, rotas
HTTP, permissão administrativa dedicada e testes.

**Esta etapa NÃO entrega:** execução da otimização por perfil, resolução de
materiais no motor, interface administrativa React, ativação automática de
regras na programação, qualquer alteração na fila WORKING/PUBLISHED.

## 2. Inventário e reutilização

| Capacidade | Equivalente existente | Decisão |
|---|---|---|
| Motor de sequenciamento | `machine_load_optimization.py` — `pa_due_date` soberano + `group_by_tool` | REUSE — perfis só armazenam config; motor inalterado |
| Data de entrega do PA | `machine_load_delivery_window.py` (`operation_due_date`) | REUSE — critério `pa_due_date` referencia a mesma regra |
| Admin CRUD + `.manage` | `product-3d-models` (service/rotas/manifest) | EXTEND padrão |
| Persistência | `plugins_postgres_connection` + migrations V0xx | EXTEND — `V018` |
| Concorrência otimista | `expected_keys`→409 do sequenciamento | EXTEND conceito — `expected_revision`→409 |
| Gate de filial | `BranchAccessService` (`view.filial-0X` + `access`) | REUSE |
| Auditoria | `mes_audit_events` é run-scoped | NEW — `sequencing_profile_revisions` + `binding_events`, append-only na mesma transação |
| Leitura TOTVS/empenhos | gateway `api-delpi` | fora de escopo nesta etapa |

## 3. Contrato de domínio

Tipos de critério (fechados — nada de scripts/expressões do usuário):

- `pa_due_date` — **obrigatório e sempre o primeiro** (regra soberana vigente);
- `tool_group` — agrupa por ferramenta dentro da data (sem params);
- `material_code` — agrupa pelo código exato do material (D4_COD), com params:
  - `material_type`: só `"MP"`;
  - `eligible_product_groups`: lista não vazia de B1_GRUPO;
  - `identity_source`: só `"operation_then_order"` (empenho da operação →
    fallback OP; empenhos com valor original **e** saldo zerados são
    ignorados na identificação);
  - `ignore_zeroed_allocations`: bool (default `true`);
  - `on_missing` / `on_ambiguous`: só `"flag"` — nunca escolher
    arbitrariamente entre códigos elegíveis distintos.

Validações (`domain/sequencing_profile.py`): critério desconhecido, duplicado
ou mal formado → `SequencingProfileInvalid` (422); `pa_due_date` fora do
primeiro lugar → 422.

## 4. Persistência (V018)

```
sequencing_profiles            (id, name, description, status, revision,
                                criteria JSONB, created/updated_*)
sequencing_profile_revisions   (profile_id, revision, action, snapshot, actor)
                               append-only; ON DELETE RESTRICT
sequencing_profile_bindings    PK (branch, work_center) → profile_id
                               ON DELETE RESTRICT
sequencing_profile_binding_events  (bound|rebound|unbound, actor, at)
                               append-only; mesma transação da mutação
```

Identidade do vínculo = **filial + CT** (nunca o CT sozinho). Um perfil pode
servir a vários CTs; cada CT tem no máximo um perfil.

## 5. Contrato HTTP

| Método | Path | Permissão | Erros |
|---|---|---|---|
| GET | `/machine-load/sequencing-profiles?branch=` | `machine-load.view` + filial | 403/422 |
| GET | `/machine-load/sequencing-profiles/{id}?branch=` | idem | 403/404/422 |
| POST | `/machine-load/sequencing-profiles?branch=` | `sequencing-profiles.manage` + filial | 403/422 |
| PUT | `/machine-load/sequencing-profiles/{id}?branch=` | manage + filial | 403/404/409/422 |
| GET | `/machine-load/sequencing-bindings?branch=&workCenter=` | view + filial | 403/422 |
| PUT | `/machine-load/sequencing-bindings?branch=&workCenter=` | manage + filial; `{profile_id|null}` | 403/404/409/422 |

- `expected_revision` no PUT do perfil → divergência = **409** (otimista).
- Nova permissão no manifest: `production-control.sequencing-profiles.manage`.
- Leitura reutiliza `production-control.machine-load.view` — separação
  view/manage mantida.
- **Concessão da permissão (revisão):** o manifesto sozinho não concede
  nada — `register_plugin` no Core só aceita versão nova (`version` bumpado
  para `0.1.4`) e o `PUT /admin/apps/{id}/manifest` rejeita mudança de
  permissões. Fluxo efetivo: merge → `scripts/register-manifest.sh` (token
  `apps.manage`) → atribuir a permissão ao papel desejado no Core.
- Resposta no envelope padrão `ok(data)`/`fail(msg, status)`.
- Rollback de deploy: basta ignorar as rotas; V018 não toca tabelas vigentes.

## 6. Perfil-piloto (CT-02B, filial 02)

Fixture de teste `pilot_profile_payload()` em
`tests/test_sequencing_profiles.py`: «Corte e Decape - Entrega e Cabo» —
`pa_due_date` + `material_code` com os 16 grupos de cabos
(1037, 1038, 1053, 1007, 1042, 1047, 1040, 1041, 1055, 1049, 1002, 1001,
1005, 1051, 1044, 1036). **Não é semeado** em produção.

## 7. Limites desta entrega

Não altera fila, motor, refresh, publish, empenhos SD4 nem api-delpi.
Verificado por construção: `SequencingProfileService` não recebe o
repositório de snapshots (teste estrutural cobre).

## 8. Próximas etapas (TARGET)

- Consumo do perfil vinculado pelo motor (resolução de material por
  `identity_source` + consulta em lote de empenhos via api-delpi).
- Interface administrativa no MFE production-control.
- Políticas adicionais de ausente/ambíguo e novos tipos de critério.

## 9. Verificação (Etapa 1)

- `tests/test_sequencing_profiles.py`: 30 testes unitários/HTTP + 1 teste de
  integração Postgres real (gated `PC_TEST_MES_DB=1`) — validação de
  critérios, ordem, 16 grupos, 403/404/409/422, escopo de filial,
  view-vs-manage, auditoria, falha de escrita sem estado parcial e
  isolamento da fila.
- Suíte API: 1171 passed, 2 falhas baseline pré-existentes (line_feeder,
  operator_directory), 30 skipped.
- OpenAPI: rotas presentes; migration V018 aplicada e válida no banco de dev.
