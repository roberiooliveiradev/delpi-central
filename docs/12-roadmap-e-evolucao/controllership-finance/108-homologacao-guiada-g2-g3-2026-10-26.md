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
