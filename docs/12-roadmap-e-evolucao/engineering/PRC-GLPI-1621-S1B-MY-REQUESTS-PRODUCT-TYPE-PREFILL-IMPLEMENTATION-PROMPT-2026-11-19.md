# PRC GLPI #1621 — S1b: Tipo MP pré-selecionado somente no My Requests

> **TASK_ID:** `ENG-PRC-GLPI-1621-S1B-MY-REQUESTS-MP-PREFILL-01`  
> **Data/decisão do PO:** 2026-11-19, após validação visual real do S1 em My Requests  
> **Status:** `EXECUTED / IMPLEMENTED_TESTS_GREEN (19/11/2026) / INDEPENDENT_VERIFICATION_REGISTERED — ledger no plano GLPI #1621 §4A`  
> **DELIVERABLE_TYPE:** `CODE+TEST`  
> **Escopo:** refinamento de experiência CREATE, exclusivamente frontend. Engenharia API permanece autoridade do contrato/validação.  
> **Evidência visual do PO:** no My Requests, Armazém padrão `01` e Conta contábil `11401002` aparecem preenchidos, mas Tipo ainda está em `Selecionar…`. O dropdown oferece `MP — Matéria-prima`, `PA — Produto acabado`, `PI — Produto intermediário`.

## Decisão funcional ratificada

- **My Requests / Nova solicitação → Matéria-prima / produto / CREATE:** o campo **Tipo** (`productKind`) deve iniciar com `MP` (`MP — Matéria-prima`) como terceira sugestão inicial, juntamente com Armazém padrão `01` e Conta contábil `11401002`.
- **A seleção continua editável e o dropdown permanece com todas as opções autorizadas pelo catálogo** (incluindo PA/PI, quando a API as oferece). A demanda **não** solicita bloqueio de edição, nem forçar `MP` no backend.
- **Portal Engenharia / CREATE:** não adicionar `productKind=MP` por padrão; o usuário da Engenharia mantém a escolha manual do tipo de produto, inclusive MP/PA/PI, de acordo com os tipos oficialmente suportados. Os defaults de armazém `01` e conta `11401002` do S1 permanecem inalterados.
- **EVA / Engenharia (capacidade semântica autorizada):** a EVA pode apoiar a solicitação/criação de **qualquer tipo de produto suportado** por contrato e permissão oficiais da Engineering API; **não recebe o default de UI `MP` do My Requests**. Não assumir nova tool MCP nem nova autorização por esta decisão; capacidade real de escrita/ação permanece sujeita ao contrato e à aprovação existentes.
- **Posicionamento de produto:** My Requests é a jornada de **cadastro e alteração de matéria-prima**; Portal Engenharia e EVA representam a **jornada de Engenharia mais ampla**. O campo `productKind` continua sendo dado validado pela Engineering API, não derivado de autoridade do `source` no frontend. Um default visual não cria nem altera uma restrição de domínio.
- **UPDATE em ambos os portais:** nunca inserir um default de CREATE, inclusive `productKind=MP`, nem contaminar o diff com valores sugeridos. Contexto oficial prevalece.
- **Edição de caso existente, devolução/correção e duplicação futura:** não substituir dados do caso nem valores digitados. A partir de um draft existente, somente os valores do próprio draft.
- **Sem alteração de contrato, API, backend, Core/RBAC, banco, TOTVS, manifests, rotas ou estado do workflow.** A validação existente permanece na Engineering API.
- **S2 duplicação e S3 cancelamento continuam fora do escopo.**

## Reancoragem factual do HEAD consultado no planejamento

- Repositório: `roberiooliveiradev/delpi-central`, `main`; HEAD consultado: `5065aa95a755d89f9e2600abe511776feeddd010` (revalidar no início da execução).
- `plugins/plugin-ui/src/components/prc/PrcRequestForm.tsx`: formulário único; `values` inicia com `CREATE_FIELD_DEFAULTS` (armazém e conta), independentemente do `source`; `requestType` inicial = `create`; dropdown `productKind` usa catálogo/enum do backend; alternância CREATE/UPDATE repara/exclui defaults do S1.
- `plugins/my-requests/src/features/product-registration/PrcRequestPage.tsx`: wrapper fino com `source="my-requests"`.
- `plugins/engineering/src/features/product-registration/pages/PrcCreatePage.tsx`: wrapper fino com `source="portal-engineering"`.
- `plugins/plugin-ui/src/utils/prcProductRegistration.ts`: `buildCreateIntakeBody` usa `values` sem inventar campos extras.
- **EXISTING_EQUIVALENT=YES; REUSE_DECISION=EXTEND**; não criar segundo wizard, store, nova API ou regra de backend.
- Referências: [Plano GLPI #1621](./PRC-GLPI-1621-UNIFIED-REQUEST-IMPROVEMENTS-IMPLEMENTATION-PLAN-2026-11-19.md), [S1 já implementado](./PRC-GLPI-1621-S1-FRONTEND-DEFAULTS-DEVIN-IMPLEMENTATION-PROMPT.md), [inventário legado, seção 9](./PRODUCT-REGISTRATION-COMPLETE-INVENTORY.md).

---

## PROMPT PARA DEVIN/CURSOR — COPIAR NA ÍNTEGRA

### Missão

**TASK_ID:** `ENG-PRC-GLPI-1621-S1B-MY-REQUESTS-MP-PREFILL-01`.

No formulário PRC compartilhado, adicionar o terceiro **valor inicial de apresentação** `productKind="MP"` **apenas** quando a origem autenticada da tela indicar **`source="my-requests"` e a jornada for nova solicitação CREATE sem `editCase`**. O valor deve aparecer como seleção do campo **Tipo**, permanecer modificável e ser enviado no mesmo `requestedData.productKind` do contrato atual. **Portal Engenharia continua sem pré-seleção do Tipo** e permite criar outros tipos de produto.

A string `source` é um sinal de composição da UI, **não** uma permissão/autoridade: a Engineering API continua decidindo acesso e validade dos dados.

### Preparação e proteção da concorrência

1. Revalidar `HEAD`, `origin/main`, branch, `git status --short`, arquivos modificados e worktrees, preservar modificações de outros agentes, sem reset/stash/force push. **Nunca usar o SHA informado neste plano como autorização para ignorar HEAD atual.**
2. Ler `AGENTS.md`, `.cursor/rules/evidence-driven-execution.mdc`, `test-and-commit.mdc`, `platform-frontend-mfe-experience.mdc`, `plugins-reusable-components.mdc`, `feature-help-sync.mdc` e `agent-kit/verifier/project-contract.md`. Cumprir mecanismo `agent-kit/scope/session_scope.py`: registrar paths de produção/teste/docs em uma reserva única antes do diff; não modificar worktree alheia.
3. Relê contrato atual da Engineering API somente para confirmar as três opções válidas de `productKind` e a jornada CREATE/UPDATE; sem tocar código da API. Revisar o estado do S1 no HEAD.
4. Manter a superfície/contrato único em `@delpi/plugin-ui`. Preferir a solução mais simples no `PrcRequestForm` baseada no `source` real, sem espalhar hardcode pelos dois MFEs. Qualquer prop opcional de política só se for necessária por consumidor real e sem alterar contrato público desnecessariamente.

### RQ obrigatórios

- **RQ-1621-S1B-01:** somente novo CREATE `my-requests`, sem `editCase`, inicia `productKind="MP"`; os defaults existentes `defaultWarehouse="01"` e `accountingAccount="11401002"` permanecem.
- **RQ-1621-S1B-02:** em CREATE no Portal Engenharia (`source="portal-engineering"`), `productKind` inicia não selecionado; campo oferece as opções autorizadas MP, PA e PI e o usuário pode escolher qualquer uma. A camada EVA, quando houver capacidade autorizada para CREATE, permanece regida pela Engineering API para qualquer tipo de produto suportado — sem herdar o default exclusivo do My Requests. Armazém/conta permanecem conforme S1.
- **RQ-1621-S1B-03:** mesmo em My Requests, a seleção MP é **sugestão**, nunca bloqueio; opções diferentes continuam selecionáveis, sem sobrescrita em refetch, navegação de etapas, troca CREATE↔UPDATE ou revisão.
- **RQ-1621-S1B-04:** UPDATE e `editCase` CREATE/UPDATE em ambos os portais não recebem `MP` como default e não geram diff espúrio; valor oficial/draft tem precedência, inclusive vazio, e campos manuais são preservados.
- **RQ-1621-S1B-05:** `buildCreateIntakeBody` e `submitIntake` mantêm payload atual; `requestedData.productKind` é MP quando não alterado no My Requests e reflete escolha do usuário quando alterado. Nada na API/RBAC/ERP muda.

### AC verificáveis

- **AC-1621-S1B-01:** render CREATE sem `editCase` com source `my-requests`, entrar na ficha; Tipo mostra `MP — Matéria-prima`, Armazém mostra `01`, Conta contábil `11401002`.
- **AC-1621-S1B-02:** fonte `portal-engineering`: Tipo continua exibindo `Selecionar…`, enquanto Armazém e Conta ficam pré-selecionados conforme S1.
- **AC-1621-S1B-03:** My Requests consegue mudar Tipo para PA/PI quando presentes no catálogo, e voltar/avançar sem reverter para MP; envio válido mantém a escolha.
- **AC-1621-S1B-04:** envio válido de CREATE My Requests envia `requestedData.productKind="MP"` quando intacto e preserva `source="my-requests"`; Portal Engenharia envia somente a escolha real do usuário.
- **AC-1621-S1B-05:** UPDATE com dados oficiais `productKind="PA"` ou `""` não apresenta MP e `changes` não inclui `productKind` se não alterado; também não envia defaults S1 de armazém/conta.
- **AC-1621-S1B-06:** `editCase` CREATE e UPDATE com `draft.productKind` já preenchido, ausente ou vazio não sofre alteração; `saveDraft` preserva o caminho atual e não vira novo intake.
- **AC-1621-S1B-07:** refetch/catálogo tardio e troca CREATE→UPDATE→CREATE não sobrescrevem seleção manual; restabelecer uma sugestão apenas quando legitimamente vazia e não tocada, sem destruir dados oficiais.
- **AC-1621-S1B-08:** testes de componente e `PrcCreatePage.unification.test.ts` comprovam uma única fonte de formulário e paridade dos dois consumidores; suites e builds pertinentes de `plugin-ui`, `plugins/engineering` e `plugins/my-requests` passam.
- **AC-1621-S1B-09:** residual search, diffs staged, gates transversais, RED/GREEN e verificador independente até 3 rodadas com RQ/AC completos, SHA-bound; nenhuma mudança em API, contratos, migrations, ERP, Core ou S2/S3; validar UI real nos dois portais ou reportar `TEST_NOT_RUN`.

### Paridade de Engenharia e correções condicionais nesta mesma iteração

**A tarefa contempla explicitamente a revisão do Portal Engenharia**, mas NÃO presume defeito nessa superfície. A decisão PO diferencia os três campos pelo canal:

| Campo | My Requests / novo CREATE MP | Portal Engenharia / novo CREATE de qualquer produto |
|---|---|---|
| Armazém padrão (`defaultWarehouse`) | `01` inicialmente, editável | `01` inicialmente, editável, conforme S1 já aceito |
| Conta contábil (`accountingAccount`) | `11401002` inicialmente, editável | `11401002` inicialmente, editável, conforme S1 já aceito |
| Tipo (`productKind`) | `MP` inicialmente, **editável** | **sem pré-seleção**, escolha livre das opções oficialmente suportadas |

**Verificação obrigatória da Engenharia:** montar/abrir o `PrcCreatePage` real (não apenas um mock com outra `source`) e confirmar a tripla acima, a troca entre CREATE/UPDATE, o preenchimento manual de `PA` ou `PI`, o payload e o fluxo de edição. A EVA não é objeto de mudança de runtime nesta task e deve manter o contrato sem default de canal.

**Se a Engenharia apresentar regressão real causada pelo estado compartilhado**, criar teste RED que a reproduza e corrigir **na mesma tarefa** o menor diff necessário: preferencialmente na lógica comum do `PrcRequestForm`; alterar `plugins/engineering` apenas para corrigir wiring/adapter/composição comprovadamente defeituoso, sem segunda cópia dos defaults e sem mudar seu escopo de tipos. Registrar motivo e arquivos extras sob lease antes de qualquer mudança. Se for bug de domínio/API, migração, RBAC, fonte oficial, ferramenta EVA, permissão ou incompatibilidade de contrato **não fazer mudança de backend nesta S1b**: reportar `EXECUTION_DRIFT`/gate e propor novo pacote ao owner adequado.

**Critérios adicionais de regressão:**
- **AC-1621-S1B-10:** integração real do `PrcCreatePage` comprova armazém `01`, conta `11401002`, Tipo vazio inicialmente, seleção manual `PA/PI` e envio de `productKind` sem forced MP; My Requests comprova os três valores sem travar Tipo.
- **AC-1621-S1B-11:** qualquer correção necessária no Portal Engenharia vem acompanhada de RED/GREEN e menor diff auditável; **se não houver defeito**, reportar `NO_ENGINEERING_DIFF_NEEDED` com testes/provas e manter wrapper intocado.
- **AC-1621-S1B-12:** a entrega distingue `COMPONENT_TEST_PASS`, `ENGINEERING_INTEGRATION_PASS` e `BROWSER_PO_ACCEPTANCE`. Não declarar S1b concluída em HML/PROD somente porque o bundle compilou ou o source contém "MP".

### Prontidão para as próximas fatias do GLPI #1621

Ao encerrar, **não implementar S2/S3**. Apenas anexar ao `EXECUTION REPORT` um **handoff curto** para a próxima iteração, recuperando do plano existente: **S2 = duplicação CREATE** via novo intake, sem copiar IDs/histórico/anexos; **S3 = cancelamento terminal submitted antes de start**, pendente ratificação formal do marco de cancelamento e das alterações da Engineering API. Registrar próximos arquivos/owners, contratos a revisar, decisões pendentes e residuals sem criar novas pastas, endpoints, tarefas de discovery redundantes nem alterar código de S2/S3.

### Implementação bounded / qualidade

- Escrever testes RED antes do código; estender ou criar spec em `plugins/plugin-ui/src/components/prc/` (por exemplo, `PrcRequestForm.createDefaults.test.tsx`) com os cenários positivos, siblings e negativos acima.
- No `PrcRequestForm.tsx`, considerar uma função mínima de defaults por origem e modo CREATE, preservando o mapa global atual de armazém/conta e adicionando MP **somente** para My Requests. Quando o modo muda para UPDATE, não permitir vazamento de defaults. **Cuidado com a semântica de valor igual ao default digitado intencionalmente**; igualdade textual não prova ausência de toque do usuário. Se a lógica atual de alternância exigir ajuste proporcional, fazer menor correção segura com testes e sem redesenhar o formulário.
- Jamais sobrescrever seleção de tipo obtida da API para UPDATE ou da edição de caso.
- Não tirar PA/PI do catálogo, não desabilitar o campo e não transformar a seleção em tipo imutável.
- Reutilizar wrappers como consumidores finos, sem copiar implementação em `plugins/my-requests` e `plugins/engineering` ou alterar seus adapters por conveniência.
- Executar testes focalizados, regressão S1, build do kit, build dos dois MFEs, checagem dos exports federados e gates relevantes de `test-and-commit.mdc`.
- Preservar autoria do intake, source, revisão, idempotência e permissões; não fazer submissões reais não autorizadas. O valor sugerido não é garantia de compatibilidade com produto oficial.
- Registrar execução e outcome na documentação já existente **somente após evidências**; sem novas pastas. Não declarar deploy ou comportamento de produção apenas com build.
- Finalizar com `EXECUTION REPORT`: BASE_HEAD, EVALUATED/VERIFIED_SHA, FINAL_HEAD quando houver, branches/worktrees/lease, files changed, **RQ-1621-S1B-01..05 e AC-1621-S1B-01..12** individualizados, RED/GREEN, testes, verificador, estado de HML/PROD, comprovação no browser se houver, `NO_ENGINEERING_DIFF_NEEDED` ou correção demonstrada, residuals e handoff S2/S3 (sem implementá-los). Seguir política de commit/push/deploy efetivamente vigente no `AGENTS.md`, sem deploy por inferência deste documento. Não autoaprovar.

VERIFICAÇÃO: antes do EXECUTION REPORT e do commit/push/deploy, siga o ciclo da seção 'Verificação (delpi-verifier)' do AGENTS.md (verify.py, até 3 rodadas), com o objetivo contendo exatamente estes RQ/AC. Anexe a tabela de rodadas e o relatório final sem edição.
