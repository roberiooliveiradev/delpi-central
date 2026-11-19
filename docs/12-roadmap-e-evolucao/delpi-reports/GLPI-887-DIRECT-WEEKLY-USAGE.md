# GLPI #887 - Delpi Reports: acessos semanais de subordinados DIRETOS

## Regra de negócio aprovada em 18/11/2026

**Cada gestor recebe unicamente os seus subordinados diretos**; nem o
administrador da agenda nem o gestor pode expandir o escopo desse provider
para equipe completa/indireta. Exemplo: A gerencia B; B gerencia C.
Relatório de A contém B, nunca C. Relatório de B contém C.

A hierarquia é obtida em tempo real do Portal RH via Core API; considera
os **colaboradores ativos atualmente associados** ao gestor. Histórico
de transferência gerencial ainda não é reconstruído, mesmo que os
eventos consultados sejam da semana anterior.

## Arquitetura

```text
Portal RH (hierarquia) -> Core API -> app_usage_events + consentimento
   GET /integrations/organization/managers/{reg}/reports/direct-weekly-opens
   X-Delpi-Service-Token: [credencial específica para Reports]
           |
           v
api-delpi / Delpi Reports
   provider team_direct_app_opens_weekly
   definição por gestor + agenda semanal (segunda)
   render HTML corporativo -> verificação destinatário -> Graph
           |
           v
Conta Core VERIFICADA do mesmo gestor (apenas 1 destinatário)
```

A integração Core ↔ Reports usa
`CORE_REPORTS_DIRECT_USAGE_SERVICE_TOKEN`: não aceitar
`CORE_ORGANIZATION_READ_SERVICE_TOKEN` nem
`CORE_API_INTEGRATIONS_SERVICE_TOKEN`. O token fica somente nos
contêineres Core e api-delpi, nunca no frontend, nem no corpo da PR.
O endpoint é somente GET e nunca grava vínculos.

## Proteções implementadas

1. A rota S2S **impõe no servidor** `include_indirect=False`,
   `include_inactive=False`, `details=True`; ignora parametrização
   por usuário que tentaria expandir o escopo.
2. Rejeita qualquer linha que não tenha `relationship="direct"`;
   rejeita gestor sem vínculo RH↔Core verificado e ativo.
3. O recipient é resolvido **pelo próprio Core** a partir da matrícula
   verificada do gestor, do UUID e do e-mail atual; nenhum remetente
   ou destinatário é informado no request do provider.
4. O provider confere contrato, gestor, semana fechada, fuso
   `America/Sao_Paulo`, linhas diretas, cobertura e totais de eventos.
5. **Antes do Graph**, o motor confere que há EXATAMENTE 1 destinatário
   com `userId` E e-mail idênticos aos da conta Core verificada do
   gestor; uma lista genérica, outro gestor ou e-mail alterado são
   recusados. É conferido a cada execução (manual/agenda).
6. Só retorna aberturas de aplicativos de interface para empregados
   com identidade e consentimento `usage_tracking` vigentes.
   Ausência de vínculo/consentimento vira **Indisponível**, sem
   revelar a justificativa pessoal ao gestor. Se o contador for 0,
   exibir **Sem abertura registrada**, não "não usou".
7. A agenda desse provider só aceita **segunda-feira** semanal.
   Se alguém tentar programar `weekStart` fixo em uma agenda,
   a execução falha para evitar reenvio de semanas antigas.
8. Não armazena uma cópia HTML nominal no volume de artefatos;
   mantém somente metadados usuais de run e delivery.
9. `REPORTS_DIRECT_WEEKLY_DELIVERY_ENABLED=false` por padrão:
   recusa **envio manual, por evento e pela agenda**, e impede
   habilitar agenda de subordinados diretos. O envio só fica disponível
   após decisão administrativa consciente.
10. Nenhum dado é automaticamente enviado ou destinatário cadastrado
    nesta PR. Não altera matrículas/vínculos já registrados.

## Conteúdo do e-mail

**Assunto:** Minha Delpi | Acessos semanais da equipe direta | DD/MM a DD/MM.

Tabela: `Colaborador | Aberturas registradas | Ferramentas`.
Cada ferramenta aparece com sua contagem agregada, ex.:
`Portal RH: 3; Delpi Reports: 1`.

Um subordinado direto sem eventos autorizados segue na lista com
`Indisponível`, sem informação sobre consentimento; quando o
rastreamento permitido não registrou abertura, mostra 0. Um evento
registrado não é prova de sessão única ou horas de trabalho.

## Passos para publicação (após merge EXCLUSIVO do solicitante)

1. Revisar as alterações locais no checkout `delpi-central` da produção.
   Não usar `git reset --hard` nem `git clean`.
2. Fazer pull fast-forward da `main` se não houver conflito.
3. Gerar uma credencial forte exclusiva, configurar no `infra/.env`
   em `CORE_REPORTS_DIRECT_USAGE_SERVICE_TOKEN`, sem partilhá-la
   em tickets ou console. Manter
   `REPORTS_DIRECT_WEEKLY_DELIVERY_ENABLED=false`.
4. Reconstruir **core-api** e **api-delpi** pela fase `core` e
   **reports** pela fase `mfe`, separadamente. A inicialização da
   Core ou api-delpi pode trazer migrações pendentes preexistentes.
5. Validar contas Core verificadas dos gestores e estado da equipe direta
   por consulta administrativa `GET /admin/organization/managers/{reg}/weekly-app-opens?include_indirect=false`.
6. No Delpi Reports, criar **uma definição por gestor**,
   provider `team_direct_app_opens_weekly`, parâmetro
   `managerRegistration` com zeros preservados e sem
   `weekStart` fixo. Escolher apenas a conta Core do gestor,
   e agenda semanal **segunda 08:00 (America/Sao_Paulo)**,
   com checkbox de habilitação **desligado**.
7. Revisar finalidade do monitoramento de colaboradores, base legal,
   proporcionalidade, transparência, destinatários e política de
   retenção antes de liberar envios nominais (LGPD). Não presumir que
   o consentimento de coleta `usage_tracking` é autorização suficiente
   para distribuir comportamento individual a gestores.
8. Somente depois de aprovado e comunicado, mudar a flag de envio para
   `true`, reconstruir api-delpi, habilitar agendas dos gestores e
   acompanhar `report_runs` + `report_deliveries`.

### Comandos sugeridos

```bash
cd /home/operador/projetos/delpi-central
git branch --show-current
git status --short
git fetch origin main
git diff --name-only HEAD..origin/main
git pull --ff-only origin main

# Após configurar a credencial em infra/.env SEM ativar envios:
bash ./infra/scripts/up-prod-sequential.sh --dry-run --fase core --build core-api api-delpi
bash ./infra/scripts/up-prod-sequential.sh --fase core --build core-api api-delpi
bash ./infra/scripts/up-prod-sequential.sh --dry-run --fase mfe --build reports
bash ./infra/scripts/up-prod-sequential.sh --fase mfe --build reports

docker ps --filter name=delpi-core-api
docker ps --filter name=delpi-api-delpi
docker ps --filter name=delpi-reports
```

Antes dos builds confirmar que nenhum outro serviço/migração inesperada
será incluído. O `portal-rh` de produção **não** é alterado.

## Testes incluídos na PR

```bash
cd core-api && pytest app/tests/test_glpi_887_direct_manager_reports.py -q
cd ../api-delpi && pytest tests/test_glpi_887_direct_weekly_reports_provider.py tests/test_glpi_887_reports_delivery_policy_and_schedule.py -q
```

Os testes são arquivos versionados e **não** representam verificação
independente pós-PR. A decisão de merge é exclusivamente do solicitante.

## Etapas seguintes

- Verificar quantas matrículas dos gestores e subordinados estão
  efetivamente vinculadas após a operação no painel de identidade.
- Preparar as definições e destinatários reais para cada gestor
  (sem criar vínculo por nome ou e-mail automaticamente).
- Habilitar entrega controlada somente depois das decisões de
  privacidade e aceitação operacional; observar falhas Graph.


## Evolução: relatório por colaborador + duração média por aplicativo

A matrícula `20001` foi apenas o piloto. O provider recebe a matrícula
textual em cada definição de Reports e **não contém um gestor fixo**.
Um relatório será gerado para cada gestor autorizado, em definição própria,
com seu único destinatário Core verificado e somente seus subordinados
**diretos ativos** resolvidos no Portal RH.

**Importante:** publicar este código não cria automaticamente definições
para todos os gestores nem liga o envio. Identificar e configurar os
demais gestores, conferir os vínculos RH/Core e a finalidade de envio
é a próxima etapa operacional.

### Novo layout de e-mail

O corpo HTML do Delpi Reports exibe:
- resumo do período, número de pessoas da equipe direta e total de
  aberturas registradas;
- seção independente **por colaborador RH**;
- dentro de cada seção, tabela de **aplicativo | aberturas | tempo
  médio estimado por sessão registrada**;
- sem eventos: `Sem abertura registrada` (não equivale a não ter
  trabalhado);
- sem dados autorizados: `Dados indisponíveis`, sem expor a razão
  nominal do consentimento ao gestor;
- aplicativo com eventos mas sem duração: `Não medido`, nunca `0 min`.

O layout continua table-based, com marca Delpi e escaping de
todos os nomes fornecidos pelo RH e pelo cadastro de aplicativos,
para compatibilidade e segurança em Microsoft Outlook.

### Origem e cálculo do tempo

**Já existe coleta!** O banco Core registra `usage_sessions`
(model `UsageSession`) com `user_id`, `app_id`, `started_at`,
`ended_at`, `duration_seconds` e fonte de encerramento.

A nova consulta `app_session_durations` agrega por **usuário Core
verificado + aplicativo** no intervalo da semana já encerrada:
- quantidade de sessões registradas;
- soma das durações, em segundos;
- média = soma das durações / quantidade de sessões registradas.

**Não dividir duração pelo número de aberturas**, pois a contagem de
eventos em `app_usage_events` não equivale à contagem de sessões.

Segurança da consulta:
- somente UUIDs dos colaboradores presentes na hierarquia autorizada;
- somente `usage_tracking` atualmente concedido e usuário ativo;
- sessão com `app_id` preenchido e aplicativo com interface;
- exclui `backend-only` e presença do portal (`app_id = NULL`);
- período aplicado a `UsageSession.started_at` em UTC;
- somente durações positivas e persistidas;
- relatórios agregados sem detalhes não fazem consulta adicional de tempo.

### Limites de precisão e disponibilidade

A duração representa o tempo decorrido de sessões abertas por socket
até fechamento, desconexão ou TTL. Pode incluir períodos de ociosidade
e não é uma medida de interação ativa, foco do navegador, atendimento,
presença em posto ou produtividade. O registrador limita cada segmento
a até 8 horas.

O período é definido pela data de **início** da sessão, sem recorte
matemático de segmentos atravessando a fronteira semanal; não tratar
o valor como tempo de uso exato dentro do calendário. O aplicativo pode
ter aberturas registradas sem uma sessão com duração persistida, inclusive
por falhas de encerramento, desconexão ou coleta não aplicável.
Esses casos são apresentados como **Não medido**.

Antes de liberar e-mails reais, validar a cobertura das sessões em
produção em cada equipe. Caso a cobertura seja insuficiente, manter
somente aberturas no relatório e reconsiderar a qualidade da telemetria.
A regra de envio `REPORTS_DIRECT_WEEKLY_DELIVERY_ENABLED=false`
permanece inalterada.

### Pós-merge (somente com autorização do solicitante)

```bash
cd /home/operador/projetos/delpi-central
git status --short
git pull --ff-only origin main

# core-api e api-delpi: sem rebuild do Reports MFE, pois o HTML é gerado na API
bash ./infra/scripts/up-prod-sequential.sh --dry-run --fase core --build core-api api-delpi
bash ./infra/scripts/up-prod-sequential.sh --fase core --build core-api api-delpi

# Continuar com envio bloqueado ate aceite expresso
```

Teste agregado de cobertura por gestor: consulte o endpoint
`/integrations/organization/managers/{registration}/reports/direct-weekly-opens`
via `api-delpi` com credencial técnica, conte somente quantos aplicativos
possuem `recordedSessions > 0`. Não registrar nomes/e-mails nas saídas
de diagnóstico compartilhadas.

Testes versionados na PR:
```bash
cd core-api
pytest app/tests/test_glpi_887_weekly_usage_sql.py app/tests/test_glpi_887_weekly_team_usage.py -q

cd ../api-delpi
pytest tests/test_glpi_887_direct_weekly_reports_provider.py -q
```
