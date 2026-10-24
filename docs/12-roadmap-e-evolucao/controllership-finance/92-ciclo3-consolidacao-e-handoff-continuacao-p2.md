# Documento 92 — Ciclo 3 · Estado consolidado e handoff para continuidade da Central de Fechamento

**Data:** 2026-10-24  
**Produto:** Portal Controladoria & Finanças · Central de Fechamento · PROC-0072  
**Natureza:** consolidação do estado documental e preparação de próximo gate, não execução de runtime  
**Baseline remoto consultado:** main `ae2e82a4fbf2f7f1c44a8426d4ddec0d73c43143` antes desta publicação; **HEAD e git status de worktree devem ser reavaliados pelo executor**. O conector GitHub não demonstra worktree local.  
**Estado:** `DOCUMENTATION_CONSOLIDATED_WITH_RESIDUAL` · `NEXT_GATE_PREPARATION` · `IMPLEMENTATION_AUTHORIZED=NO`.

## 1. Resposta de status: o que está consolidado

A consolidação E2E foi realizada, **em nível de etapas, capacidades P1–P6, linhas R01–R15, principais RQ/AC e gaps**, e publicada no [Documento 90](./90-ciclo3-crosswalk-end-to-end-proc0072-teo-rq-ac-portal.md). Não significa que os RQs detalhados de todos os anexos TÉO tenham sido reconciliados literalmente nem que existam contratos físicos para tudo.

| Ciclo/fonte | Material consolidado | Estado e autoridade |
|---|---|---|
| **1 — processo e checklist** | [03 — Evidências e checklist](./03-evidencias-proveniencia-e-rastreabilidade.md); TÉO PROC-0072 docs 04/05/06/07/30/31 etc.; bancos/extratos, baixas, estoque, custos, CC, importação, destinatários e handoffs | Fonte do inventário operacional; cada entregável requer responsável, origem, obrigatoriedade, competência, destinatário e regra de validação. **Não** assumir equivalência 1:1 com grupo Rxx |
| **2 — dados e relatórios** | [47 — gates R01–R15](./47-t01-report-column-audit-tracker-v1.md), [80 — evidências](./80-ciclo2-registro-vivo-investigacao-devin.md), [82 — owners E1–E12](./82-ciclo2-handoff-pacote-evidencias-owners.md), [85 — BR/testes](./85-ciclo2-catalogo-regras-negocio-r01-r15.md), [86 — encerramento](./86-ciclo2-relatorio-final-consolidado-e-handoff.md) | Coleta 47/60; auditoria 55/90; **G6 0/15**; sem promoção de readiness/homologação |
| **3 — alinhamento da funcionalidade** | [87 — abertura](./87-ciclo3-abertura-design-central-fechamento-read-only.md), [88 — inventário real](./88-ciclo3-r01-inventario-contratos-e-pacote-decisoes.md), [89 — D01..D06](./89-ciclo3-decisoes-aprovadas-e-gate-documental-r02.md), [90 — crosswalk completo](./90-ciclo3-crosswalk-end-to-end-proc0072-teo-rq-ac-portal.md), [91 — destinatários Contabilidade](./91-ciclo3-contabilidade-acesso-documentos-historicos-gate.md) | E2E funcional documentado e decisões registradas. **Não** implica gate transversal de runtime |

## 2. Produto inteiro versus fatia técnica

**Produto:** P1 Cockpit; **P2 Checklist/Documentos e validação de evidências**; P3 Estoque/Cutoff/Conciliação; P4 Classificação/Pendências; **P5 Pacotes/versões/disponibilização/review/esclarecimentos**; P6 Administração. A Home do produto e páginas comuns (Início, Visão geral, Sala de interação, Minhas tarefas, Administração, Ajuda, perfil por deep-route) mantêm seu padrão.

**O Ciclo 3 D01=A/D02=A/D03=B/D04=B/D05=A/D06=A aprova apenas o escopo/design da primeira fatia read-only**, sem excluir P2 e P5 do produto. As consultas MFE/BFF existentes de baixas e estoque permanecem CODE_PRESENT, não RUNTIME_VERIFIED nesta revisão. Não criar scaffold repetido.

**Fluxo de negócio aprovado/reconciliado:**
1. Controladoria abre competência e utiliza checklist versionado, configurado em P6.
2. Joici/responsável gera ou obtém relatórios TOTVS, extratos bancários e arquivos externos; associa documentos ao item da competência; a automatização das fontes comprovadas deve substituir atividades manuais quando autorizada.
3. Validador elegível analisa evidências, aceita ou rejeita com motivo e preservação de versões; **Joici pode anexar e validar quando autorizada a cada ação**, com eventos separados; `ATTACHED != VALIDATED`.
4. P3/P4 tratam conciliação, cutoff e pendências; ausência de fonte não equivale a resultado zero ou aceite.
5. P5 consolida PackageVersion por destinatário. `FINALIZE != SUBMIT != NOTIFY != MONTHLY_CLOSING_COMPLETED`.
6. Destinatários DRE/Contabilidade consultarão e baixarão seu histórico no Portal **quando a permission e página específicas forem implementadas em fase futura**, sem aceitar/rejeitar na primeira versão.

**Cuidado:** o contrato vigente de conclusão mensal P5 C2/[37](./37-p5-submissao-e-revisao-no-portal.md) ainda prevê aceites humanos por pacote/área. A nova decisão DRE/Contabilidade = destinatário read-only **não deve ser convertida em aceite fictício, nem cancelar os outros aceites do P5 silenciosamente**. Reconciliar a semântica de conclusão com o owner funcional antes de alteração de estados.

## 3. Decisão de faseamento — permission/página da Contabilidade ficam futuras

O PO aprovou a **direção de produto Opção B: nova permission específica**, com experiência restrita no Início/área de documentos e leitura/download histórico por destinatário. A decisão está registrada no [Documento 91](./91-ciclo3-contabilidade-acesso-documentos-historicos-gate.md).

**Novo esclarecimento expresso do PO (2026-10-24):** **criar a permission no manifesto e a página específica somente no momento oportuno, em fase futura, após gates/contratos aplicáveis**. **Não realizar agora**:
- alteração de `plugins/controllership-finance/controllership-finance.manifest.json`;
- cadastro/grant no Core ou alteração de rota/root/launcher;
- implementação de `/closing/accounting-documents`, BFF de download, persistência de pacotes;
- publicação/deploy ou promoção de escopo de acesso.

Até nova autorização, baseline de runtime segue **duas permissions efetivas no manifesto** (`controllership-finance.access`, `controllership-finance.manage`). Isso não revoga a decisão funcional de adicionar capability futura. O código `controllership-finance.closing-documents.read` e a rota `/closing/accounting-documents` são **candidatos técnicos** do doc 91, ainda não contratos ratificados.

**Critério para abrir esta fatia futura:** fonte de PackageVersion/evidências e histórico comprovados, regra de liberação e recipient_scope, impacto sobre P5 C2 resolvido, contrato do Core/route guard/Home/BFF revalidado, compatibilidade/rollback do manifesto, owner/gate transversal e GO page-by-page explícitos.

## 4. Próximo incremento recomendado: preparar P2 antes da programação

P2 é a primeira superfície operacional que materializa o checklist de documentos, anexos e validação. Ela alimenta o P5 e reaproveita fontes R01–R15; esta é **recomendação de sequenciamento**, não autorização para runtime e não uma alteração de prioridade do PO sem aprovação.

| Fase candidata | Entrega | Requisitos/fontes | Condição antes de runtime |
|---|---|---|---|
| **C3-P2-G0 — agora** | Inventário técnico, crosswalk linha-a-linha checklist C1/TÉO, RQ/AC detalhados, owners, contratos existentes, storage e autorização | TÉO 31.2–31.13; GitHub [03](./03-evidencias-proveniencia-e-rastreabilidade.md), [09](./09-p2-checklist-e-documentos.md), [17](./17-backlog-de-confirmacoes-e-inventarios.md), [22](./22-handoff-implementacao-p1-p6.md), [23](./23-ledger-rq-ac-testes.md), [90](./90-ciclo3-crosswalk-end-to-end-proc0072-teo-rq-ac-portal.md) | `READ+VERIFY+DOCUMENTATION_ONLY`, sem código |
| **P2-A — após GO** | Checklist de competência, itens/estado/requisito, detalhes e histórico navegável | RQ-P2-01/02/12; P6 snapshot | binding e modelo físico aprovados; tests positive/negative |
| **P2-B — após GO próprio** | Anexos externos e resultados automatizados rastreáveis, múltiplos arquivos, versões e download com AuthZ | RQ-P2-03/05/06; E05/T01/storage owner | segurança de conteúdo, owner e versionamento, auditoria e contrato aprovado |
| **P2-C — após GO próprio** | Validação humana, rejeição/motivo, substituição e reversão segura | RQ-P2-03..06, RQ-P2-10; E06/T05 | business-rule e validator_scope resolvidos; não há aceite por upload |
| **P2-D — após GO próprio** | Exceções, N/A, correção estrutural, notificações e Help | RQ-P2-07..12; T02/T05/P6 | regras e catálogo governado; Testes e Help no mesmo gate |

**Não escolher storage/framework/esquema físico ou endpoint por preferência:** se houver alternativas materiais, abrir `DECISION_REQUIRED` com owner, impactos e recomendação, e interromper o avanço de runtime até aprovação.

## 5. Gaps que impedem autorizar P2 imediatamente

- **XW-02 / RQ/AC TÉO detalhados:** docs TÉO 31.3–31.13 possuem IDs adicionais (ex.: `RQ-P2-039` no 31.13). Ledger GitHub 23 agrupa RQ-P2-01..12. É necessário crosswalk **literal** de IDs/regras/AC/negative tests ou justificativa documentada de agrupamento, sem fabricar equivalência.
- **XW-03 / contratos físicos P2:** confirmar owner/capability do storage de upload; vinculação de item/evidência/versão, audit, eligibility do validador, concurrency, política de arquivo, retention e autorização de preview/download.
- **E05/E06/T02/T05 ([17](./17-backlog-de-confirmacoes-e-inventarios.md)):** catálogo dos tipos de anexo, motivos, notifications, Core effective permissions e resource_scope/ownership. Não confundir E05 de P2 com E5 writer SB9 do C2.
- **Dependência P6:** snapshot de template e catálogo de competência, sem exigir implementação total da página P6 se contratos owners forem aprovados de forma incremental.
- **C1 → P2:** comprovar matriz item do checklist → ator que gera → origem (TOTVS/externo) → competência/filial → destinatário → requisito → regra de satisfação/validação → automatização candidata; não usar R01–R15 como substitutos do checklist.

## 6. Brief de execução da próxima rodada documental (pronto para delegar)

**ID:** `CF-C3-P2-DOCUMENTS-CHECKLIST-READINESS-001`  
**Modo:** READ+VERIFY+INVENTORY+DOCUMENT+REPORT, sem runtime, sem criar permission/página da Contabilidade.

1. Capturar `HEAD`, branch e **git status local**; ler Project Instructions, [instrução oficial](../11-padroes-de-desenvolvimento/instrucoes-oficiais-gpt-arquiteto-delpi-central.md) pelo caminho canônico `docs/11-padroes-de-desenvolvimento/instrucoes-oficiais-gpt-arquiteto-delpi-central.md`, apenas .cursor aplicáveis, README e docs 03/09/17/18/19/22/23/37/86/90/91/92.
2. Consultar TÉO/PROC-0072 (AS-IS/checklist e TO-BE P2 31.1–31.13, 33) e recuperar os textos completos ou atestar precisamente trechos truncados. Não reinterpretar decisões fechadas.
3. Inspecionar código/manifest/core/rotas MFE/BFF/api-delpi/storage, producers/consumers e testes; documentar `CODE_PRESENT` versus `TARGET` e nunca converter search miss em ausência.
4. Produzir crosswalk **por item oficial do checklist**: item e identificador, competência, filial, responsável pela produção/upload, fonte, possibilidade de automação, arquivos/evidências, regra de satisfação/validador, destinatário, versão/histórico, RQ/AC, contracts, owner, prioridade/risco.
5. Produzir crosswalk dos RQ/AC detalhados TÉO→GitHub e matriz de negative tests de autoaceite, replacement, multi-anexo, scope, permission e Core/storage indisponíveis.
6. Inventariar solução canônica de anexos da plataforma e contratos Core de pessoas/validator-scope, incluindo segurança de arquivos e retenção; não criar schema ou API.
7. Produzir proposta de primeiros slices P2 com RQ/AC, owner/contrato, reuso @delpi/plugin-ui, Help, testes e critérios de GO; abrir `DECISION_REQUIRED` sobre escolha material não resolvida.
8. Atualizar docs **somente** do tema/autoridades, registrar delta, residual search, SHAs e EXECUTION REPORT. Não alterar manifesto, endpoints, migrations, storage, runtime UI ou deploy. Não promover C2 G6.

**Gate de saída esperado:** revisão arquitetural do pacote P2 para decidir **se** e **qual fatia** poderá receber autorização transversal seguida de GO de implementação por página. A presente decisão de continuidade **não é esse GO**.

## 7. Veredito e próximo passo

**Situação:** `ACCEPT_WITH_RESIDUAL` para consolidação documental do PROC-0072 e decisões vigentes; `PENDING` para contratos P2/P5, `TEST_NOT_RUN` para runtime novo, `IMPLEMENTATION_AUTHORIZED=NO`.

**Próxima ação recomendada:** executar `CF-C3-P2-DOCUMENTS-CHECKLIST-READINESS-001` com executor (Devin/Cursor), revisar evidências e aprovar gate P2 específico antes de implementar. A permission e página da Contabilidade **não** entram nesta rodada, ficando registradas para o estágio próprio P5/documentos históricos.
