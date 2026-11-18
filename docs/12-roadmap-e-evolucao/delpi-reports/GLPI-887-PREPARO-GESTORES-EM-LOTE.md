# GLPI #887 | Preparar relatórios semanais para múltiplos gestores

## Fato confirmado em 18/11/2026

O piloto do gestor `20001` recebeu da Core API:
- 7 subordinados **diretos**, 7 usuários vinculados e 5 com dados consentidos;
- 1.925 aberturas registradas na semana 09/11–15/11;
- 46 aplicativos com aberturas, 46 com alguma duração de sessão e
  4.370 segmentos de sessão persistidos.
- O e-mail **não foi enviado** e a flag de envio continua desligada.

**A matrícula 20001 não é o único gestor.** Ela identifica a hierarquia
usada como piloto; outras lideranças dentro dela são descobertas através
de `managerRegistration` dos próprios colaboradores RH.

A contagem de sessões é distinta da contagem de aberturas: desconexões
e flush TTL podem segmentar uma mesma utilização. A média é por sessão
persistida, não por abertura, e não prova produtividade.

## Entrega desta PR

**Core API:** endpoint S2S somente leitura, autenticado pelo token
`CORE_REPORTS_DIRECT_USAGE_SERVICE_TOKEN`:

```text
GET /integrations/organization/managers/{rootRegistration}/reports/eligible-managers
```

Usa o Portal RH oficial com `include_indirect=true` apenas para
**descobrir gestores** dentro da subárvore consultada. Conta os
subordinados **diretos de cada gestor** pelo campo RH
`manager_registration` e valida vínculo Core verificado, usuário Core
ativo e e-mail válido. Gestor sem vínculo/e-mail recebe status de
pendência. **Nunca** expande o escopo do relatório nominal: a apuração
semanal continua `include_indirect=false` para cada matrícula.

**API Delpi:** comando administrativo versionado em
`app.scripts.glpi_887_prepare_manager_reports`:

- Modo padrão = somente prévia; não altera dados.
- `--root` pode ser repetido para hierarquias independentes (SC/ES).
- Deduplica gestores em raízes sobrepostas e detecta divergências.
- Não tenta associar usuários por nome/e-mail e não inclui gestores sem
  Core verificado.
- Identifica definições de relatórios já existentes e as **preserva**.
  Se já existirem múltiplas definições da mesma matrícula, sinaliza
  conflito em vez de sobrescrever ou duplicar.
- `--apply --confirm PREPARAR` só funciona com
  `REPORTS_DIRECT_WEEKLY_DELIVERY_ENABLED=false`.
- Para cada gestor elegível ainda não configurado, prepara
  **uma definição ativa por gestor**, um destinatário único Core
  verificado e agenda para **segunda-feira às 08h** no fuso
  `America/Sao_Paulo`, com **enabled=false**.
- Nenhum e-mail é enviado, nenhuma agenda é habilitada, nenhum vínculo
  RH↔Core é criado/alterado e nenhuma permissão é ampliada.
- Máximo por execução: 12 raízes e 250 gestores distintos.

### Atenção à abrangência

O Portal RH atualmente expõe hierarquia **por gestor**, não um
inventário global de todas as árvores independentes. Portanto,
uma preparação com somente `--root 20001` **não comprova que
toda a Delpi foi coberta**. Para incluir outras hierarquias
independentes, informe também sua matrícula raiz oficial.
Se não souber quais são, confirme com RH antes de considerar a fase
de cadastro completa.

## Execução após merge e publicação

Primeiro, atualizar o checkout com cuidado e reconstruir **apenas**
`core-api` e `api-delpi`; manter a flag de envio desligada:

```bash
cd /home/operador/projetos/delpi-central

git status --short
git fetch origin main
git diff --name-only HEAD..origin/main
git pull --ff-only origin main

bash ./infra/scripts/up-prod-sequential.sh --dry-run --fase core --build core-api api-delpi
bash ./infra/scripts/up-prod-sequential.sh --fase core --build core-api api-delpi

docker ps --filter name=delpi-core-api
docker ps --filter name=delpi-api-delpi
```

Não usar reset/clean/stash; não interferir no Portal RH com arquivos
locais em edição. Verificar migrações pendentes já existentes antes
de qualquer rebuild.

### 1. Prévia (LEITURA, NENHUMA GRAVAÇÃO)

```bash
docker exec delpi-api-delpi python -m app.scripts.glpi_887_prepare_manager_reports \
  --root 20001
```

Para mais raízes (substitua pela matrícula oficial confirmada, sem
adivinhar):

```bash
docker exec delpi-api-delpi python -m app.scripts.glpi_887_prepare_manager_reports \
  --root 20001 --root MATRICULA_RAIZ_ADICIONAL
```

O retorno JSON tem `totalManagersFound`, contagens de
`prepare_disabled`, `already_exists`, `missing_mapping`,
`missing_email`, `duplicate_definitions` e
`requiresAttention` (somente matrícula + motivo, sem e-mails ou
dados nominais). **A prévia deve ser examinada antes do modo apply.**
Não execute `apply` se a abrangência de raízes ainda for duvidosa.

### 2. Preparação (EXIGE AÇÃO EXPLÍCITA)

Após aprovar a lista de gestores e confirmar a flag de envio desligada:

```bash
docker exec delpi-api-delpi python -m app.scripts.glpi_887_prepare_manager_reports \
  --root 20001 --apply --confirm PREPARAR
```

Adicione outros `--root` aprovados conforme necessário. Ao
reexecutar, as definições que já existem são preservadas e não
recebem duplicatas. Se uma criação falhar após o INSERT, uma
definição parcial pode ficar no banco; pare, confira no Reports e
repare administrativamente antes de repetir.

### 3. Conferência no Delpi Reports

Em cada definição preparada:
- Provider `team_direct_app_opens_weekly` e matrícula RH do gestor.
- Uma conta destinatária com UUID e e-mail verificados.
- Agenda semanal, segunda 08:00, `enabled=false`.
- Sem parâmetro `weekStart` fixo.
- Relatório agrupa cada colaborador direto e seus aplicativos, com
  aberturas e média por sessão (se medida).

O motor de envio continua exigindo que o destinatário corresponda ao
gestor validado pela Core **a cada execução**. Não autorizar
distribuição para endereços genéricos ou outros gestores.

### Próximas verificações antes dos e-mails reais

1. Obter a cobertura da lista de gestores de todas as árvores RH.
2. Resolver matrículas `missing_mapping` / `missing_email` no painel.
3. Revisar finalidade, transparência, destinatários e política de
   retenção para relatórios nominais (LGPD).
4. Validar a prévia HTML do e-mail e sua legibilidade no Outlook.
5. Apenas com autorização explícita, habilitar a flag e as agendas.
   Nenhuma dessas ações de envio está incluída nesta PR.

## Testes versionados

```bash
cd core-api
pytest app/tests/test_glpi_887_manager_discovery.py -q

cd ../api-delpi
pytest tests/test_glpi_887_prepare_manager_reports.py -q
```

A PR não inclui mudanças de schema ou migrações. A aprovação/merge
continuam exclusivamente com o solicitante, sem aprovações externas
ou deploy automático.
