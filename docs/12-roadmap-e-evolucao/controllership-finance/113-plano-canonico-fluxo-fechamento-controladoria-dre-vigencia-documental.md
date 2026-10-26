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


## 9. UX detalhada por superfície — decisão PO de 26/10/2026 (TARGET)

**Alcance:** exclusivamente fechamento mensal. São três abas internas; a Administração é uma área de gestão separada; a página de Contabilidade/DRE será a última entrega. O detalhe de documento é **deep route contextual**, não uma quarta aba. Regra aprovada: cadastro/edição da configuração documental em **página completa, não modal**. O PO também solicitou **detalhe do documento com interação**; a disposição duas colunas e o uso de deep route são especificação visual TARGET sujeita a validação e contratos de colaboração. Não confundir definição de documento exigido com PDF anexado.

### 9.1 Início
- Hero comum Minha DELPI e entrada principal **Fechamento mensal**; atalhos a Documentos e interações e Relatórios e divergências preservando mês/tab.
- Componentes prioritários: `createDashboardPageHero`, `createDashboardEventsSection`, `createDashboardCatalogSearchBar`, `createDashboardRecentAccessStrip`, `createDashboardSectionRouteCard`, `ActionButton`, `EmptyState`; não refazer TopBar/chrome.
- Estados loading/empty/error e cards sem métricas inventadas.

### 9.2 Fechamento mensal — Visão geral (aba 1)
- PagePath, referência `YYYY-MM`, contexto de fechamento existente ou botão **Abrir fechamento** se ausente (Access sob AuthZ); selecionar mês não cria registro.
- Indicadores Bloqueios, Divergências e Documentos a tratar são links contextuais às três abas, nunca novas rotas. Não exibir contagem sem fonte/semântica.
- Estados Estoque, Documentação e Pacote separados. Conclusão distinta de envio P5.
- Kit: `createDashboardPagePath` (verificar factory), `createDashboardPageHero`, `QuickPeriodSelector` (avaliar adequação para mês; não lista apenas OPEN), `KpiCard`, `MetricKpiCard`, `ProgressTracker`, `AlertQueue`, `WorklistItem`, `Timeline`, `StateBanner`, `EmptyState`, `ActionButton`.

### 9.3 Fechamento mensal — Documentos e interações (aba 2)
- Lista dos entregáveis aplicáveis à referência e PDFs efetivamente anexados, com estado de entrega/validação, versão, comentários, ajustes e histórico; ausência é empty state honesto.
- Ação de abrir detalhe do documento **sem sair do contexto de competência**; anexo e replacement conforme P2. Comentários e solicitações de complemento não equivalem a aceite formal P5.
- Kit: `DataTableSection`, `DataRecordCard`, `ResizableColumns` (validar export/factory), attachment primitives e `FilePreview` (confirmar nome real), `Timeline`, `EmptyGuidance`, `ActionButton`, `FieldLabel`, `HelpTooltip`, `StateBanner`.

### 9.4 Detalhe do PDF / interações — deep route contextual
- Entrada Controladoria: aba Documentos e interações > documento; entrada DRE: Documentos recebidos > competência > documento. **Mesma thread e histórico de documento/competência**, porém projection e ações autorizadas diferentes.
- Desktop: **prévia PDF e versões à esquerda**, **thread/comentários/solicitações à direita**, **histórico auditável abaixo**; mobile empilha regiões e conserva foco e scroll/contexto.
- Mostrar documento/tipo, competência, versão atual, versões anteriores, autoria/datas, estados do pedido e log de upload/substituição. Contabilidade pode comentar, baixar e pedir refazimento; Controladoria responde e anexa nova versão conforme permissões. **Responder não encerra automaticamente**: validação do atendimento pela parte autorizada. Não dar à DRE upload, relatórios TOTVS, divergências, administração, aceite P2/P5.
- Kit candidato: `createDashboardPagePath`, `BackLink`, `ResizableColumns` (verificar API), primitives de preview/download e attachment, `Timeline`, `DataRecordCard`, `ActionButton`, `FieldLabel`, `HelpTooltip`, `StateBanner`, `EmptyState`; **conversation composer/threads apenas após verificar contrato de colaboração e exports concretos**, não importar domínio de Minhas Solicitações. Não usar `FilePreviewModal` como substituto da página completa quando preview inline disponível; identificar alternativa real.

### 9.5 Fechamento mensal — Relatórios e divergências (aba 3)
- Matriz de relatórios calculados por backend owner, totais, proveniência, diferenças, detalhe progressivo até o ponto exato corrigível no ERP, reconsulta pós-correção e container de prévia do PDF. Relatórios internos não são entregáveis DRE por padrão.
- Kit: `DataTableSection`, `DataRecordCard`, `MetricKpiCard`, `AlertQueue`, `DetailFieldGrid`, `Timeline`, `ActionButton`, `StateBanner`, `EmptyState`, `createDashboardPagePath` (confirmar export).
- Sem cálculo financeiro no React, sem write ERP, sem linha a linha obrigatória como fluxo principal.

### 9.6 Administração — listagem dos documentos exigidos para DRE
- Acesso somente Manage ou Super Admin com effective permission/scope. Tabela com nome, destino DRE, obrigatoriedade, vigência inicial/final/excepcional, status, versão, autoria e ações **Adicionar**/**Editar**/**Histórico**.
- Kit: `createDashboardPageHero`, `createDashboardPagePath`, `DataTableSection`, `DataRecordCard`, `ActionButton`, `EmptyGuidance`, `StateBanner`, filtros/confirm kit público.
- Nenhuma quarta aba no Fechamento mensal.

### 9.7 Administração — página de cadastro de documento exigido
- **Rota própria**, não modal. Formulário com nome, descrição, destinatário DRE, obrigatoriedade, vigência a partir de competência, término opcional, exceção para competência/intervalo, justificativa e ações Salvar/Cancelar.
- Kit: `createDashboardPagePath`, `BackLink`, `createDashboardPageHero`, `ActionButton`, `FieldLabel`, `HelpTooltip`, `createDashboardNativeFormFields` (campos TextField/SelectField/TextAreaField e date nativo conforme catálogo); validar export e API antes de usar.
- Backend efetua validação de sobreposição/vigência conforme contrato ainda a definir; não inventar schema.

### 9.8 Administração — página de edição de documento exigido
- **Rota própria** reutilizando formulário anterior; mostrar edição de vigência com preview de impacto e histórico de versões, sem retroagir sobre competências finalizadas. Cancelar/voltar preserva filtros e foco.
- Mesmo kit do cadastro + `Timeline`, `StateBanner` e controles de confirmação do catálogo. Preservar o modal legado até substituição homologada e depreciação autorizada.

### 9.9 DRE — documentos recebidos (última fase)
- Competência selecionada, somente PDFs **liberados** para aquele público; lista com status de análise, versão, data, download, abrir detalhe e solicitar refazimento (na página de detalhe).
- Kit: `createDashboardPageHero`, `createDashboardPagePath`, `DataTableSection`, `DataRecordCard`, `EmptyGuidance`, `ActionButton`, `StateBanner`, `Timeline`; habilitação condicionada a gate de segurança do público DRE, sem permission nova antecipada.
- Não exibir relatórios operacionais, divergências, upload/substituição, administração ou ações de aceite P2/P5.

### 9.10 Protocolo obrigatório de componentes (Devin)
- **Visitar/inventariar antes de codificar:** `plugins/plugin-ui/src/index.ts`, `plugins/plugin-ui/docs/component-catalog.md`, `plugins/plugin-ui/src/catalog/visualComponents.ts`, exemplos em `plugins/plugin-ui/src/catalog/demos/` e, quando acessível, app de demonstração `/apps/plugin-ui`. Conferir export público, props reais, CSS/tokens e se componente é factory ou componente direto.
- Preferir `import { ... } from "@delpi/plugin-ui/index"` e `import("@delpi/plugin-ui/styles")`, conforme mapa 30. **Nomes deste plano são candidatos de reuso, não certificação de que todos são exports diretos**. Particularmente `ResizableColumns`, `PagePath`, preview inline, editor de conversa e attachment kit exigem validação de export/factory.
- Se componente adequado não existir, reportar GAP/owner e propor adapter mínimo ou evolução compartilhada, sem duplicar chrome, formulário, modal ou estilos. UI consistente em tema claro/escuro, desktop/mobile, teclado/foco, URL/F5. Ajuda deve mudar no mesmo gate.
- Testar acesso DRE vs Controladoria e Manage, ausência de documento, V1→pedido→V2→verificação, histórico imutável, fail-closed, deep link, retorno e janela de competência.
- Este detalhamento **não amplia o GO vigente** nem autoriza execução concorrente ao prompt que Devin já recebeu.


## 10. GO DE PRODUTO — remover travas contratuais que contrariem o fluxo aprovado (26/10/2026)

**DECISÃO EXPRESSA DO PO:** implementar o Plano 113, adaptando contratos, validações, persistência e código existentes às decisões funcionais atuais. Contratos AS-IS são insumos do inventário e alvos de reconciliação, **não veto permanente ao TARGET**. Esta decisão constitui **GO de produto/escopo** para elaborar e executar incrementalmente as correções, mas não dispensa gates técnicos de migração, segurança, rollout e evidência, nem autoriza alteração direta de produção.

**Comportamentos mandatórios:**
1. Selecionar mês mostra informações disponíveis, inclusive consultas TOTVS period-keyed, mesmo sem competência formal aberta; `R01–R15` de checklist não devem ser apresentados como se fossem relatórios financeiros calculados.
2. Usuário com `controllership-finance.access` e escopo efetivo pode **Abrir fechamento** contextual, mesmo sem template publicado ou documentos cadastrados. Abrir sem exigências resulta legitimamente em lista vazia e auditoria; jamais produzir template fictício, zero financeiro inventado ou migrar registros anteriores por conveniência.
3. Cadastro mestre de **exigências documentais para DRE** administrado por `manage`, com vigência inicial, final opcional e exceção por referência; fechamento finalizado mantém conjunto/versões preservados. Alteração em fechamento **em andamento** exige política definida antes da mutação de dados (não atualizar snapshots silenciosamente); propor opção preservadora de histórico para validação.
4. Analista consulta relatórios operacionais e divergências em sua aba, corrige no ERP manualmente, reconsulta; DRE vê apenas os PDFs selecionados e liberados e pode solicitar novas versões na página de detalhe compartilhada, com histórico e confirmação de atendimento separada de resposta.
5. Preservar exatamente três abas, cadastro/edição do documento em páginas administrativas (não modais), `@delpi/plugin-ui` first, Help concomitante, rotas antigas até depreciação futura.

**Orientação executiva para DR-C1/C2/C3 do doc 112 §32:**
- DR-C1: resultado de negócio está **decidido**: abertura sem template é obrigatória. O executor deve inventariar impacto e projetar **migration versionada mínima** (nullable ou alternativa robusta) com teste de migração e rollback; não executar migration produtiva antes de gate de dados/owner e plano de rollback. Não usar placeholder PUBLISHED sintético. **EXECUTADO (CF-PROC0072-MONTHLY-OPEN-003):** opção nullable aplicada — `V015__monthly_competence_optional_template.sql` + `open_competence` com snapshot vazio e audit `opened_without_template`; testes PG verdes; deploy produtivo segue gated (doc 112 §33).
- DR-C2: resultado de negócio está **decidido**: relatórios operacionais consultáveis por mês com os dados disponíveis, sem abertura. Reusar os endpoints period-keyed existentes. Relatórios faltantes devem ter owners/producers identificados e contratos de consulta próprios; matriz documental R01–R15 permanece separada.
- DR-C3: resultado de negócio **decidido para finalizados**: nenhuma mutação retroativa. Para abertos/em andamento, mudança que altere obrigações exige decisão de política e trilha de auditoria; oferecer duas alternativas embasadas, sem escolher silenciosamente.

**Sequência de execução autorizável:** (a) inventário técnico/contratos e matriz de consumers; (b) proposta de migração e gates de dados; (c) aprovação técnica de migração e execução LOCAL/testes; (d) BFF de abertura + consulta mensal, AuthZ e auditoria; (e) catálogo de exigências effective-dated e páginas Manage; (f) relatórios/divergências; (g) documentos/interações/P5; (h) DRE por último. Entrega por slices fechados, sem commit parcial que quebre consumers. O executor deve solicitar o gate específico quando exigido e entregar `EXECUTION_REPORT` para `GPT REVIEW`. Sem smoke autenticado, resultado operacional = `INCONCLUSIVE`.

**Limites:** não criar permission code, não gravar TOTVS, não expor relatórios internos à DRE, não remover legado antecipadamente. Qualquer migration, breaking change e deploy continuam sujeitos à authority transversal e owner. Não interpretar esta autorização funcional como licença para ignorar integridade ou AuthZ.


---

**ATUALIZAÇÃO DE RUNTIME — 2026-10-26 (CF-PROC0072-MONTHLY-OPEN-PROD-CLARA-004):** DR-C1 está **em produção**. Deploy canônico @`052d344d90` aplicou V015 (template_version_id nullable) no startup; primeira abertura real já registrada — `2026-09` aberto sem template via Portal autenticado (audit `opened_without_template: true`, checklist vazio legítimo). DR-C2 (relatórios por mês sem competência) e DR-C3 (propagação a competência em andamento) seguem pendentes conforme §3.


## 11. REDESIGN VISUAL — PROPOSTA V0.1: ABA VISÃO GERAL (PO REVIEW PENDING, 26/10/2026)

**Estado:** `TARGET / DESIGN_PROPOSED / PENDING_PO_VISUAL_APPROVAL / NO_RUNTIME_GO`. Escopo exclusivo: Fechamento Mensal / PROC-0072. A captura de setembro/2026 mostra blocos P1–P5 em sequência, códigos `p3_source_unavailable`, listas técnicas, KPIs sem semântica evidente e muitas áreas vazias. O redesign **não apaga** domínio, backend, audit, rotas legadas ou contratos; substitui gradualmente apenas a composição de UX, após aprovação componente a componente.

### 11.1 Objetivo e hierarquia visual
O analista deve responder sem rolar extensivamente: **qual mês estou vendo? qual é o estado do fechamento? o que me impede de avançar? qual é o próximo trabalho?** A Visão geral é um **painel de decisão e acompanhamento**, não a repetição integral das telas técnicas P2/P3/P4/P5.

**Wireframe textual desktop (proposta):**
```
Início > Fechamento mensal > Visão geral             [Ajuda]
Fechamento mensal       [Mês de referência: 09/2026 v] [Atualizar]
[ Visão geral | Documentos e interações | Relatórios e divergências ]
[ Situação do fechamento: Em andamento ] [responsável/autoria e atualização]
[ Bloqueios ]  [ Divergências ]  [ Documentos a tratar ]   (atalhos contextuais)
[ Próximos passos / bloqueios explicados em PT-BR       ]
[ Estado por eixo: Estoque | Documentos | Pacote DRE    ]
[ Atividade recente / eventos materiais               ]
[ Concluir etapa ] / [Enviar pacote]  (operações distintas; gated)
```

### 11.2 Componentes propostos
| Ordem | Componente | Conteúdo / ação | Fonte e honestidade | Kit candidato |
|---|---|---|---|---|
| 1 | PagePath + header compacto | Início > Fechamento mensal > Visão geral, Help, título único | Links preservam competência/aba; sem duplicar TopBar | `createDashboardPagePath`, `createDashboardPageHero`, `HelpTooltip` |
| 2 | Seletor mensal persistente | Escolher `YYYY-MM`, atualizar dados; navegar com F5/back | Consulta não abre automaticamente; meses sem competência permitidos | controle de período conforme API real `QuickPeriodSelector` ou campo nativo do kit, `ActionButton` |
| 3 | Faixa de estado | Não iniciado / em andamento / etapas concluídas / histórico conforme lifecycle REAL | Não inventar status global; derivar de P1/P3/P5 com proveniência e sem falsa equivalência | `StatusBadge`, `StateBanner` |
| 4 | Três indicadores clicáveis | Bloqueios → Visão geral; Divergências → Relatórios; Documentos a tratar → Documentos | Sem fonte = “—” + explicação; zero só com cálculo comprovado; indicadores não criam páginas | `KpiCard`, `MetricKpiCard` |
| 5 | Próximas ações priorizadas | 2–4 situações materiais em português com causa/ação; expandir “Ver todos” | Sem mostrar códigos técnicos crus; origem/atualização no detalhe. Não deduzir prioridade arbitrária | `AlertQueue`, `WorklistItem`, `ActionButton` |
| 6 | Estado por eixo | Estoque/conciliação, Documentos, Pacote DRE, independentes | `STOCK_CLOSED != PACKAGE_SENT != MONTHLY_CLOSING_COMPLETED`; parcial/unavailable explícito | `ProgressTracker` ou cards compartilhados, `StateBanner` |
| 7 | Histórico compacto | 3–5 últimos eventos com autor/data e link para contexto | Se endpoint não disponibiliza eventos, empty state honesto; não inventar atividade | `Timeline`, `EmptyState` |
| 8 | Ações de conclusão | Exibir condições e ações autorizadas para concluir Controladoria e enviar pacote separadamente | Server-side AuthZ, status e precondições; não habilitar sem contrato P5 | `ActionButton`, confirmação compartilhada após inventário |

### 11.3 Regras de visual e comportamento
- **Não repetir** cards `Checklist e evidências P2`, `Cutoff P3`, `Pendências P4`, `Pacotes P5` como seções técnicas extensas na Visão geral. Esses dados continuam acessíveis por indicadores, eixo e detalhes contextuais nas abas proprietárias.
- **Não mostrar** códigos como `no_applicable_packages`, `p3_cutoff_not_confirmed`, `p3_source_unavailable:P7` sem tradução PT-BR e orientação simples; preservar códigos no telemetry/log/diagnóstico para suporte.
- **Ausente ≠ zero:** o KPI de divergências não pode dizer “0” quando P7/H02/ENTRADAS_SAIDAS estão indisponíveis. Da mesma forma “Documentos a tratar” é “—” até contrato semântico provado.
- O contador de bloqueios é diagnóstico composto; diferenciar `fonte indisponível` de divergência identificada.
- **Quando não há fechamento:** estado informativo com botão `Abrir fechamento` apenas para access autorizada, sem bloquear consulta por mês. Com fechamento sem checklist: documentação vazia legítima.
- Histórico finalizado é read-only; preservar snapshots históricos, origem e versões.
- Priorizar primeiro viewport desktop; mobile empilhar KPI e eixos de forma legível, preservar teclado/foco/URL, mesmos tokens claro/escuro, Help no mesmo gate.
- Não permitir que a simplificação visual oculte uma pendência impeditiva; usar progressão “resumo → detalhe contextual”.

### 11.4 Perguntas de validação visual ao PO
1. A faixa de estado e as **próximas ações** são o elemento principal, com três KPIs logo abaixo/acima?
2. Deseja que **Atividade recente** fique na Visão geral ou apenas no detalhe/histórico?
3. As ações `Concluir etapa` e `Enviar pacote` devem aparecer na Visão geral, mas só serem habilitadas quando permitidas?
4. O acompanhamento de Estoque/Documentos/Pacote DRE em três cards compactos está adequado?

**Próxima ação:** PO revisa V0.1 na conversa. Registrar ajustes e aprovação visual expressa antes de criar prompt de execução. Não remover código legado nesta fase. CLARA: registrar aprovação no corpus antes de publicar como regra consolidada; não indexar proposta V0.1 como runtime.


## 12. VISÃO GERAL — DECISÕES PO APROVADAS E ESPECIFICAÇÃO VISUAL V0.2 (26/10/2026)

**Decisões expressas do PO (PROVEN, DESIGN_APPROVED para estas quatro escolhas):**
- `destaque=actions`: **O que precisa de atenção / Próximos passos** é a área dominante, acima de detalhes secundários.
- `histórico=summary`: **Atividade recente** aparece na Visão geral como resumo, com acesso contextual ao histórico completo onde existir contrato.
- `ações de conclusão=overview`: **Concluir etapa da Controladoria** e **Enviar pacote** ficam no final da Visão geral, separados, com condições e AuthZ server-side; não presumir habilitação nem transição automática.
- `acompanhamento dos eixos=cards`: **Estoque, Documentos, Pacote DRE** apresentados em três cartões compactos independentes.

**Estado:** escolhas acima `PO_APPROVED`; disposição refinada `VISUAL_SPEC_V0.2 / PENDING_FINAL_PO_PAGE_APPROVAL`; implementação `NOT_AUTHORIZED`. Seções 11.1–11.4 são histórico de proposta V0.1; esta seção resolve as quatro perguntas e prevalece em conflito de layout.

### 12.1 Composição desktop (de cima para baixo)

```text
[ PagePath: Início > Fechamento mensal > Visão geral ]                         [Ajuda]
Fechamento mensal           [Mês de referência: 09/2026] [Atualizar consulta]
[Visão geral] [Documentos e interações] [Relatórios e divergências]
[Estado da competência: em andamento / não iniciado / histórico; autoria e freshness]
[ BLOQUEIOS ]       [ DIVERGÊNCIAS ]        [ DOCUMENTOS A TRATAR ]
┌─────────────────────────────────────────────────────────────────────────────┐
│ O QUE PRECISA DE ATENÇÃO                                                  │
│ 1. Conciliação sem confirmação: fontes necessárias ... [Ver detalhes]     │
│ 2. Documentos exigidos pendentes, caso comprovados     [Ver documentos]   │
│ 3. Pacote não preparado, caso aplicável                [Ver contexto]      │
│ [Mostrar todas as pendências] (somente quando fonte e rota comprovadas)    │
└─────────────────────────────────────────────────────────────────────────────┘
[ESTOQUE: estado/fonte]    [DOCUMENTOS: estado]    [PACOTE DRE: estado]
[ATIVIDADE RECENTE: últimos eventos comprovados, autor e momento] [Histórico]
[CONCLUSÃO DA CONTROLADORIA: elegibilidade e bloqueios] [Concluir etapa]
[ENVIO DO PACOTE: elegibilidade e confirmação separada] [Enviar pacote]
```

### 12.2 Conteúdo, dados, acessibilidade e interações

| Componente | Contrato de UX | Fonte/gate e honestidade | Reuso obrigatório a inspecionar |
|---|---|---|---|
| PagePath e título | Título único, caminho e Ajuda; sem segundo chrome | Preservar YYYY-MM e aba; sem criar rota | `createDashboardPagePath`, `createDashboardPageHero`, `HelpTooltip` |
| Mês | Referência selecionada, mudança e atualização explícita | Mudar mês **não** abre; abort/requisições keyed; história separada | `FilterInputField` type=month em uso ou equivalente oficial após inventário |
| Estado do fechamento | Badge + autoria, data/freshness quando disponíveis; vazio sem abertura exibe CTA Abrir | Não unificar P3/P5 num status fictício, status de consulta histórica | `StatusBadge`, `StateBanner`, `ActionButton` |
| Indicadores | Três cards clicáveis: Bloqueios→atenções da Visão geral; Divergências→aba de relatórios; Documentos a tratar→aba documental | Divergência `0` só se fontes aptas e cálculo comprovado; sem fonte `—`; documentos `—` sem semântica contratual | `KpiCard` ou `MetricKpiCard` |
| Atenção / próximos passos | **Seção principal** com 2–4 alertas ordenados por severidade comprovada, motivo em PT-BR, ação contextual e fonte; expandir se necessário | Converter códigos técnicos a mensagens via mapa auditável, sem ocultar causa; não inventar recomendações | `AlertQueue`, `WorklistItem`, `ActionButton` |
| Cards de eixo | Três cartões de Estoque, Documentos e Pacote DRE; estado e próximo passo curto | Eixos independentes; `ATTACHED != VALIDATED`, `PACKAGE_SENT != MONTHLY_CLOSING_COMPLETED` | `StatusBadge`, `StateBanner`, cards de layout kit |
| Atividade recente | 3–5 eventos com tipo, autor, data/hora, link quando existente; empty state neutro | Somente eventos retornados por owner/auditoria; não inferir ações | `Timeline`, `EmptyState` |
| Conclusão/envio | Dois blocos consecutivos no final, com elegibilidade e CTA separados; confirmação quando suportada | Regra de negócio BFF, Core effective permissions; falha de fonte impede falso PASS; P5 vigente | `ActionButton`, `StateBanner`, confirmação do kit |

### 12.3 Estados de tela obrigatórios
- **Sem mês selecionado:** instrução simples “Selecione um mês de referência”; não carregar dados cruzados.
- **Mês não aberto:** dados de leitura disponíveis podem ser consultados; CTA **Abrir fechamento** para `access` elegível. Nenhum avanço por mutação implícita.
- **Aberto sem checklist:** cards e lista documental com estado “Sem exigências cadastradas”, sem bloqueio de entrada nem conclusão automática.
- **Fonte P3 indisponível:** Bloqueios podem apontar indisponibilidade, Divergências = `—` (“Não foi possível verificar”), nunca `0` falso.
- **Histórico finalizado:** leitura contextual e snapshot preservado; sem controles de mutação.
- **Loading/partial/error:** skeleton/spinner do kit, atualização e origem por bloco; uma falha não deve zerar dados de outros eixos nem exibir stale de competência anterior.
- **Permissão negada:** fail-closed no backend; UI explica sem expor dados.
- **Sem eventos recentes:** seção compacta “Nenhuma atividade registrada para esta competência”, sem dados sintéticos.

### 12.4 Visual e mobile
- Desktop: área de atenções em destaque, três KPI pequenos e três cards de eixos compactos; texto humano e espaços moderados. Histórico e ações ao final.
- Mobile: PagePath compacto, mês em linha própria, KPIs empilhados, atenções primeiro após indicadores, eixos empilhados; sem tabela horizontal forçada, botões acessíveis e retorno ao foco após navegação.
- Claro/escuro usam mesma estrutura com tokens do kit; contraste, teclado/enter/space, foco visível, `aria` e Help atualizada.
- Não exibir P2/P3/P4/P5 como blocos grandes na Visão geral. **Retirada visual ≠ exclusão de backend/legacy**.

### 12.5 Critérios de aceite do próximo gate visual
1. 3 abas mantidas e contexto de referência preservado em deep link/F5.
2. Atenções são o maior bloco informacional e têm ações para contextos reais.
3. Histórico resumido aparece com somente eventos comprovados.
4. Cards compactos independentes de Estoque, Documentos e Pacote DRE.
5. Conclusão e envio separados, no rodapé operacional, condicionados a backend.
6. Nenhum código de erro técnico cru exibido ao usuário.
7. Não mostrar zero de divergência quando fontes estiverem indisponíveis.
8. Desktop/mobile, teclado/foco, temas e Ajuda passam QA visual.
9. Kit `@delpi/plugin-ui/index` conferido no export e demonstrações antes de implementação.
10. CLARA e Help sincronizadas com o **que for implementado**, não com um wireframe não publicado.

**Próxima ação:** validar refinamento V0.2 com o PO; depois fechar DESIGN_FREEZE e preparar brief limitado à aba Visão geral. Nenhum runtime/legado foi modificado por esta decisão.
