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

## 13. RUNTIME UPDATE — Visão geral V0.2 implementada (CF-PROC0072-OVERVIEW-UX-004, 26/10/2026)

A composição da §12 foi implementada **somente na aba Visão geral** (`MonthlyOverviewPanel.tsx`), render-only sobre os contratos existentes — nenhum endpoint, schema, owner ou permissão novo. As três abas, o seletor de mês, deep links, refresh, isolamento por período e a compatibilidade legada (`closing/cockpit` com `CockpitSummaryPanel`) permanecem.

Implementado exatamente como aprovado: atenções dominantes com códigos traduzidos (sem código técnico cru na interface), três indicadores clicáveis com «—» honesto, três eixos independentes Estoque/Documentos/Pacote DRE, atividade recente de eventos reais (escopo P3 — feed completo continua `TO_INVENTORY`), e conclusão/envio como blocos separados sem ação de conclusão inventada (estado derivado pelo backend + navegação às superfícies reais).

**Pendente:** homologação visual do PO (desktop/mobile, temas) e reindexação do corpus CLARA com este registro — `PENDING`.


## 14. Visão geral V0.3 — refinamento de linguagem simples e densidade (PO, 26/10/2026)

**Decisão de direção visual:** linguagem PT-BR clara, evitar inglês e jargão; reduzir volume de texto; manter layout V0.2, três abas e integridade dos estados. **Status:** `TARGET / UX_REFINEMENT_APPROVED` para simplificação; textos finais exigem confronto com significado dos contratos; `RUNTIME_NOT_CHANGED`. O PO apontou nas capturas: 'Cutoff', 'Fonte ... indisponível', 'Conciliação P3', 'checklist', 'pacote aplicável', contagem '0 de 3 disponíveis' e enunciados extensos de conclusão.

**Orientação por zona:**
- Hero/header: compacto, manter mês, breadcrumb e atualizações sem texto de marketing repetitivo.
- Indicadores: Bloqueios → `O que falta resolver` ou `Pendências que impedem a conclusão` conforme fonte; Divergências e Documentos a tratar conservam semântica apenas se comprovada; indisponível mostra `—`, não 0 fictício.
- Atenções: título humano breve, uma frase sobre impacto, botão de ação direta. Evitar repetição de 'condição impeditiva de conclusão' em todas as linhas e cartões coloridos longos. Ex.: `p3_cutoff_not_confirmed` → 'Conferência do mês ainda não finalizada'; `p3_source_unavailable:P7` → 'Não foi possível consultar o relatório P7'; `p3_source_unavailable:ENTRADAS_SAIDAS` → 'Não foi possível consultar entradas e saídas'. Referência técnica pode existir em detalhe acessível, não headline.
- Cuidado semântico: `no_applicable_packages` significa que **não há pacote configurado/aplicável**, e NÃO prova que existam documentos exigidos ainda por preparar. Mensagem recomendada: 'Não há um conjunto de documentos para envio definido neste mês', com ação coerente e ownership.
- Cards: Estoque → 'Conferência do estoque', status + próximo passo; Documentos → 'Documentos do mês', 'Nenhum documento exigido para este fechamento' quando verdade; Pacote DRE → 'Documentos para a Contabilidade', sem atribuir estado de envio inexistente. Evitar jargão `cutoff`, `P3`, `template`, `checklist`, `snapshot`, `package`, `source` em copy primária.
- Histórico: 'Atividades recentes', dados reais P3 apenas; informar escopo de modo discreto; ausência 'Ainda não há atividades registradas nesta conferência' sem fingir histórico completo.
- Rodapé: 'Concluir fechamento' e 'Enviar documentos à Contabilidade' — operações distintas, sem habilitar ações novas por copy. Condições de conclusão resumidas em frase simples e link para detalhes.
- Alertas e ações: nunca prometer 'Ver todas as pendências' se a navegação leva apenas a P4 e a contagem inclui P3/P5; permitir expandir atenção na própria Visão geral ou utilizar rótulo que corresponda ao destino real.
- Fallback de blocking_reason desconhecido: mensagem genérica amigável, código técnico somente em telemetria/detalhe para suporte.

**Componentização:** consultar `@delpi/plugin-ui/index` e catálogo real; usar o kit, sem criar novos containers decorativos. Reaproveitar V0.2; não redesenhar domínio nem rotas. Critérios: PT-BR simples, sem inglês em texto principal; curto/legível; não distorcer significado dos estados; manter zero ≠ indisponível; acessibilidade e temas; Help e CLARA no mesmo gate; testes semânticos de labels e links. Remoção de legado proibida neste refinamento.

**Próximo gate:** revisar copy em código/contratos, implementar diff de apresentação após brief delimitado, homologar visual no navegador, publicar conhecimento CLARA somente como realidade implantada.

## 15. RUNTIME UPDATE — Visão geral V0.3 implementada (CF-PROC0072-OVERVIEW-UX-REWORK-005, 26/10/2026)

Refinamento de apresentação/linguagem da Visão geral conforme §14 — **estrutura V0.2 preservada** (três abas, indicadores clicáveis, atenção dominante, três eixos, atividade, conclusão/envio). Nenhum contrato, rota, cálculo ou permissão alterado; diff confinado a `MonthlyOverviewPanel.tsx`, subtítulo do hero, `helpTooltips.ts`, mock e testes.

**Linguagem aplicada (antes → depois):**
- `Cutoff do mês ainda não confirmado` → `Conferência do mês ainda não finalizada`
- `Fonte P7 indisponível` → `Não foi possível consultar o relatório P7`
- `Fonte ENTRADAS_SAIDAS indisponível` → `Não foi possível consultar entradas e saídas`
- `0 de 3 fontes disponíveis` → `Não foi possível consultar N de 3 relatórios necessários`
- `Sem checklist publicado` → `sem lista de documentos definida` (metadado) / `Nenhum documento exigido para este fechamento` (eixo)
- `Nenhum pacote aplicável neste mês` → `Não há um conjunto de documentos para envio definido neste mês`
- `Atividade recente` → `Atividades recentes`; vazio → `Ainda não há atividades registradas nesta conferência`
- `Conclusão da etapa da Controladoria` → `Concluir fechamento`; `Envio do pacote documental` → `Enviar documentos à Contabilidade`
- Indicador `Bloqueios` → `O que falta resolver`
- Fallback de código desconhecido → `Existe uma situação pendente que precisa ser verificada` (código jamais no copy)

**Correção de navegação:** `Ver todas as pendências` (destino P4 parcial) substituído por expansão in-place `Mostrar todas as N situações` / `Mostrar menos` — a lista cobre P3+P4+P5 e nenhuma promessa falsa permanece.

**Honestidade preservada:** `—` continua = indisponível/sem contrato, nunca zero; `no_applicable_packages` não afirma preparação pendente; Atividades recentes segue identificada como escopo das conferências (auditoria P3); conclusão sem botão; envio navega à página real.

**Evidência:** Vitest `MonthlyClosingPage.test.tsx` 31/31 (inclui expansão in-place e fallback sem código cru); suíte do plugin 213/213; `tsc --noEmit` e ESLint limpos; build federado OK.


## 16. Documentos e interações — proposta de wireframe V0.1 (26/10/2026)

**Estado:** `DESIGN_PROPOSED / PENDING_PO_APPROVAL / NO_RUNTIME_GO`. Escopo somente **segunda aba do Fechamento Mensal**. Esta proposta não considera a mera passagem à página seguinte como aceite formal da V0.3 de Visão geral; homologação mobile/temas continua residual.

### 16.1 Propósito e fluxo de uso
O analista escolhe mês; encontra **documentos exigidos para aquela referência**, seus arquivos/versões efetivamente enviados e **solicitações em andamento**. Pode anexar quando autorizado, abrir **detalhe do documento** (deep route contextual mantendo mês/aba), acompanhar comentários/solicitações, enviar nova versão e verificar atendimento. Uma exigência é distinta de um arquivo, que é distinto de um aceite. Se não houver exigências, a aba continua útil e vazia, sem criar cadastro mestre automaticamente. **Cadastro global dos tipos e vigências é Manage/Admin em páginas próprias, não nesta aba.**

### 16.2 Layout proposto — lista
```text
[PagePath: Início > Fechamento mensal > Documentos e interações]
[COMPETÊNCIA COMPARTILHADA YYYY-MM] [Visão geral | Documentos e interações | Relatórios e divergências]
Documentos deste mês                         [Pesquisar documento] [Filtro: Todos/...] 
[Exigidos N*] [Recebidos N*] [Aguardando ajuste N*]  (* só com fonte/semântica validada)
[Lista/tabela responsiva por DOCUMENTO: nome | exigência/estado | versão | última alteração | ação "Ver documento"]
[Estado vazio: "Nenhum documento exigido para este fechamento"; anexos avulsos só por contrato/owner]
[Solicitações de ajuste e mensagens: resumo de solicitações reais | ação "Ver conversa" no detalhe]
```
**Evitar** upload genérico solto no topo e botão que saia para checklist legado. Em vez disso **anexação contextual** pelo documento/detalhe. Preservar upload atual até substituição comprovada e homologada. Não exibir métricas inventadas. Listagem ordenada e filtro devem preservar referência na URL e teclado.

### 16.3 Detalhe do documento e interações — deep route, não quarta aba
- Breadcrumb: Fechamento mensal > Documentos e interações > Documento. Ao voltar, competência, filtro, posição/foco restaurados.
- Desktop: painel esquerdo com prévia PDF inline, download e seletor de versões; painel direito com thread de comentários, pedidos de ajuste e respostas, com identificação de autor e data; seção de histórico de eventos embaixo.
- Mobile: prévia e thread empilhadas; botões e áreas de toque adequados; sem modal extenso.
- A Controladoria pode anexar/enviar nova versão e responder quando autorizada; a Contabilidade/DRE recebe apenas PDFs liberados e pode baixar, comentar e solicitar ajuste quando o gate da sua audiência existir. **Mesmo histórico/versões autorizados, projeções por audiência diferentes**. DRE continua última fase.
- Pedido `ABERTO → RESPONDIDO/AGUARDANDO_CONFERÊNCIA → ATENDIDO` é fluxo ilustrativo, **não enum/contrato aprovado**. **Resposta não encerra automaticamente**; não inventar estados persistentes ou WebSocket antes do gate.
- `ATTACHED != VALIDATED`, complementos não equivalem a aceite formal P2/P5; preservar as versões e snapshot de fechamentos finalizados.

### 16.4 Linhas e campos mínimos
Documento (nome e breve orientação), exigência aplicável à competência (sim/não/sem exigências), arquivo enviado e versão, situação de conferência/ajuste, última interação comprovada, ação contextual de detalhe. Sempre diferenciar **documento exigido**, **arquivo anexado**, **validação do anexo**, **liberação DRE** e **pacote formal**. Se backend não fornece dado, usar `—` + ajuda, não inferir.

### 16.5 Reuso do @delpi/plugin-ui a verificar
- PagePath: `createDashboardPagePath`; título/ajuda: `createDashboardPageHero`, `TitleWithHelp`.
- Listagem: `DataTableSection` ou `DataRecordCard` conforme padrão responsivo real; `EmptyState`/`EmptyGuidance`, `StatusBadge`, `ActionButton`, `FieldLabel`, filtros/forms do kit.
- Detalhe: `BackLink`, `SectionCard`, `Timeline` ou `EventsSection`, campos de anexo/preview PDF e composição lado a lado **somente depois de confirmar exports**; identificar kit real de conversas e versionamento (não supor que exista).
- Visitar `plugins/plugin-ui/src/index.ts`, catálogo `plugins/plugin-ui/docs/component-catalog.md`, `visualComponents.ts`, demos e Portais pares; preferir reuso real à duplicação. Não importar application/domain de Minhas Solicitações.

### 16.6 Contratos/gates pendentes
- Cadastro mestre effective-dated e quais documentos são aplicáveis ao mês (P2/P6); sem criar template por mês.
- Associação de upload a tipo/documento e competência quando checklist está vazio, preservando evidências antigas.
- Comentários, solicitações de ajuste, versões, audiência e notificações/WebSocket, backend AuthZ e auditoria (sem inventar endpoints).
- Regras de alteração para competência aberta versus histórica; integração P5 sem confundir anexo/validação/envio.
- As três abas existem; a página detalhe é deep route e não altera a navegação principal.
- Eventuais decisões de persistência, owner, integração e breaking change seguem `DECISION_REQUIRED` antes de implementar.

### 16.7 Questões para o PO na validação
1. A lista principal mostra **uma linha por documento exigido**, com anexos/versões dentro do detalhe, ou agrupa documentos em cartões?
2. Upload ocorre prioritariamente no detalhe do documento, evitando dropzone genérico na aba?
3. Solicitações de ajuste devem ter pequeno resumo na lista, com toda conversa dentro do detalhe?
4. PDF e conversa lado a lado no desktop, histórico abaixo; no celular um embaixo do outro?
5. Quando não houver documento exigido, deve haver **anexo avulso** no mês ou somente estado vazio até Manager cadastrar tipo aplicável? (Depende também de contrato/owner.)

**Próximo passo:** PO revisa a composição e escolhas antes do freeze visual; depois inventário técnico, RQ/AC, Help e CLARA e brief page-by-page. Nenhum código/deploy autorizado por esta proposta.


## 17. Documentos e interações V0.2 — decisões PO aprovadas e wireframe detalhado (26/10/2026)

**Decisões expressamente aprovadas pelo PO (PROVEN / PRODUCT_DESIGN_APPROVED):** `apresentação=cards`, `upload=detail`, `solicitações=summary`, `documentos sem exigência=optional`. Esta seção **prevalece sobre alternativas da seção 16.7**. **Estado do detalhamento:** `TARGET / DETAILED_WIREFRAME / PENDING_FINAL_VISUAL_APPROVAL`; não concede GO de runtime, migrations ou integração. Somente Fechamento Mensal (PROC-0072).

### 17.1 Aba Documentos e interações — composição

```text
Início > Fechamento mensal > Documentos e interações
[Fechamento mensal] [Mês de referência YYYY-MM] [Atualizar consulta]
[Visão geral] [Documentos e interações] [Relatórios e divergências]
Documentos deste mês                                   [Adicionar documento opcional*]
[Pesquisar documento........] [Filtrar por situação v]
[  CARD: Nome do documento | Exigido/opcional | Estado comprovado ]
[        Arquivo/versão mais recente | Última interação | Ver documento ]
[  CARD: ...                                                        ]
[Solicitações que precisam de atenção — resumo real / Ver conversa]
[Estado vazio honesto se não houver exigência nem arquivo]
```

`*Adicionar documento opcional` não modifica cadastro mestre nem cria obrigação para outras competências; visibilidade e gravação dependem do contrato/owner de anexos avulsos, resource scope e gate. Até implementação comprovada, exibir CTA apenas se ação real existir; senão registrar TO_INVENTORY e manter estado vazio honesto.

**Cartões por documento, não tabela de linhas:** cada cartão tem nome, descrição curta quando disponível, selo Exigido/Adicional, situação real (não enviado, enviado, em análise, ajuste solicitado, conferido — somente se estados contratuais comprovados), versão do arquivo, data e autoria quando disponíveis, contador de solicitações em aberto se comprovado e única ação principal **Ver documento**. Informação ausente = `—`; jamais inventar estado/quantidade. Área de cartões responde em 1 coluna mobile e layout consistente desktop; foco/teclado e leitura de tela.

**Filtros:** pesquisa pelo nome e filtro de situação, sem inferir estado pelo simples upload. Preservar `YYYY-MM`, `tab=documents`, busca/filtro ao navegar ao detalhe e voltar. Listagem de exigidos e adicionais diferenciada sem ocultar os opcionais.

**Solicitações (resumo na aba):** seção compacta exibe os pedidos reais que demandam atenção (documento, situação, última mensagem, data/autor, quando permitido); ação **Abrir conversa** aponta ao detalhe do próprio documento. Não recriar thread completa na lista; não inferir que resposta encerrou a solicitação.

**Upload:** não haverá dropzone genérico no topo da aba. Anexação/substituição de PDFs ocorre **dentro da página de detalhe do documento**, com validação de tipo/tamanho e autorização no backend. Preservar fluxo anterior até substituição testada.

### 17.2 Página de detalhe — wireframe contextual

```text
Fechamento mensal > Documentos e interações > [Documento]
[Voltar aos documentos]      [Documento • referência YYYY-MM] [Estado real]
┌ PRÉVIA E VERSÕES (esquerda) ─────────┐ ┌ INTERAÇÕES (direita) ───────────────┐
│ Prévia PDF inline / indisponibilidade │ │ Pedidos de ajuste e mensagens       │
│ Versão selecionada; data e autoria   │ │ Autor/data/contexto da versão       │
│ [Versões] [Baixar] [Anexar nova]*     │ │ [Comentar] [Solicitar ajuste]*      │
└──────────────────────────────────────┘ │ [Responder] [Verificar atendimento]*│
                                         └─────────────────────────────────────┘
[HISTÓRICO AUDITÁVEL: arquivos, versões, pedidos, respostas e verificações]
```

No desktop, PDF à esquerda, interações à direita e histórico abaixo; no mobile, blocos empilhados. Toda ação `*` requer contrato, autenticação, audience, scope e business rule. Versões antigas permanecem recuperáveis conforme autorização. Falha de preview não impede download autorizado. Uma resposta da Controladoria **não** marca automaticamente pedido como atendido; a parte autorizada verifica. `ATTACHED != VALIDATED`, revisão documental não equivale a aceite P5. Página de detalhe é deep route da aba, **não quarta aba**.

### 17.3 Documento opcional / sem exigências

- PO aprovou **permitir documento adicional** por competência, inclusive sem exigência geral publicada, desde que usuário possua autorização efetiva de anexação.
- Documento opcional é evidência daquele mês, **não** novo tipo obrigatório no catálogo master, **não** obrigação prospectiva nem item fictício de checklist. Não altera finalizados nem períodos vizinhos.
- Requer inventário e decisão de modelagem/contrato para tipo livre versus tipado, vínculo ao fechamento/versão e admissibilidade P2/P5. Se o contrato atual não comportar a operação, emitir `DECISION_REQUIRED` antes de migration/novo endpoint; **não** criar item artificial no template para habilitar upload.
- Um fechamento sem exigências continua acessível; mostrar mensagem “Nenhum documento exigido para este mês” e ação de documento opcional somente quando disponível.

### 17.4 Kit, QA e gates

Inventariar `plugins/plugin-ui/src/index.ts`, `plugins/plugin-ui/docs/component-catalog.md`, `visualComponents.ts` e demos. Candidatos por superfície: `createDashboardPagePath`, `createDashboardPageHero`, `DataRecordCard`/cartão real compartilhado, `StatusBadge`, `ActionButton`, `EmptyState`/`EmptyGuidance`, controle de pesquisa/filtro do kit; detalhe: `BackLink`, `SectionCard`, `EventsSection`/`Timeline`, anexo/preview e campos de mensagem **após confirmar export e contrato**. Sem duplicar chrome, padrões de layout ou importar domínio de Minhas Solicitações. Responsividade, foco, teclado, temas e Ajuda são DoD.

**AC:** (1) cartões por documento, sem tabela principal; (2) upload só no detalhe; (3) resumo de solicitações na aba e thread completa no detalhe; (4) opcional por mês sem virar exigência geral; (5) versões e histórico preservados; (6) ausência de documentos é estado normal; (7) authorized audiences separadas; (8) deep link/URL/F5/voltar preservam contexto; (9) sem dados ou estados inventados; (10) nenhuma quarta aba; (11) colaboração/WebSocket somente após gates; (12) CLARA e Help atualizadas no mesmo gate da implementação comprovada.

**Próxima etapa:** apresentar a V0.2 ao PO para ajuste/aprovação final do desenho (detalhe lado a lado permanece proposta anterior não contrariada pelas quatro escolhas). Após freeze e inventário, elaborar execução incremental page-by-page. Legado não será removido nesta etapa.

## 18. RUNTIME UPDATE — Documentos e interações V0.2 implementada (CF-PROC0072-DOCUMENTS-UX-006, 26/10/2026)

Implementada a segunda aba do Fechamento Mensal conforme §16–17 e decisões PO do doc 112 §38. Sem migration, sem endpoint novo, sem contrato de colaboração inventado.

### 18.1 O que foi implementado
- **Cartões por documento** (`MonthlyDocumentsPanel`): um cartão por **exigência** do checklist (badge «Exigido», estado real do item — aguardando/conferido/não se aplica) e um por **documento adicional** (`link_kind=competence`, badge «Adicional»). Versão mais recente e última alteração vêm de `listClosingDocuments`; nunca tabela como apresentação principal.
- **Pesquisa e filtro por situação** via `FiltersRow`/`FilterInputField`/`FilterSelectField`; pesquisa (`q`) e situação (`state`) vivem na query da aba — F5, deep link e retorno do detalhe preservam o contexto.
- **Solicitações que precisam de atenção**: decisões `REJECTED` correntes por item via `getItemValidation` — motivo estruturado, comentário, autor e data reais; «Abrir conversa» leva ao detalhe do item. Reversões (`REVERSED`) removem a solicitação do resumo.
- **Detalhe do documento** (`DocumentDetailPanel`) na deep route `closing/monthly-closing/{YYYY-MM}/documents/{ref}` — não é quarta aba: `ref=item:{item_key}` (exigido), `ref={document_id}` (adicional), `ref=new` (anexação contextual de adicional). Layout: prévia/documento à esquerda, «Interações» à direita, «Histórico» abaixo; mobile empilha.
- **Prévia autenticada** por `FilePreviewView` + `useFilePreviewLoader` sobre o blob de `downloadClosingDocument` — falha de prévia nunca bloqueia o download.
- **Upload contextual**: no detalhe do item anexa com `snapshot_item_id`; em `new` anexa documento adicional sem `snapshot_item_id` (contrato U1 já admitia — **documento adicional não cria exigência geral** nem item fictício). «Enviar nova versão» usa `replaceClosingDocument` com `revision`+`idempotency_key`; versão anterior preservada (`SUPERSEDED`).
- **Histórico real**: `listDocumentEvents` por documento (anexação, versão, download autorizado/negado, cancelamento).
- **U3 — `getClosingDocument`** adicionado ao client `documentsApi` (endpoint GET por id já existente).
- Legado preservado: `ClosingDocumentsPanel` continua na página `closing/checklist/{period}`; rotas legadas intactas.

### 18.2 O que NÃO existe (honestidade)
- **Conversa livre por documento não possui contrato** — a coluna «Interações» mostra decisões reais (ajuste solicitado/conferido/revertido) e declara explicitamente que a conversa livre ainda não está disponível. Nenhuma mensagem é simulada.
- Notificações/WebSocket: `PLANNED`, sem afirmação de tempo real.
- Audiência DRE/Contabilidade no detalhe: `PLANNED` para fase futura; sem permissão nova.
- `ATTACHED != VALIDATED`; resposta/decisão não encerra solicitação automaticamente.

### 18.3 Componentes do kit efetivamente usados
`createDashboardPagePath`, `createDashboardPageHero`, `createDashboardSectionCard` (com `hint`), `createDashboardStatusBadge`, `ActionButton`, `EmptyState`, `StateBanner`/QueryErrorBanner, `FiltersRow`+`FilterInputField`+`FilterSelectField`, `FileDropzone`, `FilePreviewView`, `useFilePreviewLoader`, `TitleWithHelp`. Nenhum componente copiado; nenhum chrome paralelo.

### 18.4 Evidência
Vitest focado: `MonthlyDocumentsPanel` 10/10, `DocumentDetailPanel` 7/7, `MonthlyClosingPage` 32/32, `pluginRoutes` 18/18. Suíte fechamento 160/160; suíte plugin completa OK. `tsc -b`/`--noEmit` e ESLint PASS; build federado OK; testes estruturais (boundary MFE→BFF, cobertura de ajuda) PASS. Smoke autenticado Devin: `TEST_NOT_RUN`; homologação visual do PO: `PENDING`.



## 19. REWORK documental V0.3 — download, ações do documento, histórico e QA frontend (decisão PO 26/10/2026)

**Estado:** `PO_APPROVED` para comportamento/UX; `REWORK_REQUIRED` para entrega V0.2; `RUNTIME_DIAGNOSTIC_PENDING` para erro de download e eventual mudança no audit producer. **Não confundir pedido de 'excluir' com DELETE físico:** contrato atual U7 é cancelamento lógico com retenção de versões e histórico; eventual apagamento físico/depreciação requer decisão separada de ciclo de vida, retenção, compliance e dados.

### 19.1 Evidências observadas e verificações
- Captura PO em `/closing/monthly-closing/2026-09?tab=documents`: cartões existentes, botão Adicionar documento, porém seção legada `Checklist da competência` ainda leva a página dedicada, contrariando centralização do fluxo na aba.
- Detalhe `/closing/monthly-closing/2026-09/documents/{document_id}`: erro visível **'Falha ao baixar o arquivo'**, prévia indefinidamente **'Carregando pré-visualização...'**; histórico preenchido por muitas linhas idênticas **'Download — v1'**, com UUID técnico e sem informação útil. Isso é evidência visual do resultado, **não prova do root cause HTTP**.
- Inspeção GitHub: `documentsApi.ts` implementa `downloadClosingDocument` (U4 bytes), `replaceClosingDocument` (U5 revisão/OCC), `listDocumentVersions` (U6), `cancelClosingDocument` (U7 cancelamento lógico), `listDocumentEvents` (U8). `DocumentDetailPanel.tsx` renderiza `DOCUMENT_DOWNLOADED` como `Download` no histórico, e não expõe ação `cancelClosingDocument`. **Reavaliar producer U4/U8 antes de remover emissão/persistência**: decisão PO é que downloads rotineiros **não compõem o histórico operacional do documento** e não devem gerar registros de negócio repetitivos. Preservar logs técnicos de segurança legalmente/contratualmente exigidos (acesso/download), se aplicável, segregados da timeline de versões e ajustes; alteração na emissão/armazenamento exige owner e security gate.
- Os uploads e arquivos atuais, inclusive `Recebidos.pdf`, devem ser preservados; não apagar eventos históricos ou documentos produtivos para 'limpar' tela.

### 19.2 UX detalhado aprovado
1. **Card:** manter cartões, inserir menu acessível de **três pontos** (padrão real `@delpi/plugin-ui`, inspecionar export) com somente operações válidas: `Abrir documento`, `Enviar nova versão` (quando contextual/autorizado), `Remover documento`/ `Cancelar documento` conforme semântica real; ação destrutiva com confirmação clara, disabled/hidden conforme capability+scope+business rule e tratamento de erro. Não duplicar quatro botões em cada card.
2. **Detalhe:** ações reais e completas de ciclo de vida **anexar**, **enviar nova versão**, **consultar versões**, **baixar**, **cancelar/remover logicamente** (quando permitido); oferecer nome legível e confirmação explícita do efeito (não apaga versões/auditoria). Para documento exigido, avaliar se a operação cancela arquivo U7, item de exigência P2, ou ambos — **não presumir que cancelar documento elimina obrigação**.
3. **Preview:** prévia autenticada com erro/retry honesto, sem spinner infinito; diferenciar falha de download, ausência, 403, 404, conteúdo inválido e rede; verificar contrato HTTP, `httpGetBlob`, response/Content-Type, proxy/BFF, versão/ID/escopo, URL blob e revogação; não sugerir download funcional quando há falha.
4. **Histórico:** mostrar versões (v1/v2), anexos, cancelamentos, solicitações, respostas e decisões **reais**, com ator/data de modo humano e sem UUID cru; **não exibir eventos `DOCUMENT_DOWNLOADED` na timeline operacional**. Evitar re-registro por prévia/refresh; confirmar se produtor U4 audita cada GET e separar auditoria de segurança do histórico do usuário.
5. **Solicitações:** resumo na aba, detalhes e versões na página de documento; não inventar conversa livre; resposta ≠ aceite.
6. **Aba:** remover da **composição visível atual** o bloco legado `Checklist da competência`/navegação obrigatória fora do workspace, **somente após** mapear funcionalidades de validação P2 que devem permanecer acessíveis no contexto ou registrar gate de integração. Não apagar código/rotas legados.
7. **Terminologia:** português simples; `Excluir` no UX exige explicação de cancelamento lógico; preferir `Remover documento` com confirmação ‘o documento não aparecerá na lista ativa, mas versões e histórico serão mantidos’, caso esta seja a semântica realmente comprovada. Não renomear estado P2 como removido sem contrato.
8. **Responsividade:** card/menu/foco em desktop e mobile, teclado Escape/Enter, tema claro/escuro, PagePath, URL/F5/voltar/preservação de competência e filtros.

### 19.3 Critérios de aceite e STOP
- Download U4 de versão existente funciona em fluxo autenticado real e prévia carrega, ou estado de erro explicita causa sem loop; HTTP 200 sozinho não basta.
- Ação de remoção (U7) disponível em menu de três pontos e/ou detalhe, autorizada backend, confirmação e efeito em listagem; item obrigatório não se torna automaticamente não exigido; testar retry, OCC, 403/404/409, arquivo vigente, histórico e concorrência.
- Nova revisão U5 preserva v1, atualiza versão atual e prévia, idempotência; não usar GET/download como fonte de mutações operacionais visíveis.
- Histórico operacional legível, limitado/paginado conforme volume, sem downloads repetitivos e sem IDs técnicos crus; eventos antigos preservados no backend conforme retenção. Decisão de **não registrar novos downloads como eventos de negócio** depende de inspeção da autoridade de segurança/auditoria; jamais eliminar trilha obrigatória sem gate.
- Cartões e detalhe aderentes §17; nenhum modal excessivo, nem perda de UX de documento adicional; seções antigas retiradas apenas da UI nova.
- Testes backend/frontend/integrados (incluindo download real e preview), CLARA e Ajuda atualizadas; deploy local/produção conforme owner e gates; smoke autenticado PO. Se alteração de U4/U8, audit retention ou download autorização exigir breaking/security decision: `DECISION_REQUIRED` no subescopo, sem impedir o rework visual independente.


## 20. RUNTIME UPDATE — Rework documental executado (CF-PROC0072-DOCUMENTS-REWORK-007, 26/10/2026)

Correção dos defeitos comprovados na V0.2 conforme §19. Sem migration, sem endpoint novo, sem permission nova, sem alteração de produtor de auditoria.

### 20.1 Causa raiz comprovada do download
O fluxo `DocumentDetailPanel → downloadClosingDocument → httpGetBlob → BFF U4 → autorização → storage → FileResponse` foi rastreado ponta a ponta: rota, método, versão, competence, effective permission, resource scope, `Content-Type` e auditoria estavam **corretos** no backend. A falha era um **loop de identidade no frontend**: o `source` passado ao `useFilePreviewLoader` era uma arrow function nova a cada render; o `useEffect` do hook depende da identidade de `source`, então cada `setState` provocava novo render → nova identidade → novo GET U4 → novo `DOCUMENT_DOWNLOADED` → novo render. Resultado: prévia presa em «Carregando pré-visualização…», enxurrada de eventos de download no histórico e interferência no download manual. Correção na fonte: `source` estabilizado via `useCallback` com deps `[period, documentId, versionNo, previewNonce]` — refetch somente por mudança real de alvo ou retry explícito.

### 20.2 Correções entregues
- **Prévia**: identidade estável (§20.1), estado de erro finito com «Tentar novamente» (`previewNonce`), download manual independente da prévia, seleção de versão carimbada por `document_id` (versão anterior nunca vaza para outro documento), abort/cleanup nativo do hook ao trocar de documento.
- **Menu de três pontos** nos cartões: `ContextMenu`/`ContextMenuItem`/`ContextMenuDivider` reais do `@delpi/plugin-ui` (portal, role `menu`/`menuitem`, Escape, foco, `aria-label` no trigger). Ações: «Abrir documento»; «Enviar nova versão» (U5) e «Remover documento» (U7) só quando existe documento vigente — exigência sem arquivo não oferece ação impossível.
- **Remoção lógica (U7)**: confirmação via `ConfirmModalPanel` com nome do arquivo, consequência («sai da lista, versões e histórico preservados») e, para item exigido, aviso explícito de que **a exigência continua valendo**. `revision` (OCC) + tratamento de `stale_revision` com refresh. Sucesso em documento adicional retorna à lista; em item exigido, atualiza in-place. `CANCELLED != DELETED` preservado; sem DELETE físico.
- **Nova versão (U5)** acessível no detalhe e no cartão: `revision` + `idempotency_key`, versão anterior preservada (`SUPERSEDED`), prévia/download respeitam a versão selecionada.
- **Histórico operacional**: eventos `DOCUMENT_DOWNLOADED` removidos da timeline visível; rodapé declara que downloads ficam na trilha de auditoria. **Nenhum evento histórico foi apagado e nenhum produtor foi alterado** — o backend continua auditando autorização/storage do U4 conforme contrato; eventual redução de emissão na origem exige owner de segurança/auditoria + gate próprio (`PLANNED`, não executado).
- **Interações reais**: `ItemValidationPanel` embutido no detalhe do item exigido — decisões ACCEPTED/REJECTED, correções e reversões reais, sem conversa fictícia.
- **Bloco legado removido da composição**: «Checklist da competência» não aparece mais na aba porque a validação item a item agora acontece no próprio detalhe do documento (`ItemValidationPanel`). Rota e página `closing/checklist/{period}` **permanecem intactas** — apenas a navegação obrigatória foi eliminada.

### 20.3 Componentes do kit efetivamente usados (acréscimo ao §18.3)
`ContextMenu`, `ContextMenuItem`, `ContextMenuDivider`, `ConfirmModalPanel`, `CfDialog` (wrapper local do kit), `ItemValidationPanel` (componente do próprio plugin já existente). Nenhum componente de menu/confirmação paralelo criado.

### 20.4 Evidência
Vitest focado: `MonthlyDocumentsPanel` 15/15 (menu, ações, U5, U7, confirmação/cancelamento), `DocumentDetailPanel` 13/13 (regressão de fetch único U4, retry, versão anterior, remoção, histórico sem downloads), `MonthlyClosingPage` 32/32 (sem bloco legado), `pluginRoutes` 18/18. Suíte fechamento 171/171; plugin 244/244. `tsc -b` PASS; ESLint dos arquivos do escopo limpo; estruturais (manifest, boundary MFE→BFF, cobertura de ajuda) PASS; build federado PASS (`App-C81K9e6S.js`). Smoke autenticado Devin: `TEST_NOT_RUN`; homologação visual PO: `PENDING`.


## 21. Interações proativas por documento — decisão PO e evolução V0.4 (26/10/2026)

**Decisão expressa do PO — PRODUCT_APPROVED:** a **Controladoria pode iniciar a conversa no documento a qualquer momento autorizado**, inclusive antes de a Contabilidade/DRE enviar sua primeira mensagem, solicitar ajuste ou receber o documento. **Não há dependência de mensagem prévia da DRE.** A conversa pertence ao contexto de `competência + documento + versão quando pertinente`, não ao usuário que iniciou ou a uma solicitação de ajuste preexistente. Comentário comum, pedido de ajuste, resposta, confirmação de atendimento e aceite formal P2/P5 são eventos diferentes; enviar mensagem não valida, não encerra pedido e não libera documento automaticamente.

**Evidência visual:** nas capturas após V0.3 o PDF abre e pode ser consultado; a coluna `Interações` mostra somente “Nenhuma solicitação registrada” e que “a conversa livre por documento ainda não está disponível”. Há lacuna funcional real entre wireframe aprovado e runtime, não apenas texto ou estilo. Os cartões permanecem compactos com menu de três pontos; manter lista em cards e abrir detalhes em deep route. Linha de histórico vazia pode ser legítima após filtrar downloads; **não sintetizar eventos**.

### 21.1 Layout detalhado do documento — proposta visual a operacionalizar
- Cabeçalho compacto com nome, mês, situação, voltar; evitar repetir hero completo com grande seletor se a página já herdou contexto.
- Desktop: PDF e versões à esquerda; **conversa real à direita**, com área rolável, mensagens cronológicas, autor, data/hora e indicação de destinatários/audiência quando autorizada. **Composer fixo ao final da coluna**, campo multiline e botão `Enviar mensagem` com loading/erro/retry sem duplicação. A Controladoria vê ação de escrever mesmo se a thread estiver vazia (quando autorizada). Estado inicial: “Nenhuma mensagem ainda. Você pode iniciar a conversa sobre este documento.”
- Ações distintas no contexto de uma mensagem ou documento: comentário; solicitar ajuste; responder a pedido; marcar atendimento/conferir com autorização. Não inventar as quatro operações se o contrato ainda não existir.
- Iniciar conversa não altera estado de validação, não envia pacote, não cria obrigação documental e não expõe o documento à DRE antes de liberação. Destinatários/visibilidade seguem escopo e audience governados; mensagem pré-liberação pode ser interna à Controladoria, **não presumir que a DRE tenha acesso**.
- Histórico abaixo mostra eventos materiais (nova versão, pedido, resposta, validação, cancelamento); mensagens aparecem na thread para evitar duplicação. Downloads permanecem fora do histórico operacional. UUID técnico não aparece como nome do autor na UI; resolver identidade autorizada ou exibir identificação neutra sem inventar.
- Mobile: PDF, thread e histórico empilhados; composer alcançável por teclado; foco, rolagem, temas, acessibilidade e deep links preservados.

### 21.2 Necessidades de contrato e gate de colaboração (TARGET; não runtime)
- Inventariar padrões técnicos de **Minhas Solicitações** e `@delpi/plugin-ui` para visual, thread, composer, badges e eventos, **sem importar domain/application/API do outro contexto**.
- Definir owner da thread e mensagens do **controllership-finance-api**, identificadores, vínculo com competência/documento/versão, audiência/participantes e regras de visibilidade antes/depois da liberação DRE, leitura, escrita, idempotência, paginação, ordenação, anexos de mensagem se houver, auditoria e retenção.
- Contratos distintos para mensagem livre, solicitação de ajuste, resposta e confirmação/encerramento do pedido. **Não exigir uma solicitação DRE para criar thread**.
- Backend: effective permissions Core + resource scope/ownership + business rule, fail-closed; sem nova permission por página. Notificações e WebSocket somente com contracts e owners autorizados; começar com mensagens persistidas e atualização manual/poll governado se preciso, sem alegar tempo real fictício.
- Proteger histórico de competências finalizadas e imutabilidade de pacote enviado; definir se comentário pós-conclusão é permitido e em qual audiência antes de implementação.
- Se mudanças de BFF, schema, lifecycle, boundaries ou security ainda não têm gate, entregar **DECISION_REQUIRED** com alternativas e impactos no subescopo, mas não bloquear o redesign visual independente.

### 21.3 UX da aba Documentos e interações
- Manter cartões e filtro; resumo “Conversas e solicitações que precisam de atenção” deve cobrir **mensagens/pedidos reais do contexto autorizado**, diferenciando pendências de ajuste de novas mensagens. Não exibir contador inventado. Ao clicar, navegar para o detalhe e focar a thread.
- **Adicionar documento** e menu três pontos permanecem; remover é cancelamento lógico U7 com confirmação. Nenhuma ação adicional é executada por iniciativa do assistente.
- Refinamento de densidade: na página de detalhe dar mais largura/altura útil ao leitor PDF e composer; compactar hero e metadados, reduzir barras vazias. Seguir padrões do kit.

### 21.4 Critérios de aceite da colaboração
1. `access` autorizado inicia mensagem em documento sem nenhuma mensagem anterior da DRE.
2. Mensagem persiste e aparece ao recarregar / trocar contexto; não só frontend state.
3. Documento não liberado não é exposto à DRE.
4. Autoria/data confiáveis; sem mensagens duplicadas em retry.
5. Mensagem não dispara validação, conclusão, envio nem encerramento de pedido.
6. Solicitação de ajuste e confirmação possuem atos separados se implementados.
7. Segurança negativa/sibling, histórico, troca de competência, temas, mobile, teclado/foco e deep link testados.
8. Ajuda e CLARA atualizadas somente conforme runtime comprovado; documentação distingue `TARGET` de `PROVEN`.
9. Deploy local e produção apenas com gates técnicos/operacionais, smoke autenticado e evidência.

**Situação:** PO aprovou a capacidade de **iniciar conversa proativamente**; visual detalhado é `TARGET` e os contratos de colaboração estão `TO_INVENTORY`. Próximo passo: inventário pelo Devin → reconciliação de owners/segurança → implementação incremental autorizada → homologação PO. Não afirmar funcionalidade já entregue.

## 22. RUNTIME UPDATE — Conversa documental implementada (CF-PROC0072-DOCUMENT-INTERACTIONS-008, 27/10/2026)

### 22.1 Contrato U9 implementado (IMPLEMENTED)

**Owner:** `controllership-finance-api`, aggregate `closing_document`
(`ClosingDocumentService`/`ClosingDocumentRepository` — mesma fonte de
U1–U8; nenhuma API paralela criada).

- `GET /closing/competences/{period}/documents/{document_id}/messages`
  — lista cronológica ASC, `limit<=100`/`offset`, `branch_scope`
  declarado; `mine` derivado do ator autenticado pelo backend.
- `POST /closing/competences/{period}/documents/{document_id}/messages`
  — corpo JSON `{body, idempotency_key}`; 201 na criação; replay
  idêntico retorna a mensagem original com `deduplicated` (200); mesma
  chave com texto divergente ⇒ 409 `idempotency_conflict`.

**Persistência V016 — `controllership_finance.document_message`:**
`message_id` PK · `document_id`+`competence_id` (FK, RESTRICT — a chave
de vínculo nunca é o nome do arquivo) · `version_no` (carimbo contextual
da versão corrente no envio — a conversa pertence ao documento, não a
uma versão) · `audience` CHECK fechado em `'INTERNAL'` (somente
Controladoria; audiência compartilhada com DRE = gate transversal
futuro) · `body` CHECK 1–4000 chars úteis · `author_subject` UUID +
`author_name` VARCHAR(255) NULL (snapshot do claim `name`; ausência
fica NULL e a UI mostra identificação neutra — UUID nunca é nome)
· `idempotency_key`+`request_hash` com `UNIQUE(document_id,
idempotency_key)` · `created_at` do servidor. Append-only.

**Segurança (mesmo padrão U3/U4):** `access` efetivo + documento da
competência do path + filial-contexto declarado — cross-competence e
cross-scope são 404 (existência nunca vaza). Envio exige `access` +
escopo + regra de negócio; service principal e ausência de permissão
falham fechado (403/401).

**Regras de negócio:** a mensagem NÃO é mutação documental — permitida
em `ATTACHED` e `CANCELLED` (a conversa documenta o contexto,
inclusive de uma remoção); não altera estado do documento, validação
do item, pacote nem fechamento; não libera documento à DRE; não exige
solicitação prévia. Item em pacote submetido não bloqueia a conversa
(congelamento vale para a evidência, não para o fio).

**Auditoria:** `DOCUMENT_MESSAGE_POSTED` em `closing_audit_event`
(entidade `closing_document`) na mesma transação da mensagem; detail =
`message_id`+`version_no`, nunca o corpo. O evento passa a constar do
filtro de tipos de U8 (trilha completa) e é excluído da linha do tempo
operacional da UI (mensagens vivem na conversa; downloads continuam
fora — §20).

### 22.2 Frontend (IMPLEMENTED)

- Coluna direita do detalhe: `Conversa sobre o documento` com
  `CfMessageThread` + `CfMentionComposer` (factories
  `createDashboardMessageThread`/`createDashboardMentionComposer` do
  `@delpi/plugin-ui`, prefixo `cf` — mesmo padrão de Minhas
  Solicitações, sem import de código de outro contexto).
- Composer visível já na thread vazia para usuário com `access`;
  `submitOnEnter={false}` (Enter não envia multiline; Ctrl+Enter e o
  botão «Enviar mensagem» enviam); rascunho preservado na falha;
  retry do mesmo texto reutiliza a `idempotencyKey` — sem duplicidade.
- A mensagem só aparece após confirmação do backend; F5/navegação
  recarrega a conversa persistida (`key={document_id}` — nenhum estado
  vaza entre documentos/competências).
- Item exigido mantém `ItemValidationPanel` em cartão próprio
  («Validação do documento») — validação P2 e conversa livre são
  conceitos separados e visíveis como tais.
- UUID removido também da linha de metadados do documento
  (`uploaded_by` não é mais exibido como identificação visual).

### 22.3 Fora de escopo entregue / pendente

- Anexos de mensagem, edição/exclusão, menções funcionais, resposta
  aninhada, contador de não-lidas, notificações e WebSocket: TARGET —
  exigem contrato/owner próprios (não inventados).
- Acesso da DRE/Contabilidade à conversa: TARGET — depende do gate de
  audiência/liberação (audience `INTERNAL` fecha o escopo hoje).
- Resumo «precisam de atenção» na aba: mantido honesto (solicitações
  reais); não foi criado contador de mensagens sem contrato de leitura.
- Homologação visual do composer (temas, mobile): verificada nos
  contratos do kit; a homologação visual PO permanece o próximo passo.

### 22.4 Evidências (VERIFIED)

- Migration V016 aplicada em banco efêmero via runner canônico;
  `applied[-1] == V016__document_messages.sql` em todas as suítes PG.
- Backend: rotas+service 110/110 · PG documental 30/30 (idempotência,
  deduplicação, conflito 409, cronologia, escopo, FK RESTRICT, CHECK de
  corpo, auditoria na mesma transação) · demais suítes PG 175/175 ·
  suíte não-PG 420.
- Frontend: detalhe 18/18 (envio proativo, confirmação antes de
  renderizar, retry idempotente, texto preservado na falha, conversa
  no item exigido) · suíte closing 176/176 · plugin 249/249 ·
  `tsc -b` PASS · ESLint escopo limpo · build federado PASS
  (`App-D0zGdiAL.js`).


## 23. Refinamento do detalhe documental V0.5 — conversa, linha do tempo e avatar (PO, 26/10/2026)

**Decisão do PO (PRODUCT_APPROVED):** melhorar a coluna de conversa com **altura mínima visual padrão**, inclusive com zero ou uma mensagem; usar componente compartilhado de **linha do tempo** para eventos materiais; exibir **avatar verdadeiro/autorizado** do usuário nas mensagens e eventos (com fallback acessível quando não houver foto). Não inventar foto, URL ou perfil. **DESIGN_TARGET / GATE_DE_IMPLEMENTAÇÃO_PENDENTE**: nenhum runtime é alterado por esta entrada.

### Evidência visual e inventário GitHub
- Na captura do detalhe de `Recebidos.pdf`, conversa com uma mensagem fica muito baixa enquanto visualizador PDF ocupa grande altura; histórico aparece como cartão vazio e sem composição de eventos; o cabeçalho da página ocupa espaço grande.
- No HEAD consultado, `DocumentConversationPanel.tsx` usa `CfMessageThread` e `CfMentionComposer`, mas `.cf-document-conversation` em `index.css` declara `min-height: 0` e limita a thread a `max-height: 420px`. **Não há altura mínima** que preserve a bancada de conversa vazia ou pouco movimentada.
- `DocumentDetailPanel.tsx` renderiza histórico em `<ul className="cf-document-detail__history">` com `actor_subject` UUID cru, não timeline compartilhada. Filtra downloads e mensagens comuns, que devem permanecer fora da linha do tempo operacional.
- `@delpi/plugin-ui/index` exporta `UnifiedAvatar` e `createDashboardEventsSection`; **este EventsSection é baseado em AlertQueue, não comprova equivalência com timeline cronológica**. Antes de selecionar a timeline, inventariar componente realmente utilizado em outros Portais e seus exports/factories/demos; reusar o compartilhado ou submeter evolução do kit ao owner.
- `UnifiedAvatar` admite `kind="person"`, `imageUrl` de contrato de foto publicado pelo owner e fallback; comentário do kit proíbe derivar nome/foto confiáveis diretamente de claims JWT. **Identidade e foto do autor de eventos/mensagens dependem de contrato de perfil autorizado**. Não interpolar UUID, não montar URL de foto por convenção e não usar a foto do usuário logado para mensagens de outros autores.

### 23.1 Conversa — comportamento e layout
1. Coluna da conversa com **altura mínima consistente** no desktop, aproximadamente alinhada à área de prévia útil do PDF, com crescimento e limite por viewport; altura fixa apenas se responsiva e testada. Referência de design: `min-height` na faixa **480–560px** no desktop, a ajustar pelo padrão real do kit; não tratar medida ilustrativa como token congelado.
2. Header da conversa; área de mensagens preenchendo o espaço entre header e composer; conversa **rolável internamente** e composer **ancorado no rodapé** da coluna, sempre disponível quando usuário autorizado, mesmo com 0/1 mensagem.
3. Estado vazio proporcional, texto amigável e ação de iniciar conversa; uma mensagem não reduz a coluna nem desloca o composer para cima.
4. Mobile: altura adaptativa, componentes empilhados e scroll sem aprisionar o usuário; foco, teclado, Enter/Tab/Escape, temas claro/escuro e leitores de tela.
5. Preservar U9, idempotência, mensagem interna e todas as regras de AuthZ; não transformar mensagem em validação/aceite.

### 23.2 Linha do tempo de eventos
1. Utilizar timeline **cronológica real** do kit/Portal (com conectores, marcos, título e texto curto), não uma lista simples nem `EventsSection` de alertas por substituição visual automática.
2. Eventos materiais: anexo, nova versão, cancelamento lógico, solicitações de ajuste e validações comprovadas; identificar tipo, data e autor autorizados, referência da versão e ação contextual quando houver. Mensagens comuns ficam na thread; downloads rotineiros ficam fora da timeline.
3. Quando nenhum evento material é retornado, apresentar empty state compacto honesto; **não inventar evento** para preencher o visual. Verificar se U8 já produz eventos do tipo necessário e mapear enum/evento real.
4. Sem UUID cru, sem dados de pessoa inferidos e sem N+1 inseguro para resolver perfis; exigir leitura autorizada do Core ou projeção BFF do owner.

### 23.3 Avatar do participante
1. Reusar `UnifiedAvatar` (export confirmado), `kind="person"`; se a factory de `MessageThread` já suporta avatar, utilizar seu mecanismo nativo em vez de duplicar avatar dentro da bolha. Para timeline, usar slot/componente compartilhado quando disponível.
2. Resolver **displayName e imageUrl** de contrato de identidade/perfil owner-published e autorização aplicável. Foto ausente/falha → iniciais ou ícone neutro com nome autorizado; não exibir UUID; não vazar dados pessoais entre audiências.
3. Mensagens U9 atualmente guardam `author_subject` + `author_name` snapshot de claim; esse valor não prova foto nem nome publicado por owner. **CONTRACT_TO_INVENTORY:** mapeamento/consulta BFF-Core de perfil, cache, autorização e comportamento de autor histórico/inativo. Se novo contrato for necessário, emitir `DECISION_REQUIRED` antes de alterar serviço/migration.
4. Não mudar permission codes `controllership-finance.access/manage`.

### 23.4 Critérios de aceite e sequência
- Desktop: conversa com 0/1/muitas mensagens mantém área utilizável e composer ao fundo, sem altura minúscula; PDF permanece visível. Mobile claro/escuro/foco/teclado testados.
- Timeline reutiliza componente compartilhado verificado e ordena eventos reais, distingue marcos e datas e não exibe downloads/mensagens comuns duplicados.
- Avatares corretos por autor quando foto contratual existir; fallback confiável sem inventar identidade; testes com dois autores, autor sem foto e dados restritos.
- Não alterar U9, P2/P5, versões, autorizações ou documentação de runtime por aparência; atualizar Ajuda e CLARA no gate de implementação comprovada.
- **Execução seguinte:** inventário da timeline real dos Portais e perfil/avatars Core → contrato/gate se necessário → diff mínimo frontend → testes → deploy local/produção autorizados → smoke PO → documentos/CLARA com evidências.

**Pendente:** escolha técnica exata do componente cronológico e fonte confiável de avatar. A regra visual/experiência já está aprovada pelo PO.


### 23.5 Implementação UX-009 — RUNTIME PROVEN (26/10/2026)

Gate de implementação executado e comprovado. Nada nesta seção altera o
contrato U9, permissões congeladas ou o lifecycle documental.

**Timeline compartilhada (PROVEN).** O histórico do detalhe deixou de
ser `<ul>` local e passa a usar `createTimeline` do `@delpi/plugin-ui`
— o mesmo componente cronológico já utilizado pelo Portal CIPA
(`CipaTimeline`), com trilha, marcadores por tom (`info/success/
warning/danger`), título, detalhe e data. `EventsSection` (AlertQueue)
confirmado como componente de alertas — **não** é a timeline e não foi
usado. Fonte: eventos U8 existentes (`DOCUMENT_UPLOADED`,
`VERSION_ADDED`, `DOCUMENT_CANCELLED`, `EVIDENCE_ACCEPTED`,
`EVIDENCE_REJECTED`); `DOCUMENT_DOWNLOADED` e
`DOCUMENT_MESSAGE_POSTED` permanecem na auditoria e fora da trilha
operacional. UUID nunca é exibido: o responsável é resolvido pelo
contrato de participantes; sem perfil, «Participante».

**Altura mínima da conversa (PROVEN).** `.cf-document-conversation`
recebeu `min-height: 520px` no desktop (faixa de design 480–560 do
§23.1) com a thread em `flex: 1` + `max-height: 560px` — rolagem
interna, composer ancorado no rodapé e estado vazio centralizado sem
colapsar a coluna. Em `max-width: 760px` a coluna empilha com
`max-height: 60vh` na thread — sem aprisionar a rolagem mobile.

**Avatar e nome oficiais (PROVEN — contrato mínimo aprovado na
implementação).** Owner do dado: Core (`core-api`). Dois canais
canônicos reutilizados, sem storage local de identidade:

- **Nomes:** `POST /me/directory/users/lookup` do Core, chamado pelo
  gateway da BFF com o **bearer do próprio usuário** (a autorização de
  leitura do diretório continua sendo a do caller; e-mails nunca
  trafegam — `mask_email` default). Mesmo padrão do proxy
  `viewer-photo` já existente na API.
- **Fotos:** `GET /integrations/person-profiles/{user_id}/photo` +
  `POST /integrations/person-profiles/lookup` via S2S
  (`CORE_API_INTEGRATIONS_SERVICE_TOKEN`) — mesmo contrato usado pelo
  `requests-api`/`CorePersonProfileAdapter`. Proxy read-through, sem
  persistência, `Cache-Control: private, max-age=300`, `nosniff`,
  allowlist `image/jpeg|png|webp`, limite 2 MB.

Rotas novas da `controllership-finance-api` (operation_ids
`lookup_closing_participants`, `get_closing_participant_avatar`):

- `POST /closing/participants/lookup` — `{ids: [...]}` (máx. 50,
  UUIDs inválidos filtrados) → `{items: [{user_id, display_name,
  has_photo}]}`; `display_name = null` para histórico/inativo.
- `GET /closing/participants/{user_id}/avatar` — blob da foto; 404
  sem foto; 503 sem configuração Core; 422 UUID inválido.
- Ambas exigem `controllership-finance.access` efetivo — nenhuma
  permission nova, nenhuma foto por convenção, nunca foto do viewer
  para terceiros.

**Frontend.** `participantsApi.ts` + hook `useParticipantProfiles`
(padrão `useParticipantAvatarUrls` de Minhas Solicitações: lookup em
lote → blob apenas quando `has_photo`, `createObjectURL` com revogação
por ciclo e no unmount, `AbortController` por troca de documento). A
thread U9 recebe `authorUserId`/`authorSrc`/`authorName` nativos do
`MessageThread` (`InitialsAvatar` interno = fallback legítimo); a
timeline usa `UnifiedAvatar kind="person"` no marcador. Ordem de nome:
diretório oficial → snapshot `author_name` do envio → «Participante».

**Evidências.** Testes: detalhe 23/23 (timeline com autor oficial, sem
UUID, downloads/mensagens fora, empty state, foto resolvida, perfil
indisponível); rotas de participantes 10/10 (positive/sibling/negative:
sem access 403, UUID inválido 422, sem foto 404, Core fora 503, lote
>50 rejeitado); gateway 10/10 (404/timeout/conteúdo inválido → `None`,
bearer do caller no diretório). Plugin 254/254, `tsc -b` e ESLint
limpos.

**Pendências honestas:** `has_photo=false` sem foto publicada continua
com iniciais (comportamento aprovado); homologação visual do PO no
navegador = PENDING. Audiência DRE para conversa/eventos permanece
`TARGET` — o endpoint de participantes **não** abre identidade para
fora do `access` da Controladoria.

### 23.6 Rework de segurança UX-009-RW01 — isolamento por documento e competência (REWORK, 26/10/2026)

Revisão arquitetural identificou que o contrato §23.5
(`POST /closing/participants/lookup` + `GET /closing/participants/
{user_id}/avatar`) exigia apenas `controllership-finance.access` e
aceitava ids arbitrários: um usuário do Portal poderia tentar resolver
nome/foto de pessoas sem demonstrar relação com documento autorizado —
superfície de enumeração de perfis. Correção cirúrgica, sem
redesenhar a UX e sem novas permissions.

**Contrato corrigido (contextual, fail-closed).** As rotas livres
foram substituídas por caminhos vinculados ao documento da competência
do path, no padrão U3/U4/U9:

- `POST /closing/competences/{period}/documents/{document_id}/
  participants/lookup` — `{ids: [...]}` (máx. 50) → devolve somente
  ids com vínculo canônico; demais são **omitidos** (ausência não
  confirma nem nega existência — sem enumeração).
- `GET /closing/competences/{period}/documents/{document_id}/
  participants/{user_id}/avatar` — participante sem vínculo recebe o
  mesmo 404 de recurso inexistente; `branch_scope` opcional segue o
  parâmetro das rotas documentais.
- operation_ids: `lookup_document_participants`,
  `get_document_participant_avatar`. Rotas antigas removidas — não há
  bypass.

**Cadeia de autorização (BFF, antes de qualquer chamada ao Core):**
`capability` (`access` efetivo via Keycloak/RBAC) **AND**
`resource_scope` (`ClosingDocumentService._document_in_scope` —
competência resolvida do `period` + `branch_scope`; cross-competence
e cross-scope = `DocumentNotFound` 404, existência nunca vaza)
**AND** `business_rule` (vínculo canônico do participante: autor de
mensagem U9, ator de evento U8 `entity_type=closing_document` ou
uploader do documento — `list_document_participant_ids` no
repository; `document_id` é PK global, a competência já foi validada
na resolução do documento).

**Vínculo como prova, não parâmetro.** O id do participante vindo do
frontend nunca prova participação — é apenas filtro sobre o conjunto
canônico derivado do banco. Participante válido no Core mas fora do
documento não é resolvido; foto fora do documento não é proxied.

**Frontend.** `participantsApi.ts`/`useParticipantProfiles` recebem
`{period, documentId}`; a chave do efeito inclui contexto + ids e o
estado resolvido é etiquetado com essa chave — perfis do contexto
anterior **nunca** aparecem após troca de documento ou competência
(sem nome/foto stale); `AbortController` + revogação de object URLs
preservados. Cache não usa `user_id` isolado como chave.

**Core permanece owner.** Diretório de nomes (bearer do caller) e
person-profile S2S (fotos) inalterados — sem storage local, sem
duplicação de cadastro, sem URL de avatar por convenção, sem token
S2S no navegador.

**Audiência.** Conversa/perfil permanecem `INTERNAL` — audiência DRE
segue `TARGET`. Nenhuma regra de negócio do fechamento foi alterada.


## 24. Relatórios e divergências — proposta de organização V0.1 (27/10/2026)

**Estado:** `DESIGN_PROPOSED / PENDING_PO_APPROVAL / NO_IMPLEMENTATION_GO`. Próxima página de trabalho, **terceira aba existente**, não quarta área. Preserva as escolhas aprovadas no §9.5 e §3 (DR-C2 resultado de negócio decidido), sem alegar disponibilidade de produtores R01–R15.

### Finalidade e hierarquia visual
O analista escolhe a referência mensal, consulta indicadores e relatórios produzidos pelos owners canônicos e encontra as **divergências comprovadas que exigem correção manual no TOTVS**, com totais/agrupamentos já calculados pelo backend. A UX deve ser limpa: situação/ação primeiro, detalhe sob demanda, PDF em área própria.

```text
[PagePath Início > Fechamento mensal > Relatórios e divergências]
[Competência YYYY-MM compartilhada] [Visão geral | Documentos e interações | Relatórios e divergências]
Relatórios e divergências                            [Atualizar dados]
[Resumo: Relatórios disponíveis | Divergências identificadas | Fontes sem consulta]
[ÁREA PRIORITÁRIA: Divergências encontradas / Fontes não verificadas]
  [Grupo de divergência: relatório, valor/quantidade real, descrição, prioridade]
    [Ver detalhes] → linhas/grupos dentro da própria aba
    [Como corrigir no TOTVS] → orientação comprovada (manual)
[RELATÓRIOS DISPONÍVEIS: cards por família de relatórios, status e última atualização]
  [Card: Baixas financeiras] [Card: Estoque] [demais somente com produtor canônico]
  [Selecionar relatório] → painel de resultado abaixo, sem sair da aba
[PAINEL CONTEXTUAL: totais calculados, grupos, origem, filtros/seleção, detalhes]
[PRÉVIA DO PDF: container preservado; PDF real só mediante produtor/contrato]
```

### Invariantes
- `R01–R15` na matriz de checklist = **classificação/entregáveis**, não quinze relatórios calculados automaticamente. Não converter documentos manuais em dados financeiros ou inventar totais.
- Baixas financeiras e consulta operacional de estoque já possuem endpoints period-keyed, mas não devem ser rotuladas como relatório oficial Protheus P7 sem homologação.
- Fonte indisponível / dado não processado / falta de reconciliação = `—` ou estado informativo, nunca divergências `0` comprovadas.
- Divergência de conciliação estoque segue `ENTRADAS_SAIDAS - P7 - H02`, paridade somente em R$0,00, quando três entradas comparáveis e válidas forem comprovadas. Causas e instruções de correção apenas com evidência de produtor/owner; nada de write ERP.
- Dentro da aba: expansão dos grupos, seleção de relatório, prévia PDF e navegação pelo PagePath; preservar mês, filtros, URL/F5/voltar. Rota legada continua até decisão de depreciação.
- Nenhum relatório operacional TOTVS é enviado automaticamente à DRE. A DRE, fase final, receberá apenas PDFs documentais designados e liberados por seu fluxo próprio.

### Componentes do kit — candidatos a verificar
`createDashboardPagePath`, `PageHero`, `SegmentToggle`, `InteractiveDataCard`, `SectionCard`, `StatusBadge`, `DataRecordCard` (catálogo), `EmptyState`, filtros e controles do plugin-ui, e componente oficial de detalhe progressivo/accordion, se existir. **Inventariar exports reais do `@delpi/plugin-ui` antes de implementar.** Evitar tabela R01–R15 como fluxo principal; preservar rastreabilidade num detalhe técnico de cobertura e fonte.

### Decisões visuais propostas para aprovação PO
A. Dar **prioridade às divergências e ações** acima do catálogo de relatórios; agrupá-las por relatório/fonte e permitir detalhe expansível.
B. Mostrar **cards por família de relatório**, não a matriz técnica R01–R15 como lista principal.
C. Selecionar um card abre resultado/detalhe **na mesma aba**, sem rota separada; conservar PDF no painel inferior.
D. Preservar a distinção visual entre `divergência comprovada` e `não foi possível consultar`, sem falso zero.
E. Manter PDF como prévia do relatório selecionado, quando houver geração homologada; caso contrário container com estado claro.

**Próximo passo:** o PO revisa e modifica/aprova a composição; após aprovação inventariar producers/consumers e RQ/AC, documentar V0.2 detalhada, só então preparar prompt incremental de implementação e CLARA/Help.


## 25. Relatórios e divergências — wireframe detalhado V0.2 (PO, 27/10/2026)

**Decisões PO aprovadas e congeladas na UX:** `prioridade=attention` (divergências/ações antes do catálogo); `catálogo=cards` (cartões por família); `detalhes=inline` (resultados e drilldown na própria aba); `PDF=inline` (prévia contextual no próprio workspace). As alternativas da seção 24 ficam SUPERSEDED apenas nesses quatro pontos. **Estado:** `PRODUCT_DESIGN_APPROVED` para as quatro escolhas; `DETAILED_WIREFRAME_TARGET / PENDING_FINAL_PO_VISUAL_APPROVAL`; `NO_RUNTIME_GO`. Não interpretar design como prova de produtores, contratos ou cálculos.

### 25.1 Wireframe da terceira aba (sem navegação para páginas técnicas)
```text
Início > Fechamento mensal > Relatórios e divergências
[Fechamento mensal | competência YYYY-MM | Atualizar consulta]
[Visão geral] [Documentos e interações] [Relatórios e divergências]

RELATÓRIOS E DIVERGÊNCIAS
[Indicadores: Divergências comprovadas | Relatórios disponíveis | Fontes não verificadas]
  (valores reais do produtor; não disponível = —, jamais zero presumido)

O QUE PRECISA DE ATENÇÃO                     [Atualizar dados]
  [Divergência real por relatório/fonte — valor e impacto]
      [Ver detalhes] abre grupos/linhas AQUI, com filtros e evidência
      [Como corrigir no TOTVS] expande procedimento comprovado, manual
  [Fonte indisponível] aviso separado, SEM inventar divergência
  [Sem divergências] só quando fontes/critério estiverem comprovadamente completos

RELATÓRIOS PARA ANÁLISE
  [CARD Baixas financeiras] [CARD Estoque e conciliação]
  [Demais cards somente com owner/produtor/contrato inventariado]
  Cada card: nome humano; descrição curta; status da consulta; atualização;
             origem/proveniência; ação "Consultar resultados"

RESULTADOS DO RELATÓRIO SELECIONADO
  [Título do relatório | período | fonte | atualização | filtros aplicáveis]
  [Totais calculados no backend | agrupamentos | divergências]
  [Grupos expansíveis → linhas/itens sob demanda | explicação comprovada]
  [Reconsultar dados] SEM write-back ERP

PRÉVIA DO PDF DO RELATÓRIO SELECIONADO
  [PDF inline se arquivo gerado e autorizado; otherwise empty state]
  [Baixar PDF se contrato existente; geração governada é gate futuro]
```

### 25.2 Comportamento por superfície
**Indicadores:** exibir apenas métricas com contrato semântico, escopo e denominador comprovados. `—` com ajuda quando não houver disponibilidade. Clique leva ao grupo dentro da aba, preservando referência, foco, filtro e URL. Não repetir três dashboards técnicos.

**Atenção:** separar visualmente `DIVERGENCE_CONFIRMED` de `SOURCE_UNAVAILABLE` e `CHECK_NOT_PERFORMED` como estados de apresentação, **não novos enums persistentes**. Exibir divergência e valor somente após cálculo/critério homologados; origem, período, data de extração e próxima ação. A causa só pode ser descrita como comprovada quando o owner fornece evidência; caso contrário dizer “A causa ainda não foi identificada”. Não marcar fonte indisponível como zero divergências.

**Catálogo cards:** famílias iniciais candidatas `Baixas financeiras` e `Estoque e conciliação`, pois há consultas operacionais period-keyed. Não apresentar R01–R15 como quinze relatórios prontos; cada fonte sem produtor homologado fica classificada como TO_INVENTORY e não é apresentada como cálculo oficial. Card selecionado recebe estado visual e revela os resultados **abaixo, sem rota separada**.

**Drilldown:** começar pelo total, depois grupos, depois linhas sob demanda; sempre no contexto da aba, sem conferência linha a linha como fluxo padrão. Ação “Como corrigir” oferece orientação de consulta/correção **manual** no TOTVS, sem alterar dados ERP pelo Portal. Reconsulta executa somente leitura autorizada.

**PDF inline:** manter contêiner no fim dos resultados; se PDF existir, prévia autenticada e download permitidos; se não houver produtor/arquivo, apresentar “A prévia do PDF ainda não está disponível para este relatório”. Não usar PDF documental anexado como se fosse relatório oficial gerado, nem enviar relatórios operacionais à DRE.

**Navegação/história:** competência pode ser apenas selecionada, sem fechamento aberto; leituras period-keyed existentes continuam acessíveis. Filtros, card selecionado e grupo expandido devem ser preservados conforme router/URL, refresh e navegação. A conclusão e envio do pacote continuam fora da aba de relatórios e não devem ser automatizados.

### 25.3 Componentes — mapa proposto, condicionado a inventário do export real
- PagePath / PageHero / SegmentToggle compartilhados: caminho e cabeçalho comum.
- `InteractiveDataCard` ou `MetricKpiCard` somente se métricas legítimas; `StatusBadge` para fonte/resultado; `SectionCard` para seções; `DataRecordCard` ou card correspondente para família.
- Controles de busca/filtro e Accordion/Disclosure compartilhados **após confirmar catálogo**; tabela de linhas apenas no detalhe expandido; `EmptyState` para fontes/relatório sem dados.
- Prévia PDF com `FilePreviewView`/`useFilePreviewLoader` somente mediante fonte binária/autorização real, evitando efeito de fetch repetitivo já corrigido na U4.
- Documentar o export, factory, consumidor e fallback escolhido no Doc 30 antes de implementação; mesmo padrão claro/escuro/mobile/foco/teclado/a11y.

### 25.4 AC de design e gates
1. Atenção vem antes do catálogo; divergência ≠ fonte indisponível.
2. Cards por família, sem tabela R01–R15 como navegação principal.
3. Resultados/totais/grupos/linhas acessíveis na mesma aba.
4. PDF inline com indisponibilidade honesta.
5. Competência/seleções/filtros preservados e sem quarta aba.
6. Resultados por BFF/owner canônico, sem cálculos financeiros em frontend.
7. Sem escrita ERP; correção manual com evidência/proveniência.
8. Não expor relatório TOTVS à audiência DRE.
9. Testes de casos completos/incompletos/erro, URL/F5, responsividade, temas, foco e Ajuda.
10. Atualizar CLARA **após** provas de runtime, distinguindo design aprovado de implementado.

**Dependências para execução:** inventário de producers/consumers dos endpoints period-keyed, homologação das famílias e valores, contrato/owner dos diagnósticos, associação PDF por relatório e estratégia de preview; security gates e RQ/AC antes de runtime. Próximo passo: PO valida wireframe V0.2; então prompt de inventário/implementação incremental.

### 25.5 Registro de execução — CF-PROC0072-REPORTS-UX-010 (27/10/2026)

Implementação V0.2 **executada** no HEAD do repositório, sobre os contratos canônicos existentes (nenhum endpoint novo, nenhuma permission nova, nenhum cálculo financeiro no navegador):

- **Estrutura:** `MonthlyReportsPanel` dentro da aba `?tab=reports` — indicadores → «O que precisa de atenção» → cartões por família → «Resultados» inline → cobertura R01–R15 (rastreabilidade) → slot de PDF. Três abas preservadas; o relatório selecionado vive na URL (`&report=settlements|stock`) com F5/back-forward.
- **Indicadores honestos:** «Divergências identificadas» conta somente divergências/inconsistências comprovadas pelos owners; mostra `—` quando alguma fonte que carrega divergência falhou (erro nunca é zero). «Relatórios disponíveis» conta famílias cuja consulta autorizada respondeu. «Fontes não verificadas» soma fonte indisponível + conferência não realizada.
- **Atenção (apresentação, não enums novos):** `divergence` (P3 `reported − expected` ≠ 0; quality flags de baixas), `source_unavailable` (P3 `source_state` ≠ AVAILABLE, erro de consulta, `source_missing`/`incomplete` do estoque) e `check_pending` (competência não aberta → conferência P3 não executada; itens pendentes da matriz R01–R15). Cada item traz origem, data da consulta, próxima ação e expansão inline com fatos; divergências dizem «A causa ainda não foi identificada» até existir evidência do owner — sem instrução TOTVS inventada e sem escrita no ERP.
- **Famílias iniciais com produtor canônico:** `Baixas financeiras` (`GET /closing/financial-settlements/summary` — grupos reais por lado/natureza/movimento com `officialTotals` e quality flags) e `Estoque e conciliação` (`GET /closing/stock-inventory` — status/totais/grupos por tipo e armazém + `GET /closing/competences/{period}/p3` — conciliação canônica ENTRADAS_SAIDAS−P7−H02 com `divergence` do backend).
- **Drilldown progressivo:** total → grupo → linhas. Grupo de baixas expande e carrega `GET /closing/financial-settlements` filtrado por `nature_code`/`movement_type`; estoque expande «Ver itens do snapshot» com paginação server-side. Nenhuma tabela extensa é o primeiro elemento.
- **Matriz R01–R15 subordinada:** tabela compacta de cobertura permanece na aba como rastreabilidade técnica; não é a navegação principal.
- **PDF:** slot contextual sempre presente — «A prévia do PDF ainda não está disponível para este relatório.» Nenhum produtor/contrato binário de PDF de relatório existe no HEAD (`TO_INVENTORY`); nenhum PDF fictício é gerado e nenhuma evidência anexada é exibida como relatório oficial.
- **Mês de referência sem abertura:** consultas period-keyed (baixas, estoque) funcionam sem competência aberta; P3/matriz 404 viram «Conferência não realizada», nunca erro genérico.
- **Não implementado / pendente:** PDF por relatório (sem produtor), famílias além das duas com contrato, drilldown por armazém dentro dos grupos de estoque (contrato suporta `warehouse`, registrado para incremento), correção TOTVS permanece manual (sem write-back). Paridade FINR190/MATR460 permanece `TEST_NOT_RUN` — consultas operacionais não são relatórios oficiais homologados. DRE não recebe relatórios operacionais.


## 26. Revisão PO — Relatórios e divergências V0.3: tabela e detalhe por relatório (27/10/2026)

**PRODUCT_APPROVED / DESIGN_TARGET / NO_IMPLEMENTATION_GO.** O PO homologou parcialmente a estrutura V0.2 com capturas reais, mas rejeitou a apresentação dos agrupamentos financeiros em linhas/cartões empilhados com títulos aglutinados e alterou a decisão anterior `details=inline`: **o detalhamento completo passa a abrir uma rota contextual própria do relatório**, com retorno preservando a análise e competência, não nova aba principal. Esta decisão específica **SUPERSEDES** o item 3 de §25 (detalhe integral inline); prioridade `attention`, catálogo `cards` e PDF contextual `inline` permanecem aprovados, sujeito a adequação do painel PDF na página do relatório.

### 26.1 Arquitetura de navegação
A terceira aba continua sendo o hub `?tab=reports`: indicadores, atenção real, cartões de famílias e resumo do relatório selecionado. A ação **Ver relatório / Ver detalhes** abre página contextual específica do relatório, preferindo **reutilizar as telas existentes de P7/Estoque e Baixas Financeiras** como base, após inventário de router, contracts, permissões, visual kit e links. Não transformar páginas técnicas legadas em nova quarta aba, não duplicar toda a implementação em outra página e não apagar legado antes de gate de depreciação.
- Exemplo conceitual: `/closing/monthly-closing/{YYYY-MM}/reports/{reportKey}` — rota precisa ser verificada e reconciliada com padrão efetivo; não congelar o path sem inventário.
- Breadcrumb `Início > Fechamento mensal > Relatórios e divergências > {Relatório}`.
- **Voltar para análises** restaura competência, aba, filtros, seleção e contexto anterior; URL/F5/back-forward e foco devem funcionar.

### 26.2 Tabela organizada no relatório
Ao selecionar categoria/grupo, apresentar **tabela de verdade**, com colunas explícitas, alinhamento consistente e cabeçalhos responsivos, usando o DataTable/DataTableSection real do `@delpi/plugin-ui`. Colunas por contrato: data, natureza, tipo de movimento, documento/título, filial, valor, situação, ação de detalhar; omitir colunas não disponíveis em vez de inventar. Totais financeiros à direita, PT-BR/BRL, milhares, limites de precisão e correspondência a valores do backend. Separar natureza/tipo por coluna — não concatenar textos como `VENDA DE PRODUTOS INDUSTR.Baixa de título`. Paginador/filtros server-side onde houver contrato; tabela acessível, mobile com estratégia adequada.

### 26.3 Revisão de densidade e componentes
Corrigir cartões de relatório que hoje exibem labels repetidas em caixa alta `RELATÓRIO / DESCRIÇÃO / SITUAÇÃO`, excesso de espaços e seções técnicas extensas; usar título, descrição compacta, estado real e CTA. Área `O que precisa de atenção` preserva fatos reais, mas prioriza legibilidade, agrupamento e expansão sob demanda. Matriz R01–R15 deve sair do fluxo visual principal ou ficar como detalhe técnico opcional/disclosure; não perder rastreabilidade contratual. Manter indicadores honestos (`0` só com verificação completa, ausência/error ≠ zero).

### 26.4 Fontes e análise dos ciclos 1/2 e vídeo
**TASK_DE_DISCOVERY obrigatória ANTES da expansão de relatórios**: recuperar de fontes canônicas dos Ciclos 1 e 2, do TÉO/Transformômetro (AS-IS) e da gravação de acompanhamento de Estoques e Custos (30/09/2026) a sequência real de análise, os arquivos oficiais, chaves, agrupamentos, divergências, causas comprovadas, correção TOTVS e responsáveis. As planilhas/PDFs do projeto são amostras/evidência de formato e confronto, **não fontes automáticas de contrato de produção**. Produzir matriz `relatório → necessidade da analista → fonte canônica → owner → consulta/SQL/API → cálculo validado → divergência → evidência → status → PDF`. Diferenciar `PROVEN/TO_INVENTORY/PLANNED/TARGET`; não alegar que vídeo e Ciclos 1/2 foram analisados nesta decisão, nem marcar paridade oficial sem teste.

### 26.5 Sequência obrigatória
1. Inventário READ-ONLY de rotas legadas P7/Baixas, componentes kit, contratos BFF, documentação Ciclos 1/2, AS-IS TÉO, vídeo e exemplos PDF; HEAD/status e owner/RQ/AC.
2. Wireframe detalhado da página do relatório e tabelas (colunas específicas por família) para aprovação PO, com mapa plugin-ui e navegação contextual.
3. Implementação do menor diff front-end e reuso de rotas/components autorizados, com testes de formato, tabela, filtros, drilldown, período, escopo, temas, mobile, keyboard, F5, retornos.
4. Integrar fontes reais e análises somente via contratos autorizados dos owners; qualquer contrato/migration/produção de PDF novo exige gate.
5. Depois de evidências: docs, Ajuda, CLARA, commit/SHA, deploy canônico local/prod, smoke autenticado e revisão GPT.

**Não confundir** mudança aprovada de UX com autorização implícita de migração, nova API ou write-back TOTVS. Página DRE continua por último.

### 26.6 Registro de implementação — UX-011 entregue (27/10/2026)

**IMPLEMENTED** na Central de Fechamento, supersede executado sobre §26.1–§26.3:

- **Rota contextual real:** `closing/monthly-closing/{YYYY-MM}/reports/{reportKey}` resolvida em `resolvePluginRoute` (`pluginRoutes.ts`), ao lado do deep link de documento — mesma view `monthly_closing`, sem quarta aba. `reportKey` ∈ `financial-settlements` | `stock-inventory`; chave desconhecida rende estado honesto, nunca página fabricada.
- **Hub V0.3 (`?tab=reports`):** indicadores honestos, «O que precisa de atenção» primeiro, cartões compactos por família via `CfInteractiveDataCard` (slot `children` do kit — sem rótulos RELATÓRIO/DESCRIÇÃO repetidos) e matriz R01–R15 em `<details>` técnico fora do fluxo principal. Resultados inline da V0.2 e o slot de PDF do hub foram removidos.
- **Reuso legado (D5):** `FinancialSettlementsPage` e `StockInventoryPage` ganharam prop `reportContext` — mesma máquina de filtros, tabela e paginação server-side; a competência vem travada da rota. Nenhuma duplicação de implementação.
- **Tabelas por colunas (D4):** agrupamentos de baixas em `DataTableSection` com colunas Natureza / Tipo de movimento / Baixas / Valor / Moeda / Ação — sem concatenação; estoque mantém Resumo por tipo e por armazém em tabelas do kit; «Ver registros» aplica `nature_code`/`movement_type` do grupo na tabela real.
- **Contexto preservado (D6):** retorno navega para `?tab=reports&report={família}` — competência, aba e última família analisada restaurados; F5/back-forward funcionam porque tudo vive na URL.
- **PDF (D7):** `ReportPdfSlot` compartilhado com estado honesto «ainda não está disponível para este relatório» em ambas as páginas — nenhum produtor/contrato binário homologado; evidências anexadas não são relatórios oficiais.
- **Fontes (D8/CP4):** nenhum endpoint, permission, migration ou cálculo financeiro novo — somente os contratos já homologados (`financial-settlements/summary`, `financial-settlements`, `stock-inventory`, `competences/{p}/p3`, `competences/{p}/reports`). Conciliação `ENTRADAS_SAIDAS − P7 − H02` renderiza somente `divergence` do backend.

Pendentes: paridade oficial FINR190/MATR460 segue `TEST_NOT_RUN`; produtor de PDF `TO_INVENTORY`; demais famílias R04–R15 `TO_INVENTORY/PLANNED` conforme matriz §24/doc 83; homologação visual PO da V0.3 `PENDING`.
