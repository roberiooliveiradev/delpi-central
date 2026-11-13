# SEC-01 — Higiene de segurança: token no access log e reset do schema LNF

Data: 2026-11-13. Decisões do owner, não reabertas: D-W6 A e D-W7 A.

Pasta usada: `docs/03-autenticacao-autorizacao/`, que é o índice de identidade e acesso da plataforma.

## Decisões

- D-W6 A. O access log redige `token` e `access_token` em toda location que pode levar esses parâmetros na query, em DEV, HML e PROD. O mapa já existente (`access_token|refresh_token|id_token|token|...`) não foi alterado. A saída das linhas de TV permanece a do formato `tv_access_sanitized`.
- D-W7 A, ampliado por D-S1. O runner de plugins da api-delpi não opera o schema do LNF: `up`, `status` e `reset` com `--plugin lancamento-notas-fiscais` recusam. O `up` sem plugin pula o LNF. A pasta de SQL permanece porque a BFF ainda confere o checksum.
- Trava de host genérica para o reset de qualquer plugin: só inventário e opções. Não implementada.

## Parte A — access log

SHA: `221ad3b641`.

O mapa em `gateway/nginx.dev.conf`, `gateway/nginx.conf` e `gateway/nginx.hml.conf` já substituía o valor por `<redacted>`. O defeito era a location usar o formato combinado, que grava `$request` com a query crua. A mudança acrescenta `access_log ... tv_access_sanitized` nas locations de Socket.IO, WebSocket nativo e SSE que ainda não tinham esse formato. Locations HTTP que não são canal de token ficam no formato anterior. A location `/realtime` do LNF não entrou no `nginx.conf` de PROD.

DEV validado no gateway local: `nginx -t` e reload. Sem sessão, requests, engineering, commercial e transformometro continuam 403; production-pulse e production-control continuam 502; Socket.IO da Core e da api-delpi continuam 101; TV continua 403; `GET /apps/financial-api/health` continua 200. Um probe de WebSocket não aparece no log do gateway (0 ocorrências). O mesmo probe na location HTTP comum continua visível, então o formato dessa location não mudou.

HML: `nginx -t` com certificado descartável, sintaxe ok. O container `delpi-hml-gateway` não estava no ar, então o reload de HML fica TEST_NOT_RUN.

PROD: o SHA-256 do `nginx.conf` em execução era igual ao de `origin/main` antes deste commit. O diff publicado é só as linhas de `access_log`. Publicação e verificação de PROD estão no relatório da execução.

Logs de aplicação: não há filtro compartilhado. Cada API sobe o próprio `uvicorn` no Dockerfile e o access log padrão inclui a query. A redação da BFF está só em `controllership-finance-api/.../access_log_redaction.py` e cobre `token=`, não `access_token=`. Nenhuma API foi alterada. DECISION_REQUIRED: corrigir API por API ou criar um ponto compartilhado.

Logs históricos: não foram apagados. No gateway de DEV, as linhas com `token=` estavam em `/apps/engineering-api/v1/realtime/ws`, `/apps/requests-api/v1/realtime/ws`, `/apps/controllership-finance-api/lancamento-notas-fiscais/realtime` e `GET /`. Não havia `refresh_token=`, `id_token=` nem `access_token=`. O access token do realm `delpi` dura 300 segundos. A exposição antiga se encerra pela expiração e pela rotação do json-file. O `error_log` do nginx ainda imprime a request crua quando o upstream falha; isso não tem `log_format`.

Retenção: o access log do nginx aponta para stdout. PROD usa json-file `10m` × 3 arquivos (`infra/docker-compose.yml` do serviço gateway). DEV não define rotação no compose.

## Parte B — reset do LNF

SHA: `ef2ea358f2`.

O startup da api-delpi chama `run_all_plugins_migrations()` (`up`), e só se `RUN_PLUGINS_MIGRATIONS_ON_STARTUP` estiver ligado. O rollback da trilha 165 religa `LNF_MODULE_ENABLED=true`; não chama `reset`. O bloqueio não atinge esse caminho. X4 não se aplica.

`reset --plugin lancamento-notas-fiscais --confirm-drop-schema` sai com código 1 e a mensagem do ADR-001 / trilha 165 D2, sem abrir conexão. O reset de outro plugin continua chegando ao banco. Testes: `tests/test_lnf_destructive_migrations_blocked.py` e `tests/test_lnf_module_enabled_flag.py`, 6 passed. A suíte completa da api-delpi contra o commit pai fica TEST_NOT_RUN.

Ensaio em DEV: com a flag true o processo sobe, o `up` do LNF reporta nenhuma migration pendente e o router entra no app. A flag voltou a false e o router deixa de entrar. HML não estava no ar; o comando real de recusa rodou no container de DEV.

PROD da api-delpi não foi publicado. A imagem em execução foi criada em 2026-11-13T17:18:50Z e não tem label de revisão. O checkout do servidor nesse intervalo coincide com `b8a31f8c12`, que não altera `api-delpi/`. O commit pendente desta frente é `ef2ea358f2`. Publicar a api-delpi continua DECISION_REQUIRED.

O runbook 164 registra: não executar reset do runner de plugins para lancamento-notas-fiscais em nenhum ambiente.

## Parte C — trava de host genérica

Quem usa `reset`: o comando é manual. Não há chamada em CI nem no startup. Tutoriais em `docs/15-documentacao-geral/tutorials/tutorial_migrations_plugins_delpi.md` resetam `strategic-indicators` e `quality-external-nc` como sandbox. Playbooks de reports e de planejamento orçamentário dizem para não resetar em ambiente com dados. O runner não lê `APP_ENV` nem hostname. O alvo é o `PLUGINS_DB_HOST` / `PLUGINS_DB_NAME` do processo (`get_plugins_db_settings`).

Opções, sem implementar:

1. Recusar reset em HML/PROD. Quebra o sandbox se a variável de ambiente estiver errada e não cobre um processo local apontando o DSN de produção.
2. Exigir a confirmação digitada do host e do banco alvo, além de `--confirm-drop-schema`. O operador vê o alvo antes do `DROP`. O sandbox de DEV continua possível. Esforço pequeno, no próprio runner.
3. Tirar o comando das imagens de HML/PROD. O `docker exec` numa imagem antiga, ou um checkout local com o DSN de produção, continua capaz de resetar.

Recomendação: a opção 2. É a única que amarra a confirmação ao banco que o processo realmente vai abrir.

## Estado final (ALINHAMENTO-01 retomada)

Runner: `57e55a8b85` (recusa up/status/reset) + `9fc0bb9a78` (remove a classe live que apagava o schema; README do plugin aponta a BFF).

HML: Y5 resolvida sem destruir trabalho alheio. Backup `/home/operador/backups/hml-local-20261113-180954.tgz`, SHA-256 `fcaff9d8009032697a00529f75fd70bce24d6228ed94a7ca4ad052849902c33a`. Sobreposição com `origin/main` = 0; `git merge --ff-only`; 157 hashes locais idênticos. Publicados api-delpi, BFF e gateway.

PROD api-delpi publicada (`sha256:2ccc9bd7…`, 15:33:49 -03). `status --plugin lancamento-notas-fiscais` recusa. `LNF_MODULE_ENABLED=false`. BFF e gateway publicados na sequência; location `/realtime` dormente com flag off; access log da location com `<redacted>`.

Rollback (imagens anteriores): api-delpi `sha256:ee93e690be03490d433ce431e8e271dc25956144ce3c69629d11be71d001ebef`; BFF `sha256:49c894ba5eb6b5ffcff3e870d823dd2d8899d2852f44a4a5750248aab3e8b4f6`; gateway `sha256:e998f96c494f275a34ad39ca59aec4f4634746f0c0b92b22a620f4dd593516a0`. Recriar sem `--build` após `docker tag <digest> infra-<serviço>`.

D-S2, D-S3 e D-S4 continuam sem implementação.
