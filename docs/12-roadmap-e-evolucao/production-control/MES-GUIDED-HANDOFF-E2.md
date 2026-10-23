# MES — Troca guiada de OP no cockpit (E2: finalização inteligente)

> Estado: **implementado — rework final da revisão aplicado (PR #109)**.
> TASK_ID: PC-MES-GUIDED-HANDOFF-E2. Escopo: somente `plugins/public-hub`
> (cockpit do operador). Nenhuma linha de backend foi alterada — os
> contratos da E1 são consumidos como publicados.
> BASE_HEAD: `11514c4fa` (merge da main atual na branch; a main já contém
> a E1 + rework, merge `46771ac4`).

## 1. Resumo executivo

O botão **Encerrar** continua sendo a única entrada de finalização do
cockpit — nenhum botão «Trocar OP» foi criado e a barra de controles não
cresceu (AC-01). O clique agora abre um modal de decisão
(`FinishProductionSheet`) com três saídas:

| Opção | Efeito |
|---|---|
| **Encerrar produção** | Executa o `stop()` vigente — mesmo endpoint, mesmas regras de classificação, mesmo erro. |
| **Ir para a próxima OP** | Um único `POST …/handoff` (E1) encerra o run atual e inicia o sucessor da fila **PUBLISHED** já em `running`, ancorado no Pulse. Sem segunda confirmação, sem Play. |
| **Cancelar** | Fecha o modal sem nenhuma escrita. |

## 2. Decisão de UX (requisito obrigatório)

- `EXISTING_EQUIVALENT = YES` para controles, sessão, overlays e contrato
  E1 → `REUSE_DECISION = EXTEND`. O modal reutiliza a infraestrutura
  `.pcp-pub-modal` (backdrop + painel) e o `OperatorSessionProvider`.
- O mesmo controlador (`useRunHandoff`) serve o card **Agora nesta
  bancada** (`CockpitPage`) e o detalhe da operação
  (`OperationDetailPage`) — uma única implementação do fluxo (E2.RQ-01).
- O card de **run órfão** («esta OP saiu da fila») mantém o Stop direto:
  o handoff seria bloqueado por `current_not_in_queue`; abrir a prévia
  seria um passo inútil. Decisão registrada, não esquecimento.

## 3. Fluxo

```
Encerrar (único botão)
  → FinishProductionSheet abre (zero escrita)
    → GET handoff-preview (branch + workCenter + X-Delpi-Bench-Session)
      → nextOperation vem SEMPRE do backend — nunca da fila visível
    → Opção B habilitada só com preview.available === true
    → clique = confirmação: POST handoff {requestId UUID, branch,
      workCenter, expectedNext, website:""}
      → sucesso → reconcilia (refreshRun + fila) → aviso
        "OP anterior encerrada. Nova OP iniciada." → navega para a nova
        operação da publicação vigente
    → Opção A → stop() tradicional → fecha
    → Cancelar/backdrop/Escape → fecha (backdrop e Escape bloqueados
      durante o POST)
```

## 4. Idempotência e resultado incerto (E2.RQ-05/06)

- `runHandoff.ts` concentra a política: um `requestId` UUID por intenção
  confirmada, gerado **somente por Web Crypto** (`crypto.randomUUID()` →
  `getRandomValues` em contexto inseguro/tablet HTTP). **Não há fallback
  `Math.random`**: sem fonte criptográfica o requestId é `null`, a
  confirmação é bloqueada e a UI mostra mensagem recuperável — nenhum POST
  sai com chave previsível.
- A intenção pendente é registrada em `pendingHandoffIntents`
  (**module-level**, `runHandoff.ts`) **antes** do POST e espelhada em
  `sessionStorage` (`pcp-pub:handoff-intent:<runId>`) — apenas metadados
  da intenção (requestId, run original, destino esperado, branch/CT),
  **sem credenciais**; o registro local nunca autoriza escrita, a
  autorização continua do backend via `X-Delpi-Bench-Session`. Ela
  sobrevive a fechar a tela, remount card ↔ detalhe e **F5**: reabrir a
  finalização restaura a tela de retry com o mesmo requestId. Só é
  removida em resposta definitiva (sucesso ou erro estruturado).
- Resultado incerto = transporte indisponível **ou** 5xx (incl. 502,
  503 e o timeout de gateway **504**): `isUncertainHandoffError` não
  comprova commit, então requestId, run original e destino ficam
  preservados até resolução segura.
- Enquanto houver intenção incerta para o run ativo, **Pause, Resume e
  Stop ficam desabilitados nos controles** (não só dentro do modal) —
  a única escrita possível é o retry idempotente da intenção original.
- Enquanto o resultado é desconhecido (`uncertain`), **Stop, nova troca e
  qualquer escrita contraditória ficam bloqueados** — a única escrita
  permitida é reenviar a mesma intenção (mesmo requestId, mesmo payload).
  `confirmNext` valida isso internamente, não só pelo `disabled`.
- Assinatura da intenção = `expectedNext`. Resultado incerto preserva a
  MESMA chave — «Tentar novamente» repete o mesmo POST e o replay
  idempotente devolve o resultado gravado. Prévia nova + escolha
  explícita = nova intenção (nova chave).
- Duplo clique é bloqueado por `submitInFlightRef` — um POST por intenção.
- Fechar em estado incerto reconcilia o estado autoritativo e **preserva**
  a intenção para o próximo open; nunca assume sucesso ou falha.
- Retry de intenção previamente incerta (fase uncertain, incl. o retorno
  restaurado após remount/F5): a sessão é validada no backend ANTES da
  consulta idempotente, então um **401 — ou qualquer resposta sem o
  código estruturado do contrato — não comprova o resultado da
  primeira tentativa**. A intenção permanece íntegra (mesmo requestId,
  run, expectedNext, branch e workCenter), as escritas contraditórias
  seguem bloqueadas e a sessão é invalidada pelo provider oficial; a
  reidentificação reabilita o retry com a mesma chave — nunca gera
  requestId novo nem Stop de fallback. A mesma política vale para o
  OrphanRunCard («Verificar troca pendente»). Só é definitivo o que
  prova avaliação pelo contrato: sucesso ou ApiError com código
  estruturado de handoff (isStructuredHandoffRejection). Na PRIMEIRA
  tentativa, um 401 prova que a requisição não foi processada —
  rejeição definitiva, sem bloqueio residual.

### Identidade imutável do run no modal

A decisão fica vinculada ao `runId` que a abriu (`boundRunId`). Se uma
reconciliação (`run_not_active`, `current_not_in_queue`, poll/WS)
substituir o run enquanto o modal está aberto, a decisão antiga é
**invalidada sem escrita**: o Stop verifica `run.id === boundRunId` antes
de enviar e o sheet apresenta a situação atual — zero POST de Stop pode
atingir o run novo por uma decisão velha.

### Identidade imutável do run no modal

A decisão fica vinculada ao  que a abriu (). Se uma
reconciliação (, , poll/WS)
substituir o run enquanto o modal está aberto, a decisão antiga é
**invalidada sem escrita**: o Stop verifica  antes
de enviar e o sheet apresenta a situação atual — zero POST de Stop pode
atingir o run novo por uma decisão velha.

### Falha do Stop tradicional

`useProductionRun.stop()` retorna `Promise<boolean>` (consumidores que
ignoram o retorno continuam iguais). O sheet só fecha após Stop
confirmado; em falha permanece aberto, exibe a falha e a ação continua
recuperável.

### Cancelamento da classificação

Cancelar o `DowntimeReasonModal` é cancelamento puro: volta ao estado
anterior **sem reabrir a finalização**. A finalização só reabre depois de
classificação efetivamente confirmada (`onClassify` com sucesso) seguida
de prévia nova válida.

### Reconciliação pós-sucesso (readback)

POST confirmado = mutação concluída. `reload` discrimina `ok`, `failed`
e `superseded`; a reconciliação só é considerada concluída quando a
leitura é válida **e coerente** com o `newRun` confirmado. Falha de
leitura, run ativo incoerente ou ausência legítima → o aviso vira
«atualização pendente» com botão **Atualizar** (read-only) — nunca vira
estado incerto e nunca repete a escrita. Qualquer leitura vencedora
coerente (reload explícito, poll ou evento WebSocket) resolve a
pendência e a navegação para a nova OP acontece exatamente uma vez,
mesmo que o reload explícito tenha sido superado por uma geração mais
recente.

## 5. Códigos 409 (E2.RQ-07)

`ApiError` ganhou `code` (retrocompatível) lido de `data.code` do
envelope `fail()`. `handoffConflictView` traduz:

| code | Ação na UI |
|---|---|
| `count_boundary_stale`, `queue_changed`, `request_conflict`, `pulse_unavailable` | Nova prévia + escolha explícita — nunca troca automática. |
| `pending_classification` | Botão «Informar motivo» abre o `DowntimeReasonModal` existente; ao classificar, a finalização reabre com prévia nova. |
| `current_not_in_queue`, `run_not_active` | Reconcilia run/fila — a condição real já mudou. |
| `no_next_operation`, `balance_unknown`, `device_mismatch`, `epoch_conflict` | Bloqueio final com orientação; Stop tradicional permanece. |

O bloco `pending_classification` também é tratado quando chega na
**prévia** (`available:false` + `block.code`) — mesmo botão, mesmo fluxo.
Nenhuma falha do handoff autoriza Stop automático. 401 usa a invalidação
de sessão vigente.

## 6. Arquivos

| Arquivo | Papel |
|---|---|
| `api.ts` | `ApiError.code`, tipos `RunHandoffPreview/Result`, `fetchRunHandoffPreview`, `confirmRunHandoff` |
| `runHandoff.ts` | requestId, assinatura da intenção, classificação de conflitos (puro) |
| `useRunHandoff.ts` | máquina de estados closed → previewing → ready → submitting → uncertain |
| `FinishProductionSheet.tsx` | modal de decisão (bottom sheet mobile / modal desktop) |
| `ProductionRunControls.tsx` | Encerrar abre a sheet; Stop e classificação preservados |
| `CockpitPage.tsx`, `OperationDetailPage.tsx` | `onHandoffCompleted` — reconcilia fila/card/detalhe e navega |
| `cockpit.css` | `pcp-pub-finish*` sobre o sistema de modal vigente |
| `runHandoff.test.tsx` | 22 testes de política pura (UUID seguro, intents, incerteza, conflitos) |
| `ProductionRunHandoff.test.tsx` | 24 testes de interação (ACs + regressões RW-01…RW-09) |
| `CockpitHandoff.test.tsx` | 4 testes de readback/corrida reload×WebSocket no cockpit real |

## 7. Acessibilidade e responsividade

`role="dialog"` + `aria-modal` + `aria-labelledby`; foco inicial na opção
conservadora e retorno ao botão Encerrar; Escape/backdrop só fora de
estado de escrita; alvos grandes para toque; bottom sheet em telas
estreitas via media query existente; temas via variáveis `pcp-pub`.

## 8. Verificação

- `vitest` (`npx vitest run src/apps/production-control`): **109/109** —
  26 de interação (`ProductionRunHandoff.test.tsx`, incl. regressões
  RW-01…RW-09 do rework final), 7 de cockpit
  (`CockpitHandoff.test.tsx`: readback falho/incoerente/corrida
  reload×WebSocket, reload vencedor do WS com GET do run falho mantendo a pendência e o run conhecido, e run órfão resolvendo a troca incerta pela intenção persistida com o mesmo requestId — as duas regressões residuais foram verificadas falhando antes e passando depois), 22 de política pura (`runHandoff.test.tsx`) e os
  demais arquivos sem regressão.
- `npx vite build` (mesmo comando do Dockerfile de produção): **OK** —
  2141 módulos.
- `tsc -p tsconfig.app.json`: **0 erros em `src/`**; o projeto referencia
  fontes dos plugins irmãos, que não têm `node_modules` no ambiente de
  teste — os erros restantes são desse ruído de ambiente, nenhum no
  escopo E2.
- `eslint` nos arquivos tocados: **0 erros novos** — os 3 reportados são
  linhas baseline idênticas no `origin/main` (comprovado por `git show`).
- `git diff --check`: limpo.
- `TEST_NOT_RUN`: smoke real com Pulse/hardware e tablet — depende da
  homologação E1 no ambiente-alvo (gate declarado no plano).

## 9. Pendências

- Homologação operacional da E1 (Pulse real) precede liberação da E2.
- Deploy de produção: aguarda autorização explícita — build local de
  produção já reproduzido via `npx vite build`.
