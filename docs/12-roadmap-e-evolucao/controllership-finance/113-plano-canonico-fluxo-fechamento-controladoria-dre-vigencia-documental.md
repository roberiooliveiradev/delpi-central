# 113 — Plano canônico de continuidade: fluxo mensal Controladoria → DRE e vigência documental

> **DECISÃO PO — UX DE CADASTRO DOCUMENTAL (26/10/2026):** criar e editar **configurações dos tipos de documentos/PDFs exigidos à DRE** deve usar **página dedicada de Administração**, e NÃO modal. Preservar listagem, botão Adicionar, rota/formulário de criação, rota/formulário de edição, retorno à listagem com contexto e foco, validação, histórico, vigência inicial/final/excepcional, responsividade e Help. Acesso à configuração apenas por `controllership-finance.manage` (ou Super Admin com autoridade efetiva); backend autoriza fail-closed. Esta página administrativa NÃO é uma quarta aba do Fechamento mensal; uploads/anexos operacionais continuam dentro da aba Documentos e interações. **TARGET**, não implementação vigente; inventariar modal atual, router, componentes `@delpi/plugin-ui`, contratos, consumidores e gates antes de executar. Preservar modal legado até substituição validada e depreciação expressamente autorizada.

**Data:** 2026-10-26  
**Produto:** Portal Controladoria & Finanças / Central de Fechamento  
**Processo:** PROC-0072  
**Authority:** decisões funcionais expressas pelo Product Owner nesta continuidade; precedência subordinada às instruções oficiais, regras .cursor, ADRs e contratos aprovados para IMPLEMENTAÇÃO.  
**Estado:** `PRODUCT_FLOW_APPROVED / TARGET`; `RUNTIME_RECONCILIATION_PENDING`; **não é GO de runtime, migração ou deploy.**  
**Baseline documental observado:** `121fd93e026e456eb3a5f9b0e99584e8a59da2e7` antes deste plano (revalidar HEAD em cada execução).

## 1. Escopo e relação com o histórico

Este documento consolida a sequência integral aprovada pelo PO e é a **referência de produto vigente** para o executor Devin, complementando o doc 112 (decisões de UX), o doc 09 (P2), doc 23 (RQ/AC), P5 doc 37 e README. Não apaga decisões nem arquivos antigos: marca premissas substituídas e estabelece gates para reconciliação com contratos existentes. A retirada de documentação e código legado é **fase posterior e separada**, somente após inventário de producers/consumers, depreciação aprovada, testes e GO explícito.

**Superação limitada das premissas anteriores:** consultar um mês não exige registro em `monthly_competence`, template `PUBLISHED` ou documentos presentes. **Contudo, executar a abertura formal do fechamento é uma ação distinta**, com a elegibilidade da permissão `controllership-finance.access` aprovada pelo PO, sujeita a AuthZ fresca, escopo e business rule. Não confundir consulta, abertura, anexação, conclusão, submissão e aceite DRE.

## 2. Fluxo funcional aprovado, de ponta a ponta

1. **Entrada e referência:** usuário acessa `/apps/controllership-finance/closing/monthly-closing` e seleciona mês `YYYY-MM` autorizado. Os relatórios e dados disponíveis podem ser consultados por período antes de abrir formalmente o fechamento. Preservar competência, aba, filtros, F5, voltar/avançar e deep links; não depender de uma lista composta somente por competências já abertas.
2. **Existência:** se o fechamento desse mês **já existe**, abrir sua visão geral, estado, histórico, relatórios, divergências e documentos conforme autorização. Se **não existe**, apresentar a opção contextual **Abrir fechamento**. Uma seleção de referência NÃO escreve, cria snapshot ou conclui nada.
3. **Abertura:** usuário elegível com `controllership-finance.access` pode iniciar formalmente o fechamento, com verificação backend de effective permissions pelo Core + scope/ownership + regra de negócio e auditoria. `manage` não é requisito adicional para essa ação, salvo novo gate expressamente aprovado. O contrato técnico hoje relatado `POST /closing/competences` depende de template publicado; esse acoplamento conflita com o TARGET e requer reconciliação controlada. **A ausência de tipos documentais ou de anexos não bloqueia a abertura.**
4. **Trabalho da Controladoria:** dentro de exatamente três abas (**Visão geral**, **Documentos e interações**, **Relatórios e divergências**), o analista consulta relatórios calculados por serviços owners, visualiza totais e agrupamentos, analisa divergências com pontos exatos e proveniência, anexa documentos pertinentes e acompanha checklist, revisões e histórico. Não obrigar análise manual linha a linha no fluxo principal. Não fabricar relatório/zero nem cálculo no frontend.
5. **Correção no ERP:** a integração atual é de **leitura**; as correções de divergências são feitas manualmente no TOTVS/Protheus pelos responsáveis habilitados no ERP. O portal informa fonte, critério, entidade/linha ou agrupamento afetado, valor, possível causa **quando comprovada** e orientação auditável; atualização/reconsulta demonstra se a divergência foi resolvida. Nenhum write-back ERP sem contrato e GO.
6. **Conclusão da etapa Controladoria:** após condições formais comprovadas, usuário autorizado conclui a etapa e realiza a disponibilização/submissão dos PDFs liberados à DRE, respeitando segregação e P5. Estados distintos: `STOCK_CLOSED != PACKAGE_SENT != MONTHLY_CLOSING_COMPLETED`, `Finalizar != Enviar`; **concluir** não pode ser confundido com **aceitar** automaticamente.
7. **Entrega restrita à DRE:** DRE recebe **apenas os PDFs/documentos designados no cadastro de entregáveis à DRE, efetivamente liberados para o período e autorizados**, tipicamente cerca de quatro ou cinco PDFs (quantidade ilustrativa, jamais hardcoded). DRE **não recebe os relatórios operacionais TOTVS** nem a aba interna de divergências. A funcionalidade/página exclusiva DRE fica **por último** no roadmap. Não criar terceira permission antecipadamente; tratamento de público DRE exige gate de segurança próprio (doc 91).
8. **Revisão e complementação:** DRE pode consultar/baixar documentos liberados, comentar e solicitar refazimento/correção de PDF. A Controladoria responde e gera/anexa nova versão; preservar versão anterior, autor, datas, motivo, auditoria e histórico de cada pedido. **Resposta ao pedido não encerra automaticamente solicitação**; fechamento da solicitação depende de validação adequada pela parte autorizada. Aplicar contratos P2/P5 e versionamento imutável de PackageVersion quando cabível.

## 3. Cadastro mestre e vigência dos entregáveis à DRE

- O **Manager** (`controllership-finance.manage`) e o Super Admin com autoridade efetiva adequada gerenciam em área de configuração, separada do workspace operacional comum, **quais tipos de PDF/documento são exigidos e destinados à DRE**. Não há cadastro mensal repetitivo.
- Usuário apenas `access` executa o fechamento e as ações operacionais autorizadas, mas **não altera o cadastro mestre, suas vigências, a lista DRE nem sua configuração**.
- A configuração permite: **vigência a partir de uma competência**, **intervalo inclusivo de início/fim** e **exigência excepcional para competência ou período delimitado**. Cada mudança tem autor, momento, justificativa/proveniência quando exigível, versionamento, publicação/ativação governada e histórico auditável.
- Inclusão exige documento a partir do início de vigência; retirada/desativação deixa de exigir a partir da referência definida, sem exclusão física de documentos/histórico. `CANCELLED != DELETED != NOT_APPLICABLE`.
- Um fechamento **finalizado** preserva o conjunto de exigências e documentos históricos aplicáveis. Não reescrever snapshot por alteração posterior do cadastro mestre. **Regra de atualização de exigências de competência já aberta e ainda em andamento está PENDENTE de inventário/contrato/decisão; não presumir autoatualização nem congelamento definitivo.**
- Diferenciar rigorosamente **tipo de documento exigido**, **exigência vigente do mês**, **arquivo efetivamente enviado**, **versão**, **validação P2**, **liberação à DRE** e **PackageVersion P5**. `ATTACHED != VALIDATED`. Pode não haver tipos exigidos ou arquivos anexados: isso **não impede selecionar mês nem iniciar processo**. Impedimentos de conclusão/submissão decorrem apenas de gates de negócio realmente aplicáveis.
- Não assumir que os relatórios R01–R15 se tornam documentos DRE: eles são instrumentos da análise interna, salvo um PDF documental explícito configurado e liberado conforme contrato próprio.

## 4. UX, integração e segurança congeladas

**Três abas e nenhuma quarta:** Visão geral; Documentos e interações; Relatórios e divergências. KPIs bloqueios/documentos/divergências são atalhos de aba. Evitar fluxo de sair/voltar para executar operações comuns. Home consolidada e deep routes existentes preservadas. PagePath compartilhado `@delpi/plugin-ui` após inventário de export real, mantendo mês, aba, relatório/filtro. UX PT-BR, temas claro/escuro, mobile, teclado, foco, Ajuda no mesmo gate.

**Identidade:** `controllership-finance`; MFE `plugins/controllership-finance`; `/apps/controllership-finance`; BFF `controllership-finance-api`; `/apps/controllership-finance-api`. Somente permissões `controllership-finance.access`, `controllership-finance.manage`. Não criar permissions por página/documento/filial/DRE. JWT não é authority; BFF consulta effective permissions Core, faz AuthZ fail-closed por capability AND resource_scope/ownership AND business_rule; dados DRE restritos a seu público via contrato/gate posterior. Browser não chama `api-delpi` diretamente; relatórios por owners canônicos e contratos, sem import de domain alheio ou escrita no ERP.

## 5. Matriz de comportamento e aceite

| Situação | Resultado esperado |
|---|---|
| Mês sem fechamento | Pode consultar informações de leitura existentes; ação contextual 'Abrir fechamento' aparece a quem pode abrir |
| Mês já aberto | Carrega estado, documentos, divergências e histórico próprios do mês, sem data stale de outro |
| Mês sem template publicado | Consulta e **abertura** não são bloqueadas apenas por isso no TARGET; reconciliar BFF/P2/P6 |
| Mês sem documentos exigidos/anexados | Estado vazio honesto; operações autorizadas disponíveis, sem erro fictício |
| Usuário access | Consulta, abre e opera fechamento dentro do próprio escopo; não configura catálogo DRE |
| Usuário manage | Capacidade operacional e gestão do catálogo conforme effective scope/regras |
| Add/retirada de documento com vigência | Afeta referências cobertas, preserva fechamentos finalizados |
| Exigência excepcional | Só se aplica ao intervalo/competência governada |
| Relatório sem dados/erro | Distingue ausência, zero real e erro/source unavailable |
| Divergência identificada | Mostra ponto verificável de correção ERP e reconsulta; portal não grava TOTVS |
| Conclusão Controladoria | Não equivale automaticamente a envio nem aceite formal DRE |
| Entrega DRE | Somente PDFs liberados, não relatórios operacionais |
| Pedido DRE de refazimento | Nova versão com histórico; resposta não valida automaticamente atendimento |
| Fechamento histórico | Consulta preserva sua fotografia, sem reatribuir versões futuras |

**Testes mínimos:** positive, negative e sibling para troca rápida de competência, stale/abort, meses anteriores/futuros conforme política permitida, sem template, sem cadastro, períodos de vigência, intervalo e exceção, fechamento em andamento/finalizado, RBAC, P2/P5, retentativa, idempotência, deep link, F5, teclados/foco, mobile, temas, Help, builds, health e smoke autenticado. Smoke não executado = `TEST_NOT_RUN`.

## 6. Plano faseado para Devin (sem execução concorrente)

**Checkpoint 0 — Assimilar decisão (READ/VERIFY):** ao concluir execução atualmente em andamento, confrontar este plano e o Documento 112 com diff, HEAD, normas, RQ/AC e owner. Registrar divergências como `EXECUTION_DRIFT`; não presumir GO.

**Checkpoint 1 — Reconciliação documental e de contratos:** mapear todos os documentos e código que vinculam **consulta e abertura** à publicação do template; separar premissas históricas, contratos atuais e decisões TARGET. Identificar producers/consumers/migrations/testes de `monthly_competence`, template de checklist, exigências e pacote P5. Submeter DECISION_REQUIRED se owner, persistência, integração, breaking change ou regras de competência em andamento não estiverem definidos.

**Checkpoint 2 — Workspace mensal Controladoria:** mediante gate explícito, seleção de mês e consulta desacopladas da abertura; abertura contextual por `access` e ausência de documentos permitida; três abas, histórico isolado, UX e Help. Evidência E2E real, não apenas HTTP 200.

**Checkpoint 3 — Relatórios e divergências:** cálculos pela API canônica, drilldown com causa comprovada e orientação para correção no ERP; relatório completo na aba, prévia PDF preservada. Homologação R01–R15 por fonte/owner. Sem escrita ERP.

**Checkpoint 4 — Cadastro geral dos PDFs exigidos à DRE:** depois de contrato/gate P2/P6, configurar gestão `manage` com vigência inicial/final/excepcional e histórico, proteger snapshots finalizados, expor exigências aplicáveis às competências e anexação operativa.

**Checkpoint 5 — Conclusão/submissão e colaboração documental:** reconciliar P2/P5, versões e evidências, conclusão versus envio, liberação dos PDFs, requests de refazimento, validação do atendimento, auditoria/notificação por contrato; sem aceite automático.

**Checkpoint 6 — DRE, último:** interface de consulta restrita a PDFs liberados, download/comentário/pedido de refazimento, segregação com relatórios internos, segurança transversal e homologação humana. Não antecipar permission ou página.

**Checkpoint 7 — Depreciação/limpeza posterior e separada:** somente após paridade funcional, inventário de consumidores/rotas/deep links, métricas de uso, estratégia de migração e rollback, autorização PO + owner e testes, planejar remoção de código e documentos legados. **PROIBIDO neste ciclo** apagar antigas rotas, schemas, componentes ou histórico.

## 7. Gates, ownership e regras de trabalho

Hierarquia: instruções oficiais > .cursor aplicáveis > ADRs/contratos > HEAD e testes > docs vigentes > roadmap > histórico. GitHub autoridade TARGET; TÉO autoridade AS-IS de processo. Antes de decisão/ação material: HEAD + git status, owners, RQ/AC, evidência e gates. `READ → VERIFY → CLASSIFY → DECIDE → IMPLEMENT MINIMAL DIFF → TEST → VERIFY OUTCOME → RESIDUAL SEARCH → DOCUMENT → REPORT`.

**Bloqueios/DECISION_REQUIRED** se precisar escolher: representação de mês sem registro, policy de períodos consultáveis/abertos, persistência e vigência, comportamento da competência aberta durante alteração de catálogo, destinatários e entitlement DRE, fronteira conclusão/submissão P5, breaking changes, migrations e lifecycle. Propor alternativas sem executar escolha não autorizada.

Fluxo canônico de delivery: local → testes → revisão → commit → push → deploy via Git autorizado → health/readiness → smoke autenticado → GPT REVIEW. Nunca alterar diretamente produção ou abrir meses, publicar templates, inserir dados/migrations por conveniência.

## 8. Execução e rastreabilidade

**Execução de Devin já encaminhada antes deste plano:** `CF-PROC0072-MONTHLY-REFERENCE-CATALOG-001`; nenhuma nova execução é iniciada por este documento. Ao apresentar relatório, revalidar HEAD e confrontar explicitamente os sete checkpoints. Documentos 112, 09, 23 e README possuem registros do PO anteriores a este plano; verificar e harmonizar referências com a nova decisão de fluxo sem reescrever o histórico. Relatório deve listar BASE/FINAL HEAD, git status, fatos `PROVEN|TO_INVENTORY|PLANNED|TARGET`, testes `PASS|FAIL|PENDING|INCONCLUSIVE|TEST_NOT_RUN|STALE_EVIDENCE`, drift, matriz de arquivos afetados, gaps, GO, SHA e próximo passo.

**Status final deste plano:** decisão funcional `PROVEN` (PO); implementação `TARGET`; verificação operacional `INCONCLUSIVE` até evidência homologada; remoção de legado `NOT AUTHORIZED`.
