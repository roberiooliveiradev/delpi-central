# GLPI #887 - Etapa 3: prévia administrativa de acessos semanais

## Objetivo e limites

Preparar a apuração de acessos por colaborador e por ferramenta para o
Delpi Reports, **sem** agendamento, destinatário automático, envio de e-mail
ou acesso direto por supervisores nesta entrega.

O Portal RH é fonte da hierarquia de gestor; a Core só aceita
`user_hr_registrations` com matrícula confirmada e usuário ativo.
A PR #285 de reconciliação fornece sugestões administrativas fracas por
nome que **nunca** participam desta apuração.

Auditoria inicial de 18/11/2026 para gestor `20001` no Portal RH:
63 pessoas, 9 candidatos RH, 54 sem UserProfile.collaborator.
**Nenhuma dessas contagens comprova UUID Core já verificado.**

## Endpoint restrito

`GET /admin/organization/managers/{registration}/weekly-app-opens`

- Autenticação JWT do usuário, exigindo conjuntamente `rbac.manage` e
  `users.manage` (ou superadmin). Sem autorização: 401 ou 403.
- Sem token S2S genérico, sem UI de gestor e sem exposição pública.
- `week_start=AAAA-MM-DD` opcional, sempre segunda-feira da semana
  **concluída**. Sem parâmetro, a última semana completa.
- `include_indirect=true|false` (default true); somente equipe ativa RH.
- `details=true|false` (default false); apenas administrador autorizado
  acessa nomes, matrículas e distribuição por ferramenta.
- Rate limit 10/min e limite 500 membros por equipe; só 90 dias de histórico
  podem ser consultados (coerente com retenção de uso da Core).
- Semana local America/Sao_Paulo: segunda 00h inclusiva até a próxima
  segunda 00h exclusiva; banco compara timestamps UTC.
- `app_usage_events`, apenas eventos de abertura para apps com
  `apps.type != backend-only`. Chamadas à API técnica e duração de
  sessão não se confundem com abertura de ferramenta.
- Eventos internos são sujeitos a debounce/consentimento: **aberturas
  registradas** não equivalem necessariamente a visitas únicas, cliques
  ou pessoas que realmente entraram no sistema.

## Contrato resumido (dados fictícios)

```http
GET /admin/organization/managers/20001/weekly-app-opens?week_start=2026-11-09
Authorization: Bearer <JWT_ADMIN>
```

```json
{
  "source": "app_usage_events",
  "managerRegistration": "20001",
  "includeIndirect": true,
  "weekStart": "2026-11-09",
  "weekEndExclusive": "2026-11-16",
  "timezone": "America/Sao_Paulo",
  "teamCount": 63,
  "verifiedMapped": 8,
  "unmapped": 55,
  "consentGranted": 7,
  "consentNotGranted": 1,
  "withRecordedOpens": 5,
  "withoutRecordedOpens": 2,
  "totalRecordedOpens": 26,
  "readOnly": true,
  "reportSent": false
}
```

As contagens acima são EXEMPLOS FICTÍCIOS, não dados da Core produção.

`details=true` acrescenta `members[]` com matrícula textual exata,
nome, filial, relacionamento, `usageStatus`, `totalRecordedOpens`
e `apps[]` com `appId`, `appName` e `recordedOpens`. A resposta
não contém e-mail, rota, tempo de sessão, consentimento histórico,
dados de CPF ou UUID candidato por nome.

Status por pessoa:
- `unmapped`: não existe vínculo Core verificado, contagem **null**.
- `consent_not_granted`: não há consentimento vigente `usage_tracking`,
  contagem **null** e nenhum evento exposto.
- `no_recorded_opens`: consentimento e vínculo verificados; eventos
  de abertura não registrados naquela semana, contagem **0**.
- `recorded_opens`: aberturas registradas para apps com interface.

A ausência de consentimento/vínculo **não significa zero acesso**.
Mesmo com consentimento, zero evento não comprova falta de utilização.
Se o rastreamento estiver desligado, zero evento continua inconclusivo.

## Privacidade, segurança e execução

- Consultas read-only; sem migração, cron, permissão de supervisor,
  arquivo exportável, envio de e-mail ou criação de vínculo.
- Validações de vínculo e consentimento por Core; SQL filtra novamente
  conta ativa, consentimento concedido, intervalo e lista verificada.
- Mudança ou revogação de consentimento não autoriza uso de dados
  coletados anteriormente; a revogação já dispara purge na Core.
- Antes de entregar relatórios individualizados aos gestores:
  formalizar finalidade/base legal LGPD, transparência aos titulares,
  autorização da lista de destinatários, necessidade/proporcionalidade
  e política de retenção; não reutilizar automaticamente a finalidade
  `usage_tracking` para avaliação individual dos colaboradores.
- Administração pode estudar a prévia com acesso restrito, **não**
  encaminhar os resultados nominais a gestores nesta etapa.

## Testes no checkout de desenvolvimento

```bash
cd core-api
pytest app/tests/test_glpi_887_weekly_team_usage.py app/tests/test_glpi_887_weekly_usage_sql.py -q
```

Apenas o usuário responsável aprova e faz merge da PR. Não há
verificador externo/independente após abertura de PR.
Não executar `pull`, `reset`, `clean` ou `stash` no
Portal RH de produção (o diretório contém desenvolvimento local do Cursor).
Quando autorizada, a publicação desta etapa envolve apenas a imagem
`core-api` do monorepo, não o portal-rh nem o plugin Reports.

## Próxima etapa

Depois de apurar o número **real de usuários Core já vinculados e consentidos**
(e não só os 9 candidatos RH), desenvolver provider específico do
Delpi Reports e autorização por supervisor, com envio semanal limitado
à equipe e após conclusão da revisão de privacidade.
