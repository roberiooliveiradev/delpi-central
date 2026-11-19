# PRC — Evolução das solicitações de matéria-prima/produto — GLPI #1621

> **Data:** 2026-11-19  
> **TASK_ID:** ENG-PRC-GLPI-1621-UNIFIED-REQUEST-IMPROVEMENTS-PLAN-01  
> **Estado:** PLANNED / S1_FRONTEND_ONLY_PO_APPROVED / S1_IMPLEMENTED_TESTS_GREEN / S2_S3_PLANNED / NO_DEPLOY_BY_THIS_DOC  
> **Origem funcional:** GLPI #1621 — “Sugestões para o App de Criação de Matéria-prima”, aberto por Julielle Jaques e atribuído a Robério Oliveira (18/11/2026).  
> **Owner de produto:** Portal Engenharia DELPI. **Owner de workflow/dados/AuthZ do caso:** Engineering API. **Consumers:** Portal Engenharia e My Requests (Minhas Solicitações).  
> **Escopo:** incremento PRC para CREATE, duplicação segura e cancelamento pré-atendimento; preservar o ciclo de UPDATE, correção, anexos, verificação, revisão e conclusão já existente.  
> **Repositório:** roberiooliveiradev/delpi-central, branch main; base de inventário consultada em 19/11/2026 (HEAD inicial 2179986c5742d0a2cebc4461459000030a6e621b).  
> **Regra:** o PO autorizou o recorte funcional **S1 frontend-only** (19/11/2026); este registro não comprova execução nem autoriza por si só deploy, migrations, RBAC, mudanças de owner ou escrita ERP. S2 e S3 permanecem planejados e exigem decisões/gates próprios.
>
> **Decisão superveniente do PO — S1 (19/11/2026):** preencher **apenas no `PrcRequestForm` de `@delpi/plugin-ui`**, sem Engineering API diff, os valores iniciais `defaultWarehouse="01"` e `accountingAccount="11401002"` para **nova solicitação CREATE de matéria-prima**. Os dois portais herdam o mesmo comportamento; preservar UPDATE, `editCase` e valores digitados. [Prompt de implementação S1](./PRC-GLPI-1621-S1-FRONTEND-DEFAULTS-DEVIN-IMPLEMENTATION-PROMPT.md). Esta decisão **substitui somente o desenho anterior de contrato/defaults no S1**; S2/S3 não mudam.

## 1. Pedido e outcome esperado

A solicitação GLPI #1621 pede:
1. Voltar a preencher automaticamente **Armazém padrão** e **Conta contábil** no cadastro, conforme o aplicativo antigo.
2. Permitir **duplicar uma solicitação** para criar outra semelhante (ex.: produtos cuja diferença é a cor), editando somente as diferenças.
3. Permitir **retirar/cancelar a solicitação antes de ser atendida pela Engenharia**, quando houver erro de envio.

**Outcome:** menos digitação e retrabalho para o solicitante, mantendo um único ciclo técnico do PRC e os mesmos estados/regras em ambas as interfaces.

**Invariante de paridade:** Portal Engenharia e My Requests são consumidores de um mesmo caso na **Engineering API**, e do formulário canônico em **@delpi/plugin-ui**. Não criar nova persistência ou máquina de estados no MFE, requests-api ou Controle MP; não clonar serviço/API e não fazer dual-write.

## 2. Evidências e autoridades existentes (PROVEN no código/documentos consultados)

| Aspecto | Evidência/arquivo | Situação |
|---|---|---|
| Intake nos dois portais | plugins/engineering/src/features/product-registration/pages/PrcCreatePage.tsx e plugins/my-requests/src/features/product-registration/PrcRequestPage.tsx | Ambos usam PrcRequestForm compartilhado com adapters para Engineering API |
| Formulário canônico | plugins/plugin-ui/src/components/prc/PrcRequestForm.tsx | CREATE novo inicializa values sem defaults; edição usa o draft existente |
| Contrato dos campos | engineering-api/engineering_app/domain/product_registration/catalog.py | defaultWarehouse = B1_LOCPAD; accountingAccount = B1_CONTA; ambos requeridos no CREATE |
| Histórico do app antigo | PRODUCT-REGISTRATION-COMPLETE-INVENTORY.md, seção 9 | UI legada tinha armazem_padrao=01, cta_contabil=11401002; também tipo=MP e produto_terceiro=1 |
| Máquina de estados | engineering-api/engineering_app/domain/product_registration/models.py | submitted, in_progress, needs_information, needs_correction, under_review, completed, rejected; **cancelled ainda não existe** |
| Autorização | models.py e service do PRC | allowedActions fornecido pelo backend; edit_draft exclusivo do criador em submitted; atendimento governado por engineering.access |
| APIs | engineering-api/engineering_app/interface/http/routes/product_registration_routes.py | Intake idempotente, leitura autorizada por objeto, ações com controle de versão; não foi identificada ação cancel no PRC |
| Paridade UX anterior | PRC-CONVERSATION-UX-PRODUCTION-CLOSURE-2026-11-18.md | Fechamento limitado da conversa/UX anterior; não cobre as três melhorias deste documento |

O owner funcional **ratificou para S1** o uso dos defaults legados `01` e `11401002` como **valores iniciais editáveis da UI para novos CREATE de matéria-prima** (mesmo PRC nos dois portais). Isso **não** aprova um default universal da API, do ERP, de outros tipos de produto ou de UPDATE; nenhuma política backend por filial é adicionada nesta fatia. Documento e código não demonstram, por si, estado operacional atualizado em produção. **Não confundir** o cancelamento do workflow genérico/legado da requests-api com uma ação do PRC atual.

**EXISTING_EQUIVALENT=YES** para formulário, leitura de casos, envio de intake, catálogos, autorização e CAS; **REUSE_DECISION=EXTEND**. **EXISTING_EQUIVALENT=NO** no modelo PRC atual para a nova transição cancel e para a jornada de duplicação; estender no owner existente, não criar um bounded context novo.

## 3. Ownership e fronteiras

| Responsabilidade | Owner | Mudança candidata |
|---|---|---|
| Identidade/SSO | Keycloak | Nenhuma |
| Permissões de plataforma | Core | Reutilizar permissões existentes; nova permissão somente com decisão explícita do Core |
| PRC: dados, regras, workflow, AuthZ por objeto, histórico, versão e auditoria | Engineering API | **S1: nenhuma alteração**, mantém validações e contratos existentes; S2/S3: contratos futuros conforme seus gates |
| Formulário e controles reutilizáveis | @delpi/plugin-ui | **S1: único owner do diff frontend** para dois valores iniciais editáveis de CREATE; S2: prefill da cópia quando autorizado |
| Experiência de solicitante | plugins/my-requests | **S1: consumir e testar o mesmo formulário sem duplicar defaults**; S2/S3: botões/estados conforme contratos futuros |
| Experiência da Engenharia | plugins/engineering | **S1: consumir e testar o mesmo formulário sem duplicar defaults**; S2/S3: botões/estados conforme contratos futuros |
| Leitura oficial do produto/fornecedor | api-delpi / TOTVS | Contratos existentes, sem novos writes e sem acesso direto da UI |
| EVA/MCP | EVA sob contrato governado | Avaliar paridade de capability após REST; nenhuma nova tool nem execução autônoma pressuposta |

A API permanece responsável pela validação e rejeita a operação mesmo quando a UI manipular ou esconder botões. A identidade do autor de uma cópia é a identidade autenticada **atual**, nunca copiada do caso original.

## 4. S1 — Valores iniciais no CREATE: **frontend-only** (PRC-1621-RQ01/RQ02)

> **Decisão PO ratificada em 19/11/2026 — S1_APPROVED_FRONTEND_ONLY / IMPLEMENTED_TESTS_GREEN (19/11/2026).** `S1` não exige nem permite implementar defaults na Engineering API. A autorização vale apenas para esta pequena modificação de UI; a API mantém validações, fonte oficial e autoridade sobre a solicitação.
>
> **Ledger S1 — execução registrada (19/11/2026):** diff de produção restrito a `plugins/plugin-ui/src/components/prc/PrcRequestForm.tsx` (+28/−1: `CREATE_FIELD_DEFAULTS` semeando `values` apenas sem `editCase`; alternância CREATE/UPDATE não injeta nem carrega sugestões). Spec `PrcRequestForm.createDefaults.test.tsx` (7 testes, AC-1621-S1-01..06) RED no HEAD (4/7 falhas — campos vazios) e GREEN no diff; regressões verdes: plugin-ui 2837/2837, engineering product-registration 264/264, my-requests 21/21; builds dos três pacotes OK. Verificação independente delpi-verifier registrada sob `eng-prc-glpi-1621-s1`. Runtime nos portais depende do deploy canônico pós-push — `RUNTIME_CHANGED` só após publicação efetiva.

### Comportamento aprovado

- Ao criar **nova solicitação CREATE de matéria-prima** no `PrcRequestForm` compartilhado (`!editCase` e modo `create`), os campos **Armazém padrão** (`defaultWarehouse`) e **Conta contábil** (`accountingAccount`) aparecem inicialmente com `01` e `11401002`, respectivamente.
- Ambos são **valores sugeridos e editáveis**. Alteração, limpeza, navegação entre etapas, carregamento tardio de catálogos e `reference-data` não podem sobrescrever o que o usuário digitou. Campo obrigatório vazio continua sujeito à validação vigente, sem restaurar default ocultamente.
- O modo **UPDATE** continua usando somente o contexto oficial obtido em `fetchEditContext`; defaults de CREATE não podem aparecer como diffs nem sobrescrever valores oficiais (inclusive um campo oficialmente vazio).
- A edição de caso existente (`editCase` CREATE/UPDATE), devolução/correção, e futuros drafts de duplicação preservam valores reais do draft. Nenhuma substituição em `saveDraft`/fluxo de edição.
- **Escopo aprovado:** somente os dois campos pedidos; outros defaults antigos (`productKind=MP`, `thirdPartyProduct=1`) são referência histórica, **fora do diff S1**.
- O mesmo comportamento é herdado automaticamente por **Portal Engenharia** e **My Requests** porque os dois wrappers atuais utilizam `plugins/plugin-ui/src/components/prc/PrcRequestForm.tsx`. Não criar segunda implementação nos MFEs.

### Contrato, ownership e escopo executável

- **Sem alteração REST/OpenAPI, novas rotas, DTOs, metadata `createDefaults`, banco, migrations, Core/RBAC, Engineering API, api-delpi, TOTVS ou requests-api**.
- Valores iniciais ficam exclusivamente no estado de UI do `PrcRequestForm`; `buildCreateIntakeBody` e `POST /intake/requests` seguem o contrato atual, enviando os valores escolhidos pelo usuário.
- **EXISTING_EQUIVALENT=YES; REUSE_DECISION=EXTEND.** Preferir diffs mínimos no formulário compartilhado e seus testes. Os wrappers de `plugins/engineering` e `plugins/my-requests` são apenas consumidores e alvos de regressão; alterá-los somente por defeito de integração demonstrado, sem duplicar a regra.
- **Fonte histórica dos valores:** [inventário Controle MP, seção 9](./PRODUCT-REGISTRATION-COMPLETE-INVENTORY.md). Os valores não são source of truth do produto no Protheus, nem aprovação de regra para famílias de produto fora deste CREATE de matéria-prima.
- **Prompt executável S1:** [PRC-GLPI-1621-S1-FRONTEND-DEFAULTS-DEVIN-IMPLEMENTATION-PROMPT.md](./PRC-GLPI-1621-S1-FRONTEND-DEFAULTS-DEVIN-IMPLEMENTATION-PROMPT.md).

### Requisitos e critérios de aceite (S1)

- **RQ-1621-S1-01:** inicializar apenas o novo CREATE MP com os dois valores aprovados.
- **RQ-1621-S1-02:** preservar input editável e validação vigente após re-render/carregamento assíncrono.
- **RQ-1621-S1-03:** não contaminar UPDATE, edição de caso, devolução/correção ou duplicação futura.
- **RQ-1621-S1-04:** manter um formulário compartilhado, mesmo comportamento nos dois portais e zero diff backend.

- **AC-1621-01:** My Requests e Portal Engenharia exibem `01` e `11401002` no novo CREATE; testes com as duas origens reais.
- **AC-1621-02:** usuário pode alterar ou limpar os campos; navegação/refetch não sobrescrevem; campos obrigatórios ainda são validados no cliente e na API existente.
- **AC-1621-03:** UPDATE, `editCase` CREATE/UPDATE e correção preservam valores oficiais ou já digitados, sem injeção de defaults.
- **AC-1621-04:** backend e seus contratos permanecem intocados; testes RED/GREEN do formulário, payload CREATE, unificação, builds/regressão dos dois portais e verificador independente no SHA exato.

Os ACs acima são requisitos macro do plano; o **prompt executável S1** detalha AC-1621-S1-01..09, sem alterar S2/S3. S1 só pode ser `PASS` após implementação real, testes, aceite apropriado e evidence SHA-bound.

## 4A. S1b — Tipo de produto MP pré-selecionado apenas em My Requests (19/11/2026)

> **Novo refinamento funcional do PO após validação visual do S1.** **Status:** `S1B_PO_APPROVED / PLANNED / PROMPT_READY / IMPLEMENTATION_NOT_STARTED / TEST_NOT_RUN`. Trata-se de pacote adicional e limitado; **não reabre nem altera os dois defaults globais do S1**, nem autoriza backend.

**Evidência funcional:** o PO apresentou a tela de produção `/apps/my-requests/new?type=raw-material-creation` com armazém `01` e conta contábil `11401002` já pré-selecionados. O campo Tipo aparecia em `Selecionar…` e seu dropdown oferecia `MP — Matéria-prima`, `PA — Produto acabado` e `PI — Produto intermediário`.

**Regra aprovada:**
- **My Requests, novo CREATE, sem `editCase`:** inicializar também `productKind="MP"`, mantendo `defaultWarehouse="01"` e `accountingAccount="11401002"`. Tipo segue **editável** e com as outras opções legítimas do catálogo. Pré-seleção não equivale a bloqueio nem regra de domínio.
- **Portal Engenharia, novo CREATE:** Tipo continua sem pré-seleção (`Selecionar…`) e permite escolher qualquer opção válida, inclusive PA/PI. Os dois defaults do S1 permanecem iguais nos dois portais.
- **Distinção entre jornadas:** My Requests é o canal de solicitação de **cadastro/alteração de matéria-prima**; Portal Engenharia e EVA atendem, quando autorizado, à jornada **mais ampla de produtos**, abrangendo outros tipos disponíveis no contrato oficial. A pré-seleção de MP é específica da apresentação do My Requests e não restringe a Engineering API ou a EVA. Uma capacidade de execução semântica da EVA exige tool/use case e AuthZ já aprovados; não nasce desta mudança no front-end.
- **UPDATE e casos existentes em qualquer portal:** usar valores oficiais/draft, não aplicar `MP` ou sugestões ao diff, não alterar valores digitados ou contexto de correção. Refetch e navegação não sobrescrevem seleção manual.
- **Implementation boundary:** estender o `PrcRequestForm` compartilhado sob `@delpi/plugin-ui`, diferenciando `source="my-requests"` de `source="portal-engineering"`. Ambos os wrappers ficam finos; a `source` é sinal de UX, **não authority**. Zero nova API, migração, RBAC ou escrita TOTVS.
- **S2/S3:** sem mudança de escopo.

**RQ-1621-S1B-01..05:** abrangem prefill MP apenas no My Requests, manutenção de seleção manual na Engenharia, preservação em alternâncias/UPDATE/editCase, e payload existente sem diff backend.

**AC-1621-S1B-01..09:** incluem visibilidade dos três defaults em My Requests; Tipo vazio na Engenharia; opções PA/PI disponíveis; troca manual e payload; proteção de UPDATE/editCase; testes de concorrência UI/refetch; builds em ambos os MFEs; RED/GREEN, verificador e evidência por SHA.

**Prompt canônico de implementação:** [S1b — My Requests / prefill MP somente nesta origem](./PRC-GLPI-1621-S1B-MY-REQUESTS-PRODUCT-TYPE-PREFILL-IMPLEMENTATION-PROMPT-2026-11-19.md). **Nenhum código foi modificado nesta decisão documental.**

## 5. S2 — Duplicar solicitação com novo ciclo (PRC-1621-RQ03/RQ04)

### Comportamento alvo

A ação **Duplicar solicitação** fica disponível para casos cuja leitura seja permitida pelo backend (ex.: caso próprio no My Requests, casos autorizados na Engenharia). Não é alteração do caso de origem.

1. Ler o caso fonte mediante autorização live do serviço, com escopo correto.
2. Construir um **novo candidato de intake** com apenas campos técnicos reutilizáveis; expor a cópia como formulário não enviado.
3. Permitir editar descrição/cor e demais dados; consultar novamente fornecedores/catálogos exigidos e validar campos obrigatórios.
4. Submeter pelo **POST de intake existente**, com novo Idempotency-Key, source da superfície atual e requester = identidade autenticada atual.
5. Retornar um **novo requestId**, status inicial submitted, histórico próprio e navegação para o novo detalhe. Falha preserva a edição sem duplicar submissões.

**Não copiar:** requestId, externalRequestId/externalItemId, requester/assignee, status, caseVersion, revisão oficial, resultado de verificação, comentários, conversa, flags, histórico, anexos ou decisões/aprovações. Anexos poderão ser selecionados manualmente pelo usuário de novo, sujeitos ao contrato vigente; sem cópia automática de bytes.

**CREATE:** primeira fatia implementável da duplicação. **UPDATE:** não replicar alteração sobre baseline antigo sem validar contexto oficial atual, fingerprint e diffs dos campos/vínculos. Tratar como fatia posterior condicionada à prova do rebase e decisão funcional; a capacidade global não é considerada concluída para UPDATE antes dessa prova.

**Contrato preferencial:** GET de detalhe autorizado + composição do formulário existente + POST de intake existente. **Não criar POST /duplicate** por conveniência; somente propor projection/endpoint backend específico caso inventário e testes provem que os dados retornados não podem ser reutilizados com segurança por múltiplos consumers. Garantir refresh/F5/deep link conforme padrão de navegação aprovado.

### Critérios de aceite

- **AC-1621-05:** duplicar CREATE na Engenharia e no My Requests abre ficha nova, permite mudar um atributo e submete corretamente.
- **AC-1621-06:** nova solicitação tem ID, autoria, versão, source e histórico próprios; caso original permanece intacto.
- **AC-1621-07:** anexos, decisões, eventos, status, verificações e flags da origem não migram para a cópia.
- **AC-1621-08:** acesso não autorizado a ID de terceiro retorna 403/404 conforme política oficial, sem pré-preencher dado sensível.
- **AC-1621-09:** retry, double click e refresh não criam duas solicitações para a mesma submissão idempotente.
- **AC-1621-10:** escopo de UPDATE duplicado fica explicitamente PENDING/NOT_IMPLEMENTED até rebase oficial testado; nenhuma cópia stale é apresentada como validação oficial.

## 6. S3 — Cancelamento pré-atendimento (PRC-1621-RQ05/RQ06)

### Decisão funcional proposta

O pedido usa “antes de ser vista pela Engenharia”; o sistema demonstra um marco observável e transacional mais seguro: **antes de iniciar formalmente o atendimento**. Propor como elegibilidade: status **submitted** e ator **requester_subject do próprio caso**, com permissão PRC existente válida. O ato de apenas abrir/visualizar a tela não bloqueia o cancelamento; se a política desejada for “primeira visualização”, o owner deverá decidir e especificar esse evento em separado.

**Cancelar não é excluir fisicamente.** O caso passa a estado terminal **cancelled**, fica auditável e visível no histórico, não é processável pela Engenharia e não participa da fila pendente. Dados/anexos seguem retenção e controles já aprovados; qualquer remoção física exige outra política.

### Contrato candidato (TARGET; exige ratificação)

- Adicionar status **cancelled** ao domínio PRC, como terminal, incluindo projeções REST, mapeamento visual, filtros e contadores.
- Adicionar transição **submitted → cancelled**, ação **cancel**, exclusivamente pelo autor/solicitante do caso, com Core permission live + object AuthZ live, nunca inferida da UI.
- Preferir o padrão REST vigente: **POST /v1/product-registration/requests/{request_id}/actions/cancel**; body com **expectedVersion** e motivo opcional (definir restrições), header **Idempotency-Key** e mesmo envelope/semântica de erro das ações existentes.
- CAS/row version garante **start x cancel** mutuamente exclusivos: se start vencer, cancel falha com 409; se cancel vencer, start falha. Nenhum dos dois pode produzir dupla transição ou registro sem auditoria.
- Persistir evento contendo ator, momento, status anterior/novo, versão, motivo quando informado, correlationId e idempotência, usando ledger/eventos já existentes.
- Atualizar allowedActions, filas, histórico, timeline, status badges, filtros, contagens, worklist, eventuais eventos realtime e tratamentos de terminais, sem reabrir completed/rejected/cancelled.
- Executar migration forward-only somente se inventário comprovar necessidade (constraints, enum/check, índices, projeções, grants). Não alterar dados históricos arbitrariamente nem deletar registros.

### Critérios de aceite

- **AC-1621-11:** autor autorizado cancela caso submitted via ambos os portais, com confirmação e feedback.
- **AC-1621-12:** outro usuário, mesmo com conhecimento do UUID, não cancela caso de terceiro; perfil de atendimento não recebe permissão de cancelamento pelo simples engineering.access.
- **AC-1621-13:** in_progress/needs_correction/under_review/completed/rejected/cancelled não são canceláveis; tentativas retornam 403/409 tipados conforme regra, sem mutação.
- **AC-1621-14:** concorrência start versus cancel e retries são consistentes, com versão, idempotência e evento auditado exatamente uma vez.
- **AC-1621-15:** cancelado é consultável em histórico/filtro, mas não acionável em fila/contadores pendentes; ambos os portais reconhecem o estado.
- **AC-1621-16:** anexos e trilha do caso permanecem sob retenção/autorização, sem DELETE físico por esta feature.

## 7. S4 — Compatibilidade, segurança e prova nos dois portais (PRC-1621-RQ07/RQ08)

**Matriz mínima de prova:**

| Dimensão | My Requests | Portal Engenharia | Engineering API |
|---|---|---|---|
| CREATE com prefill | UI/E2E, edição e refresh | UI/E2E, edição e refresh | **Sem diff S1**: contrato e validação atuais preservados; regressão por payload |
| Duplicação CREATE | origem própria, submit, retry | caso autorizado, submit, retry | object AuthZ + intake idempotente |
| Duplicação UPDATE (fatia posterior) | baseline atual obrigatório | baseline atual obrigatório | official reader + 409 stale |
| Cancelamento | confirmação/estado/timeline | fila/detalhe/counters | status machine + CAS + audit |
| Negativas | caso de terceiro, 403/404, errors | sem privilégio inventado | permission live + object denial |
| Regressão | edição submitted, correção, anexos, conversa | fila, devolução, conclusão | verificação TOTVS e revisão imutável |

- Testar permissão cruzada: requester puro de My Requests, analista com engineering.access, criador analista, terceiro não autorizado e cenários de mudança de permissão em runtime.
- Cobrir paginação/contagem/ordenação e links antigos; navegação F5/back-forward; erros 401/403/404/409/422/5xx e acessibilidade teclado/diálogo.
- Testar PostgreSQL real em HML se migration for material; confirmar histórico e integridade em refresh, reconexão e dois browsers.
- Rodar unit/contract/integration/frontend/E2E pertinentes no SHA exato; seguir AGENTS.md e protocolo do verificador independente com RQ/AC integrais antes de qualquer aceite ou deploy.
- Não declarar PASS/produção pelo simples commit ou por documentação, healthcheck 200 ou mock.
- Avaliar paridade semântica REST/EVA sob as seis ferramentas existentes e suas permissões, **sem criar nova tool MCP nem expor cancelamento autônomo** por consequência do REST.
- **AC-1621-17:** resultados de S1, S2 e S3 comprovados nas duas interfaces e via API para os perfis permitidos; evidências SHA-bound e screenshot HML.
- **AC-1621-18:** regressão PRC sem violar validação de conclusão TOTVS, proibições de escrita no ERP e boundaries com requests-api.

## 8. Sequência de execução bounded

| Pacote | Prioridade | Owner/escopo | Saída verificável | Gate |
|---|---|---|---|---|
| G0 — baseline curto S1 | 0 | Plugin UI + wrappers PRC (read-only) | HEAD/status/leases, evidência da tela vazia, teste RED e dois valores já ratificados pelo PO | Sem projeto novo de default na API; inventário mínimo e direto |
| S1 — defaults frontend-only | 1 | **plugin-ui** (código+testes); **2 MFEs** (regressão/build), **Engineering API intocada** | CREATE MP mostra 01 e 11401002, editáveis, sem afetar UPDATE/editCase nos dois portais | AC-01..04 e AC-1621-S1-01..09 do prompt |
| S2 — duplicar CREATE | 2 | plugin-ui + Engineering API (reuso preferencial) + 2 MFEs | novo caso válido, sem herança proibida | AC-05..09; AC-10 registra residual UPDATE |
| S3 — cancel submitted | 3 | Engineering API (domínio/application/infra/HTTP) + 2 MFEs | terminal cancelled auditável | AC-11..16; decisão “visualização vs início” |
| S4 — QA/integração/release | 4 | QA/owners Engenharia + Coordination | HML, testes negativos, verifier e aceite por pacote | AC-17..18; autorização de publicação independente |
| S2b — duplicar UPDATE | posterior | mesmo PRC, após rebase oficial aprovado | novo intake UPDATE com diff fresco | decisão funcional e contrato adicional |

**RUNTIME_CHANGED=NO; USER_OUTCOME_PROVEN=NO; IMPLEMENTATION_STATUS=PLANNED; INDEPENDENT_VERIFICATION=TEST_NOT_RUN.** A escrita deste plano no GitHub não deve executar serviço, migration, alteração de permissão ou deploy.

## 9. Decisões e limites em aberto

| ID | Decisão necessária | Proposta / estado |
|---|---|---|
| D-1621-01 | Estratégia e valores S1 | **PO_RATIFIED 2026-11-19:** prefill **somente frontend** em novos CREATE MP dos dois portais com `01` e `11401002`, editáveis; sem contrato/default na API. Outras famílias/ERP fora do escopo. |
| D-1621-02 | Limite para retirada | Usar submitted antes de start, não abertura de tela; **PROPOSED / PENDING_PO_RATIFICATION** |
| D-1621-03 | UPDATE duplicável | Após busca oficial fresca e novo diff, pacote S2b; **PENDING_CONTRACT** |
| D-1621-04 | Anexos em cópia | Não copiar automaticamente; **DEFAULT_SAFE / EXPANSION_REQUIRES_OWNER** |
| D-1621-05 | Política de cancelamento/retenção | Estado terminal auditável sem hard delete; revisar projection, timeline e retenção existente; **PROPOSED** |
| D-1621-06 | Publicação/deploy | Cada pacote exige verificação e autorização pertinentes; nenhuma inferência a partir deste plano; **NOT_AUTHORIZED_BY_THIS_DOC** |

**STOP/ESCALATE:** decisão que crie novo owner, fonte de verdade, alteração de permissões Core, acoplamento cross-context, escrita Protheus ou modelo de retenção diverso → ARCHITECTURE_DECISION_REQUIRED, retornar à Coordination. Divergência entre plano, HEAD e contrato real → EXECUTION_DRIFT; corrigir evidência e desenho antes do diff afetado.

## 10. Arquivos de referência e rastreabilidade

- [Roadmap do Portal Engenharia](./ROADMAP.md)
- [Índice de Engenharia](./README.md)
- [Inventário completo do Controle MP](./PRODUCT-REGISTRATION-COMPLETE-INVENTORY.md)
- [Contrato técnico do PRC](./PRODUCT-REGISTRATION-MVP-TECHNICAL-CONTRACT.md)
- [Decisões de PO PRC](./PRODUCT-REGISTRATION-PO-DECISIONS-2026-11-06.md)
- [Fechamento limitado PRC / UX 18-11](./PRC-CONVERSATION-UX-PRODUCTION-CLOSURE-2026-11-18.md)
- [AGENTS.md do repositório](../../../AGENTS.md)
- Engineering API: engineering-api/engineering_app/domain/product_registration/models.py; catalog.py; interface/http/routes/product_registration_routes.py.
- Formulário comum: plugins/plugin-ui/src/components/prc/PrcRequestForm.tsx.
- Portais consumidores: plugins/my-requests/src/features/product-registration e plugins/engineering/src/features/product-registration.
- Demanda de negócio: GLPI Helpdesk DELPI #1621; não confundir com issue do GitHub.

**Próximo passo bounded (19/11/2026):** S1 de armazém/conta foi implementado conforme commit `a38db789a3bbe5adc69b4f482c77ae644c72780c` e confirmado visualmente pelo PO **em My Requests**; aceitação completa do Portal Engenharia continua `TEST_NOT_RUN` nesta conversa. Implementar **S1b** (Tipo MP pré-selecionado **somente** em My Requests) conforme [prompt S1b](./PRC-GLPI-1621-S1B-MY-REQUESTS-PRODUCT-TYPE-PREFILL-IMPLEMENTATION-PROMPT-2026-11-19.md), com regressão dos dois portais e sem diff na Engineering API. S2/S3 permanecem posteriores; D-1621-02 ainda precisa de decisão para S3.
