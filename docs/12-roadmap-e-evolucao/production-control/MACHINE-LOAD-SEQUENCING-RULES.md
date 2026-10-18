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

## 4. Persistência (V018 + V019)

```
sequencing_profiles            (id, name, description, status, revision,
                                criteria JSONB, origin_branch (V019),
                                created/updated_*)
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

## 6a. Hardening pós-integração (HEAD `fa234d546` + correções locais)

Correções aplicadas após o merge, motivadas pelo CI remoto e pela revisão:

1. **operationIds** — o gate remoto `architecture-gate` reprovou a Etapa 1
   com 6 `FASTAPI_OPERATION_ID_REQUIRED` (rota nova exige `operation_id`
   literal). Adicionados ids explícitos e estáveis:
   `list_machine_load_sequencing_profiles`,
   `get_machine_load_sequencing_profile`,
   `create_machine_load_sequencing_profile`,
   `update_machine_load_sequencing_profile`,
   `list_machine_load_sequencing_bindings`,
   `set_machine_load_sequencing_binding`.
2. **Autorização cross-branch** — a Etapa 1 autorizava `update_profile`
   apenas pela filial da requisição: um admin da filial 01 poderia editar um
   perfil vinculado só à filial 02 (violação provada por teste). V019
   adiciona `origin_branch` (nullable; CHECK `('01','02')`). A política
   vigente é a **estrita** (ver ADR abaixo): edição exige administração em
   **TODAS** as filiais afetadas — `origin_branch` ∪ filiais vinculadas —
   verificada DENTRO da transação do update, sob a mesma trava (FOR UPDATE)
   que `set_binding` segura antes de mutar vínculos. Isso fecha o TOCTOU
   entre «ler filiais afetadas» e «gravar». O parâmetro `branch` do request
   não é autorização — o escopo real é computado das permissões do usuário.
   Linhas legadas `origin_branch NULL` sem vínculo: conjunto afetado vazio →
   edição negada (não se inventa proprietário).
   **Expansão de vínculo:** vincular o perfil a uma filial nova exige
   administração em TODAS as filiais afetadas (origem ∪ vínculos ∪ nova),
   sob a mesma trava da linha do perfil — um admin só-01 não pode acoplar
   um CT seu a um perfil da 02 e travar a edição do dono (cenário provado
   antes/depois). Vínculo a novo CT numa filial já associada não exige
   escopo extra. Perfil legado `origin_branch NULL` não pode ser
   reivindicado por primeiro vínculo.
3. **Corrida de vínculo** — `SELECT FOR UPDATE` não trava linha inexistente;
   dois binds simultâneos no mesmo CT produziam `UniqueViolation` → 500.
   `set_binding` agora reexecuta uma vez: a segunda tentativa serializa pela
   trava e resolve como `rebound`; falha persistente → 409 controlado.

### ARCHITECTURE_DECISION_REQUIRED (decisão recomendada — ratificação pendente)

**Problema confirmado:** com a política «qualquer filial afetada», um admin
da filial 01 (que legitimamente vinculou o perfil compartilhado a um CT seu)
conseguia editar o perfil usado pelo CT-02B da filial 02 — alteração
indireta de configuração de outra filial.

**Decisão recomendada (implementada como padrão seguro):** edição exige
`sequencing-profiles.manage` + escopo administrativo em **todas** as
filiais afetadas (origem ∪ vínculos). Perfis exclusivos de uma filial
seguem editáveis por quem a administra; perfis compartilhados ficam
editáveis apenas para admin dual (ou superadmin). Expandir o perfil a uma
filial nova exige o mesmo escopo total — caso contrário o bind criaria a
violação que a edição agora bloqueia. Desvincular/substituir permanece
ação da própria filial no SEU CT.

**Alternativas rejeitadas:**
- qualquer-filial-afetada edita → a violação original;
- owner exclusivo (`origin_branch`) → bloquearia edição legítima de quem
  administra todas as filiais envolvidas.

**Condição de aceite:** pendente de ratificação formal pelo owner do PCP
antes da Etapa 2. Enquanto isso o padrão implementado é o mais restritivo
das alternativas plausíveis — nenhum acesso é concedido além do provado.

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
