# Documento 87 — Ciclo 3 · Abertura de escopo e design condicionado da Central de Fechamento

**Produto:** Portal Controladoria & Finanças — Minha DELPI  
**Funcionalidade:** Central de Fechamento  
**Processo:** PROC-0072  
**Origem:** aceite do PO ao encerramento documental do Ciclo 2 (doc 86), com direção de iniciar o Ciclo 3 pelo design **read-only**.  
**Natureza:** abertura documental / inventário / decisões / contratos candidatos.  
**Estado:** `DESIGN_INTAKE_OPEN` (marco administrativo, não gate G1–G6). `IMPLEMENTATION_AUTHORIZED=NO`.

## 1. Baseline e limites

O Ciclo 2 encerrou sua investigação documental com **47/60** gates de coleta (78,3%), **55/90** de auditoria (61,1%) e **0/15** itens integralmente homologados. Contagem correta de prontidão do doc 86 §8: **11 itens READY_WITH_CONSTRAINTS** (R01, R02, R05–R12, R15) e **4 BLOCKED_BY_OWNER** (R03, R04, R13, R14). Todos mantêm G6 PENDING.

A distinção técnica é mandatória: a sequência MATA320/MATA300/MATA330/MATA280 foi identificada/correlacionada, porém a **função interna que escreve SB9/atualiza MV_ULMES** depende de E5; não alegar prova direta de insert ou homologação funcional.

Documentos de authority: instruções oficiais do arquiteto, regras `.cursor` aplicáveis, ADRs/contratos/HEAD, README, doc 80 §0 e §§46–48, docs 47, 56/57/78, 81–86. TÉO é autoridade AS-IS e proveniência; GitHub é authority TARGET.

## 2. Direção de produto aprovada para estudo

**Iniciar o Ciclo 3 pela especificação de uma experiência read-only da Central de Fechamento**, dedicada à consulta do estado da competência, visão por filial, andamento/etapas e evidências associadas, conforme contratos e dados já existentes. Esta direção aprova **planejamento e design**, não criação de endpoint, escolha de persistência ou implementação.

Fora do primeiro escopo proposto: executar fechamento, recálculo, refaz saldos, reabrir competência, alterar dados Protheus, escrever estados do wizard e orquestrar jobs.

Manter já decidido: CPV mensal **LIVE** (doc 80 §40); MOD E6=C como direção de produto sem autorização de runtime (doc 81).

## 3. Inventário obrigatório antes de desenho de contrato

Para cada necessidade, identificar `owner → consumer → contrato existente → use case → adapter/repository → producer → campos → segurança → teste → evidência`:

- Competência e filial: `MV_ULMES`, regra de cutoff, existência de interface contratual (não presumir).
- Snapshots de fechamento: SB9 por `B9_DATA`, `stock_value_official_closure_sql`, `stock_value_historical_sql`.
- Custo de reposição: `B1_CUSTD` e `standard_cost`, sem confundir com custo médio.
- Acompanhamento: histórico e status do wizard de Acompanha Custos, com provenance e regras de acesso a inventariar.
- Evidências/paridade: relatórios R01–R15 e artefatos já reconciliados, sem transportar dados sensíveis para Git.
- CPV: `GET /supplies/cpv` existente; reuso parcial e sem reescrita da regra.
- UI: inventariar componentes existentes em `@delpi/plugin-ui` e seguir padrão visual vigente antes de criar wireframes.

Search miss não equivale a ausência; `TARGET` não equivale a contrato implementado. Antes de qualquer novo scaffold de API, inventariar portais/APIs atuais e o padrão efetivo da plataforma.

## 4. Boundaries e segurança não negociáveis

Identidade congelada: plugin `controllership-finance`; MFE `plugins/controllership-finance` em `/apps/controllership-finance`; BFF `controllership-finance-api` em `/apps/controllership-finance-api`. Permissions **somente** `controllership-finance.access` e `controllership-finance.manage`.

MFE consome a própria BFF para contratos do Portal. `api-delpi` mantém SQL/regras TOTVS; Core é authority de effective permissions e usuários; `strategic-indicators-api` mantém metas/indicadores. Integração por HTTP/evento/contrato, nunca import de domain/application de outro contexto ou DB vizinho como API.

JWT identifica, não autoriza sozinho. Backend fail-closed: `capability AND resource_scope/ownership AND business_rule`. Filial é dimensão/escopo de recurso, não permission. Nenhum secret no frontend, prompt ou log comum.

Páginas comuns do Portal a preservar: Início, Visão geral, Sala de interação, Minhas tarefas, Administração e Ajuda; página do usuário como deep route. `@delpi/plugin-ui` first, UX PT-BR, teclado/foco, mobile/desktop, temas claro/escuro na mesma árvore e Help acompanhando feature. Nada está autorizado a implementar nesta fase.

## 5. Decisões reais a levar ao PO — DECISION_REQUIRED

| ID | Decisão | Opções a avaliar | Impacto / recomendação provisória |
|---|---|---|---|
| C3-D01 | Qual recorte mínimo de consulta do fechamento? | (A) competência/filial + estado de dados comprovado; (B) também status do wizard; (C) incluir evidências e divergências detalhadas | **A** como ponto inicial de design; B/C só depois de inventário de contratos, owners e aceite do escopo |
| C3-D02 | Qual é a semântica pública de estado? | (A) separar cálculo, persistência, conferência, homologação; (B) estado único `fechado` | **A** evita equiparar `MV_ULMES` ou SB9 a G6 |
| C3-D03 | Como tratar reabertura na primeira entrega? | (A) mostrar apenas indicação/histórico read-only quando provado; (B) excluir da V1 | **B** até E12.6; jamais executar |
| C3-D04 | Onde expor status/competência não disponível em contrato? | (A) estender contrato do contexto owner após inventário; (B) adiar campo; (C) criar nova persistência | **A ou B** condicionados ao inventário; C não recomendado sem necessidade provada |
| C3-D05 | Qual critério funcional de homologação? | (A) aceite explícito da Controladoria por item/competência; (B) inferência técnica por SB9/`MV_ULMES` | **A**, condicionado a E12.7 e owner |
| C3-D06 | Como tratar dependências não resolvidas em design? | (A) excluir do MVP e acompanhar E1–E12; (B) incluir como informação parcial com proveniência e aviso | Preferir **A** em superfícies não demonstradas; B apenas mediante AC verificável |

Nenhuma recomendação da tabela equivale a decisão tomada ou a contrato autorizado. Solicitar decisão explícita antes de fixar boundary, payload, persistência, ciclo de vida ou regra de homologação.

## 6. Entregáveis do primeiro pacote de design (sem código)

1. **Inventory-first:** APIs/portais, contratos, producers/consumers, padrões de auth, UI e testes no HEAD.
2. **Mapa de jornadas e informações:** usuário, competência, filial, evidências, estado técnico versus homologação, cenários sem dados, erros e permissões.
3. **RQ/AC rastreáveis:** cada requisito vinculado a R-ID, regra BR, evidência, owner e teste; estado `PROVEN/TO_INVENTORY/TARGET`.
4. **Matriz de reuso:** `REUSE_CONFIRMED/REUSE_PARTIAL/NOT_EQUIVALENT/PENDING_EVIDENCE/TARGET`, por bounded context.
5. **Propostas de contratos**, não definições aprovadas, com lacunas e decisão material destacadas.
6. **Mapa de UI** com correspondência a `@delpi/plugin-ui`, padrões comuns do Portal e necessidades de Help.
7. **Plano page-by-page** e DoD proposto, sem implementação.
8. **Handoff de decisões e dependências** E1–E12; G6×15 continua PENDING.

## 7. Gates de transição

- **Ciclo 3 / intake e design inicial:** aberto pela direção do PO, documental.
- **Contrato/design definitivo:** somente após ownership, reuso, RQ/AC e decisões materiais explícitas.
- **Runtime:** **bloqueado** até gate transversal explícito, depois autorização page-by-page. Não criar scaffold, migration, endpoint, componente ou integração.
- **Homologação funcional:** continua G6 PENDING até evidência/aceite humano, inclusive para relatórios tecnicamente reconciliados.

## 8. Primeira rodada sugerida ao Devin

`CF-C3-01-READONLY-CLOSING-INVENTORY-AND-DECISION-PACK-001`

Modalidade `READ_ONLY + DOCUMENTATION_ONLY`. Ler HEAD/status + authorities; inventariar contratos e UI existentes, rastrear R15/R12 e R05–R11 pertinentes, produzir RQ/AC candidatos e pacote C3-D01..D06 para o PO. **Não implementar, não editar contratos de runtime e não afirmar G6**.

**Saída esperada:** relatório de inventário + opções/impactos/recomendação + decisão requerida + plano de design por página, preservando referências a docs 47/80/82/85/86. O GPT fará REVIEW antes de qualquer rodada de implementação.
