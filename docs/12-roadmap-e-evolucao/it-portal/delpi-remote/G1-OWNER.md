# G1-OWNER | Responsavel do computador como usuario da Minha DELPI

**Estado:** NAO INICIADO, incluido no roadmap em 2026-11-13 a pedido do responsavel de TI. **Prioridade:** proximo incremento de cadastro depois da homologacao do G1, antes de G2-AGENT.

## Problema e objetivo

Hoje o formulario `Computadores > Cadastrar/Editar` solicita o campo `Responsavel` como texto livre. O operador deve poder **pesquisar e selecionar um colaborador que ja exista na plataforma**, vinculando o equipamento ao usuario real sem digitar ou manter nomes manualmente. Esse colaborador e o **usuario principal / detentor do ativo**, nao necessariamente a pessoa de TI que administra o cadastro.

## Requisitos de interface (frontend)

1. Trocar o campo de texto `Responsavel` por um combobox com busca por nome e, conforme exposicao autorizada da API, identificador corporativo, sem listar todos os usuarios sensiveis do sistema.
2. Apresentar nome do colaborador e indicacao segura de unidade/setor quando esses atributos existirem no diretorio; nao inventar tais campos. Exibir estado de carregamento, sem resultados, erros e selecao clara.
3. Ao selecionar, guardar **ID estavel do usuario** no formulario e apresentar nome legivel. Nao usar nome ou e-mail como chave de relacionamento.
4. Na ficha do computador, mostrar colaborador vinculado, com referencia ao perfil no Portal apenas se houver rota autorizada e segura.
5. Permitir deixar **Sem responsavel** para estoque/maquinas compartilhadas, caso a politica aprovada permita; a escolha de usuario nao pode conceder permissoes de TI.
6. Edicao e troca de colaborador devem exigir `it-portal.computers.manage`; leitura requer `it-portal.computers.view`.

## Backend, Core e banco (a definir na implementacao)

- Antes de codificar, inspecionar as APIs e permissoes **existentes** de usuarios no Core/Keycloak para definir uma consulta autenticada, paginada, filtrada e com principio de menor privilegio. Nao chamar endpoints administrativos diretamente do navegador nem inventar uma rota de diretorio.
- Acrescentar via **nova migration imutavel** um identificador nullable do usuario da plataforma no cadastro da workstation (nome de coluna e integridade definidos apos inspecao de schema e contratos). Usar o ID canonico exposto pelo Core; nao assumir de antemao que e o mesmo UUID do Keycloak.
- Manter compatibilidade com `responsible` legado no periodo de migracao. Nao vincular automaticamente por coincidencia de nomes; itens existentes so serao relacionados por selecao confirmada.
- Validar no backend que o usuario selecionado existe e e elegivel a ser atribuido. Registrar mudanca do responsavel no historico da workstation: anterior, novo, usuario de TI que efetuou alteracao e timestamp. Evitar registrar dados pessoais desnecessarios.
- Se o usuario for desativado/excluido/transferido, preservar a referencia historica e sinalizar `Inativo` ou `Vinculo indisponivel`, sem apagar historico ou assumir substituto automaticamente.
- Manter referencia ao colaborador separada das credenciais de agente, identidade Windows e permissoes de suporte remoto. Atribuicao do equipamento nao autoriza conexao remota.

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

**Proximo passo tecnico quando iniciar:** mapear a fonte canonica de usuarios no Core e os endpoints autorizados, propor contrato/ADR do vinculo e somente entao desenvolver migration, API, UI e testes.
