# Documento 97 — Decisões do PO e solicitação de GO transversal — P6-MIN + P2-READ

**Data:** 2026-10-24. **Referência de base GitHub:** `3039f729c89d8111ea4a8b120e34b529c5d75020` (HEAD antes da publicação; revalidar HEAD e worktree no executor).  
**Produto:** Portal Controladoria & Finanças · Central de Fechamento · PROC-0072.  
**Estado:** **PO_DECISIONS_APPROVED / TRANSVERSAL_GO_REQUEST_PREPARED / IMPLEMENTATION_AUTHORIZED=NO**.  
**Escopo da aprovação:** somente decisões de **produto, arquitetura e desenho contratual** abaixo. **Nenhum GO para código, migration, manifesto, banco, API ou UI.**

## 1. Decisões expressas do PO (não reabrir por preferência)

- **CP-D01=A (já aprovada):** persistência do próprio bounded context `controllership-finance-api`, isolada no schema `controllership_finance` do `postgres-plugins`, conforme padrão vigente e inventário do [doc 96](./96-ciclo3-gate-contrato-e-persistencia-p6-min-p2-read.md).
- **CP-D04=A — seed inicial `DRAFT` (aprovada nesta rodada):** inserir em migration versionada o template v1 e os **53 itens do checklist** com estado **DRAFT**, nunca `PUBLISHED` automático. A Controladoria com `manage` efetivo **e** escopo administrativo publica a versão somente após revisão governada. Sem publicação, abrir competência falha explicitamente com `no_published_template`; não criar snapshot vazio, bypass ou auto-publicação para melhorar UX.
- **CP-D05=A — administração mínima somente por API (aprovada nesta rodada):** o primeiro slice inclui operações administrativas restritas de listar/criar/editar rascunho, publicar e inativar prospectivamente, **sem página administrativa P6**. As ações poderão ser operadas por cliente governado autenticado; não utilizar script direto no banco, bypass S2S ou `manage` como equivalente a `access`. A interface P6 completa segue etapa posterior do roadmap.
- **Objetivo de P2-READ:** abrir competência mensal de forma idempotente a partir da versão publicada/vigente e apresentar **itens `EXPECTED`** com proveniência, filtros, detalhamento, F5/deep link, estados honestos e Ajuda sincronizada. **Anexar, validar, automatizar relatórios, operar P5 e tools CLARA permanecem fora deste slice.**
- **Permissões:** somente `controllership-finance.access` e `controllership-finance.manage` neste slice. A nova capability e página de histórico da Contabilidade/DRE continuam aprovadas como produto, mas **adiadas** no [doc 91](./91-ciclo3-contabilidade-acesso-documentos-historicos-gate.md).

**Efeito da decisão:** encerra as duas escolhas residuais do [doc 96 §9](./96-ciclo3-gate-contrato-e-persistencia-p6-min-p2-read.md). Não transforma automaticamente os contratos HTTP/DDL candidatos em runtime homologado.

## 2. Contrato candidato para ratificação no gate

**Owner:** `controllership-finance-api` (Clean Architecture; domain/application/ports/adapters). Core continua authority de effective permissions e identidade; MFE acessa somente BFF; **sem chamadas api-delpi do browser**.

**Persistência proposta e padrão verificado no doc 96:** `psycopg`, schema isolado, migrations versionadas com SHA-256/runner gated, `revision` otimista, unicidade/idempotência, auditoria append-only e testes reais em PostgreSQL isolado. Entity model candidato: `checklist_template`, `checklist_template_version`, `checklist_template_item`, `monthly_competence`, `competence_checklist_item`, `closing_audit_event`. Esquema físico, chaves, constraints, envelopes HTTP, operationIds, tx boundaries e migration/rollback devem ser reconciliados com o HEAD no gate transversal; usar as propostas do doc 96 como baseline, não como convite para inventar outra arquitetura.

**P6-MIN:** template v1 DRAFT com 53 itens; `publish` autorizado e auditado, com vigência; versões publicadas imutáveis; inativação prospectiva e concorrência `stale_revision`.

**P2-READ:** `POST /closing/competences` cria snapshot atômico do template publicado; replay do mesmo período deve retornar a mesma competência sem duplicidade; `GET` lista competências/itens e detalhe; todos os itens iniciais são `EXPECTED`. Falta de template publicado devolve erro tipado, não 200 enganoso.

**AuthZ e UX:** `access` para leitura/abertura mediante regras de recurso, `manage` **e escopo administrativo** para operações do template, deny em falha Core; rota nova do checklist no manifest **somente após GO**, com Help, mobile/desktop, light/dark, teclado/foco e componentes `@delpi/plugin-ui`.

## 3. Solicitação específica de GO transversal — ainda NÃO concedido

**GO solicitado para futura deliberação:** `CF-C3-P6-MIN-P2-READ-RUNTIME-GO-001`.

**Limites candidatos da futura autorização:** exclusivamente migrations/runner/config/compose da BFF; domínio/aplicação/persistência de template e competência; endpoints P6-MIN e P2-READ; nova rota do checklist no MFE/manifest usando permission `.access`; Help e testes do slice. **Não** adicionar permission, funcionalidade de upload/validação, P3/P4/P5, exportação de relatórios oficiais, CLARA MCP, página Contabilidade, escrita no ERP ou deploy de produção.

**Pré-condições objetivas para emitir GO:**
1. Executor atualiza `HEAD`, branch e `git status`; valida autoridades, .cursor, owners e impactos em producers/consumers.
2. Revisão transversal final dos contratos propostos no doc 96 e ajustes necessários sem alterar decisões do PO; declarar `CONTRACT_FREEZE=PASS` apenas com evidence.
3. Trilha de migrations e rollback, startup gated, isolamento de schema, seed 53/53 mapeado à fonte sanitizada, sem dados pessoais ou bancários brutos no repo.
4. Resolver discrepâncias entre `DRAFT` como estado inicial, `publish` por API e abertura subsequente; definir operador de publicação/escopo administrativo de forma comprovada (não pressupor conta/grant). Nenhum `POST competence` faz publish implícito.
5. Matriz RQ/AC de [doc 23](./23-ledger-rq-ac-testes.md), incluindo proposta RQ-P2-13/14; positive/sibling/negative, PG real, idempotência simultânea, falhas Core/DB, publish sem scope, snapshot antigo preservado.
6. Reuso `@delpi/plugin-ui`, rota/manifest limitados ao slice, Help sincronizada e testes de F5/desktop/mobile/teclado/tema.
7. Evidência do gate transversal e decisão posterior **expressa** do PO: `IMPLEMENTATION_AUTHORIZED=YES / SCOPE=P6-MIN+P2-READ`, SHA e boundary. Aprovação documental **não** substitui autorização runtime.

**Release/deploy:** gate operacional separado, independentemente do GO de código. Migration aplicada, endpoint HTTP 200 ou teste verde isolado nunca provam business outcome.

## 4. Checkpoints obrigatórios do próximo incremento (após GO)

| Checkpoint | Prova de resultado | Estado nesta decisão |
|---|---|---|
| `CP02-DB` | Migrations aplicadas em Postgres de teste; schema isolado; rollback/recuperação testados; não reseta dados | PLANNED / TEST_NOT_RUN |
| `CP02-P6` | Seed DRAFT 53/53; sem published inicial; admin autorizado publica; usuário ACCESS-only recebe 403, `manage` sem scope recebe 403; concorrência e audit | PLANNED / TEST_NOT_RUN |
| `CP03-P2` | Com versão publicada vigente, abrir competência cria snapshot com 53 itens `EXPECTED`; POST repetido idem; nova versão não altera competência antiga; filtro/deep link/Help | PLANNED / TEST_NOT_RUN |
| `CP03-SECURITY` | Sem `access`, sem Core, outro recurso, DB fora → negação/erro tipado fail-closed; MANAGE != ACCESS | PLANNED / TEST_NOT_RUN |
| `CP03-UX` | UI usando plugin-ui, responsividade, dark/light, teclado/foco, F5, estados honesto e Help no mesmo diff | PLANNED / TEST_NOT_RUN |
| `CP03-INTEGRATION` | Testes unit/domain, contrato producer/consumer, PG real, MFE e smoke autorizado; leitura posterior do snapshot e audit no SHA final | PLANNED / TEST_NOT_RUN |

CP00 do [doc 95](./95-ciclo3-cp00-cp01-rebaseline-e-brief-primeiro-slice-p2.md) permanece PASS com residual; CP01 possui testes operacionais PASS e equivalência oficial FAIL, sem E2E humano concluído. Não promover CP02/CP03 por documentação.

## 5. Decisões/residuais fora do GO

`CP-D02`: responsáveis/validadores/regras de satisfação ainda `TO_INVENTORY` da Controladoria — não bloquear leitura honesta P2, mas bloquear validação C05.  
`CP-D03`: CK-E-27 faturamento filial continua sem produtor identificado; preservar item no checklist sem inventar automação.  
`CLARA-D01=B`: capacidade futura PREPARE/ACT mediante confirmação expressa, mas sem tools novas.  
`P5 C2`: aceites humanos e destinatário DRE somente leitura exigem reconciliação quando o P5 entrar no gate.  
`G6 R01..R15`: 0/15 aceites funcionais, não alterado por P2-READ.

## 6. Pedido de execução subsequente

**Próxima rodada ao executor:** `CF-C3-P6-MIN-P2-READ-TRANSVERSAL-GO-REVIEW-001`. Modo READ/VERIFY/REVIEW/DOCUMENT_ONLY. Produzir avaliação objetiva de readiness do gate transversal com `GO_RECOMMENDED` ou `NO_GO`, evidências e SHA, e texto exato da solicitação de autorização PO. Se não houver bloqueios, GPT Arquiteto apresenta GO ao PO. **Não implementar runtime nem emitir autorização em nome do PO.**

**Veredito desta rodada:** `ACCEPT_WITH_RESIDUAL` para decisões de produto e preparação do pedido; `IMPLEMENTATION_AUTHORIZED=NO` para execução.

---

## 7. Adendo — Decisões PO sobre P2-Upload (`CF-C3-P2-UPLOAD-DECISIONS-CONTRACT-CLOSURE-001`)

`DECISION_SOURCE=PO_EXPLICIT` · `DECISION_STATUS=PO_APPROVED` · `IMPLEMENTATION_AUTHORIZED=NO` · `DEPLOY_PRODUCTION_AUTHORIZED=NO`. Registro literal das decisões; contratos e consequências consolidados no [doc 103](./103-ciclo3-p2-upload-contract-gate.md), Adendo §A–§E.

- **D-U1=A — Owner-editability:** substituição de evidências somente pelo uploader original ou usuário elegível com `controllership-finance.manage`. Sempre `effective permissions` do Core + `access` conforme contrato vigente + resource scope/ownership + business rules. `manage` não concede bypass.
- **D-U2=A — Limites e formatos:** 25 MB/arquivo. Allowlist V1: PDF, imagens e planilhas XLS/XLSX/CSV (doc 103). OFX/QIF/TXT bancário e demais formatos **não** aprovados na V1 — preservar inventário com TÉO/Controladoria. Validação defensiva por conteúdo real + extensão + MIME, nunca só declaração do cliente.
- **D-U3=A — Auditoria de downloads:** `DOCUMENT_DOWNLOADED` para downloads autorizados — ator UUID, recurso, versão, competência, resultado, timestamp e contexto de autorização; tentativa/autorização/entrega separadas (sem sucesso falso); sem bytes, tokens ou dados sensíveis.
- **D-U4=A — Retenção V1:** sem exclusão automática de evidências de negócio na V1; sem prazo formal inventado; política corporativa de retenção permanece pendência própria — a opção A **não** é retenção perpétua juridicamente aprovada. Limpeza de temporários/órfãos é especificada separadamente da retenção de evidências válidas e não está ativa neste gate.
- **D-U5=A — Attachment role inicial:** `attachment_role=generic` explícito na V1; sem papéis inventados por item. E05 (catálogo/obrigatoriedade real) permanece pendente — bloqueia validação C05, não o upload.
- **D-U6=A — Dois níveis de vínculo:** evidências vinculadas diretamente à competência **ou** a um item do snapshot, com integridade referencial e identificação inequívoca do tipo de vínculo; vedada referência a item de outra competência.

## 8. Adendo — D-U7 aprovada no GO de implementação (`CF-C3-P2-UPLOAD-IMPL-GO-001`)

`DECISION_SOURCE=PO_EXPLICIT` · `DECISION_STATUS=PO_APPROVED` · `IMPLEMENTATION_AUTHORIZED=YES` (SLICE-1_ONLY) · `PRODUCTION_DEPLOY_AUTHORIZED=NO` · `PRODUCTION_MIGRATIONS_AUTHORIZED=NO` · `SLICE-2_AUTHORIZED=NO`. Substitui o status anterior `DECISION_REQUIRED` registrado no doc 103, Adendo §B, e no doc 17 — a recomendação A do rework foi adotada pelo PO sem alterações.

- **D-U7=A — Idempotência de upload (padrão supplies-api):** `idempotency_key` **obrigatória** no corpo do request (campo `idempotency_key` do multipart — jamais header HTTP inventado); unicidade `UNIQUE(competence_id, idempotency_key)`; `request_hash` persistido por registro; replay idêntico retorna a evidência original **sem duplicação** (`deduplicated`); payload divergente com a mesma chave ⇒ HTTP 409 `idempotency_conflict`; **sem TTL** — registros de idempotência são persistentes; hash de conteúdo **não** colapsa evidências distintas (o mesmo binário pode vincular-se a itens diferentes).
