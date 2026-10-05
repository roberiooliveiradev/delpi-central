# PROC-0072 — Instance Summary Snapshot

> Instance ID: `fa3074bd-c852-44d1-b145-72a2f17043d6`  
> Snapshot: 2026-10-05  
> Source: TÉO instance `resumo_melhoria`

PROC-0072 — ESTADO ATUAL RECONCILIADO 05/10/2026.

AS-IS=CLOSED/ACCEPTED. IMPLEMENTATION=NOT_STARTED.

NAMING / PRODUTO:
- nome oficial: Portal Controladoria & Finanças;
- portal = produto multi-macroprocesso na Minha DELPI;
- Central de Fechamento = primeira funcionalidade/macroprocesso;
- PROC-0072 = primeiro processo implementado;
- "Portal Controladoria/Financeiro" = working label histórico, superseded;
- authority: 31.19.

AUTHORITIES TO-BE:
31 master; 31.1 UX; 31.2 RQ/AC; 31.3–31.12.1 P2; 31.13 P2 residual; 31.14 P3; 31.15 P4; 31.16 P5; 31.17 P6; 31.18 índice/readiness; 31.19 naming; 33 decisões consolidadas; 34 backlog implementação.

DECISÕES FECHADAS:
Q01 B; Q02 B; Q03 C; Q04 C; Q05 B; Q06 A; Q07 C; Q08 A; Q09 A.
Q10 A; Q11 C; Q12 C; Q13 B condicionado a T03.
Q14 B; Q15 C; Q16 B; Q17 B.
Q18 C; Q19 A; Q20 B; Q21 B; Q23 A; Q24 B; Q25 A; Q26 A.
Q27 C; Q28 B; Q29 C; Q30 B.
Q22=PENDING_IMPLEMENTATION até E04/T04.

TARGET:
- ACCESS opera; MANAGE administra; sem permission por botão.
- item excepcional por competência; cancelamento pré-execução=CANCELLED; correção pós-execução por request/review/nova revisão.
- MANAGE pode autoaprovar correção estrutural; approval != evidence validation.
- NOT_APPLICABLE reversível por ACCESS antes de PACKAGE_SENT, com justificativa.
- motivos de rejeição = núcleo + extensões MANAGE.
- attachment roles = catálogo configurável + genérico quando aplicável.
- validator pode ser reatribuído por MANAGE com justificativa.
- P3 sem escrita ERP no V1; cutoff = sinais + confirmação humana; revalidação núcleo automática + reprocessamento manual.
- STOCK_CLOSED deve vir do owner/ERP se houver estado canônico; sem fallback manual silencioso.
- P4 IA sugere e humano confirma; sem escrita ERP no V1.
- P5 Finalizar cria versão; Enviar é separado; pacotes por destinatário; PACKAGE_SENT imutável; conclusão mensal exige pacotes aplicáveis enviados e sem esclarecimento aberto.
- P6 template = draft/publish/effective_from; inativação sem delete.
- notificações canônicas na Minha DELPI; e-mail segue plataforma; sem SLA.
- bancos/contas e demais catálogos operacionais são configuráveis.

PENDING_IMPLEMENTATION_CONFIRMATION:
E01 seed bancário; E02 pós-sacramentação; E03 executor/permissões; E04 canal real de envio; E05 attachment roles; E06 cobertura dos motivos.

TO_INVENTORY:
T01 DAVI/api-delpi; T02 notificações; T03 STOCK_CLOSED/cutoff; T04 capability de envio; T05 Core ACCESS/MANAGE/scopes.

READINESS:
P1/P2/P4/P6=READY_FOR_IMPLEMENTATION_INVENTORY.
P3=READY com stop condition em T03.
P5=PARTIALLY_READY; Q22 depende E04/T04.

Não reabrir decisões fechadas por preferência. Contradição de evidência nova = EXECUTION_DRIFT.
