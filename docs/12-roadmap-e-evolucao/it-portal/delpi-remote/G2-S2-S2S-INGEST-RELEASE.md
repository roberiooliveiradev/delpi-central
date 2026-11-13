# G2-S2 | Envio de inventario Windows por S2S, com feature gate desligado

**Data:** 2026-11-13
**Estado:** EM REVISAO, CI de API/PostgreSQL V011/PowerShell e UI verde em 13/11/2026; sem deploy produtivo, sem teste real do cliente Keycloak nem piloto Windows confirmados.
**Importante:** nenhum agente remoto foi instalado; este incremento nao concede controle de tela, teclado, mouse ou arquivos.

## O que esta implementado

- Contrato local G2-S1 reutilizado: `windows_workstation_local_v1`, somente hardware/OS/volumes/IP privado com opt-in.
- `POST /collector/v1/workstations/{id}/snapshots`: valida token S2S por `X-Delpi-Service-Authorization` com escopo exato `it-portal.workstations.ingest`, binding `client_id -> workstation_id` estritamente 1:1 e feature gate.
- `GET /workstations/{id}/snapshot`: exige JWT humano mais `it-portal.computers.view`; mostra ultimo snapshot observado e indicador de atualidade, nunca estado online instantaneo.
- Migration aditiva **V011__workstation_snapshots.sql**: tabela `it_portal.workstation_snapshots`, FK para cadastro de workstations, `(workstation_id, run_id)` unico, hash da carga para evitar replay com conteudo alterado, retenção maxima limitada, timestamps UTC e sem tokens.
- Backend compara hostname observado com hostname curado **dentro da transacao com FOR SHARE** e impede atualizacao de maquina arquivada.
- Reenvio identico retorna `duplicate: true` sem gravar outra linha. Reenvio do mesmo run ID com carga diferente retorna 409. Snapshot novo fica em tabela separada; nao altera nome, setor, local, responsavel nem status administrativo.
- Corpo JSON limitado a 32 KiB, campos estritos e sem chaves sensiveis, run_id UUID v4, timestamp em janela definida. Sem shell, WinRM, RDP, tarefas, controle de servicos ou coleta de arquivos.
- `Send-ItPortalWorkstationSnapshot.ps1`: piloto **manual** apenas; exige cliente S2S individual e secret armazenado em DPAPI local, URLs HTTPS, sem redirecionamentos, sem registrar token em logs. Nenhum agendamento automatico foi criado.

## Protecoes obrigatorias antes de habilitar

- `IT_PORTAL_WORKSTATION_INGEST_ENABLED=false` e default. Sem true, nenhum POST e aceito.
- `IT_PORTAL_WORKSTATION_COLLECTOR_BINDINGS` vazio e default. Formato privado: `client-id-001=<workstation-uuid>`. Identificadores nao sao secretos, mas mapeamento da rede deve permanecer em `infra/.env` privado e nao no GitHub.
- Um `client_id` corresponde a um UUID e vice-versa. Duplicatas, entradas malformadas ou vinculos vazios bloqueiam ingestao.
- Criar no Keycloak **um client confidencial por estacao autorizada**, com audiencia S2S da API e permissao restrita `it-portal.workstations.ingest`. Nao reutilizar clientes de servidores, nem permitir `it-portal.host-services.control`, `it-portal.observations.ingest` ou permissoes remotas. Inspecionar `S2S_ALLOWED_CLIENTS` e audiencia existentes no deployment.
- Registrar apenas computadores corporativos de laboratorio aprovados; vincular UUID verificado no Portal e hostname do Windows. Nao usar IP, serial ou hostname como autenticacao do cliente.
- Requisicoes sem S2S devem responder 401; com escopo negado 403; com binding ausente/cadastro arquivado 409; JSON invalido 422, sem persistir nada.
- Segredo individual com armazenamento DPAPI do mesmo usuario/maquina, permissao NTFS adequada, geracao por processo oficial, rotacao/revogacao testadas, sem copia para outros hosts.
- Analisar LGPD (IP/host como dados internos), retencao minima e logs. Este projeto e publico; nunca anexar payload real, hostname, IP, secrets ou tokens em issues.

## Preflight e testes antes de qualquer deploy

Na copia revisada do codigo, execute suite real da API e MFE:

```bash
cd ~/projetos/delpi-central/it-portal-api
python3 -m pytest -q tests/test_workstation_snapshots.py tests/test_workstation_snapshot_ingest.py tests/test_workstations_http.py
python3 -m pytest -q
cd ../plugins/it-portal
npm ci
npm test -- --run src/features/workstations/WorkstationSnapshotPanel.test.tsx src/features/workstations/WorkstationsPage.test.tsx
npm run lint
npm run build
```

Para testar a migration com PostgreSQL REAL e descartavel, `IT_PORTAL_TEST_DSN` deve apontar para instancia **fora da producao** e com permissao para criar/remover banco de teste. O fixture aplica V001..V011 e exclui a base somente apos finalizar o teste:

```bash
cd ~/projetos/delpi-central/it-portal-api
IT_PORTAL_TEST_DSN='postgresql://usuario@servidor-lab:5432/postgres' python3 -m pytest -q tests/test_postgres_integration.py
```

Nao executar o fixture acima sobre `plugins_hub` ou Postgres de producao.

## Publicacao futura controlada (somente apos suites verdes)

1. Confirmar branch `main`, working tree limpo, pull `--ff-only` e commit de G2-S2 no HEAD; nao reconfigurar git/resetar/stash sem autorizacao.
2. Fazer novo backup `pg_dump -Fc -n it_portal`, conferir `pg_restore -l` e planejar restauracao de teste.
3. Conferir `IT_PORTAL_WORKSTATION_INGEST_ENABLED=false`, bindings vazios, e `IT_PORTAL_RUN_MIGRATIONS_ON_STARTUP=true`. `V011` e executada pelo runner ao iniciar API. **Nao** executar SQL manual.
4. Usar `./infra/scripts/up-prod-sequential.sh --dry-run --build it-portal-api it-portal`; publicar API primeiro somente com backup e aprovação, conferir health+logs+SELECT em `it_portal.schema_migrations WHERE version=11` e existencia da tabela.
5. Publicar frontend apos API healthy, verificar `GET /workstations/{id}/snapshot` com usuario autorizado. Sem coleta, resposta 200 com `data:null`. O manifesto `0.3.4` nao muda: sem novas rotas do Portal/menu nem permissoes humanas.
6. Somente em janela de piloto configurar um client Keycloak exclusivo, 1:1 binding, regras de firewall/TLS e a flag true para um equipamento previamente autorizado; reiniciar so a API mediante processo de mudanca. Nao habilitar varios hosts nem agendamento.
7. Pilotar `Send-ItPortalWorkstationSnapshot.ps1` manualmente com o segredo DPAPI proprio. Confirmar 201, repeticao identica 200 e ficha de inventario. Verificar revogacao do client e rejeicao de outro workstation UUID.
8. Se todas as verificacoes passarem, considerar implementacao e testes de agendamento **em G2-S3**, nunca instalar automaticamente a partir deste merge.

O aviso anterior de collation de `plugins_hub` (versao 2.41 versus 2.36) e manutencao separada: nao executar `REINDEX` ou `ALTER DATABASE ... REFRESH COLLATION VERSION` como parte desta release.

## Rollback

- Se falha na ingestao: voltar `IT_PORTAL_WORKSTATION_INGEST_ENABLED=false`, retirar o binding 1:1 e revogar o client dedicado no Keycloak; interromper piloto antes de mexer no banco.
- Reverter imagens API e frontend para release anterior pelo procedimento de infra com evidencias; nao usar `git reset --hard`.
- Nao remover V011 nem editar migrations anteriores, para preservar trilha e snapshot. Se necessario corrigir schema, criar uma migration nova.
- Nenhum motor remoto foi instalado; a identidade de inventario nao vale para acesso grafico.

## Pendencias em aberto

- CI/pytest, Vitest/lint/build e integracao PostgreSQL V001..V011 executados e aprovados em GitHub Actions; testes Windows PowerShell 5.1 em host real e envio S2S de ponta a ponta ainda pendentes.
- Testes de rate limit em gateway, revogacao em Keycloak, TTL real de tokens, rotate de segredo, duplo envio simultaneo e limites de retencao no Postgres.
- G2-S3 para installer assinado, enrolment governado, agendamento e uninstall de agente, sem habilitar acesso remoto.
- Gate G0-SEC para MeshCentral e controle remoto permanece pendente.

Roadmap: [README](README.md) | Evidencias: [EXECUTION-LOG](EXECUTION-LOG.md) | Issue [#179](https://github.com/roberiooliveiradev/delpi-central/issues/179).

## Evidencias CI registradas em 13/11/2026

- [API: job test-it-portal-api sucesso](https://github.com/roberiooliveiradev/delpi-central/actions/runs/43515628259/job/132196752412), commit `2295725e96eb991909fa390eb0a7db0bb0c9a0bc`, suite HTTP, syntax parser PowerShell, PostgreSQL real descartavel V001..V011 e integracao G2.
- [UI: validate-it-portal sucesso](https://github.com/roberiooliveiradev/delpi-central/actions/runs/43514437749/job/132192627676), commit `4a7318dea15c5d7b972a5c8cd0a8321d0eecc205`, lint, Vitest e build.
- O status do CI nao comprova instalacao, rede/TLS do host, atuacao de S2S real, revogacao de clients ou backup da base produtiva.
