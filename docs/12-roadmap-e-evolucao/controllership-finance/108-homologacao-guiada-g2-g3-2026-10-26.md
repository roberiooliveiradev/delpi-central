# Documento 108 — Homologação guiada G2/G3 do Portal Controladoria & Finanças e CLARA

**Sessão:** `CF-PROC0072-G2G3-GUIDED-ACCEPTANCE-20261026-001`  
**Data de abertura:** 2026-10-26 (America/Sao_Paulo)  
**Produto:** Portal Controladoria & Finanças · Central de Fechamento · `PROC-0072`  
**Condutor:** GPT Arquiteto; **usuário testador/PO:** participante da conversa de homologação; **G2 sign-off:** Controladoria/PO; **G3 sign-off:** Operador SSH autorizado.  
**Baseline GitHub ao abrir:** `4e64c2f571fa897641d6263eed132aa2fd9527e8`. **Código implantado:** `2eeb5fb943` *reportado pelo operador, não readback independente desta sessão*.  
**Autoridades:** instruções oficiais, regras .cursor aplicáveis, [ledger 23](./23-ledger-rq-ac-testes.md), [roadmap 93](./93-roadmap-executivo-central-fechamento-end-to-end-checkpoints.md), [plano 104](./104-plano-mestre-execucao-e2e-fechamento-aceite-deploy.md), [CLARA 106](./106-clara-batch-ssh-keycloak-chatgpt-go-e-gates.md), [release 107](./107-clara-validacao-antecipada-chatgpt-release-hoje.md), mapa UI 30, contratos P1–P6.

## 0. Regras da sessão

- **Interação guiada:** testar uma tela/fluxo de cada vez, comparar com RQ/AC e registrar resultado no mesmo documento; nenhum PASS presumido para as demais telas.
- **Status:** `PASS`, `FAIL`, `PENDING`, `INCONCLUSIVE`, `TEST_NOT_RUN`, `STALE_EVIDENCE`. A classificação da fonte será `PROVEN`, `TO_INVENTORY`, `PLANNED` ou `TARGET`. `PASS` restrito a critério observado, não ao G2/G3 inteiro.
- **Evidência:** data/hora, ambiente, URL/rota, ator/perfil com identificação mínima, competência/área, comportamento esperado, observado, identificador de screenshot/smoke/DB, RQ/AC e outcome. A screenshot enviada ao chat **não foi anexada ao GitHub**; este registro conserva somente descrição/proveniência, sem inventar arquivo persistido.
- **Produção:** na fase inicial realizar exclusivamente navegação e leituras; **não abrir competência, enviar/validar/rejeitar documentos, submeter pacotes, alterar catálogos ou executar ACT** sem cenário autorizado, dados de teste definidos e autorização humana competente. Não expor dados de colaboradores, valores sensíveis, segredos ou credenciais nas capturas enviadas.
- **Correções:** registrar sintomas, impacto, passos para reprodução, owner, severidade `BLOCKER/MAJOR/MINOR`; corrigir posteriormente pelo menor diff autorizado. Mudança material de owner, Core, schema, permissão, integração ou regra ⇒ `DECISION_REQUIRED`, sem implementar por suposição.
- **Encerramento:** G2 tem decisão humana explícita `ACCEPT`, `ACCEPT_WITH_RESIDUAL` ou `REWORK`; G3 tem evidência datada e autorização do Operador SSH, release, backup/rollback e smoke. Aceite não é inferido do deploy já reportado.

## 1. Primeira evidência — captura Início (2026-10-26)

**ID EVD-G2-0001**, origem: imagem enviada pelo PO na conversa; navegador desktop, URL visível `https://minhadelpi.com.br/apps/controllership-finance`, tema escuro, horário de interface 07:17 de 26/10/2026. Captura está parcialmente rolada; não prova ausência de conteúdo fora do enquadramento.

| ID | Verificação delimitada | Observado no print | Estado |
|---|---|---|---|
| G2-HOME-01 | URL do produto e renderização da página Início | URL canônica e tela Início visíveis, sem erro global de renderização no enquadramento | **PASS** (renderização visual apenas) |
| G2-HOME-02 | Topbar de navegação e identidade | Aba Início, controle Buscar e avatar/nome do usuário visíveis | **PASS** (elementos visuais apenas); ação/perfil/permnissões `TEST_NOT_RUN` |
| G2-HOME-03 | Catálogo das áreas ativas | Atalhos para Checklist, Baixas financeiras, Administração, Catálogos governados, Pendências, Pacotes e revisão, Cockpit, Estoque histórico P7 | **PASS** (existência visual); destino/funcionamento `TEST_NOT_RUN` |
| G2-HOME-04 | Acesso recente e busca interna | Barra de busca e chips de acessos recentes aparecem | **PASS** (renderização apenas); busca/filtros `TEST_NOT_RUN` |
| G2-HOME-05 | Eventos e interações | Mensagem explícita `Eventos operacionais indisponíveis nesta versão.` O código da Home usa lista `items=[]`, ou seja, placeholder intencional | `PENDING` aceite de escopo; **não** declarar eventos operacionais funcionais |
| G2-HOME-06 | Telas comuns dedicadas: Visão geral/Ajuda | `pluginRoutes.ts` no HEAD lista essas rotas como futuras; Ajuda contextual existe. Sala e expansão de Minhas tarefas adiadas pelo PO | `TO_INVENTORY`/G2: confirmar se a versão aceita as superfícies ausentes/adiadas, sem confundi-las com fluxo P1–P6 |
| G2-HOME-07 | Navegação efetiva, contraste, teclado, tema claro, mobile e F5 | Sem teste interativo na captura | `TEST_NOT_RUN` |

**Conclusão da evidência:** Home visualmente disponível `PASS` apenas para renderização/atalhos; **G2 global continua PENDING**, pois nenhuma transição de negócio foi testada. Não inventar status das rotas a partir de presença de atalhos.

## 2. Roteiro G2: demonstração guiada e registro incremental

Testar inicialmente **leitura apenas**, preferir competência existente já permitida, sem uploads/alterações em produção. Depois planejar mutações somente em cenário autorizado e com contas/artefatos adequados. Cada linha migra de `TEST_NOT_RUN` para o status do AC observado, sempre com evidência.

| Ordem | ID | Página/fluxo | Comportamento esperado e teste-base | Owner/RQ | Status de sessão |
|---|---|---|---|---|---|
| 01 | G2-01 | Início, busca e navegação | Buscar `Checklist`, resultado correto, abrir rota, F5/deep link, sem links não autorizados; revisar G2-HOME-01..07 | Home/IMP-02 | **EM ANDAMENTO** (somente renderização verificada) |
| 02 | G2-02 | Checklist da competência (P2) | Competência disponível, período correto, status `EXPECTED`/anexos separados de validação, itens/obrigatoriedade, contexto, erros de fonte, histórico | RQ-P2-01..22; ledger 23 | `TEST_NOT_RUN` |
| 03 | G2-03 | Documentos/evidências (P2) | Upload autorizado `ATTACHED != VALIDATED`, download, versões, substituição/rejeição com motivo, histórico e elegibilidade; não usar dados reais para mutação sem consentimento | RQ-P2/AC-P2-UP | `TEST_NOT_RUN` |
| 04 | G2-04 | Baixas financeiras R01/R02 | Consulta operacional por período/contexto; totais, filtros, disponibilidade; **não** chamar FINR190/DLP06R01 oficial sem paridade G5/G6 | CP01, R01/R02 | `TEST_NOT_RUN` |
| 05 | G2-05 | Estoque histórico/P7 R03 e P3 | Snapshot SB9/P7 auxiliar, filtro competência/filial, `officialP7=false` quando aplicável; nenhum falso `STOCK_CLOSED`, divergência R$ 0,01 bloqueia | R03, P3/T03 | `TEST_NOT_RUN` |
| 06 | G2-06 | Pendências P4 | Lista/estado/owner, claim/atribuição, decisões humanas e auditoria; nenhum write no ERP por sugestão | RQ-P4 | `TEST_NOT_RUN` |
| 07 | G2-07 | Pacotes e revisão P5 | Versão, destinatário, submissão, revisores/áreas, esclarecimento e C2 sem quórum vazio; somente mutação autorizada | RQ-P5, Doc 37 | `TEST_NOT_RUN` |
| 08 | G2-08 | Cockpit P1 | Eixos independentes P2/P3/P4/P5, competência preservada, blockers/fonte/freshness, sem falso sucesso | RQ-P1-01..07 | `TEST_NOT_RUN` |
| 09 | G2-09 | Administração P6 | MANAGE real, catálogo/template vigente, snapshot sem retroatividade, publicação/impacto somente sob autorização | RQ-P6 | `TEST_NOT_RUN` |
| 10 | G2-10 | Perfil, Help e UX transversal | Dados próprios, Help contextual, tema claro/escuro, desktop/mobile, teclado/foco, busca, rotas ocultas/autorização | RQ transversais + UI 30 | `TEST_NOT_RUN` |
| 11 | G2-11 | Segurança de atores/escopos | Usuário ACCESS vs MANAGE, resource_scope, actor errado, competência irmã, 401/403/404/503, fail-closed; testar com perfis habilitados sem compartilhar tokens | Doc 14, Core | `TEST_NOT_RUN` |
| 12 | G2-12 | CLARA MCP e consentimento | OAuth real, READ/KNOWLEDGE + citações, plano 2/5/20, consentimento único, ACT só sobre dados de teste, audit/read-back | Docs 94/106/107 | `TEST_NOT_RUN` (Keycloak bloqueado) |
| 13 | G2-13 | Aceite integrado Controladoria/PO | Matriz RQ/AC observável, fontes oficiais G5/G6 quando aplicáveis, limitações/decisões G1 explícitas, assinatura e escopo | G2/Doc 104 | `PENDING` |

### Dependências G1 que **não podem ser presumidas aprovadas**

T03 owner `STOCK_CLOSED`; T05 eligibility Core; relatório oficial R04+ / equivalência R01–R15 e G6; seeds P5-H/P6; documentação/eventos/outros recursos não implementados. Owner deve autorizar regra/fonte; G2 aceita apenas escopo real demonstrado e pode registrar `ACCEPT_WITH_RESIDUAL`.

## 3. Roteiro G3: auditoria de release existente e próximo ato operacional

O operador informou produção implantada em `srv-api`, código CLARA incluso na imagem, migrations V001–V014 e corpus `5541097a-8608-4470-b971-7c28b3ae6c40` (52 fontes, 1298 itens); evidência documental no [Doc 107](./107-clara-validacao-antecipada-chatgpt-release-hoje.md), **não** SSH verificado nesta sessão. G2/G3 ainda sem sign-off contemporâneo arquivado. Não assinar retroativamente.

| ID | Critério G3 | Evidência necessária | Estado |
|---|---|---|---|
| G3-01 | Aprovação/GO operador, escopo, identidade e janela | Registro original assinado/datado ou desvio formal do deploy ocorrido; autorização válida para próximas escritas | `PENDING` |
| G3-02 | SHA imutável, imagem e health atual | SSH read-only: host, serviço, digest, SHA, startup, upstream/gateway, recursos | `PENDING` |
| G3-03 | Banco e migrations | Ledger real V001–V014, dados e checksum, compatibilidade, migration runner, recovery | `PENDING` (operador relatou aplicação) |
| G3-04 | Backup e rollback | Evidência de PostgreSQL, arquivos/upload e corpus, janela e restauração viável; não fazer rollback destrutivo inferido | `PENDING` |
| G3-05 | IAM / Keycloak | Credencial admin legítima (não exposta), `--check` sanitizado, diff, escopo compartilhado, owner transversal aprovado antes de `--apply` | `BLOCKED` por credenciais/admin segundo último relatório |
| G3-06 | OAuth/MCP end-to-end | Keycloak `mcp-clara`, audience, callback real ChatGPT, token válido, tools/list, ACL, READ/citação/batch seguro | `TEST_NOT_RUN` |
| G3-07 | Persistência e business smoke | F5/login autenticado, Core RBAC, P1–P6 aceitos, proteção cross-user, docs sobrevivem, negócios com pós-condição | `TEST_NOT_RUN` |
| G3-08 | G3 sign-off e publicação | Operador identificado/assinatura, timestamp, SHA, G2 referenciado, G1/residuais, janela e evidência sanitarizada, resultado | `PENDING` |

**Regra:** nenhum novo `--apply` IAM, migration, alteração de dados ou ACT real produtivo antes de gates vigentes e owner correto. O engine Keycloak compartilhado não comprovou `--apply` restrito à CLARA; inventariar impacto em TÉO/DAVI/VISTA/DÉLIA.

## 4. Ledger de descobertas, defeitos e decisões durante o teste

| Finding | Origem | Comportamento observado | Classificação | Impacto | Owner / Próxima ação |
|---|---|---|---|---|---|
| OBS-001 | Screenshot Home (EVD-G2-0001) | Eventos operacionais mostram placeholder indisponível; código confirma `items=[]` | `PENDING` decisão de aceite V1 | Sem eventos/alertas nessa seção | PO confirma se limitação aceita no escopo atual; expansão de Minhas tarefas/Sala diferidas |
| OBS-002 | Código/manifest | Visão geral dedicada e Ajuda dedicada listadas como futuras em `pluginRoutes.ts`; Help contextual existe | `TO_INVENTORY` / não inferir erro apenas da captura | Padrão de páginas comuns vs prioridade de P1–P6 | G2 validar escopo e classificar residual, não ampliar sem owner |
| OBS-003 | Doc 107 | Deploy reportado antes de sign-offs G2/G3 comprovados | `EXECUTION_DRIFT` documental | Governança do release | Operador/PO apresentar autorização original se existir, ou registrar desvio sem retrodatação |
| OBS-004 | Doc 107 | Keycloak `mcp-clara` sem provisionamento autenticado; admin credenciais testadas falharam | `BLOCKED` | ChatGPT não conectável via OAuth | Owner IAM/Operador: acesso legítimo, `--check` e diff antes de apply autorizado |

### Modelo de registro por interação

```text
TEST_ID:
DATA_HORA:
AMBIENTE/ROTA:
PERFIL/COMPETÊNCIA:
AÇÃO:
ESPERADO (RQ/AC):
OBSERVADO:
EVIDÊNCIA:
RESULTADO: PASS | FAIL | PENDING | INCONCLUSIVE | TEST_NOT_RUN
SEVERIDADE / IMPACTO:
OWNER:
AÇÃO DE CORREÇÃO / DECISION_REQUIRED:
```

## 5. Sign-offs — **não concedidos por este documento**

```text
G2_SIGNOFF: PENDING
BUSINESS_OWNER:
PO_DECISION: PENDING
G2_ACCEPTED_SCOPE:
G2_RESIDUALS:
G2_EVIDENCE_REF:
G2_DATE:

G3_SIGNOFF: PENDING
AUTHORIZED_SSH_OPERATOR:
PRIOR_DEPLOY_AUTH_EVIDENCE: PENDING
G3_TARGET_RELEASE_SHA:
BACKUP_RESTORE_EVIDENCE:
KEYCLOAK_IMPACT_APPROVAL:
SMOKE_AUTHENTICATED:
G3_OPERATOR_DECISION:
G3_DATE:

CLARA_CHATGPT_CONNECTION: TEST_NOT_RUN
CLARA_MCP_OAUTH: BLOCKED
NEXT_GUIDED_ACTION: Na página Início, pesquisar "Checklist" em "Caminhos e funcionalidades", abrir "Checklist da competência" e enviar captura do resultado com dados sensíveis ocultos.
```

**Este documento começa o ciclo de homologação, não o encerra. Toda evidência nova da conversa será adicionada por commit antes de mudar o estado do respectivo critério.**



## 6. Rodada 2 — Busca, checklist setembro/2026 e template mestre (26/10/2026)

**Origem da evidência:** sequência de **9 capturas de tela** enviada pelo testador na conversa, navegador Chrome no Portal produtivo `minhadelpi.com.br`, ~07:26–07:27 BRT, 2026-10-26. As imagens foram observadas nesta conversa, **não armazenadas no repositório**. Em todas, deve-se distinguir a URL visível no navegador dos endpoints/requests do DevTools. O teste demonstra visualmente componentes e respostas HTTP mostradas, mas não inspeciona os corpos/headers de requests nem trilhas backend. **Nenhuma mutação de negócio foi autorizada por este registro**; existe na sequência POST de tentativa de abertura recusado (409), sem competência aberta comprovada.

### Achados verificáveis, por tela e critério

| ID / Teste | Esperado | Evidência observada | Status estrito / Resultado | Próximo aceite |
|---|---|---|---|---|
| EVD-G2-0002 / G2-HOME-04A | Busca global encontra rota válida | `Ctrl+K`/palette com busca `che` mostra `Checklist da competência` e `Administração do checklist` | **PASS** para filtro/renderização da palette; busca própria do hub não verificada | Abrir resultado por seleção ou atalhos |
| EVD-G2-0003 / G2-01 | Clique leva a rota do checklist | URL `/apps/controllership-finance/closing/checklist`; hero da Central e seletor de competência `outubro de 2026`; lista vazia, texto `Nenhuma competência aberta` | **PASS** para roteamento/renderização e estado vazio; consulta de itens `TEST_NOT_RUN` | Selecionar competência existente ou validar ausência |
| EVD-G2-0004 / G2-02 | Deep link `2026-09` preserva contexto | URL `/closing/checklist/2026-09`; texto `A competência 2026-09 ainda não foi aberta` e botão `Abrir competência` | **PASS** no deep link, detecção de competência ausente; P2 itens `PENDING` | Publicação de template vigente é pré-condição para abrir competência |
| EVD-G2-0005 / G2-02 | Abrir competência apenas com template vigente | Após tentativa, POST `/closing/competences` no DevTools = **409 Conflict**; mensagem backend/UI `Não existe versão publicada vigente para esta competência`; GET de `items` anteriores = **404**, e GET `competences` aparece em rede | **PASS** da proteção contra abrir sem versão publicada (resultado negado); **BLOCKER da homologação funcional** até template aprovado/publicado. `404` de itens é compatível com competência inexistente e frontend trata `competence_not_opened` separadamente; não é evidência isolada de bug | Confirmar estado/validação das versões antes de publicar. Nunca publicar por iniciativa do teste |
| EVD-G2-0005b / OBS-005 | Mensagem distinguir falha técnica vs. impedimento de negócio | Banner `Falha de comunicação` para condição 409 com mensagem funcional `Não existe versão publicada vigente` | **FAIL UX**, severidade `MINOR`, não é prova de falha de infraestrutura | Tratar 409/domínio como `Pré-requisito pendente: publique a versão aprovada do checklist`; preservar HTTP 409 e backend fail-closed |
| EVD-G2-0006 / G2-09 | Administração lista versões corretamente | Página `/closing/admin` lista template `monthly-closing-checklist`, versão **v1 Rascunho**, **53 itens**, sem datas de vigência/publicação; botão `Criar versão rascunho` inativo, pois existe rascunho | **PASS** apenas para leitura/estados/lista de versão; lifecycle submit/review/publish `TEST_NOT_RUN` | Revisão de conteúdo e decisão owner antes de submissão/publicação |
| EVD-G2-0007 / G2-09 | Detalhamento read-only dos itens do draft | Tela `Itens — v1 (Rascunho)`, tabela com **53 registros**, por exemplo CK-E-01..CK-E-10, folha Eletrônico, origem Fonte externa, destinatário Contábil, Obrigatório, validação Por anexo | **PASS** para apresentação/paginação da tabela vista; **não** é aceite de correção/totalidade de 53 itens, nem prova de persistência | Controladoria valida completude, destinatário, obrigatoriedade, fonte, escopo e correspondência |
| EVD-G2-0008 / G2-09 | Formulário de item exibe metadados controlados | Modal `Editar item CK-E-03` com chave, nome `Aplicações financeiras — conta 02`, ordem 3, folha Eletrônico, origem Fonte externa, Contábil, Obrigatório, Matriz, `Por anexo`, referência TOTVS `R13`; campos adicionais abaixo da dobra | **PASS** para abertura da UI/form pré-preenchido; mudança, gravação, permissões efetivas e referência oficial R13 `TEST_NOT_RUN/TO_INVENTORY` | Não usar `Salvar rascunho`, `Enviar para revisão` ou `Publicar` sem aceite da matriz |
| EVD-G2-0009 / Console | Ausência de exceções no console | Nas capturas de Home/Admin, console indica `No errors`; na navegação checklist de setembro, mensagens de GET 404 e POST 409 são visíveis | **INCONCLUSIVE** para ausência geral de erros/qualidade; códigos 404/409 requerem interpretação funcional, não transmutar em erro técnico sem corpo | Capturar error code de resposta se houver ambiguidade, evitando tokens/secrets |

**Correlação técnica pelo código do HEAD nesta sessão:** `plugins/controllership-finance/src/features/closing/ClosingChecklistPage.tsx` mapeia `competence_not_opened` para estado `not_opened`; `openCurrentPeriod` utiliza `openCompetence(activePeriod)` e exibe erro do servidor; `plugins/controllership-finance/src/api/competencesApi.ts` chama a BFF `GET|POST /closing/competences`; `plugins/controllership-finance/src/app/cfFeedbackUi.tsx` faz fallback para título genérico `Falha de comunicação` em erros sem correspondência especial, inclusive 409 de regra de negócio. `ChecklistAdminPage.tsx` modela etapas de rascunho/revisão/publicação com vigência; salvar rascunho **não** publica.

### Findings e decisões exigidas

| Finding | Severidade | Evidência | Owner | Próxima ação |
|---|---|---|---|---|
| **OBS-005 — checklist de setembro bloqueado sem publicação** | **BLOCKER para G2-P2 operacional**, proteção do backend consistente | Print `v1=Rascunho/53 itens`, sem vigência; POST abertura 409 | Controladoria/PO (conteúdo, competência alvo e vigência); owner P6 template | Revisar versão 1 item a item conforme contrato/planilha, decidir vigência para competência de homologação **apenas com autorização**, depois submeter/revisar/publicar pelo fluxo governado; não fazer write automaticamente |
| **OBS-006 — erro UX confunde regra com falha de comunicação** | MINOR | 409 com banner “Falha de comunicação” | MFE `controllership-finance` | Backlog de correção tipada, sem alterar a proteção 409; não bloqueia revisão do template |
| **OBS-007 — referência R13 em CK-E-03 sem paridade** | `TO_INVENTORY` | Form edit mostra `R13`; não houve comparação oficial | Owner das fontes/R13 e Controladoria | Conferir mapeamento correto antes de homologar/paridade; sem afirmar erro ou acerto da referência |
| **OBS-008 — nenhuma competência aberta na lista** | `PENDING` | Home do checklist sem registro, deep route 2026-09 não aberta | P2/P6/Controladoria | Distinguir falta de setup de defeito de implementação; G2 de workflow fica sem prova até haver cenário governado |

### Rebaseline do G2 e próxima etapa

- **G2-01 (Home):** `PASS` **parcial** para busca global, atalho, roteamento e estado vazio. Tema claro, teclado abrangente, mobile, erro cross-user, busca dentro do hub continuam `TEST_NOT_RUN`.
- **G2-02 (P2):** **BLOCKED_BY_PRECONDITION** — template v1 ainda `DRAFT`, nenhuma versão publicada vigente para 2026-09, não abrir competência de forma forçada. Estado correto da recusa documentado; erro de título UX separado.
- **G2-09 (Admin/P6):** `PASS` **parcial** para listagem de 53 itens, abertura de modal e campos; DRAFT→REVIEW→PUBLISH, revision e audit não provados. A permissão MANAGE não é comprovada apenas pela visibilidade da UI.
- **G2-03 (evidências), P3/P4/P5/C2:** `TEST_NOT_RUN`, bloqueados no cenário de competência não aberta ou dependências específicas; seguir leituras independentes quando possível.
- **G3:** permanece `PENDING` e sem novo evento SSH nesta sessão.

**Próxima ação guiada e segura, somente leitura:** fechar modal de edição sem salvar; em `Administração do checklist mestre`, abrir **`Eventos de auditoria`** e capturar seu conteúdo para comprovar histórico de template. Opcionalmente examinar item/metadados de um trecho representativo do rascunho, sem enviar para revisão/publicar. Pergunta de aceite funcional ao PO/Controladoria: **esta versão v1 com 53 entregáveis já foi conferida e autorizada para publicação, e qual competência deve ser a primeira?** Não inferir resposta sem o owner.
