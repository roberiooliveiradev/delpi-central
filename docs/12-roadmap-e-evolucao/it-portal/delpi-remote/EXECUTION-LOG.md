# Delpi Remote | Diario de execucao e handoff

Este arquivo registra o **estado real verificado**. A cada tarefa: adicionar entrada nova, preservar historico, referenciar evidencias, alterar o roadmap em `README.md` e atualizar a issue #179.

## 2026-11-13 | Inicio de projeto, pacote G0-DOC

**Pedido autorizado:** iniciar o desenvolvimento conforme arquitetura aprovada pelo responsavel de TI; documentar cada tarefa no repositorio para permitir continuidade entre chats.

**Inspecionado:** `AGENTS.md`; `plugins/it-portal/README.md`; manifesto `0.3.2`; app React; API FastAPI; `it-portal-api/README.md`; migrations V001 a V008; controle Windows restrito; runbook de servidores Windows. O repositorio foi consultado via conector GitHub, **sem checkout local**.

**Implementado nesta tarefa:**
- Ponto de entrada canonico `delpi-remote/README.md` com roadmap, estados e regras de handoff.
- ADR-001/arquitetura, isolamento do motor remoto, identidade, agente, API e requisitos de UX.
- Matriz de ameacas, permissao minima e gates de seguranca.
- Contrato para o primeiro incremento de inventario G1.

**Sem mudanca operacional:** nao instalamos MeshCentral, nao cadastramos maquinas, nao habilitamos acesso remoto, nao alteramos firewall, Keycloak, banco nem containers. Nenhum teste de producao foi executado. Nao existe validacao do motor nesta entrega.

**Validacao disponivel:** leitura posterior dos arquivos no GitHub. Revisao de seguranca e testes de integracao continuam pendentes.

**Risco residual:** licenca, versao, maturidade, compatibilidade SSO/embed, Windows/UAC, privacidade e custo de operacao dependem de avaliacao e prova de laboratorio. Nao inferir funcionalidade completa do motor pela documentacao.

**Proxima tarefa:** G1-DOM (validacao pura de dados de estacao) e G1-API, sem coletor/controle remoto; registrar resultados aqui.


## 2026-11-13 | G1-DOM | codigo inicial do inventario

**Objetivo:** iniciar implementacao sem alterar runtime, isolando regras puras de estacoes.

**Arquivos novos:** `it-portal-api/it_portal_app/domain/workstations.py` e `it-portal-api/tests/test_workstations_domain.py`.

**Implementado:** tipo de estacao; normalizacao de hostname/IP; unidade, situacao e limites; rejeicao de segredos em campos livres; `PC-0001` como codigo publico; exclusao intencional de permissao de controle remoto do cadastro.

**Testes feitos:** `python -m py_compile` local e `pytest -q tests/test_workstations_domain.py`: **17 testes aprovados em ambiente isolado com stubs de dependencias**. Testes da API completa, Postgres real, workflow de PR e deploy **NAO** foram executados; estes resultados nao equivalem a homologacao.

**Producao:** nada instalado, nenhum banco alterado, nenhuma rota adicionada e nenhum dispositivo tocado.

**Risco:** verificar modulo com dependencias reais e suite completa antes de G1-API/deploy. Nao marcar G1-DOM como validado ate isso ocorrer.

**Rollback:** reverter somente os dois arquivos novos, se necessario; nenhum estado persistido.

**Proximo passo:** executar suite real e criar migration nova, repositorio, rotas e RBAC de `workstations` (G1-API), sem acesso remoto.

## 2026-11-13 | G1-API | backend versionado, aguardando verificacao integrada

**Objetivo:** cadastro de computadores corporativos separado dos servidores e sem controle remoto.

**Arquivos:** V009__workstations_inventory.sql; application/workstation_ports.py e workstation_service.py; postgres_workstation_repository.py; workstations_routes.py; authz, dependencies, schemas, main, capabilities, manifesto 0.3.3, tipos TypeScript e testes HTTP/contrato/Postgres.

**Implementado:** GET/POST /workstations; GET/PUT /workstations/{id}; POST archive/restore; GET /history. Lista com filtros e paginacao, hostname unico por unidade entre ativos, revision otimista, validacao de payload, rejeicao de segredos, eventos transacionais com autor e tipo workstation, sem obrigacao de server_id. Nao existe agente nem controle remoto nesta entrega.

**Permissoes:** it-portal.computers.view e it-portal.computers.manage, separadas dos papeis de servidor. Escritas usam authorize_write com RBAC fresh e falha fechada.

**Testes locais executados:** sintaxe compilada dos modulos novos em ambiente de validacao; teste isolado do WorkstationService com repositorio fake (CRUD, revisoes, filtros, duplicatas, auditoria) passou; G1-DOM: pytest local com dependencias isoladas 19 passed (incluidos campos name/operating_system). Verificacao do WorkstationService com fake PASS. Leitura de retorno do GitHub confirmou manifesto 0.3.3, rota registrada, DTO, V009 e diario. GitHub nao exibiu checks de CI associados ao commit de implementacao. Suite HTTP real do projeto, Postgres real e CI do GitHub nao foram executados neste ambiente. O G1-API permanece EM REVISAO.

**Producao:** NENHUMA migration executada, nenhum usuario cadastrado ou permissao configurada pelo agente, nenhum deploy e nenhuma maquina modificada. Nao interpretar commit como homologacao.

**Revisao obrigatoria:** suite completa da API; Postgres descartavel V001..V009; manifesto e regresao de servidores. Nova versao do manifesto 0.3.3 deve ser registrada estruturalmente no Core antes de atribuir RBAC.

**Risco e rollback:** deploy com migracoes no startup deve ter backup e janela aprovada; se V009 for aplicada nao editar/apagar migrations nem apagar registros/auditoria; bloquear a feature por RBAC, restaurar imagem anterior com procedimento canonicamente revisado. Sem migration aplicada, reverter apenas o commit.

**Proximo passo:** validacao integrada do G1-API e, apos aceite, G1-UI. G0-SEC permanece pendente para a tecnologia de acesso remoto.

## 2026-11-13 | G1-UI | interface de computadores preparada para revisao

**Decisao:** nao executar deploy apenas de G1-API; combinar backend e frontend apos verificacao integrada, para evitar exposicao de API/migration sem fluxo visual e sem testes completos.

**Objetivo:** integrar o cadastro de workstations a UI do Portal de TI sem controlar maquinas.

**Arquivos criados:** `plugins/it-portal/src/features/workstations/WorkstationsPage.tsx`, `WorkstationFormModal.tsx`, `WorkstationDetailPage.tsx`, `WorkstationsPage.test.tsx`; `docs/12-roadmap-e-evolucao/it-portal/delpi-remote/G1-UI.md`.

**Arquivos alterados:** cliente `itPortalApi.ts`, queryKeys, rotas, App, menu/command palette, Home (acesso rapido), textos, historico, manifesto `0.3.4`, testes de rotas e fixtures `Capabilities`, README do plugin, roadmap e contrato.

**Funcionalidade:** lista paginada e filtravel, busca por nome/hostname/IP/setor, cadastro/edicao com erros da BFF, arquivar/restaurar com confirmacao, ficha somente leitura quando arquivada, historico auditavel. Menu e rotas condicionados a `can_view_computers`, escrita a `can_manage_computers` mais RBAC do backend.

**Seguranca:** nao criar botoes de acesso remoto, nao exibir monitoramento inventado (sem agente), nao expor telas ou arquivos, nao criar nova permissao de controle remoto.

**Testes:** casos de Vitest escritos para negacao de acesso, leitura, formulario, arquivamento, historico e ausencia de conexao remota. Suite real com `node_modules` do projeto, `npm run lint`, `npm run build` e integracao Postgres **NAO EXECUTADAS nesta entrega**; nao declarar homologacao/CI verde. Validacao estatica de integracao por leitura de codigo e read-back apos commit.

**Deploy:** NAO executado nem aprovado; a migration V009 e o manifesto 0.3.4 dependem de backup/revisao e registro estrutural. Nenhuma maquina sofreu alteracao; sem agente nem MeshCentral.

**Risco/rollback:** discrepancias do Core/manifesto e da base exigem teste conjunto. Se nao implantado, reverter commit de UI com auditoria Git. Se implantado, nunca editar V009 ja aplicada; revogar permissoes, reverter imagens de API/MFE e preservar dados e logs conforme runbook.

**Proximo passo unico:** validar G1-API + G1-UI com dependencias reais e banco descartavel, corrigir falhas, homologar e preparar deploy conjunto. Em seguida G2-AGENT (inventario read-only), nao acesso remoto.

## 2026-11-13 | G1-RELEASE | publicacao autorizada, execucao pendente

**Autorizacao:** responsavel de TI confirmou a publicacao do inventario para testar no Portal de TI.

**Verificado:** script canonico `infra/scripts/up-prod-sequential.sh`, `AGENTS.md`, Compose com `it-portal-api` e `it-portal`, `V009` e manifesto `0.3.4`. O Core exige registro estrutural de nova versao para rota/permissao.

**Validacao local (copia isolada atualizada):** `19 passed` para testes de dominio G1; smoke `test_local_service.py` passou. Suite HTTP, UI e banco real **nao executados**, CI do main nao cobre esse incremento via workflow `pull_request` apenas.

**Acao:** runbook `G1-RELEASE.md` criado com preflight, backup, ordem de deploy, registro no Core, teste de permissao e plano de rollback. **Nao** ha sessao SSH remota neste chat para executar comandos no srv-api.

**Estado real:** NAO implantado, nao testado em producao. Nada alterado em servidores, banco nem no Core por esta etapa.

**Proximo passo:** operador com acesso SSH realiza deploy segundo runbook, confere saude, migration e registro 0.3.4; retorna evidencias para atualizar este diario e somente entao marcar G1-DOM/ API/UI IMPLANTADOS ou EM CORRECAO.

## 2026-11-13 | G1-RELEASE | backup informado e alerta de collation

**Evidencia comunicada pelo operador:** backup logico do schema `it_portal` em `plugins_hub` criado em arquivo privado e validado por listagem `pg_restore -l`; caminho nao incluido no repositorio publico por seguranca. Isto verifica legibilidade do catalogo do arquivo, **nao** constitui restauracao integral testada.

**Aviso observado:** `database "plugins_hub" has a collation version mismatch` com versao registrada **2.41** e versao de runtime **2.36**. O aviso e de metadados de ordenacao do banco compartilhado, nao confirma falha no backup nem migration V009. Ha risco em indices e comparacoes de texto que precisa ser inspecionado e reparado com janela propria.

**Orientacao de seguranca:** nao executar `ALTER DATABASE ... REFRESH COLLATION VERSION` isoladamente; PostgreSQL recomenda reconstruir objetos afetados, por exemplo via REINDEX planejado, **antes** de atualizar a versao registrada. Nao executar REINDEX geral no banco compartilhado no meio do deploy G1. Fazer leitura de `pg_database_collation_actual_version` e planejar revisao independente com infraestrutura.

**Estado:** backup relatado, deploy **ainda sem evidencia de execucao**, sem alteracao remota pelo assistente. Proximo passo do G1: observar saude da API e aplicacao de V009 na publicacao autorizada, depois MFE, manifesto 0.3.4 e teste por usuario. Registrar resultados sem dados de acesso.

## Template obrigatorio das proximas entradas

```markdown
## YYYY-MM-DD | ID da tarefa | resultado
**Objetivo:**
**Arquivos alterados:**
**Commit/issue:**
**Testes executados e evidencias:**
**Estado de producao / implantacao:**
**Riscos e limitacoes:**
**Rollback:**
**Proximo passo unico:**
```
