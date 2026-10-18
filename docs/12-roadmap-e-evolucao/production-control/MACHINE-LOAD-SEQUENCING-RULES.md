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

## 10. Etapa 2 — resolução automática de material (integrada em `5d22c4519`)

Integrada à `main` no merge `5d22c4519` (commits `6add6f3bd` producer + `882632b9f` resolvedor), sobre o HEAD base `02021c680` (Etapa 1 + hardening). A Etapa 2 implementa a
identificação do código exato do cabo por operação, **sem** conectar o
resultado ao motor: ordenação, fila WORKING/PUBLISHED, refresh e publish
permanecem intocados.

### 10.1 Arquitetura

```text
operation-materials (api-delpi, SD4+SB1)   — owner da leitura TOTVS
        ↓ fetch_operation_materials_batch (gateway existente, S2S)
sequencing_material_resolver_service      — aplicação: dedup, fatiamento,
        ↓                                   paralelismo, fail-closed
sequencing_material_resolution            — domínio PURO: elegibilidade,
        ↓                                   zerados, fallback, ambiguidade
motor de carga máquina (Etapa 3, TARGET)  — consome o contrato interno
```

`application/services/integration_batches.py` passa a ser o owner do
fatiamento/fan-out de consultas em lote à api-delpi — extraído do
`LineFeederService` (que delega; mesmos knobs `commitmentBatchSize`,
`maxCommitmentBatches`, `maxProductionOrdersPerBatch`, `fetchMaxWorkers`).
O resolvedor **não** reutiliza métodos privados de outro serviço.

### 10.2 Fonte e contrato (evolução ADITIVA na api-delpi)

O contrato `operation-materials` (consulta unitária + batch, mesmo SQL de
`production_order_operation_materials_sql.py`) ganhou dois campos aditivos:

- `product_group` (`SB1.B1_GRUPO`) — entra no SELECT e no GROUP BY. Grupo só
  qualifica elegibilidade; o agrupamento futuro usa `product_code` (D4_COD).
- `zeroed_commitment_count` — quantos registros SD4 fonte têm
  `D4_QTDEORI = 0 AND D4_QUANT = 0` simultaneamente. O agregado
  `original_qty`/`open_qty` pode zerar por soma de positivos e negativos;
  "totalmente zerado" só é provado por `zeroed_commitment_count ==
  commitment_count`. Sem o campo (producer antigo), o consumidor trata o item
  como **não zerado** — fail-closed para ambiguidade, nunca descarte.

Nenhum campo removido/renomeado; as duas rotas compartilham a consulta;
operationIds preservados. Consumidor legado (Alimentador de Linha) ignora os
campos novos — compatibilidade PROVEN pelos testes producer + regressão.

### 10.3 Contrato interno do resolvedor

`SequencingMaterialResolverService.resolve_materials(branch, work_center,
operations, criteria)` → `{branch, work_center, material_criterion, items[],
summary}`.

Por operação (identidade completa filial + CT atual + OP + operação):

| Campo | Significado |
|---|---|
| `status` | `resolved` / `missing` / `ambiguous` / `source_unavailable` / `incomplete` |
| `product_code` / `product_group` | cabo identificado + grupo (só em `resolved`) |
| `source` | `direct` (OP+operação) / `fallback_op` (OP inteira) |
| `candidate_codes` | códigos elegíveis distintos (diagnóstico) |
| `detail` | motivo técnico (`material_identified_at_operation`, …) |

Regras: MP + `eligible_product_groups` definem elegibilidade; exatamente um
código distinto resolve; dois+ é `ambiguous`; nenhum é `missing`; falha de
integração isola o lote em `source_unavailable`; resposta malformada e OPs
acima do teto de janela (`commitmentBatchSize` × `maxCommitmentBatches`)
viram `incomplete` — nada é truncado nem vira `missing` falso.
`identity_source` única vigente: `operation_then_order`; outra fonte cai em
`missing` sem fallback implícito. Não há fallback SG1.

### 10.4 Limites da Etapa 2

- Leitura pura: sem rota nova, sem persistência, sem mutação de snapshot.
- `optimize_sequence`, `MachineLoadOptimizationCriteria`, refresh e publish
  inalterados (regressão: 449 testes machine_load/line_feeder/sequencing PASS,
  única falha = baseline pré-existente
  `test_product_detail_aggregates_work_centers_in_cutoff`).
- Nenhum perfil/vínculo é criado ou associado automaticamente.

### 10.5 Evidências e piloto CT-02B

- 30 testes novos (`tests/test_sequencing_material_resolution.py`):
  direto, fallback, mesmo-código-duplicado, ambiguidade direta/fallback,
  missing, MP/PI/PA, grupo fora/dentro da config, open_qty=0 com original>0,
  zerado canônico, netting-zero agregado, campo zerado ausente, OP de
  referência, zeros à esquerda, CT transferido, OPs repetidas, chunks >300,
  falha parcial/total, resposta malformada, teto de janela, determinismo.
- Producer: `tests/test_production_order_operation_materials.py` cobre
  `product_group` no SQL/GROUP BY e `zeroed_commitment_count`; contratos
  davi wave-001/002: 154 PASS.
- **Leitura real (dev, somente leitura):** OP `11173301001` filial `02` —
  SD4 trouxe `10070371` (orig 0,252 / saldo 0,252) e `10071279` (0/0,
  `zeroed_commitment_count = commitment_count` → ignorado). Resultado:
  `resolved` → `10070371`, `source: fallback_op`, grupo `1007`. O empenho veio
  com `D4_OPERAC` vazio — a resolução direta não encontrou vínculo e o
  fallback da OP resolveu, como previsto.
- A fila WORKING dev estava vazia na data da medição — a cobertura completa
  do CT-02B fica como evidência a repetir quando houver programação
  carregada; discrepâncias SH8×WORKING serão registradas, não classificadas
  como erro automaticamente.

### 10.6 Dependências para a Etapa 3

- Motor consome `resolve_materials` por CT, agrupa por `product_code` dentro
  de cada janela de `pa_due_date` (soberano), nunca por `product_group`.
- Conectar perfis compartilhados a mutação de fila **depende** da ratificação
  da política estrita de autorização (ver ARCHITECTURE_DECISION_REQUIRED).

### 10.7 Hardening pós-revisão independente (E2)

Três correções aplicadas sobre o merge `5d22c4519`, sem alterar a arquitetura:

1. **Dados indispensáveis ausentes** — a elegibilidade de um item passou a ter
   três estados: `eligible` provado, `ineligible` provado e `indeterminate`
   (falta dado que pode mudar a decisão). `indeterminate` cobre: `product_type`
   vazio; MP sem `product_group`; item elegível sem `product_code`; e contagens
   inválidas (`commitment_count` ≤ 0/não numérico, `zeroed_commitment_count`
   negativo, não numérico ou acima de `commitment_count`). Convivência de
   versões: sem `zeroed_commitment_count` (producer antigo), agregado
   original/open ambos zero não prova nem zerado nem ativo → indeterminado;
   agregado positivo prova não-zerado e segue elegível. Qualquer item
   indeterminado no escopo avaliado torna a operação `incomplete` — nunca
   `resolved`/`missing` com evidência insuficiente. `ambiguous` permanece
   quando há 2+ códigos provados (um indeterminado a mais não muda que não dá
   para escolher).
2. **Validação integral dos lotes** — `_validated_items` rejeita o lote
   inteiro como `incomplete` quando: resposta não é dict; envelope declara
   `success: false` (mesmo com itens bem formados); `items` não é lista;
   `summary.returned_count` diverge do número real de linhas (lista vazia
   legítima exige `returned_count: 0` quando o resumo é informado); alguma
   linha não é dict; linha sem `production_order`; linha de OP não
   solicitada; filial do envelope ou da linha diverge da pedida; envelope
   `production_orders` presente sem cobrir todas as OPs pedidas. Nenhum
   registro é descartado silenciosamente — não dá para provar a qual OP um
   registro estranho pertenceria. `items: []` válido continua significando
   OP sem empenho → `missing` legítimo.
   Números não finitos (NaN/Infinity) em contagens e quantidades são
   inválidos — nunca lançam exceção nem provam saldo/zeragem.
3. **Identidade e escopo** — `resolve_materials` valida antes de qualquer
   consulta externa: filial e CT obrigatórios; operação com `branch` explícita
   diferente do contexto → `ValueError`; operação sem `work_center` ou de outro
   CT → `ValueError`; OP/operação ausentes → `ValueError`. A filial canônica
   vem do contexto confiável (snapshot WORKING carregado pelo backend) — itens
   legítimos sem campo `branch` herdam o contexto; o resultado sempre carrega
   a filial do contexto, não a da entrada. Zeros à esquerda preservados.
   Entrada inválida não dispara nenhuma chamada à api-delpi.

Compatibilidade: contrato `operation-materials` inalterado (nenhum campo novo,
removido ou reinterpretado); Alimentador de Linha não consome os campos E2;
cockpit público usa allowlist `_public_item` — inalterado.

Testes: `test_sequencing_material_resolution.py` subiu de 31 para 69 casos —
dados insuficientes (8 cenários), integridade de lote (envelope errado, linha
malformada, OP estranha, filial divergente, envelope de erro com cara de
sucesso — inclusive `success: false` com itens válidos —, divergência de
`summary.returned_count`, NaN/Infinity em contagens e quantidades, vazio
legítimo, OP pedida ausente do eco) e escopo/identidade (filial
divergente, CT errado, OP/operação ausente, herança de filial do contexto,
não-disparo de consulta em entrada inválida). Regressão: suíte completa da
API PASS com as duas falhas baseline pré-existentes já documentadas.

## 11. Etapa 3 — perfis aplicados pelo botão Otimizar (implementada)

`POST /machine-load/optimize` passa a consultar os vínculos `(filial, CT)` da
fila WORKING e aplica o perfil ativo de cada CT, na ordem cadastrada — o CT
sem perfil segue os critérios gerais do modal, exatamente como antes. O
endpoint legado `/machine-load/optimize-delivery` nunca ativa perfis
(`use_sequencing_profiles=False`).

### 11.1 Semântica do motor

- `pa_due_date` continua soberano e primeiro — sempre.
- Critérios de agrupamento do perfil (`tool_group`, `material_code`) viram
  ranks lexicográficos por data, na ordem de cadastro; ranking por primeira
  ocorrência livre na fila, desempate estável.
- `material_code` agrupa pelo código exato resolvido pela E2 — nunca por
  grupo SB1. Operações `missing`/`ambiguous` (política `flag`) não formam
  grupo: ficam depois dos grupos reais da data, preservando a ordem relativa.
- Operações sem data seguem ao final sem reagrupamento.

### 11.2 Fail-closed

- Vínculo para perfil inexistente, `draft`/`archived` ou critério inválido →
  erro 422 controlado, sem fallback silencioso e sem mutação.
- Perfil compartilhado entre filiais (vínculo em outra filial ou
  `origin_branch` diferente) → bloqueado até a ratificação da política
  cross-branch (ARCHITECTURE_DECISION_REQUIRED segue pendente).
- Resolução `incomplete`/`source_unavailable` → a otimização inteira aborta
  sem mutação; nunca otimização parcial sobre dado insuficiente.
- Toda leitura externa (vínculos, perfis, resolver E2) ocorre fora do lock;
  dentro dele, drift de fila, de vínculo ou de revisão/status do perfil
  vira `MachineLoadSequenceConflict` (409) — nada é gravado com base velha.
- Resposta `optimization.profiles` (aditiva) informa, por CT, `profile_id`,
  `name`, `criteria` aplicados e `flagged_count` (missing/ambiguous).

### 11.3 Escopo preservado

Sem novas rotas, migrations ou controles no modal; proteção de runs abertos,
retiradas, DRAFT/LIVE, no-op sem write e notificação pós-commit inalterados.

### 11.1 Hotfix pós-implantação — segurança e precisão (main `028f81b1`+)

Correções pontuais no motor já em produção, sem nova confirmação, simulação
ou segundo motor. O clique em **Otimizar** autoriza recalcular a ordem —
inclusive substituindo ajustes manuais anteriores — mas nunca muda CT de
operação, restaura retiradas ou move operações com execução aberta.

1. **Concorrência por versão da fila** — em vez de comparar o conjunto de
   chaves (que não detectava mudança de ordem), o serviço compara o
   `row_version` (xmin) lido no início com a versão sob lock. Qualquer
   escrita concorrente — reordenação, refresh, transferência ou retirada —
   resulta em 409 sem gravação, para CTs com e sem perfil. Ajustes manuais
   *anteriores* à otimização são normalmente substituídos.
2. **Runs relidos dentro da transação** — a lista de operações em execução
   é lida na fonte canônica local já dentro da região transacional do
   mutate, não mais antes da resolução de materiais. Um run iniciado
   durante a preparação também trava o slot. Falha de leitura impede a
   mutação; flags HZA seguem sem papel. Janela residual entre leitura dos
   runs e commit permanece limitada ao UPDATE da linha (lock de linha).
3. **Critérios combinados aninhados** — o ranking de cada critério
   secundário é calculado *dentro* do grupo formado pelos critérios
   anteriores (e pela data), por primeira ocorrência naquele grupo —
   corrigindo a classificação independente por data. Ex.: perfil
   `pa_due_date → tool_group → material_code` agrupa por ferramenta e,
   dentro de cada ferramenta, pelos cabos na ordem em que aparecem ali.
4. **Validação integral da resolução E2** — a resposta do resolvedor deve
   cobrir exatamente uma resolução por operação solicitada, com filial, CT,
   OP e operação coerentes; itens extras, ausentes, duplicados ou
   `resolved` sem código abortam a otimização inteira antes de qualquer
   mutação.

DRAFT/LIVE, atomicidade, no-op, proteção de retiradas/transferências,
isolamento de filiais e o endpoint legado `optimize-delivery` permanecem
inalterados. A política cross-branch de perfis compartilhados segue
pendente (`ARCHITECTURE_DECISION_REQUIRED`) — compartilhamento continua
bloqueado com erro controlado.

Ajustes da revisão do hotfix: o drift-check de vínculos cobre apenas os CTs com operações na fila (vínculo em CT ocioso não bloqueia; vínculo criado/alterado/removido em CT participante continua = 409); `row_version` ausente falha de forma controlada em vez de dispensar a proteção; e operações `missing`/`ambiguous` preservam a ordem relativa mesmo quando critérios posteriores ao material existem no perfil.

## 12. Etapa 4 — administração visual (MFE `production-control`)

A configuração de perfis e vínculos passa a ter interface própria no Portal
PCP, sem alterar o motor da Etapa 3 nem os contratos do backend.

- **Área**: *Regras de Sequenciamento*, subplugin do catálogo do
  `production-control`, com acesso pela rail do Portal e por atalho discreto
  no cabeçalho do Carga-Máquina.
- **Perfis**: lista com busca e filtro por situação; criação em rascunho,
  edição, ativação, retorno a rascunho e arquivamento via
  `PUT /machine-load/sequencing-profiles/{id}` com `expected_revision`
  (409 → aviso de atualização concorrente com opção de recarregar).
- **Critérios**: `pa_due_date` fixo no topo (não removível nem movível);
  `tool_group` e `material_code` opcionais, reordenáveis e sem duplicidade.
  Para `material_code` a tela orienta os grupos de produto SB1 elegíveis
  (preservando zeros à esquerda) e fixa os parâmetros `material_type=MP`,
  `identity_source=operation_then_order`, `ignore_zeroed_allocations`,
  `on_missing=flag`, `on_ambiguous=flag`; o agrupamento real continua pelo
  código exato do cabo.
- **Vínculos**: `(filial, CT)` tem no máximo um perfil; vincular/substituir
  exige perfil ativo; vínculo com perfil inativo é sinalizado para correção.
  Fonte de CTs: fila do Carga-Máquina + vínculos já cadastrados (sem refresh
  TOTVS para abrir a tela).
- **Permissões**: leitura `production-control.machine-load.view`;
  administração exige `production-control.sequencing-profiles.manage`
  (autoridade final no backend; o MFE apenas oculta ações).
- **Efeito**: salvar/ativar/vincular não otimiza a fila — as regras valem na
  próxima execução de **Otimizar planejamento**.
- Perfis de outra filial não são apresentados como administráveis; a
  política cross-branch segue `ARCHITECTURE_DECISION_REQUIRED`.
