# GLPI #1621 — S2: duplicar solicitação CREATE sem duplicar workflow

> **TASK_ID:** `ENG-PRC-GLPI-1621-S2-CREATE-REQUEST-DUPLICATION-01`  
> **DELIVERABLE_TYPE:** `CODE + TEST`  
> **Data:** 2026-11-19  
> **Estado:** `PLANNED / PROMPT_READY / IMPLEMENTATION_NOT_STARTED / TEST_NOT_RUN`  
> **Owner:** Portal Engenharia / Engineering API; **consumers:** Portal Engenharia e My Requests  
> **Plano aprovado:** [GLPI #1621](./PRC-GLPI-1621-UNIFIED-REQUEST-IMPROVEMENTS-IMPLEMENTATION-PLAN-2026-11-19.md), seção 5  
> **Antecedentes:** S1 `a38db789a3`, S1b `57d7f1924b`, comprovados por commit/relatório; S2 não foi implementado por essas tarefas.

## PROMPT EXECUTÁVEL — DEVIN/CURSOR

### 1. Resultado, escopo e owner

**TASK_ID:** `ENG-PRC-GLPI-1621-S2-CREATE-REQUEST-DUPLICATION-01`  
**USER_OUTCOME:** Um usuário autorizado abre uma solicitação PRC existente do tipo CREATE, escolhe **Duplicar solicitação**, recebe uma nova ficha editável com **somente os dados técnicos reutilizáveis** pré-preenchidos, modifica cor/descrição ou outro atributo e, após revisar, envia por intake normal. O novo caso é independente, sem alterar o caso original.

**CURRENT_RUNTIME_GAP:** Os detalhes PRC de My Requests e Portal Engenharia não oferecem atualmente jornada de duplicação. O formulário compartilhado `PrcRequestForm` suporta CREATE normal e `editCase` para editar o mesmo caso, mas não possui modo de cópia para um *novo* caso.

**NEXT_CODE_DIFF:** Criar uma rota/jornada de duplicação CREATE aproveitando o GET de detalhe PRC autorizado, um prefill filtrado no `@delpi/plugin-ui` e o POST de intake existente. **Sem novo bounded context, sem requests-api paralelo e sem novo endpoint backend salvo prova de insuficiência dos contratos existentes.**

**Ownership:** Engineering API é autoridade de leitura, criação, autoria, permissões por objeto, idempotência e histórico. O frontend permite apenas compor uma intenção nova; `source` é contexto de consumo, não autorização. Keycloak identidade, Core permissions, api-delpi/TOTVS origem dos dados oficiais, sem escrita ERP por esta task.

**Escopo incluído:** duplicação somente de **solicitações `requestType=create`** cujo detalhe esteja acessível à identidade atual; múltiplos estados da origem podem ser elegíveis para consulta, **sem** reabrir status do caso fonte. A disponibilidade da ação não implica criar uma permissão nova; exigir GET autorizado live antes de prefill. My Requests usa `scope=mine`; Engenharia usa escopo autorizado próprio.

**Escopo excluído:** duplicação de `requestType=update` (S2b com baseline oficial fresco); cancelamento (S3); mudança de permissões, alteração oficial TOTVS, clonagem de anexos, histórico ou decisões; integração com EVA/MCP nova. Não declarar capacidade de ação EVA por consequência da UI.

### 2. Reancorar no HEAD e aplicar reuse-before-design

1. Abrir `roberiooliveiradev/delpi-central` no checkout autorizado. Inspecionar `git rev-parse HEAD`, `origin/main`, `git status --short`, `git worktree list` e alterações concorrentes antes de qualquer escrita. Base consultada neste plano: `0247e885b773194fb737216d1639c36ccc104257` — **revalidar no momento da execução**.
2. Ler `AGENTS.md`, `.cursor/rules/evidence-driven-execution.mdc`, `plan-execution.mdc`, `test-and-commit.mdc`, `platform-frontend-mfe-experience.mdc`, `plugins-reusable-components.mdc`, `platform-security-identity-authorization.mdc`, `feature-help-sync.mdc`, protocolo `agent-kit/verifier/project-contract.md` e contrato de sessão/lease existente. Reservar todos os paths autorizados de uma só vez conforme mecanismo vigente, sem alterar WIP alheio, criar worktree/branch ou force push.
3. Ler plano GLPI #1621, `engineering-api/engineering_app/interface/http/routes/product_registration_routes.py` (**GET /requests/{request_id}**, **POST /intake/requests**), serviço/domain PRC, testes de leitura por objeto, intake/Idempotency-Key e envelope de `PrcRequestDetail`.
4. Ler os consumidores atuais:
   - `plugins/my-requests/src/features/product-registration/PrcCasePage.tsx`, `prcApi.ts` e roteamento de nova solicitação.
   - `plugins/engineering/src/features/product-registration/pages/PrcDetailPage.tsx`, `PrcCreatePage.tsx`, `prcNavigate.ts`, `api/productRegistrationApi.ts`.
   - `plugins/plugin-ui/src/components/prc/PrcRequestForm.tsx`, `src/utils/prcProductRegistration.ts` e testes S1/S1b.
5. **Gate explícito:** registrar `EXISTING_EQUIVALENT=YES|NO|TO_INVENTORY` para GET detalhe autorizado, POST intake idempotente, modelagem de draft, campos fornecedores e navegação. **REUSE_DECISION=REUSE/EXTEND** quando atenderem ao contrato. O plano aprovado prefere não criar `POST /duplicate`: se houver bloqueio concreto para reutilizar GET+POST com segurança, demonstrar teste/contrato e **parar somente a fatia afetada**, retornando proposta bounded ao owner. Não criar API por especulação.

### 3. Contrato de comportamento

**Fluxo desejado:**
`Detalhe autorizado do caso CREATE → comando Duplicar → novo draft efêmero e saneado → formulário CREATE com prefill → usuário ajusta e revisa → POST /intake/requests atual → novo requestId/status submitted → detalhe do novo caso`.

- O botão **Duplicar solicitação** deve aparecer somente em detalhe CREATE já acessível via API. **My Requests** não permite abrir nem duplicar case de terceiro por UUID ou query. **Engenharia** respeita seu próprio escopo de GET. Não é necessário e nem permitido inventar `allowedActions=duplicate` no backend sem contrato; essa é uma **ação de navegação que começa novo intake**, não uma transição de estado do caso fonte.
- Os campos duplicáveis vêm de allowlist do **catálogo atual**/reutilização de `technicalDraft` ou `requestedPayload.requestedData` autorizados. Inspecionar wire shape real e confirmar semântica de `supplierLinkChanges`: **não copiar** entidades de caso, status, `id`, `requestId`, `externalRequestId`, `externalItemId`, versão, requester, assignedTo, timestamps, revisões/publicação, flags, decisões, auditoria, conversa, comentários, links de arquivos, verificação, fingerprint e baseline oficial.
- **Fornecedores:** só prefill de linhas de formulário que representam dados técnicos reaproveitáveis de CREATE e que são compatíveis com o contrato atual do catálogo/lookup; revalidar identidade/código/loja, Part Number e duplicidade pelo fluxo vigente. Não converter vínculos de UPDATE/SA5 em candidatos CREATE sem autorização/prova.
- **Anexos:** não copiar metadados nem bytes. O usuário pode anexar novos arquivos manualmente pela capacidade existente.
- **My Requests:** default de novo CREATE conforme S1/S1b é `armazém=01`, `conta=11401002`, `Tipo=MP` **somente em campo ausente no prefill**. Não substituir valores técnicos explicitamente trazidos da origem nem o que o usuário modificar; se a origem tiver outro tipo de produto, permitir seleção válida conforme política do usuário/UX, sem impor MP autoritativamente. **Portal Engenharia:** armazém/conta mantêm defaults S1 como fallback, **Tipo não recebe default** além do valor técnico copiado do caso quando legítimo; seleção MP/PA/PI livre.
- `editCase` tem semântica de **salvar o mesmo requestId via PATCH /draft** e **NÃO pode ser utilizado para duplicação**. Criar entrada opcional de `copySeed`/modo `duplicateCreate` **distinto de editCase**, mantendo etapa de identificação e submit via intake normal. Evitar alterar a assinatura do builder ou criar payload oculto só para copiar.
- Ao falhar busca do caso origem, não abrir formulário com dados parciais ou sensíveis; mostrar erro e permitir retorno. Ao falhar catálogo oficial, preservar valores com estado de erro sem falsa validação. Nenhuma nova autorização derivada de fonte do frontend.
- Submissão cria **caso realmente novo**, com `source` do portal atual, requester autenticado atual, novo UUID/versão/histórico. A idempotência do intake é nova por tentativa de criação, mas estável em retry/double-click para a mesma tentativa. O fluxo nunca chama PATCH do caso fonte.
- Navegação/detalhe de nova solicitação devem respeitar refresh/deep link/F5 e estado de retorno conforme padrões existentes. Se o prefill for mantido apenas em memória de rota, documentar comportamento de refresh sem submeter inadvertidamente ficha vazia ou dados incompletos; preferir padrão persistente/protegido já presente antes de inventar storage local (não colocar dados técnicos sensíveis em URL, localStorage ou logs).
- A cópia não constitui aprovação de produto, dados oficiais, revisão, norma, tolerância ou material — o formulário continua candidato até análise.

### 4. RQ obrigatórios

- **RQ-S2-01:** duplicar caso CREATE acessível do My Requests, com novo formulário CREATE saneado e sem alterar caso origem; My Requests limita leitura `mine`.
- **RQ-S2-02:** duplicar caso CREATE acessível no Portal Engenharia, mantendo escolha ampla de tipos suportados e paridade de novo caso pela Engineering API.
- **RQ-S2-03:** preservar apenas campos técnicos permitidos, com precedence explícita `source draft autorizado > default de UI apenas para campo ausente > entrada manual`, sem copiar campos de contexto de caso, anexos/histórico/decisões.
- **RQ-S2-04:** enviar com `POST /intake/requests` e Idempotency-Key próprios, novo caso/ator atual, status inicial `submitted`; não editar o origin nem reutilizar `editCase`.
- **RQ-S2-05:** live object AuthZ fail-closed e scope `mine` ou `authorized`, erros sem vazamento de informação, no backend bypass e sem novas permissão/routes por inferência.
- **RQ-S2-06:** `requestType=update` nunca duplica como CREATE por acidente; operação bloqueada de forma explícita até o pacote S2b com baseline oficial atualizado.
- **RQ-S2-07:** robustez diante de loading, erro 401/403/404/409, catalog failure, click repetido, retry, refresh, controle da source e contexto de navegação; conteúdo da cópia editável.
- **RQ-S2-08:** preservar S1/S1b (dois defaults globais + MP somente no My Requests como fallback), UPDATE, edit_draft, correção, suppliers, anexos, builds e arquitetura de MFEs finos.

### 5. Critérios de aceite

- **AC-S2-01:** detalhe CREATE de autoria própria em My Requests possui ação Duplicar, e abrir a nova ficha não chama PATCH do original.
- **AC-S2-02:** detalhe CREATE autorizado no Portal Engenharia possui ação Duplicar; tipos MP/PA/PI permanecem possíveis conforme catálogo oficial; a source do novo intake = `portal-engineering`.
- **AC-S2-03:** a cópia traz descrição/grupo/unidade/armazém/conta/tipo/fornecedores compatíveis quando disponibilizados e preserva valores editados; campos ausentes recebem apenas defaults de UI vigentes.
- **AC-S2-04:** não copiar requestId/requester/assignedTo/status/versão/IDs externos, auditoria/timeline, flags, completedRecord, revisões, verificações, conversa, anexos; origem permanece idêntica.
- **AC-S2-05:** o usuário altera ao menos um atributo da cópia (ex.: cor/descrição), valida obrigatórios e confirma revisão antes do POST normal.
- **AC-S2-06:** submissão gera um novo requestId e status submitted, com identidade autenticada atual, source correta e trilha nova; assert API mock/integration e DB/HML quando seguro e autorizado.
- **AC-S2-07:** double-click/retry na mesma tentativa não gera casos duplicados; retry após falha não apaga draft nem troca indevidamente a Idempotency-Key.
- **AC-S2-08:** tentativa de duplicar caso alheio via My Requests ou UUID manipulado devolve 403/404 conforme contrato sem exibir prefill; Portal Engenharia segue object AuthZ atual.
- **AC-S2-09:** caso UPDATE e detalhe indisponível não oferecem cópia CREATE enganosamente; S2b = NOT_IMPLEMENTED/PENDING_CONTRACT.
- **AC-S2-10:** editar solicitação anterior via `editCase` continua salvando o mesmo caso; duplicar nunca usa `saveDraft`.
- **AC-S2-11:** S1/S1b permanecem corretos nos dois canais, inclusive ausência de `MP` imposto na Engenharia, navegação e seleção manual.
- **AC-S2-12:** RED/GREEN de componente, integração dos dois MFEs, GET scope e intake/idempotência no limite disponível, builds, negative tests, arquitetura/guardrails, verificação independente e evidência SHA-bound.
- **AC-S2-13:** tentativa de UX real em HML/PROD somente com permissão e dado de teste não sensível, sem gravar casos artificiais em PROD; marcar `TEST_NOT_RUN` quando não executável. Não declarar resultado humano só por build.

### 6. Execução bounded e gates

1. Inventário breve limitado a `PrcRequestDetail`, `technicalDraft`, URL/nav e `PrcRequestForm`. Se GET+POST forem suficientes e ACL vigente proteger o objeto: **parar discovery e escrever teste RED**.
2. Implementar menor transformação neutra `duplicateCreateSeed` com allowlist explícita e testes unitários de pureza (sem mutação, nem metadata proibida); selecionar valor de draft real somente após leitura autorizada.
3. Implementar modo CREATE de prefill distinto de edição no formulário comum; manter steps/review/supplier validators e idle vs error states. Evitar CSS/layout duplicados. Se UI precisar de ação no detalhe dos dois portais, manter apresentação e navegação por convenções de cada um, sem replicar rule de cópia.
4. Implementar tela/jornada e wiring nos dois MFEs; resolver refresh/deep-link com arquitetura existente. Evitar componente que importa internals de outro MFE.
5. Testar RED baseline, GREEN, positive/sibling/negative, API fake scope e rota, retry e idempotência. Rodar builds e suítes pertinentes plugin-ui, my-requests, engineering; enforcement transversal se material; teste com banco/HML somente se necessidade for provada e execução autorizada.
6. Aplicar `feature-help-sync` e documentação já existente, sem criar pastas. Revisar diffs/staged/lease, flags e arquivos de outras sessões. O executor não faz nova API por conveniência; divergência de contrato exige evidência e escalonamento.
7. Antes de declarar concluído, rodar delpi-verifier no SHA/config testado, no máximo três rodadas, com **todos RQ-S2-01..08 e AC-S2-01..13 no objetivo literal**, reportando decisões/OCs sem edição e sua independência real.
8. Obedecer ao `AGENTS.md` atual para branch, push, deploy e gates superiores de produto/segurança. A aprovação de S2 nesta conversa não é autorização para operação ERP, criação de permissões, nova ferramenta EVA, alteração da Engineering API ou burlar protocolos produtivos.

**EXECUTION REPORT:** `TASK_ID | BASE_HEAD | EVALUATED_SHA | VERIFIED_SHA | FINAL_HEAD | ORIGIN_MAIN | LEASE | FILES_CHANGED | CONTRACT_REUSE | RQ/AC_MATRIX | RED/GREEN | BUILDS | NEGATIVE_TESTS | VERIFIER_VERDICT | RUNTIME_CHANGED | USER_OUTCOME_PROVEN | IMPLEMENTATION_STATUS | INDEPENDENT_VERIFICATION | EXECUTION_DRIFT | RESIDUALS | NEXT_BOUNDED_STEP`. Declarar explicitamente se S2 foi entregue nos dois portais, qual foi o mecanismo de prefill seguro, qual endpoint existente foi reutilizado e se houve prova visual real.

**NEXT:** S3 cancelamento pré-atendimento somente após S2 entregue e decisão funcional sobre marco `submitted` vs primeira visualização. Nenhuma implementação S3 por inferência.

VERIFICAÇÃO: antes do EXECUTION REPORT e do commit/push/deploy, siga o ciclo da seção 'Verificação (delpi-verifier)' do AGENTS.md (verify.py, até 3 rodadas), com o objetivo contendo exatamente estes RQ/AC. Anexe a tabela de rodadas e o relatório final sem edição.
