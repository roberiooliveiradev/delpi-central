# G1 | Publicacao coordenada do inventario de computadores

**Data de autorizacao:** 2026-11-13 (responsavel de TI autorizou publicar para teste).
**Estado de execucao (13/11/2026):** backend e frontend reiniciados pelo operador; V009 aplicada e tabela `it_portal.workstations` comprovada. PENDENTE registro/confirmacao estrutural do manifesto 0.3.4 no Core e homologacao funcional. Nenhum acesso remoto/agent autorizado ou ativado.
**Escopo unico:** \`it-portal-api\` + \`it-portal\`; manifesto estrutural \`0.3.4\` no Core; migration aditiva \`V009__workstations_inventory.sql\`.
**Issue de controle:** [#179](https://github.com/roberiooliveiradev/delpi-central/issues/179).

## Por que o deploy nao foi executado neste atendimento
Foi possivel conferir codigo, arquivos, script canonico e documentacao via conector GitHub, mas **nao existe neste chat sessao SSH autenticada no srv-api ou permissao de executar comandos no host de producao**. Acesso ao GitHub nao significa acesso de deploy. Nao marcar implantado sem evidencias do operador.

## Preflight obrigatorio no srv-api (usuario com acesso aprovado)

1. **Nao fazer pull** se houver mudancas nao commitadas ou worktree/branch inesperada. Nao usar stash/reset/clean para contornar alteracoes concorrentes.
2. Confirmar que a API atual esta saudavel, que ha janela operacional e backup do schema \`it_portal\` do \`postgres-plugins\`.
3. Para esta release, o runner aplica V009 automaticamente na inicializacao da nova API **se** \`IT_PORTAL_RUN_MIGRATIONS_ON_STARTUP=true\` (Compose usa true por default); se false, **parar** e planejar migration por fluxo aprovado, nunca modificar SQL manualmente no banco de producao.
4. Guardar uma copia protegida do banco antes da migration e validar formato. Nao publicar o arquivo em Git, logs ou chat.

### Check do checkout

\`\`\`bash
cd ~/projetos/delpi-central
git rev-parse --short HEAD
git branch --show-current
git status --short
git worktree list
# Somente se branch = main e working tree estiver limpa:
git pull --ff-only origin main
git rev-parse --short HEAD
test -f it-portal-api/migrations/V009__workstations_inventory.sql
grep -n '"version": "0.3.4"' plugins/it-portal/it-portal.manifest.json
grep '^IT_PORTAL_RUN_MIGRATIONS_ON_STARTUP=' infra/.env || echo 'Sem override: Compose default true'
./infra/scripts/up-prod-sequential.sh --dry-run --build it-portal-api it-portal
\`\`\`

### Backup de esquema (exemplo; confirmar usuario/banco do ambiente)

\`\`\`bash
umask 077
mkdir -p "$HOME/backups/it-portal"
backup="$HOME/backups/it-portal/it_portal_$(date +%Y%m%d_%H%M%S).dump"
docker exec delpi-postgres-plugins pg_dump -U plugins_user -d plugins_hub -n it_portal -Fc > "$backup"
test -s "$backup"
# Se pg_restore esta instalado localmente; caso contrario, documentar verificacao no host com ferramenta aprovada:
pg_restore -l "$backup" >/dev/null
printf 'Backup verificado: %s\n' "$backup"
\`\`\`

Se o container estiver configurado com usuario/banco diferentes dos exemplos, ajustar os dois parametros aos valores de ambiente autorizados. Falha de backup ou \`pg_restore -l\` **bloqueia o deploy**.

### Deploy canonico, em ordem API depois frontend

\`\`\`bash
cd ~/projetos/delpi-central
./infra/scripts/up-prod-sequential.sh --build it-portal-api
# Confirmar container saudavel e migration V009 aplicada antes de prosseguir:
docker inspect --format '{{.State.Health.Status}}' delpi-it-portal-api
docker logs --tail 120 delpi-it-portal-api
# Somente se saudavel e com V009 aplicada:
./infra/scripts/up-prod-sequential.sh --build it-portal
docker ps --filter name=delpi-it-portal --format 'table {{.Names}}\t{{.Status}}'
\`\`\`

A ordem API -> frontend evita deixar formulario exposto com backend ainda antigo. Se o primeiro comando falhar, **nao executar** o segundo.

## Registro estrutural do manifesto (passo humano indispensavel)

No Portal Admin: **Aplicacoes -> Portal de TI -> Manifesto -> Publicar nova versao**, enviando o arquivo \`plugins/it-portal/it-portal.manifest.json\` da release (versao \`0.3.4\`).
- A mudanca adiciona permissao de computadores desde G1-API e a rota de computadores no G1-UI; exige **nova versao estrutural** pelo fluxo do Core (\`POST /core-api/admin/apps/register\`), nunca edicao cosmetica \`PUT /manifest\`.
- Conferir historico de versoes apos registro; nao registrar a mesma versao de novo se ja constar ativa.
- Conceder \`it-portal.computers.view\` (leitura) e \`it-portal.computers.manage\` (escrita) somente a papeis autorizados; confirmar que so \`computers.manage\` nao basta para salvar sem \`computers.view\`.
- Nenhuma permissao \`remote.*\` ativa.

## Pos-publicacao: evidencias para marcar implantado

1. API \`/openapi.json\` contem rotas \`/workstations\`; container \`delpi-it-portal-api\` saudavel.
2. V009 registrada em \`it_portal.schema_migrations\` (version=9) **somente por consulta read-only**. Falha impede liberar funcionalidade.
3. Frontend \`remoteEntry.js\` responde JS, nao 404/HTML; \`delpi-it-portal\` sem loop de restart.
4. Com perfil autorizado, menu **Computadores**, lista, cadastro de UMA maquina ficticia/de laboratorio, editar, pesquisa, arquivar/restaurar e historico funcionando.
5. Perfil sem acesso recebe 403 e nao ve nem consegue operar a area; Core/RBAC revogado bloqueia escrita.
6. Servidores, controle restrito de servicos Windows e home do Portal de TI continuam funcionais.
7. Nenhuma alegacao de dispositivo online ou botao **Conectar** antes do G2/G3 e de G0-SEC aprovado.

## Testes pendentes registrados anteriormente

- G1-DOM em copia correta de codigo G1-API: **19 testes isolados passaram**; \`test_local_service.py\`: PASS. Teste integrado Postgres e suite TypeScript/CI real ainda **nao verificados**.
- Registrar as saidas reais de \`npm test\`, \`npm run lint\`, \`npm run build\`, \`pytest\` e Postgres em homologacao. Se qualquer falha comprometer a release, interromper a implantacao.
- **Nao rodar** o fixture de PostgreSQL descartavel (\`IT_PORTAL_TEST_DSN\`) apontando para ambiente produtivo: o fixture cria e deleta bancos.

## Falhas e rollback

- Manter backups, imagens e codigo de release anterior; nao usar \`git reset --hard\` nem descartar trabalho de outros desenvolvedores.
- Se o novo frontend falhar: suspender permissao do menu, reverter a imagem do frontend segundo o runbook canonico.
- Se a nova API falhar apos V009: preservar a nova tabela e historico, usar imagem da API anterior de forma controlada; migrations sao imutaveis e nao devem ser apagadas/reescritas.
- Se houver falha de autorizacao, revogar as permissoes novas e escalar a validacao, sem habilitar bypass.
- Apos resultado, atualizar este documento, \`README.md\`, \`EXECUTION-LOG.md\` e issue #179 com HEAD real, comandos, logs sanitizados, versionamento, backup (sem dados sensiveis), testes e resultado.

**Nao confundir autorizacao para publicar com deploy concluido.** Proximo estado: \`IMPLANTADO\` somente quando evidencia humana/tecnica confirmar.
