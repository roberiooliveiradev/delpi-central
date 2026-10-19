# Carga-Máquina — Seleção múltipla de operações (Etapa 1: inventário e contratos)

> Estado: **inventário concluído — contratos PROPOSTOS, não aprovados**.
> Escopo deste documento: E1 apenas. Nenhuma implementação funcional foi feita.
> Base factual: `main` @ `34cc744f71b4bb9063c88ee7e302acf52cc5ea23`.

## 1. Resumo executivo

O analista de PCP quer selecionar várias operações na tela Carga-Máquina e executar
três ações coletivas: **agrupar** (reorganizar a fila), **transferir** para outro CT
e **retirar** da programação. Este documento registra o estado atual comprovado no
código, a matriz de reutilização, os contratos propostos e as decisões pendentes
antes das Etapas 2–4.

Conclusões principais:

1. **Agrupamento não exige endpoint novo.** `PATCH /machine-load/sequence` aceita a
   permutação exata do CT; o agrupamento é uma permutação computada no cliente e
   validada no servidor (ver §6.B).
2. **Transferência coletiva exige endpoint novo.** O contrato individual
   (`POST /machine-load/transfer`) identifica a operação só por `OP+operação` —
   sem CT de origem — e chamadas sequenciais não são transacionais (ver §6.C).
3. **Retirada coletiva diverge da semântica vigente.** Hoje a unidade de retirada
   é o **conjunto (C2_NUM, cross-CT)**. Retirar operações arbitrárias exige uma
   nova lista de escopo no snapshot (`withdrawn_operations`), sem redefinir
   silenciosamente `withdrawn_conjuntos` (ver §6.D).
4. **Proteção de execução não é uniforme.** `prioritize`/`optimize` consultam os
   runs abertos do cockpit (`_protected_operation_keys`); `transfer`,
   `withdraw`/`restore` e o `PATCH /sequence` **não** — fato atual, decisão
   pendente para o lote (ver §7).

## 2. Estado atual comprovado (E1.S1)

### 2.1 Carregamento da fila

`GET /machine-load?branch&workCenter&includeAllCenters` →
`MachineLoadService._present` (`machine_load_service.py:2255`):
a fila inteira da filial vai em `payload.operations` (`ALL_OPERATIONS_KEY`);
`selected` é recorte de apresentação por CT. Operações **retiradas continuam no
snapshot na posição original** — a marca `is_withdrawn` é derivada na leitura de
`withdrawn_conjuntos`, nunca gravada na operação
(`machine_load_withdrawal.py:40-54`). O MFE recorta o CT ativo em
`selectMachineLoadCenter` (`utils/machineLoadSelection.ts:28`) — apesar do nome,
é seleção de **centro**, não de linhas.

Polling do MFE (`hooks/useMachineLoad.ts`): `GET /machine-load` sob demanda +
`GET /machine-load/cockpit-status` e `GET /machine-load/balances` a cada
`EXECUTION_STATUS_INTERVAL_MS` (30s), merge local sem reordenar a fila
(`utils/machineLoadCockpitStatus.ts`).

### 2.2 Reordenação drag-and-drop e persistência

```text
arraste na linha (HTML5 DnD)
→ useMachineLoadRowReorder<T> (index-based; moveArrayItem)
→ MachineLoadPage.onReorder
   → hideFinished: mergeActiveOrderIntoMachineLoadQueue (finalizadas pinadas)
→ persistOrder → keysFromOperations(rows) = [{production_order, operation_code}]
→ PATCH /machine-load/sequence?branch&workCenter  body: {ordered_keys}
→ MachineLoadService.reorder_sequence → _persist_queue_change
   → SELECT ... FOR UPDATE na linha WORKING → _apply_center_order
   → update_payload (+ publications se LIVE) → notify pós-commit
→ resposta = payload completo → applyPayload
```

`_apply_center_order` (`machine_load_service.py:1931-1982`):
- exige **permutação exata** das operações não-retiradas do CT — qualquer chave
  a mais/a menos/duplicada → `ValueError` → 400;
- rejeita CT com `OP+operação` duplicada dentro do mesmo centro;
- **não** consulta runs abertos — drag manual move operação em produção
  (comportamento vigente, não bug novo).

### 2.3 Undo/redo

`useMachineLoadSequenceHistory(scopeKey)` — pilhas de `SequenceKey[]`
(`{production_order, operation_code}`), escopo `branch|start|end|workCenter`,
Ctrl+Z / Ctrl+Shift+Z via `bindKeyboard`. `applyRemoteKeys` reenvia a permutação
pela mesma `PATCH /sequence`. Ações multi-CT (priorizar/retirar/transferir/
otimizar) chamam `history.reset()` — o histórico só cobre o CT ativo.

### 2.4 Menu contextual e ações atuais

`MachineLoadRowContextMenu` (ContextMenu de `@delpi/plugin-ui`), botão direito
por linha, cinco ações: rastrear conjunto, priorizar conjunto, retirar conjunto,
transferir conjunto do CT atual, transferir a operação. Modais:
`MachineLoadTransferModal` (`mode: "operation" | "conjunto"`, lista de CTs),
`MachineLoadWithdrawnModal` (lista de conjuntos retirados → restore).

### 2.5 Publicação e consumidores

`POST /machine-load/publish` → `publish()` (`:722`): `SELECT FOR UPDATE` no
WORKING + upsert da publicação na mesma transação; republicar a mesma
`generation_id` é idempotente (`changed=false`, sem broadcast). Estado semântico
`unpublished | draft | live` derivado de `generation_id` — nunca persistido.

Mutação em LIVE atualiza `machine_load_publications` na mesma transação e chama
`_notify_change(reason, work_center)` **após o commit** →
`notify_machine_load_changed` → hub realtime → `WS /public/machine-load/{token}/ws`.
Em DRAFT, mutações ficam no WORKING até o próximo publish.

Consumidores verificados:

| Consumidor | O que lê | Contrato |
|---|---|---|
| Cockpit do operador (`plugins/public-hub`) | fila **publicada** | `GET /public/machine-load/{token}` + WS |
| Portal PCP (este MFE) | snapshot WORKING + estado de publicação | `GET /machine-load` |
| Line feeder | fila congelada + «está na programação» | snapshot via `MachineLoadSnapshotRepositoryPort` |
| Locate/rastreio | snapshot + execução | `GET /machine-load/locate` |

Refresh (`_pull_and_store`): reaplica `withdrawn_conjuntos` e
`transferred_operations` sobre a fila nova do TOTVS — retirada e transferência
**sobrevivem** ao «Atualizar»; a ordem manual **não** (fila volta em
`schedule_no_status_asc`). Exceção de slot: operações com run aberto no cockpit conservam o índice visível que ocupavam no seu centro de trabalho (`carry_pinned_positions` em `machine_load_queue_slots.py`, mesma mecânica de priorizar/otimizar/reordenar) — sem o reparo a protegida cairia na posição cronológica do ERP e, travada para qualquer mutação, ficaria congelada no lugar errado.

## 3. Identidade das operações (E1.S2)

### 3.1 Matriz de identidade por superfície

| Superfície | Chave usada hoje | Onde | Adequada? |
|---|---|---|---|
| Fila/snapshot (`_operation_key`, `ordered_keys`) | `OP+op` | `machine_load_service.py:206` | Sim **porque** o escopo é CT único; unicidade intra-CT só garantida na reordenação |
| Execução/cockpit (`ProtectedOperationKey`) | `CT+OP+op` | `machine_load_queue_slots.py:37` | Sim — Etapa 03 |
| MFE execução (`machineLoadExecutionKey`) | `CT+OP+op` | `utils/machineLoadCockpitStatus.ts` | Sim |
| Localização/highlight (`machineLoadLocateRowKey`) | `CT::OP::op` | `utils/machineLoadLocate.ts:14` | Sim |
| `rowKey` do DataTable | `OP-op` | `MachineLoadPage.tsx:1173` | Aceitável (visão mono-CT); colide se mesmo `OP+op` aparecer 2× no CT — a API já rejeita reorder nesse caso |
| Undo/redo (`SequenceKey`) | `OP+op` | `useMachineLoadSequenceHistory.ts:3` | Idem |
| Transferência individual (`find_operation`/`move_operation`) | `OP+op` — **sem CT de origem** | `machine_load_transfer.py:67-77,137-177` | ⚠ **GAP**: primeiro match vence; se `OP+op` existir em 2 CTs, move a linha errada |
| Log de replay `transferred_operations` | `OP+op` | `machine_load_transfer.py:241-278` | Mesmo gap no `apply_transfers` |
| Retirada (`withdrawn_conjuntos`) | `C2_NUM` (6 chars) | `machine_load_withdrawal.py` | Sim para a semântica **conjunto cross-CT** |
| Conjunto (`order_belongs_to_conjunto`) | `C2_NUM` | `production_order_key.py:42` | Sim — legado; pacote mãe/filhas usa `C2_NUM+C2_ITEM` (8) |
| Saldos ERP (SH6/SC2) | `OP+op` | `utils/machineLoadCockpitStatus.ts` | Sim — identidade ERP distinta da execução, por decisão |

**Regra derivada:** a identidade canônica de fila/execução é
`branch + work_center + production_order + operation_code`. Qualquer contrato de
lote novo deve carregar essa identidade completa por item — `OP+op` é insuficiente
fora do contexto mono-CT e já produz ambiguidade comprovada na transferência
individual.

### 3.2 Elegibilidade — o que existe hoje

| Situação | Reordenação | Transferir | Retirar conjunto |
|---|---|---|---|
| run aberto (producing/stopped/paused/unknown) | **não protege** | **não protege** | **não protege** |
| operação retirada | excluída da permutação, fica na posição | bloqueia (`withdrawn` → 400) | já retirado → 400 |
| conjunto retirado | — | bloqueia transfer-set | — |
| CT destino inexistente no snapshot | — | bloqueia (`unknownTarget`) | — |
| `OP+op` duplicada no CT | bloqueia (400) | pega o primeiro (silencioso) | — |

**Não inventado — pendências de negócio para as ações em lote** (decisão, não
suposição):

- lote com operação em execução: bloquear, avisar ou permitir?
- lote com operações finalizadas/sem saldo: elegíveis a agrupar/transferir/retirar?
- seleção sob filtro `hideFinished`/`onlyFeedback`: agir sobre itens selecionados
  não visíveis? (ver §6.A)
- operações em CTs diferentes na mesma seleção: hoje a seleção é por aba mono-CT —
  confirmar se a seleção é sempre de um único CT (recomendado) ou cross-CT.

## 4. Inventário de reutilização (E1.S3)

| Capacidade | EXISTING_EQUIVALENT | REUSE_DECISION | Owner | Evidência |
|---|---|---|---|---|
| Seleção de linhas (Ctrl/Shift) | **YES** — `DataTableSelection {kind:"row"}` + `resolveRowSelection` (toggle+range) | **EXTEND** | `plugins/plugin-ui` `dataTableSelection.ts` | Índice-based, voltado a cópia TSV; seleção produtiva deve ser por **chave de linha**, não índice |
| Checkbox por linha | NO | NEW (coluna no MFE) ou extensão do kit | a decidir com owner do kit | sem prop de checkbox hoje |
| Drag-and-drop por linha | YES | REUSE | `useMachineLoadRowReorder` | index-based; lote arrastável exigiria evolução — fora do MVP proposto |
| Persistência de sequência | YES | **REUSE** (`PATCH /sequence`) | `reorder_sequence` + `_apply_center_order` | contrato de permutação exata cobre agrupamento |
| Undo/redo | YES | REUSE | `useMachineLoadSequenceHistory` | agrupamento entra como mais uma permutação na pilha |
| Transferência individual | YES | EXTEND → endpoint de lote | `transfer_operation` + `move_operation` | corrigir identidade com `source_work_center` |
| Transferência de conjunto | YES | REUSE da mecânica (`_insert_at_end_of_center`, `register_transfer`, `apply_transfers`) | `machine_load_transfer.py` | escopo conjunto ≠ seleção arbitrária |
| Retirada | YES (por conjunto) | **NEW** para escopo por operação | `machine_load_withdrawal.py` | unidade hoje é C2_NUM cross-CT |
| Restauração | YES (por conjunto) | EXTEND para itens da lista nova | idem | restore devolve à posição original no snapshot |
| Lock/transação/auditoria | YES | REUSE | `_persist_queue_change` (`SELECT FOR UPDATE`, `*_updated_at/by`) | serialização por linha WORKING já resolve A×B |
| Notificação realtime | YES | REUSE | `_notify_change` → `notify_machine_load_changed` → WS | novos `reason` entram no mesmo canal |
| ContextMenu | YES | REUSE | `@delpi/plugin-ui` | menu coletivo = mesma família com ações de lote |
| Modal de CT destino | YES | EXTEND (`mode` novo ou prop) | `MachineLoadTransferModal` | hoje `operation|conjunto` |
| Modal «fora da programação» | YES | EXTEND para listar operações | `MachineLoadWithdrawnModal` + `withdrawn.items` | entries hoje agregam por conjunto |

**Sem duplicação:** nenhum hook/serviço/API paralela deve nascer enquanto as
peças acima forem estendidas no owner canônico.

## 5. Regras de negócio comprovadas vs pendentes

Comprovadas:

- transferidos entram **no fim da fila** do CT destino (`_insert_at_end_of_center`);
- voltar ao CT de origem desfaz o registro de replay (`register_transfer:266`);
- retirado some da fila e do cockpit, mas permanece no snapshot para restore
  posicional;
- mutação em LIVE propaga para a publicação na mesma transação;
- refresh reaplica retiradas/transferências e descarta a ordem manual.

Pendentes (**ARCHITECTURE_DECISION_REQUIRED**):

- **D1 — proteção de execução no lote.** `transfer`, `withdraw`, `PATCH /sequence`
  não consultam `_protected_operation_keys`. Agrupar via PATCH herda isso. Para
  lote, recomendado: rejeitar itens com run aberto (403/409 por item ou 422 no
  lote) — mas decisão de negócio, não inferência.
- **D2 — escopo da retirada por operação:** item `(CT+OP+op)` — recomendado — vs
  `OP+op` cross-CT. Alinha-se à identidade canônica §3.1.
- **D3 — `OP+op` duplicada dentro do mesmo CT** torna `ordered_keys` ambíguo; a
  API já rejeita, mas a seleção precisa de chave visual estável — incluir posição
  na key de UI (índice) não é estável sob refresh; preferir `CT+OP+op` e tratar
  duplicata intra-CT como erro de dados.
- **D4 — ações sobre itens selecionados fora do filtro visível** (hideFinished /
  onlyFeedback / localização). Recomendado: ação aplica-se ao conjunto
  selecionado inteiro com confirmação que mostra o total, ou a seleção é podada
  aos visíveis — decisão de UX/negócio.

## 6. Contratos — atuais e propostos (E1.S4)

Convenções vigentes: filial/params na **query** (`branch`, `workCenter`, …),
corpo JSON só quando há lista; envelope `ok(data, message)`; erros de negócio →
400 (`ValueError`), permissão → 403, ausência → `SnapshotNotFound`.

### 6.A Seleção múltipla (comportamento, sem contrato de API)

Client-side puro; proposta:

- Ctrl+click alterna item; Shift+click seleciona intervalo desde a âncora —
  reutilizando a semântica de `resolveRowSelection`, mas estado indexado por
  chave `CT+OP+op` (não índice).
- Checkbox opcional na primeira coluna só se o kit ganhar a capacidade — senão
  destaque + contador em barra contextual.
- Botão direito em linha **selecionada** → menu coletivo (agrupar/transferir/
  retirar); em linha **não selecionada** → seleção vira só aquela linha e abre o
  menu individual vigente (padrão SO).
- Limpar seleção em: troca de CT, troca de filial, refresh manual, ação
  concluída. F5 sempre limpa (estado local).
- Seleção sob filtro: itens que saírem da visão permanecem selecionados mas a
  barra indica «N selecionadas (M visíveis)» — pendente D4.
- Reordenação durante seleção: permitida; a seleção segue as chaves.
- Teclado: setas + Ctrl/Shift conforme kit; Esc limpa.

### 6.B Agrupamento — REUSE `PATCH /machine-load/sequence`

Contrato atual (provado): `PATCH /machine-load/sequence?branch&workCenter`,
body `{"ordered_keys":[{production_order, operation_code}]}` = permutação exata
das ops não-retiradas do CT; `ordered_keys` é validado como conjunto exato
(`:1965-1971`), CT sem ops → 400, duplicata → 400.

**Algoritmo do agrupamento (especificação):**

```text
dado: ordem atual O (visível=ativos no CT), seleção S ⊆ O
âncora = primeiro item de O que ∈ S
resultado = prefixo(O até âncora, excluindo S\{âncora})
          + S na ordem relativa de O
          + restante de O excluindo S
```

Exemplo: `A B C D E F G`, `S={B,E,G}` → `A B E G C D F`.
Caso irmão: seleção já contígua → permutação idêntica → API no-op seguro
(resposta normal; `sequence_updated_at` atualiza — ou tratar no cliente e não
chamar). Caso negativo: S ⊄ O (fila mudou desde a seleção) → podar S às chaves
vigentes e, se sobrar <2, avisar e não chamar — ou deixar a API rejeitar.

Aplicável com `hideFinished`: montar a permutação sobre as **ativas** e expandir
via `mergeActiveOrderIntoMachineLoadQueue` (finalizadas pinadas) — mesmo caminho
do drag. Undo: `history.pushUndo(previousKeys)` — entra na pilha existente.
F5: estado persiste porque a ordem já é do snapshot.
Concorrência A×B: se B mudou a fila, a permutação de A falha na validação
exata → 400 → recarregar. **Coberto hoje.**

Delta contratual: **nenhum**. Opcional futuro: incluir `work_center` em cada
`ordered_keys` item — hoje o CT vem da query e basta.

### 6.C Transferência coletiva — NEW endpoint

Contratos atuais: `POST /machine-load/transfer` (OP+op → fim do CT destino; sem
CT de origem no request) e `POST /machine-load/transfer-set` (conjunto no CT de
origem → destino; `move_conjunto_at_work_center`).

Proposta — **`POST /machine-load/transfer-operations`**

```text
Query:  branch (obrig.), workCenter? (CT ativo p/ resposta), includeAllCenters?
Body:   {
          "source_work_center": "CT-01",           # obrigatório
          "target_work_center": "CT-02",           # obrigatório, ≠ origem
          "operations": [                           # 1..N, ordem preservada
            {"production_order": "...", "operation_code": "..."}
          ]
        }
200:    payload completo (mesmo shape de transfer) +
        transfer: { moved_count, source_work_center, target_work_center,
                    operations: [...], message }
400:    lista vazia/dup, item fora do CT de origem, item retirado, destino
        desconhecido, source==target
403:    sem permissão / filial fora do escopo
409/422: item com run aberto — pendente D1
```

Semântica: os itens entram **no fim da fila do destino** na ordem relativa da
origem (mesma mecânica de `move_conjunto_at_work_center` + `register_transfer`
por item → replay sobrevive ao refresh). Uma transação (`_persist_queue_change`),
tudo-ou-nada; `reason="transfer"`, `work_center=target`.

Identidade por item: `(CT origem implícito + OP + op)` — o `source_work_center`
do body desambigua o gap de `find_operation` e passa a ser a referência durante a
mutação; após mover, a chave de execução passa a ser `(target+OP+op)`.

**Não** fazer N chamadas sequenciais ao `/transfer` no frontend: sem atomicidade,
estados parciais e N broadcasts.

Compatibilidade: rota nova, nada quebra; `/transfer` e `/transfer-set` intactos.

### 6.D Retirada coletiva — NEW endpoint + nova lista no payload

Atual: `POST /machine-load/withdraw` / `/restore` por `orderNumber` (C2_NUM),
`withdrawn_conjuntos` no `payload_json`, restauração posicional.

Divergência explícita: retirar seleção arbitrária **não** é retirar conjunto —
o conjunto pode ter operações não selecionadas, e a seleção pode juntar OPs de
conjuntos diferentes.

Proposta — **`POST /machine-load/withdraw-operations`** e
**`POST /machine-load/restore-operations`**

```text
Query:  branch, workCenter? (CT ativo p/ resposta)
Body:   {
          "operations": [
            {"work_center": "CT-01", "production_order": "...", "operation_code": "..."}
          ]
        }
200:    payload completo + withdrawal: { action, operations: [...], message }
400:    item inexistente no snapshot / já retirado / lista vazia
403:    sem permissão / filial fora do escopo
409/422: item com run aberto — pendente D1
```

Persistência proposta: nova chave `withdrawn_operations: [{work_center,
production_order, operation_code, withdrawn_at, withdrawn_by}]` no
`payload_json` — **sem alterar** `withdrawn_conjuntos`. `is_withdrawn` passa a
checar as duas listas; `visible_operations` idem. Restore remove só as chaves
listadas (não reabre o conjunto inteiro). Refresh reaplica a lista como já faz
com `withdrawn_conjuntos`.

Payload `withdrawn`: evoluir para expor os itens por operação (o modal atual
agrupa por conjunto) — mudança aditiva de shape, consumidores: só o PCP.

**Não** redefinir `withdraw` por conjunto: contrato e semântica ficam intactos.

### 6.E Localização (rastreio) e demais rotas

`GET /machine-load/locate` já devolve `work_center + production_order +
operation_code` por parada com `execution_*` — nenhuma evolução necessária;
seleção por chave canônica alinha-se ao highlight existente.

## 7. Concorrência, segurança e impacto (E1.S5)

**Concorrência — o que já existe:** todas as mutações passam por
`_persist_queue_change`: `SELECT ... FOR UPDATE` na linha WORKING → serialização
real entre analistas (A e B não se sobrescrevem silenciosamente; o segundo lock
lê o estado do primeiro). O cenário crítico do brief — A calcula agrupamento, B
mexe antes — é coberto para o agrupamento pela validação de permutação exata
(falha com 400) e, para lote, pela validação de existência/escopo dentro do lock.
**Não existe** versionamento otimista exposto (ETag/`expected_generation`) —
não é bloqueante para o MVP, pois a validação semântica já rejeita estado
stale; registrar como melhoria futura se a UX pedir «diff educado» em vez de erro.

**Autorização:** hoje `_assert_can_view` = `assert_can_view_branch` +
`PC_MACHINE_LOAD_VIEW` — leitura e escrita compartilham a mesma permissão.
Ações de lote herdam o mesmo gate; se a governança quiser permissão de escrita
separada, é decisão de segurança (pendente, não bloqueante).

**Impacto em consumidores:**

| Superfície | Efeito da ação coletiva |
|---|---|
| Cockpit (publicado) | idem ações unitárias: em LIVE propaga + WS; em DRAFT espera publish |
| Contagem MES / runs | **não é alterada** por nenhuma ação — ações mexem na fila, não no run; run do CT de origem continua aberto até o operador mexer (daí D1) |
| Line feeder | lê «está na programação» — `is_withdrawn` ampliado cobre automaticamente |
| Saldos SH6/SC2 | inalterados (identidade ERP separada) |
| Audit | `sequence_updated_*`, `transferred_at/by`, `withdrawn_at/by` por item |

**Riscos:**

- R1 — lote com run aberto move/esconde operação em produção (D1);
- R2 — seleção por índice perde referência após refresh/reordenação → chave
  canônica `CT+OP+op` obrigatória;
- R3 — retirada por operação cria estado «conjunto parcialmente retirado» —
  modal e listas devem mostrar isso sem ambiguidade;
- R4 — `ordered_keys` exige lista completa do CT: fila grande → payload ok
  (strings curtas), mas o erro de validação precisa de UX clara;
- R5 — replay de transferência no refresh é por `OP+op` (gap §3.1); lote com a
  mesma `OP+op` em 2 CTs amplificaria o efeito — mitigar fixando
  `source_work_center` no contrato novo e, idealmente, no log.

## 8. Matriz requisito → decisão → etapa → teste → aceite

| Req | Decisão | Etapa | Teste futuro | AC |
|---|---|---|---|---|
| RQ-1 selecionar N ops | EXTEND DataTableSelection→chave canônica; estado no MFE | E2 | vitest seleção ctrl/shift/filtro | AC-01,03 |
| RQ-2 agrupar | REUSE PATCH /sequence; algoritmo §6.B | E3 | vitest merge + pytest permutação exata | AC-04 |
| RQ-3 transferir N ops | NEW `/transfer-operations` + `source_work_center` | E4 | pytest lote atômico/parcial 400; fim de fila; replay refresh | AC-05 |
| RQ-4 retirar N ops | NEW `/withdraw-operations` + `withdrawn_operations` | E4 | pytest retirar/restaurar parcial; cockpit some; line feeder oculta | AC-05 |
| RQ-5 proteger runs | PENDENTE D1 | E3/E4 gate | pytest item com run → 409/422 | AC-02,06 |
| RQ-6 concorrência A×B | REUSE FOR UPDATE + validação exata | — | pytest duas mutações concorrentes | AC-06 |
| RQ-7 identidade canônica | `branch+CT+OP+op` em todo contrato novo | transversal | contrato/casos duplicados | AC-02 |

## 9. Critérios de aceite da Etapa 1

- **AC-01 PASS** — fluxos mapeados com referências (§2, §3).
- **AC-02 PASS** — matriz de identidade + colisões documentadas (§3); fix de
  `source_work_center` proposto, não implementado.
- **AC-03 PASS** — matriz de reutilização (§4).
- **AC-04 PASS** — regra de agrupamento com positivo/irmão/negativo (§6.B).
- **AC-05 PARTIAL** — contratos de lote propostos (§6.C/D) com divergência de
  retirada explicitada; **pendem aprovação** — não são aprovados por estarem
  escritos.
- **AC-06 PASS** — persistência/concorrência/autorização/cockpit/publicação
  documentados (§7).
- **AC-07 PASS** — rastreabilidade §8.
- **AC-08 PASS** — gates de prontidão §10.
- **AC-09 PASS** — zero implementação funcional nesta etapa.

## 10. Prontidão das próximas etapas

### Etapa 2 — seleção múltipla na interface: **READY (condicional)**

Resolvido: padrão Ctrl/Shift existe no kit (`resolveRowSelection`), menu
contextual e modal de destino existem, chave canônica definida.
Pendente: decisão D4 (seleção sob filtro) e se checkbox entra no kit.
Gate: aprovar comportamento §6.A; implementar sem chamar nenhuma rota nova.

### Etapa 3 — agrupamento e persistência: **READY (condicional)**

Resolvido: contrato `PATCH /sequence` cobre o caso; algoritmo e casos
especificados; undo e concorrência mapeados.
Pendente: **D1** — decidir se o agrupamento (via PATCH) pode mover itens com
run aberto, alinhando ou não à proteção de prioritize/optimize.
Gate: aprovar D1 (mesmo que a resposta seja «não protege», deve ser decisão
explícita).

### Etapa 4 — transferência e retirada em lote: **IMPLEMENTADA** (ver §14)

Contratos aprovados pelo owner na revisão pós-E3 (D1 rejeita lote; D2/D6
aditivos; D7 mantém `.view`; `expected_keys` da origem como precondição).
Backend + rotas + frontend entregues; ver §14 para semântica e evidências.

## 11. Decisões abertas (consolidado)

| ID | Questão | Recomendação |
|---|---|---|
| D1 | Lote pode afetar operação com run aberto? | Rejeitar por item com 409/422 (alinhado à Etapa 02) |
| D2 | Escopo da retirada por operação | `CT+OP+op` (identidade canônica) |
| D3 | `OP+op` duplicada dentro do CT | Tratar como erro de dados; seleção usa `CT+OP+op` |
| D4 | Ação sobre selecionados não visíveis (filtro) | Mostrar «N selecionadas (M visíveis)» + agir sobre N |
| D5 | Evoluir `ordered_keys` com `work_center` por item | Desnecessário agora (CT vem da query) |
| D6 | `transferred_operations`/find_operation sem CT | Incluir `source_work_center` no contrato novo; avaliar hardening do log |
| D7 | Permissão de escrita separada da de leitura | Manter `PC_MACHINE_LOAD_VIEW` salvo decisão de segurança |

## 13. Resultado da Etapa 3 — agrupamento (implementado + hardening)

### Algoritmo e persistência

- **Algoritmo:** «utils/machineLoadGrouping.ts»
  («groupSelectedMachineLoadOperations») — âncora = primeira selecionada na
  ordem da fila; selecionadas e não selecionadas preservam ordem relativa;
  permutação exata; já contíguas → «noop» sem write.
- **Persistência:** «PATCH /machine-load/sequence» via «persistOrder»
  — sem endpoint novo, mesma pilha de Ctrl+Z e mesma propagação
  WORKING/PUBLISHED.
- **Filtros:** «Ocultar finalizadas» suportado via
  «mergeActiveOrderIntoMachineLoadQueue» (mesmo caminho do DnD);
  «Somente com impedimento» deixa a ação indisponível com explicação —
  semântica sob filtro parcial não aprovada.

### Decisões tomadas (owner do PCP, revisão pós-E3)

- **D1 — APROVADO e implementado no backend:** «reorder_sequence» passa a
  aplicar a regra canônica de «machine_load_queue_slots» — operação com
  run aberto no cockpit fica travada na posição; só posições livres
  permutam. A validação ocorre dentro da transação («_apply_center_order»),
  cobre deslocamento direto e indireto, vale para DnD, agrupamento e
  undo/redo, e rejeita com «MachineLoadSequenceConflict» (409). A fonte
  oficial («open_run_items») é consultada dentro do FOR UPDATE e falha
  propaga como erro controlado — fail-closed, nunca fallback. O gate de
  cliente da E3 («groupingGate») permanece como UX; o backend é a
  autoridade final. **Risco residual documentado:** um run que abra entre a
  consulta e o commit ainda escapa — mesma semântica aceita de
  priorizar/otimizar; fechamento completo exigiria lock compartilhado com a
  fonte de runs (advisory lock / tabela única), decisão de arquitetura
  pendente sem necessidade comprovada.
- **D7 — decisão do owner: manter «_assert_can_view»** (adiado). A
  separação leitura/escrita («production-control.machine-load.manage»)
  segue como dívida de segurança registrada — exige manifest + migração
  de papéis no Keycloak.
- **Concorrência — APROVADO e implementado:** «expected_keys» no PATCH
  /sequence — a ordem-base que o cliente tinha na tela é comparada ao
  estado vigente dentro do FOR UPDATE; divergência → 409, sem write.
  **Sem bypass:** cliente que não envia o campo (bundle legado) recebe
  409 «A programação foi atualizada. Recarregue a página…» — falha
  fechada que se autocorrige: o reload carrega o «remoteEntry.js» novo
  (assets por hash) e o próximo retry já sai pelo contrato novo.
- **Frontend:** «persistOrder» e «applyRemoteKeys» enviam a ordem-base
  (o mesmo «previousKeys» do undo / «currentKeys» do undo-redo).
- **Histórico undo/redo corrigido:** o topo da pilha só é consumido
  depois que a API confirma («peekUndo»/«peekRedo» + pop pós-sucesso) —
  falha ou 409 não perde entradas nem registra redo de ordem que nunca
  existiu. Em 409 «history.reset()» zera as pilhas locais para impedir
  replay de permutação obsoleta sobre a programação de outro analista,
  e o GET recarrega a fila autoritativa. Nenhuma entrada de histórico é
  criada para mutação rejeitada.

### Compatibilidade e rollout (breaking change governado)

«expected_keys» é classificado **BREAKING** no contrato PATCH /sequence.
Único consumidor = MFE production-control (mesmo repo). Matriz:

| Combinação | Resultado |
|---|---|
| FE antigo + API antiga | funciona (sem proteção de concorrência — baseline) |
| FE antigo + API nova | 409 «recarregue»; reload serve bundle novo; retry ok |
| FE novo + API antiga | campo extra ignorado → write sem validação de frescor |
| FE novo + API nova | funciona com concorrência + proteção de runs |
| Bundle antigo em cache | igual «FE antigo» até o reload do remoteEntry |
| Rollback só da API | FE novo → API velha: campo ignorado, perde-se só a validação |
| Rollback só do MFE | FE velho → API nova: 409 com recarga até deploy da API antiga |
| Rollback conjunto | retorna ao baseline pré-hardening |
| Instâncias API mistas | só um pod por app (compose single-container); sem mixed-version |

**Estratégia aprovada:** sequência de deploy **API → MFE** (cutover
coordenado curto). Enquanto a API nova conviver com bundle antigo o
pior caso é um 409 pedagógico por analista; deploy do MFE logo em
seguida encerra a janela. Feature flag/expand-contract foi rejeitada:
«expected_keys» ausente NUNCA pode significar «mutação permitida sem
frescor» — seria bypass silencioso da proteção que motivou o fix.
Critério de aceite observável: ausência de 409 «recarregue» nos logs
após o deploy do MFE.

### Verificação

- Backend: «tests/test_machine_load.py» + «test_machine_load_publication.py»
  — 211 testes (reorder: permutação, stale→409, protegida direta e
  indireta→409, posições livres ok, fail-closed, HTTP 409 divergente,
  HTTP 409 cliente legado sem expected_keys).
- Suíte completa da API: 1120 passed, 2 falhas baseline fora do escopo
  (line_feeder, operator_directory).
- Frontend: 37 arquivos / 267 testes (hook de histórico: peek sem pop,
  pop pós-confirmação, reset limpa pilhas, escopo zera); build OK;
  lint/tsc só baseline.

## 14. Resultado da Etapa 4 — lote coletivo (implementado)

### Contratos entregues (aditivos — nada do legado mudou)

| Rota | Body | Semântica |
|---|---|---|
| `POST /machine-load/transfer-operations` | `source_work_center`, `target_work_center`, `operations[{production_order, operation_code}]` (1..200), `expected_keys` (origem) | Move as selecionadas do CT origem para o fim do destino, na ordem relativa |
| `POST /machine-load/withdraw-operations` | `operations[{work_center, production_order, operation_code}]` (1..200, mono-CT), `expected_keys` | Retira só as operações — o conjunto e as irmãs permanecem |
| `POST /machine-load/restore-operations` | `operations[{work_center, production_order, operation_code}]` | Devolve à fila só operações retiradas individualmente |

Erros: `422` validação (lista vazia/duplicada, item fora do CT, já retirado,
não retirado, destino desconhecido, source==target, CTs mistos na retirada);
`409` `expected_keys` divergente ou item com run aberto (lote inteiro rejeitado
— D1); `403`/escopo conforme `assert_can_view` (D7 mantido).

### Backend — decisões implementadas

- **Atomicidade:** as três rotas usam `_persist_queue_change` (FOR UPDATE +
  transação) — qualquer item inválido/protegido aborta o lote inteiro; nunca
  há write parcial.
- **Concorrência:** `expected_keys` do CT de origem é comparado à ordem vigente
  dentro do lock (`_assert_expected_center_order`); divergência → 409.
- **Identidade CT-scoped (D6):** match por `(work_center + OP + op)` —
  `operation_matches_in_center`/`move_operations_at_work_center` exigem
  exatamente uma instância na origem; OP+op duplicada em CTs distintos não
  é mais ambígua. `register_transfer`/`original_work_center`/`apply_transfers`
  passaram a usar `source_work_center` como identidade da instância; entradas
  legadas sem origem só são aplicadas quando OP+op é inequívoca na fila.
- **Origem ERP correta:** a origem é resolvida antes do move
  (`transferred_from`/registro anterior) — `A→B→A` cancela a entrada e o
  replay pós-refresh não move nada.
- **Runs protegidos (D1):** `_protected_operation_keys` (CT+OP+op do cockpit,
  fail-closed) rejeita o lote com 409 antes de qualquer write.
- **`withdrawn_operations` (D2):** nova chave no `payload_json`; marca por
  `(CT+OP+op)` com `withdrawn_at`/`withdrawn_by`. `WithdrawnMarks` consolida
  conjuntos + operações como única entrada de visibilidade — `is_withdrawn`,
  `visible_operations`, line feeder e cockpit consultam o estado completo
  (sem fallback de meia-verdade). Refresh reaplica a lista (sobrevive ao
  «Atualizar»), idempotente e independente de `withdrawn_conjuntos`.
- **Payload:** `withdrawn.operations[]` expõe as retiradas individuais para o
  modal «Fora da programação» (aditivo — `items[]` de conjuntos intacto).

### Frontend

- Menu contextual em modo coletivo: «Enviar selecionadas» abre o modal de
  destino (modo `selection`, contagem + centro de origem) e «Retirar
  selecionadas» pede confirmação — ambos desabilitados com hint quando a
  execução do cockpit está indisponível (gate de UX; o backend continua
  autoridade).
- `expected_keys` enviado = ordem vigente do CT ativo na tela
  (`keysFromOperations(rows)`), mesmo contrato do reorder.
- 409 → mensagem do servidor + `history.reset()` + `reload()` (mesmo
  comportamento do sequenciamento).
- Modal «Fora da programação» lista operações retiradas individualmente com
  devolução por item; o botão conta conjuntos + operações.

### Verificação

- `tests/test_machine_load.py`: +20 testes E4 — lote move/ordena no destino,
  stale `expected_keys`→409 (service e HTTP), item ausente/duplicado→422,
  source==target/destino desconhecido→422, run protegido→409 sem write,
  fail-closed quando a fonte de runs falha, OP+op em dois CTs move só a
  instância da origem, replay A→B→A cancela entradas, permissão negada,
  retirada esconde só as marcadas/irmãs do conjunto visíveis, união de marcas
  (op retirada + conjunto retirado continua oculta), restore por operação,
  refresh preserva `withdrawn_operations`, HTTP 409/422.
- `tests/test_machine_load_withdrawal.py`: domínio migrado para
  `WithdrawnMarks` (sem fallback de set solto).
- Suíte completa da API: 1141 passed, 2 falhas baseline fora do escopo
  (line_feeder, operator_directory).
- Frontend: 37 arquivos / 269 testes (menu coletivo: ações habilitadas
  executam callbacks, bloqueio coletivo desabilita com hint); build OK;
  lint/tsc só baseline.
