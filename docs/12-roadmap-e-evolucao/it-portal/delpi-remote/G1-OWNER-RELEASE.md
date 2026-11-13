# Delpi Remote | G1-OWNER: validacao e release futura

**Criado em:** 2026-11-13
**Estado:** codigo em revisao. **NAO implantar antes dos testes e da aprovacao da release.**

## Escopo

- V010 aditiva: `it_portal.workstations.responsible_user_id UUID NULL` (sem FK cross-database).
- Backend valida novos vinculos no Core via `POST /me/directory/users/lookup`, com JWT do operador e nome canonico.
- Frontend: seletor de colaborador da Minha DELPI por busca com `include_self=true`, opcao sem responsavel, indicacao de conta inativa e texto legado.
- Permissoes G1 inalteradas: `it-portal.computers.view` e `it-portal.computers.manage`. O manifesto `0.3.4` nao precisa de novo registro estrutural exclusivamente por esta mudanca de codigo.
- Sem agente, acesso remoto ou novas contas administrativas.

## Preflight tecnico (checkout em ambiente aprovado)

```bash
cd ~/projetos/delpi-central
git status --short
git branch --show-current
git worktree list
git pull --ff-only origin main
```

Parar se houver working tree alterada ou branch inesperada: nao descartar mudancas locais de outros desenvolvedores.

### API e PostgreSQL descartavel

```bash
cd it-portal-api
python -m pytest -q tests/test_workstations_domain.py tests/test_workstations_http.py tests/test_workstation_owner.py tests/test_http_contract.py
python -m pytest -q
```

Em banco de testes **descartavel**, nunca no `plugins_hub` produtivo:

```bash
IT_PORTAL_TEST_DSN='postgresql://usuario_teste@host_de_testes:5432/postgres' \
  python -m pytest -q tests/test_postgres_integration.py
```

O fixture cria/destroi uma base por execucao. O DSN ilustrativo deve ser substituido por infraestrutura autorizada e isolada.

### MFE

```bash
cd plugins/it-portal
npm ci
npm test -- --run src/features/workstations/WorkstationOwnerPicker.test.tsx src/features/workstations/WorkstationsPage.test.tsx
npm run lint
npm run build
```

Verificar tambem suites do projeto, compatibilidade visual, acesso como leitura e gestao, erros/timeout do Core, usuario inativo, texto legado, arquivamento/restauracao e historico. Nao interpretar teste escrito como teste executado.

## Gate de deploy

Depois de suites verdes e aceite, confirmar:
- Backup recente do schema `it_portal` verificado por `pg_restore -l`; para uso em recuperacao, planejar teste de restauracao isolado.
- V010 nova e imutavel, aplicada por runner de migrations ao iniciar `it-portal-api` com `IT_PORTAL_RUN_MIGRATIONS_ON_STARTUP=true`.
- Config `DELPI_AUTH_CORE_API_URL=http://core-api:8000` ja utilizada no Compose; validar conectividade via rede interna.
- Aviso anterior de collation `plugins_hub` (2.41 vs 2.36) permanece um assunto independente e nao deve ser corrigido cegamente durante esta release.
- Janela operacional e rollback aprovados.

Ordem de execucao **somente depois de aprovacao**:

```bash
cd ~/projetos/delpi-central
./infra/scripts/up-prod-sequential.sh --dry-run --build it-portal-api it-portal
./infra/scripts/up-prod-sequential.sh --build it-portal-api
docker inspect --format '{{.State.Health.Status}}' delpi-it-portal-api
docker logs --tail 100 delpi-it-portal-api
# Confirmar V010 no schema_migrations e presence de responsible_user_id por SELECT.
# Somente com API healthy:
./infra/scripts/up-prod-sequential.sh --build it-portal
docker ps --filter name=delpi-it-portal --format 'table {{.Names}}\t{{.Status}}'
```

### Consultas read-only em producao (apos release aprovada)

```bash
docker exec delpi-postgres-plugins psql -U plugins_user -d plugins_hub \
  -c "SELECT version, name, applied_at FROM it_portal.schema_migrations WHERE version = 10;"
docker exec delpi-postgres-plugins psql -U plugins_user -d plugins_hub \
  -c "SELECT column_name, data_type FROM information_schema.columns WHERE table_schema='it_portal' AND table_name='workstations' AND column_name='responsible_user_id';"
```

## Homologacao pelo usuario

- Selecionar o proprio usuario no combobox e salvar: o detalhe reabre com vinculo e UUID correto no banco (o UUID nao precisa ficar visivel na tela).
- Transferir equipamento a outro colaborador e verificar historico da alteracao.
- Tentar informar ID inexistente/inativo: API devolve 422 sem escrita.
- Simular Core indisponivel em homologacao: 503 sem escrita.
- Editar cadastro legado sem escolher usuario: texto historico preservado e nenhuma vinculacao automatica.
- Em conta com `computers.view` sem `computers.manage`, ver vinculo mas nao poder alterar.
- Confirmar que nao ha funcao de controle remoto ativa.

## Rollback

1. Revogar temporariamente `computers.manage` se houver falhas graves de vinculacao.
2. Reverter imagens API e MFE para versoes anteriores conforme runbook infra, sem `git reset --hard` e sem modificar migrations antigas.
3. **Nao remover V010 nem coluna ja migrada**, para preservar historico e dados do campo; eventual correção exige migration nova.
4. Documentar incidente, commits, logs sanitizados, situacao de usuario e passos de recuperacao.

Atualizar `EXECUTION-LOG.md`, `README.md` e issue #179 apos os testes e apos eventual publicacao. **G1-OWNER = IMPLANTADO** somente com evidencia do host e validação funcional.
