# PRC — Evolução das solicitações de matéria-prima/produto — GLPI #1621

> **Data:** 2026-11-19  
> **TASK_ID:** ENG-PRC-GLPI-1621-UNIFIED-REQUEST-IMPROVEMENTS-PLAN-01  
> **Estado:** PLANNED / DOCUMENTATION_ONLY / IMPLEMENTATION_NOT_STARTED / TEST_NOT_RUN / NO_DEPLOY  
> **Origem funcional:** GLPI #1621 — “Sugestões para o App de Criação de Matéria-prima”, aberto por Julielle Jaques e atribuído a Robério Oliveira (18/11/2026).  
> **Owner de produto:** Portal Engenharia DELPI. **Owner de workflow/dados/AuthZ do caso:** Engineering API. **Consumers:** Portal Engenharia e My Requests (Minhas Solicitações).  
> **Escopo:** incremento PRC para CREATE, duplicação segura e cancelamento pré-atendimento; preservar o ciclo de UPDATE, correção, anexos, verificação, revisão e conclusão já existente.  
> **Repositório:** roberiooliveiradev/delpi-central, branch main; base de inventário consultada em 19/11/2026 (HEAD inicial 2179986c5742d0a2cebc4461459000030a6e621b).  
> **Regra:** este documento registra o plano; não autoriza alteração de código, migrations, publicação/deploy, alteração de RBAC, mudança do owner do PRC ou escrita no ERP.

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

A leitura da UI antiga **não** torna seus defaults automaticamente regras atuais para todas as filiais ou famílias de produtos. O escopo 01 / 11401002 precisa ser validado pelo owner funcional antes de materializar uma política na API. Documento e código não demonstram, por si, estado operacional atualizado em produção. **Não confundir** o cancelamento existente no workflow genérico/legado da requests-api com uma ação do PRC atual.

**EXISTING_EQUIVALENT=YES** para formulário, leitura de casos, envio de intake, catálogos, autorização e CAS; **REUSE_DECISION=EXTEND**. **EXISTING_EQUIVALENT=NO** no modelo PRC atual para a nova transição cancel e para a jornada de duplicação; estender no owner existente, não criar um bounded context novo.

## 3. Ownership e fronteiras

| Responsabilidade | Owner | Mudança candidata |
|---|---|---|
| Identidade/SSO | Keycloak | Nenhuma |
| Permissões de plataforma | Core | Reutilizar permissões existentes; nova permissão somente com decisão explícita do Core |
| PRC: dados, regras, workflow, AuthZ por objeto, histórico, versão e auditoria | Engineering API | Defaults governados, eventual projection para duplicação, novo cancel |
| Formulário e controles reutilizáveis | @delpi/plugin-ui | Aplicar defaults de modo não destrutivo; prefill da cópia; controles comuns quando apropriado |
| Experiência de solicitante | plugins/my-requests | Botões/estados, navegação e consumo REST da Engineering API |
| Experiência da Engenharia | plugins/engineering | Botões/estados, navegação e consumo REST da Engineering API |
| Leitura oficial do produto/fornecedor | api-delpi / TOTVS | Contratos existentes, sem novos writes e sem acesso direto da UI |
| EVA/MCP | EVA sob contrato governado | Avaliar paridade de capability após REST; nenhuma nova tool nem execução autônoma pressuposta |

A API permanece responsável pela validação e rejeita a operação mesmo quando a UI manipular ou esconder botões. A identidade do autor de uma cópia é a identidade autenticada **atual**, nunca copiada do caso original.

## 4. S1 — Valores padrão no CREATE (PRC-1621-RQ01/RQ02)

### Comportamento alvo

- Para **nova solicitação CREATE de matéria-prima**, iniciar Armazém padrão com **01** e Conta contábil com **11401002**, sujeitos à ratificação por filial/família de produto.
- Ambos aparecem visíveis e **editáveis**; são propostas iniciais, não confirmação de dados oficiais nem imposição para todos os produtos.
- Em **UPDATE**, carregar os valores reais do contexto oficial de edição, sem aplicar defaults de CREATE.
- Ao **editar solicitação já existente** ou duplicar solicitação, não sobrescrever valores reais/copied nem alterações digitadas pelo usuário.
- Se referência/configuração de defaults estiver indisponível, apresentar estado/erro de maneira honesta; não inventar valor pelo navegador nem usar fallback silencioso diferente do aprovado.

### Desenho de contrato (TARGET; não implementado)

Preferir extensão **aditiva** do GET de reference-data já existente (por exemplo, metadata opcional de createDefaults para produto/família/filial aplicável), sob controle da Engineering API, evitando endpoint novo. O schema, a origem autorizada da política e o recorte por filial devem ser definidos e versionados pelo owner; clientes legados devem continuar aceitos. O formulário consome essa resposta e semeia os campos **somente quando ainda não tocados**. O backend continua validando required, tipos, escopo e valores permitidos; jamais presumir que o valor exibido concede autorização de cadastro oficial.

### Critérios de aceite

- **AC-1621-01:** My Requests e Portal Engenharia exibem 01 e 11401002 no novo CREATE após policy/config ratificada.
- **AC-1621-02:** alterar/remover manualmente os valores não causa reidratação que os sobrescreva; obrigatoriedade segue catálogo oficial.
- **AC-1621-03:** UPDATE, edit_draft, correção de campo devolvido e duplicação preservam seus valores específicos; sem default aplicado fora de CREATE inicial.
- **AC-1621-04:** Engineering API valida e expõe contrato versionado/aditivo de default, com testes de filial/ramo não contemplado e compatibilidade.

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
| CREATE com prefill | UI/E2E, edição e refresh | UI/E2E, edição e refresh | contract + catálogo + negativa |
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
| G0 — baseline curto | 0 | Engineering API + docs PRC | HEAD/status, policies, default por filial, contrato real e teste RED | Inventário somente do necessário; sem refazer discovery já comprovado |
| S1 — defaults | 1 | engineering-api + plugin-ui + 2 MFEs | CREATE com defaults governados nos dois portais | AC-01..04 |
| S2 — duplicar CREATE | 2 | plugin-ui + Engineering API (reuso preferencial) + 2 MFEs | novo caso válido, sem herança proibida | AC-05..09; AC-10 registra residual UPDATE |
| S3 — cancel submitted | 3 | Engineering API (domínio/application/infra/HTTP) + 2 MFEs | terminal cancelled auditável | AC-11..16; decisão “visualização vs início” |
| S4 — QA/integração/release | 4 | QA/owners Engenharia + Coordination | HML, testes negativos, verifier e aceite por pacote | AC-17..18; autorização de publicação independente |
| S2b — duplicar UPDATE | posterior | mesmo PRC, após rebase oficial aprovado | novo intake UPDATE com diff fresco | decisão funcional e contrato adicional |

**RUNTIME_CHANGED=NO; USER_OUTCOME_PROVEN=NO; IMPLEMENTATION_STATUS=PLANNED; INDEPENDENT_VERIFICATION=TEST_NOT_RUN.** A escrita deste plano no GitHub não deve executar serviço, migration, alteração de permissão ou deploy.

## 9. Decisões e limites em aberto

| ID | Decisão necessária | Proposta / estado |
|---|---|---|
| D-1621-01 | Regras de defaults por filial/tipo/família | Confirmar se 01 e 11401002 se aplicam a todos os CREATE de MP ou a escopo restrito; **PENDING_OWNER** |
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

**Próximo passo bounded:** ratificar D-1621-01 (escopo de defaults) e D-1621-02 (marco de cancelamento), reancorar HEAD e executar **S1** como pacote end-to-end Engineering API + plugin-ui + Portal Engenharia + My Requests, com testes e revisão independente. Nenhuma pasta ou bounded context adicional é necessário.
