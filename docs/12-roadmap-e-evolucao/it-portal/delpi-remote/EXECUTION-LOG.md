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
