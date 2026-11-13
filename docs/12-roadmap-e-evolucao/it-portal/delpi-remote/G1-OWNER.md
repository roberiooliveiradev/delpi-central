# G1-OWNER | Responsavel do computador como usuario da Minha DELPI

**Estado:** EM REVISAO em 2026-11-13. Codigo de vinculo, migracao V010, UI e testes preparados no repositorio; verificacao integrada e deploy pendentes. G1 anterior ainda aguarda homologacao funcional completa. Nada desta etapa foi implantado.

## Problema e objetivo

Hoje o formulario `Computadores > Cadastrar/Editar` solicita o campo `Responsavel` como texto livre. O operador deve poder **pesquisar e selecionar um colaborador que ja exista na plataforma**, vinculando o equipamento ao usuario real sem digitar ou manter nomes manualmente. Esse colaborador e o **usuario principal / detentor do ativo**, nao necessariamente a pessoa de TI que administra o cadastro.

## Requisitos de interface (frontend)

1. Trocar o campo de texto `Responsavel` por um combobox com busca por nome e, conforme exposicao autorizada da API, identificador corporativo, sem listar todos os usuarios sensiveis do sistema.
2. Apresentar nome do colaborador e indicacao segura de unidade/setor quando esses atributos existirem no diretorio; nao inventar tais campos. Exibir estado de carregamento, sem resultados, erros e selecao clara.
3. Ao selecionar, guardar **ID estavel do usuario** no formulario e apresentar nome legivel. Nao usar nome ou e-mail como chave de relacionamento.
4. Na ficha do computador, mostrar colaborador vinculado, com referencia ao perfil no Portal apenas se houver rota autorizada e segura.
5. Permitir deixar **Sem responsavel** para estoque/maquinas compartilhadas, caso a politica aprovada permita; a escolha de usuario nao pode conceder permissoes de TI.
6. Edicao e troca de colaborador devem exigir `it-portal.computers.manage`; leitura requer `it-portal.computers.view`.

## Backend, Core e banco (contratos identificados e implementacao preparada)

- Antes de codificar, inspecionar as APIs e permissoes **existentes** de usuarios no Core/Keycloak para definir uma consulta autenticada, paginada, filtrada e com principio de menor privilegio. Nao chamar endpoints administrativos diretamente do navegador nem inventar uma rota de diretorio.
- Acrescentar via **nova migration imutavel** um identificador nullable do usuario da plataforma no cadastro da workstation (nome de coluna e integridade definidos apos inspecao de schema e contratos). Usar o ID canonico exposto pelo Core; nao assumir de antemao que e o mesmo UUID do Keycloak.
- Manter compatibilidade com `responsible` legado no periodo de migracao. Nao vincular automaticamente por coincidencia de nomes; itens existentes so serao relacionados por selecao confirmada.
- Validar no backend que o usuario selecionado existe e e elegivel a ser atribuido. Registrar mudanca do responsavel no historico da workstation: anterior, novo, usuario de TI que efetuou alteracao e timestamp. Evitar registrar dados pessoais desnecessarios.
- Se o usuario for desativado/excluido/transferido, preservar a referencia historica e sinalizar `Inativo` ou `Vinculo indisponivel`, sem apagar historico ou assumir substituto automaticamente.
- Manter referencia ao colaborador separada das credenciais de agente, identidade Windows e permissoes de suporte remoto. Atribuicao do equipamento nao autoriza conexao remota.

## Implementacao preparada no codigo (sem deploy)

- Contratos oficiais do Core verificados: `GET /me/directory/users?q=...&include_self=true&limit=15` lista usuarios ativos; `POST /me/directory/users/lookup` resolve UUIDs existentes e **ativos**. O Core responde JSON `{items: [{id,name,email?}]}`, distinto do envelope da BFF. Nao usar endpoint administrativo.
- Frontend usa o token do usuario logado (mesma sessao Keycloak) na chamada same-origin ao Core; busca debounced e selecao explicita, sem expor token em URL, logs ou cadastro. Permissoes de escrita permanecem `computers.manage` + `computers.view`.
- Backend persiste o ID Core em `workstations.responsible_user_id UUID NULL` via migration aditiva **V010**. `responsible` continua como snapshot legivel/legado. Nenhum FK entre bancos separados.
- Em nova atribuicao/troca, `WorkstationService` usa `CoreDirectoryOwnerResolver` com JWT do operador via `DELPI_AUTH_CORE_API_URL` e o Core devolve o nome canonico. ID inexistente/inativo responde 422; Core indisponivel responde 503 sem gravacao; requisições sem RBAC fresh recebem 403.
- Atualizacoes com ID existente/inalterado preservam o snapshot para nao impedir edicao de outras informacoes quando conta for inativada. Cliente G1 antigo sem campo `responsible_user_id` nao perde o vinculo atual.
- Remocao expressa remove UUID e nome snapshot; dados historicos continuam nos eventos `audit_events`.
- Na ficha, o nome salvo aparece mesmo se a conta estiver inativa. Quando lookup falha, indica indisponibilidade sem alterar o banco.
- Nenhum agente, monitoramento online ou acesso remoto neste incremento.
- Manifesto `0.3.4` permanece, pois nenhuma nova rota ou permissao estrutural foi criada nesta etapa.

**Verificacao pendente:** testes HTTP de backend, PostgreSQL descartavel com V001..V010, Vitest, TypeScript/lint/build, revisao de UI e smoke em homologacao. Testes foram escritos mas nao executados no runtime de producao. Seguir [runbook de publicacao](G1-OWNER-RELEASE.md).

## Criterios de aceite

- [ ] Com permissão de gerenciar computadores, pesquisar por nome encontra usuarios autorizados no Core.
- [ ] Selecionar um usuario cria vinculo persistente pelo identificador correto, exibido apos atualizar a pagina.
- [ ] Alterar responsavel audita a troca, sem sobrescrever os demais dados.
- [ ] Usuario sem `computers.manage` nao altera vinculo, mesmo chamando a API diretamente.
- [ ] Usuario inexistente, invalido ou inelegivel e rejeitado pelo backend; falhas no Core nao gravam vinculos incertos.
- [ ] Campos de texto legados continuam visiveis durante migracao; nenhuma associacao automatica por nomes homonimos.
- [ ] Conta inativa nao quebra a ficha; mostra situacao apropriada e preserva historico.
- [ ] Campo opcional/sem responsavel segue a politica aprovada e nao bloqueia cadastro de maquina de uso compartilhado.
- [ ] Testes de API, componente, RBAC, PostgreSQL e regressao do cadastro vigente passam.
- [ ] Alteracao documentada no `EXECUTION-LOG.md`, issue #179 e instrucoes de deploy/rollback apos implementacao.

## Fora do escopo deste incremento

- Instalacao de agentes, coleta de hardware, conexao de desktop remoto e liberacao de privilegiados.
- Criacao de usuarios da plataforma pelo Portal de TI.
- Sincronizacao irrestrita ou copia integral da base de usuarios para o inventario.

**Proximo passo tecnico:** executar suites reais e homologacao V010, corrigir falhas de integracao, solicitar aceite para deploy conforme G1-OWNER-RELEASE.md e registrar o resultado. Nao marcar IMPLANTADO sem evidencia do host.
