# G1-UI | Computadores no Portal de TI

**Projeto:** [Delpi Remote](README.md) | **Issue:** [#179](https://github.com/roberiooliveiradev/delpi-central/issues/179) | **Data:** 2026-11-13
**Estado:** implementado em codigo, EM REVISAO; **NAO** esta implantado em producao.

## Objetivo entregue no codigo

Criar a area **Computadores** do Portal de TI, conectando o inventario de desktops/notebooks a API G1-API sem permitir controle remoto. A navegacao utiliza `/apps/it-portal/workstations` e `/apps/it-portal/workstations/{uuid}`.

### Modulos e operacao

- `WorkstationsPage.tsx`: lista paginada da BFF, ordenacao, busca debounce e filtros unidade, tipo, situacao e ativos/arquivados. Nao mostra online/offline, pois nao existe agente.
- `WorkstationFormModal.tsx`: cadastro e edicao, nomes e campos do contrato backend, estado pendente, erros de validacao da BFF, aviso contra segredos, `revision` otimista.
- `WorkstationDetailPage.tsx`: ficha com identificacao, responsavel, localizacao, sistema, trilha de atualizacao, historia, arquivar/restaurar por confirmacao e bloqueio de edicao se arquivado. Painel informa claramente que suporte remoto nao esta disponivel.
- `itPortalApi.ts`: sete metodos HTTP de computadores usando o cliente existente com Keycloak/BFF.
- `app/routes.ts`, `PluginShell.tsx`, `App.tsx`, `HomePage.tsx`: roteamento, menu, busca de areas e atalho da Home so se `can_view_computers`.
- `queryKeys.ts`: cache TanStack Query isolado em `workstations`. Mutacoes invalidam apenas o inventario de computadores.
- `HistorySection.tsx` e `content/labels.ts`: nomes PT-BR e eventos G1.
- `it-portal.manifest.json` `0.3.4`: rota de lista, `permission=it-portal.computers.view` (as duas permissoes ja presentes desde 0.3.3). Exige registro **estrutural** da nova versao no Core.

## Gates de seguranca

1. `it-portal.access` + `it-portal.computers.view` sao obrigatorios para lista/detalhe/historico. UI esconde menu e conteudo sem capability; **backend deve autorizar em cada request**.
2. `it-portal.computers.manage` exige `computers.view` para criar, editar, arquivar e restaurar, com RBAC fresh na BFF; a UI so exibe botoes em perfis permitidos.
3. Nao existe permissao de `it-portal.remote.*` ativa neste incremento, nem botao Conectar, agente, MeshCentral, clipboard ou transferencia de arquivos.
4. Situação cadastral `in_operation` **nao significa** maquina ligada/online. Nao inventar status de heartbeat.
5. Nenhuma credencial em notas, hostname ou descricao; backend mantem validação e guarda de segredos.

## Validacao pendente (nao marcar como concluida sem saidas reais)

No checkout confiavel do repositorio, **antes do deploy**, verificar working tree e versao dos commits:

```bash
git rev-parse HEAD
git branch --show-current
git status --short
git worktree list
```

Executar, idealmente em ambiente isolado/homologacao:

```bash
cd plugins/it-portal
npm ci
npm test -- --run src/app/routes.test.ts src/features/workstations/WorkstationsPage.test.tsx src/manifestContract.test.ts
npm run lint
npm run build
```

No backend, com ambiente de testes e DB descartavel:

```bash
cd it-portal-api
python -m pytest -q tests/test_workstations_domain.py tests/test_workstations_http.py tests/test_http_contract.py
IT_PORTAL_TEST_DSN=postgresql://<usuario_teste>@<host_teste>:5432/postgres python -m pytest -q tests/test_postgres_integration.py
```

**Nao** copiar o DSN de exemplo sem substituir. PostgreSQL de testes exige conta e banco descartavel, nunca executar criacao/destruicao de bases sobre banco produtivo. Validar tambem a suite completa da API e do MFE, e smoke da Home e inventarios de servidores.

### Aceite funcional para homologacao

- [ ] Usuario sem computers.view: menu oculto, lista/detalhe bloqueados e nenhuma chamada `/workstations` disparada
- [ ] Usuario com computers.view: lista, busca, filtros, paginação, detalhes e historia aparecem sem botoes de escrita
- [ ] Usuario com computers.manage + view: criar computador, editar e refletir atualizacao na ficha
- [ ] Conflito 409 por hostname ativo duplicado e `revision` antigo exibido corretamente
- [ ] Erros 422 exibidos com campos em PT-BR
- [ ] Arquivar/restaurar exige confirmacao, preserva historico, e arquivado nao pode ser editado
- [ ] Permissao revogada no Core bloqueia escritas imediatamente; Core indisponivel retorna 503 sem escrita
- [ ] Nao existe botao Conectar, acesso ao desktop, status online falso ou instalacao de agente
- [ ] Migracao V009 aplicada apenas uma vez em PostgreSQL de homologacao com checksum correto
- [ ] Manifesto 0.3.4 registrado por nova versao estrutural e perfis no Core revisados
- [ ] Testes existentes do Portal e backend passam, sem regressoes

## Publicacao conjunta posterior (nao executada)

- Review de PR ou commits em `main`, verificacao de checks, backup e janela operacional.
- `V009` e aditiva e pode ser aplicada na inicializacao do `it-portal-api` segundo o runner do projeto. Nao aplicar manualmente no banco produtivo.
- Registrar o manifesto `0.3.4` no Portal Admin via fluxo de versao estrutural; atribuir `it-portal.computers.view` e `it-portal.computers.manage` somente a perfis corporativos aprovados.
- Deploy canônico documentado em `AGENTS.md`: `git pull --ff-only` + `./infra/scripts/up-prod-sequential.sh --build it-portal-api it-portal`, **apenas depois da validacao** e conferencia da sintaxe do script nos services/profiles reais.
- Conferir `/openapi.json`, `/me/capabilities`, CRUD em um host de laboratorio cadastrado, erro de usuario sem permissao e regressao de servidores.
- Se houver falha: revogar permissões/ocultar menu, restaurar imagens conforme runbook; nao modificar migrations historicas nem remover eventos de auditoria.

## Handoff

Leia [README.md](README.md) e [EXECUTION-LOG.md](EXECUTION-LOG.md) no inicio de cada sessao. A proxima tarefa obrigatoria e validar **G1-API + G1-UI** com dependencias reais e preparar a publicacao coordenada. **G0-SEC continua pendente para acesso remoto.**
