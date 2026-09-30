# Delpi MES

## Objetivo

O **Delpi MES** é a plataforma gerencial MES da Delpi destinada à supervisão dos centros de trabalho, análise de estados produtivos, análise de paradas, histórico dos runs e, em fases futuras, capacidades de Performance, Qualidade e OEE.

Identificadores reservados para as próximas fases:

- plugin: `delpi-mes`;
- API/BFF: `delpi-mes-api`.

## Ownership atual

```text
production-pulse-api
    → telemetria e hardware
production-control-api
    → owner atual dos fatos MES
/integrations/mes/*
    → contrato interno S2S (leitura gerencial + administração governada
      do catálogo de motivos de parada)
plugins/delpi-mes
    → futura interface gerencial
    ↓ JWT
delpi-mes-api
    → BFF gerencial stateless/read-only
    ↓ S2S
production-control-api
    → owner e persistência dos fatos MES
```

O ownership dos fatos MES permanece no `production-control-api` nesta etapa. Uma futura refatoração poderá extrair esse domínio, mas ela não faz parte do MVP inicial do Delpi MES. O Production Control não se torna um guarda-chuva gerencial: PCP, Delpi MES e OEE permanecem capacidades com fronteiras próprias.

Não há banco, tabela ou cópia de fatos do Delpi MES nesta fase. Production Runs, estados operacionais, paradas, segmentos de contagem, motivos, timeline e auditoria continuam no schema do owner atual.

## Contrato interno

As rotas exigem `API_DELPI_INTERNAL_SERVICE_TOKEN`, aceito em `X-Delpi-Service-Token` ou `Authorization: Bearer ...`. O consumidor previsto deve enviar `X-Delpi-Caller-App: delpi-mes-api`; esse header identifica o chamador para operação, mas não substitui a credencial S2S. JWT humano e sessão de bancada não concedem acesso.

| Método | Endpoint | Finalidade |
|---|---|---|
| GET | `/integrations/mes/work-centers/live?branch=01` | Snapshot consolidado dos runs ativos e estados operacionais atuais da filial |
| GET | `/integrations/mes/runs/{runId}/timeline` | Timeline do run com a mesma regra de duração do cockpit, sem sessão de bancada |
| GET | `/integrations/mes/downtimes?branch=01&workCenter=&from=&to=&page=1&pageSize=50` | Histórico paginado de paradas MES |
| GET | `/integrations/mes/work-centers/{workCenter}/timeline?branch=01&from=&to=` | Timeline do CT no período, unindo múltiplos runs/OPs com sobreposição temporal |
| GET | `/integrations/mes/downtime-reasons` | Administração: lista motivos de parada **ativos e inativos** |
| POST | `/integrations/mes/downtime-reasons` | Administração: cria motivo (`code` técnico imutável; 201; duplicado → 409) |
| PUT | `/integrations/mes/downtime-reasons/{code}` | Administração: edita `label`/`category`/`requiresNote`/`sortOrder` (não renomeia `code`; 404 se inexistente) |
| PATCH | `/integrations/mes/downtime-reasons/{code}/active` | Administração: ativa/desativa motivo (`setup` é protegido — `active=false` → 409) |

Todas as respostas usam o envelope `{ success, message, data }`. `pageSize` é limitado a 100. Timestamps são timezone-aware.

### Administração do catálogo de motivos (Cadastros — Etapa 1)

O catálogo único continua sendo `production_control.downtime_reason_catalog` — sem tabela, schema ou cópia paralela. Regras: `code` imutável após a criação, **não existe DELETE físico** (desativação preserva `downtime_events.reason_code` e o histórico), `setup` não pode ser desativado enquanto a classificação automática depender dele, e os campos OEE (`default_planned`, `default_counts_as_availability_loss`) ficam fora do contrato administrativo. O catálogo é global (sem `branch`). O cockpit público continua recebendo somente motivos ativos — desativar esconde do operador, não do histórico nem da visão administrativa. Detalhes: [MES-STATE-DOWNTIME.md](../production-control/MES-STATE-DOWNTIME.md) § 12.

O filtro temporal de paradas usa sobreposição de intervalos:

```text
event.started_at < to
AND (event.ended_at IS NULL OR event.ended_at >= from)
```

Assim, uma parada iniciada antes da janela e encerrada dentro dela é retornada. A rota live deriva seus contadores dos mesmos itens retornados, não consulta timeline e não consulta o Production Pulse por centro. Run ativo sem estado aberto retorna `operationalState: null` e `integrityStatus: incomplete`; a leitura não repara fatos.

## Fases

1. **Fase 0 — Contrato e Fundação (concluída):** contrato S2S somente leitura dentro do owner atual.
2. **Fase 1 — `delpi-mes-api` (implementada):** BFF gerencial autenticado, stateless e consumidor de `/integrations/mes/*`.
3. **Fase 2 — plugin `delpi-mes` + Manifesto/RBAC (implementada):** shell federada, rotas, filial, permissões declaradas e manifesto pronto para importação manual; sem registro automático.
4. **Fase 3 — Monitoramento Industrial MVP (implementada):** polling consolidado de 5 s, pausa hidden/offline, timers corrigidos por relógio do servidor, filtros locais e timeline sob demanda sem N+1. A visão cobre somente runs ativos e ainda não inclui telemetria offline.
5. **Fase 3.1 — Histórico diário do CT (implementada):** o detalhe do Monitoramento passa a listar todos os estados do CT no dia corrente (início do dia local → agora), cobrindo múltiplos runs/OPs via `GET /work-centers/{workCenter}/timeline`. Carregamento lazy ao abrir o CT, refetch pontual quando a assinatura do run muda, sem polling próprio e sem N+1. O grid de Monitoramento permanece inalterado.
6. **Cadastros — Etapa 1 (implementada):** contrato S2S administrativo do catálogo de motivos no `production-control-api` (`/integrations/mes/downtime-reasons*` — ver seção acima).
7. **Cadastros — Etapa 2 (implementada):** superfície humana no `delpi-mes-api` (`GET/POST/PUT/PATCH /registrations/downtime-reasons*`), exigindo principal humano + `delpi-mes.access` + `delpi-mes.downtime-reasons.manage`. Catálogo global — sem `branch` nem permissão de filial; principal S2S é rejeitado mesmo como superadmin. O BFF encaminha ao gateway S2S, aplica allowlist de DTO (campos OEE nunca vazam) e preserva 404/409/422 do owner — a escrita continua pertencendo ao Production Control. Sem frontend e sem declaração da permissão no manifesto nesta etapa.
8. **Cadastros — Etapa 3 (implementada):** área **Cadastros** no MFE `plugins/delpi-mes` (`/apps/delpi-mes/registrations` + `/registrations/downtime-reasons`), visível apenas com `delpi-mes.downtime-reasons.manage` ou superadmin humano e bloqueada por URL direta sem a permissão. O catálogo é global: a área não exige filial, oculta o seletor e indica «Cadastro global». A página lista ativos e inativos com busca e filtro locais, cria/edita motivos (`code` imutável na edição), desativa com confirmação preservando o histórico e reativa com feedback; `setup` desativado → 409 do BFF exibido como conflito funcional. Sem DELETE, sem campos OEE, sem `branch` nas chamadas. Manifesto `0.2.0` declara a permissão `.manage` e as duas rotas (`showInMenu: false`) — pronto para importação manual, sem registro automático nem provisionamento de RBAC. Auditoria administrativa permanece fora de escopo.
9. **Fase 4 — Histórico e Paradas:** exploração gerencial dos runs e downtimes.
10. **Fase 5 — Hardening do MVP:** capacidade, operação, observabilidade e homologação.
