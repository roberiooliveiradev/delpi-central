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

## 2026-11-13 | G1-RELEASE | backend e frontend reiniciados, migration verificada

**Evidencia fornecida pelo operador (nao executada remotamente pelo assistente):**
- PostgreSQL `it_portal.schema_migrations`: version **9**, nome `V009__workstations_inventory.sql`, aplicada em **2026-11-13 15:38:05.181431-03**.
- `SELECT to_regclass('it_portal.workstations')` retornou `it_portal.workstations` (tabela efetivamente criada).
- Script de publicacao do frontend retornou `=== Concluido ===`; `delpi-it-portal` com `Up 2 seconds` na listagem, evidenciando recriacao do container.
- `delpi-it-portal-api` com `Up 31 minutes (healthy)`. Os logs anteriores mostraram respostas HTTP 200 em /health e operacoes do agente de controle de servicos Windows.
- Aviso de mismatch de collation em `plugins_hub` persistiu: 2.41 registrada vs 2.36 do SO; pendencia independente a ser agendada com infraestrutura.

**Estado atual verificado:** deploy do backend/frontend relatado como concluido pelo script; migration V009 e estrutura de tabela comprovadas. Nao ha ainda teste fim-a-fim do frontend, prova de versao ativa 0.3.4 no Core, confirmacao de asset servido ou validacao RBAC. **G1 ainda em homologacao funcional, nao marcar concluido.**

**Proximo passo unico:** no Portal Admin publicar e verificar manifesto **0.3.4** pelo fluxo de nova versao estrutural, atribuir permissoes `it-portal.computers.view` e `it-portal.computers.manage` aos perfis aprovados e realizar cadastro de uma maquina de teste, lista, edicao, arquivamento/restauracao e historico. Testar bloqueio sem permissao. Se possivel confirmar remoteEntry.js (HTTP 200 e JS) e checks de API.

**Rollback:** nao apagar V009 nem objetos; revogar as permissoes novas e restaurar imagens conforme o runbook se houver falha.

## 2026-11-13 | G1-UI | validacao visual no portal

**Evidencia do operador:** captura de tela da area `Computadores` no Portal de TI em producao, enviada no atendimento; o screenshot nao foi publicado no repositorio, para evitar dados pessoais no GitHub publico.

**Comprovado visualmente:** menu Computadores ativo, cabecalho do inventario, botao `Cadastrar computador`, busca, paginacao, filtros Unidade/Tipo/Situacao/Cadastro e estado vazio `0 registros`, sem erro visivel. Usuario confirmou acesso.

**Limites da prova:** o print nao comprova escrita/edicao no banco, versionamento do Core 0.3.4, persistencia, arquivamento/restauracao, trilha de auditoria, permissao de usuario sem acesso, nem execucao do agente. A presenca do botao de cadastro sugere `can_manage_computers` ativo para este usuario, nao prova a politica negativa de RBAC.

**Status:** backend e MFE publicados conforme logs; UI inicial visualmente validada; G1-API/UI permanecem em homologacao funcional ate testar CRUD e controle de acesso. Nenhuma sessao remota ou agente ativado.

**Proximo passo:** cadastrar um equipamento corporativo de teste (sem credenciais), confirmar listagem e detalhe, editar, verificar historico, arquivar e restaurar; testar acesso negado em perfil sem `it-portal.computers.view`. Registrar os resultados antes de fechar G1 e avancar G2-AGENT.

## 2026-11-13 | G1 piloto | proposta de nomenclatura e coleta inicial

**Objetivo:** estruturar os campos do cadastro piloto de um desktop corporativo sem alterar o hostname Windows e sem instalar agente.

**Evidencia:** usuario executou coleta PowerShell manual e enviou dados de modelo, CPU, RAM, disco, Windows, hostname e IP. Informacoes especificas do equipamento nao foram publicadas no GitHub publico.

**Proposta:** adicionar `NAMING-CONVENTION.md` com `DLP-<UF>-<SETOR>-<TNN>`, exemplos ficticios, separacao entre codigo `PC-0001`, nome operacional, hostname real, UUID e IP. Caso piloto: `DLP-ES-TI-D01` (filial/setor sujeitos a confirmacao).

**Estado:** cadastro preparado para preenchimento pelo operador no Portal, **ainda sem evidencias de registro salvo ou CRUD validado**. Nao atualizar G1 para VALIDADO.

**Proximo passo:** usuario cadastra a estacao, envia a confirmacao e testa abertura da ficha, edicao, historico, arquivamento e restauracao; depois validar RBAC negativo e atualizar este diario.

## 2026-11-13 | Planejamento G1-OWNER | responsavel vinculado a usuario da plataforma

**Solicitacao:** substituir digitacao manual do campo Responsavel do cadastro de computador por seletor de colaboradores ja cadastrados na Minha DELPI. O responsavel representa o usuario principal do ativo, nao o administrador do Portal.

**Alterado apenas no planejamento:** linha G1-OWNER inserida antes de G2-AGENT no roadmap, contrato de inventario complementado e documento `G1-OWNER.md` criado com escopo de UI, API/Core, migracao futura, historico, privacidade e criterios de aceite.

**Implementacao:** NAO INICIADA. Nenhum campo, banco, permissao, manifesto ou deploy alterado. Atual campo texto livre continua funcionando durante a homologacao G1.

**Proximo passo:** finalizar validacao funcional G1. Em seguida mapear diretorio autorizado do Core e desenvolver o seletor/vinculo com ID canonico; documentar entrega e testes no repositorio.

## 2026-11-13 | Helpdesk #1593 | retorno e solucao registrados

**Evidencia GLPI:** o solicitante autorizou expressamente a solucao do chamado #1593. A operacao `helpdesk_add_solution` foi executada e verificada pelo Helpdesk BFF: status final **Solucionado** (id=5), solucao registrada (id=1352) e horario de solucao **2026-11-13 16:27:35-03**.

**Conteudo do retorno:** resumo de G1-DOM, G1-API, G1-UI, V009 aplicada, API/frontend publicados, acesso a tela Computadores comprovado, coleta inicial de inventario, proposta de nomenclatura e G1-OWNER planejado. Solucao com cabecalho corporativo e referencia a issue #179.

**Escopo da solucao:** somente o ticket referente ao registro de entregas ja realizadas ate 13/11/2026. **Nao** significa que o desenvolvimento do Delpi Remote acabou, nem que o CRUD completo, controles RBAC negativos ou o acesso remoto foram homologados. O roadmap tecnico permanece aberto.

**Proximo passo:** continuar homologacao funcional do inventario e implementar G1-OWNER depois de validacao; G2-AGENT em fase posterior e G0-SEC obrigatorio para o motor remoto.

## 2026-11-13 | G1-OWNER | codigo preparado, dependente de validacao

**Objetivo:** permitir que o Responsavel da workstation seja selecionado entre usuarios ativos da Minha DELPI em vez de ser digitado como texto.

**Contrato Core verificado em fonte oficial:** `GET /me/directory/users` com `include_self=true`, `POST /me/directory/users/lookup` para ID canonico. Somente usuarios ativos, sem precisar de usuario administrativo ou de nova tabela de funcionarios.

**Arquivos:** migration `V010__workstation_responsible_user.sql`; CoreDirectoryOwnerResolver; dominio/servico/repositorio/rotas/DTO/config da API; cliente HTTP Core, componentes `WorkstationOwnerPicker` e `WorkstationOwnerStatus`, formulario/detalhe/estilos; testes `test_workstation_owner.py`, `WorkstationOwnerPicker.test.tsx` e integracao V010.

**Implementado em codigo:** busca debounced no Core, escolha por ID UUID, nome canonico validado no backend e salvo como snapshot, compatibilidade com cadastros legados, historico e revogacao (Core offline = 503 / sem permissao = 403). V010 e apenas aditiva. Nenhum codigo de acesso remoto foi tocado.

**Teste/evidencia neste ambiente:** leitura dos contratos e revisao estatica de arquivos; testes novos escritos. **NAO foram executados** Vitest/lint/build, suite HTTP real com dependencias e PostgreSQL descartavel. Nao declarar testes verdes/homologacao.

**Producao:** sem migração V010 aplicada, sem deploy, sem alteracoes no banco produtivo ou no Portal Admin. A V009 e o G1 publicado anteriormente permanecem intactos.

**Riscos/rollback:** dependendo do banco compartilhado `plugins_hub`, preparar backup antes de V010; verificar divergencia anterior de collation separadamente. Em caso de rollback, voltar imagens de API/MFE e preservar coluna V010 ja aplicada; nunca editar migration historica.

**Proximo passo:** validar suites reais e PostgreSQL V001..V010, tratar incompatibilidades, liberar publicacao do G1-OWNER com aceite; depois iniciar desenho G2-AGENT de leitura de inventario. G0-SEC permanece gate para remoto.

## 2026-11-13 | Aceite G1-OWNER e inicio G2-S1 (coletor offline)

**Aceite relatado:** operador afirmou expressamente que a publicacao do G1-OWNER e a funcionalidade de vinculo a usuario funcionaram perfeitamente, autorizando a continuidade do roadmap. Aceite funcional informado pelo usuario; nao equivale a comprovacao de todos os testes CI e controles RBAC negativos.

**Proxima entrega implementada no codigo:** G2-S1, coletor PowerShell independente para estacoes Windows, somente leitura e execucao manual, sem acesso remoto, instalacao, tarefa agendada, rede, API de ingestao, credenciais ou migration.

**Arquivos:** `collectors/windows_workstation/Collect-ItPortalWorkstationSnapshot.ps1`, `domain/workstation_snapshots.py`, `tests/test_workstation_snapshots.py` e `G2-S1-LOCAL-COLLECTOR.md`.

**Contrato:** JSON v1 (source/run_id/timestamp/host/hardware/os/volumes/network/status); limite de tamanho e listas, UTC e rejeicao de chaves desconhecidas e IP publico. Hostname e run_id nao autenticam a estacao.

**Testes realmente executados:** nove testes unitarios do validador Python em ambiente isolado **PASS**, `py_compile` **PASS**. Hash de objeto Git do modulo e do script confrontado com os arquivos testados. Sem Windows PowerShell na ferramenta, portanto **NAO** houve execucao PS5.1 e nenhum computador foi consultado pelo assistente. Teste estatico do script sem APIs de rede/instalacao.

**Producao:** nenhuma migracao, servico, agente, container ou permissao alterada pelo G2-S1. O G1-OWNER funciona conforme confirmacao do operador; o codigo do G2-S1 ainda nao foi publicado por deploy.

**Proximo passo unico:** piloto **local e manual** do script em um Windows nao critico, revendo apenas estrutura/resultado agregado. Em seguida projetar G2-S2 com escopo S2S por workstation, credencial individual e revogavel, ingestao idempotente e retencao. G0-SEC segue como gate do motor de acesso remoto.

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
