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

### 26.7 Registro de implementação — UX-011-RW01 entregue (28/10/2026)

**IMPLEMENTED** — rework de navegação/filtros após parecer `REWORK` do GPT Arquiteto: a preservação integral dos filtros não estava comprovada porque eles viviam somente em `useState` e o `backToReports` devolvia apenas `tab`+`report`. Visual V0.3 intacto; nenhum endpoint/contrato/cálculo alterado.

- **Problema/causa:** filtros de Baixas (`side`, datas, `nature`, `movement`, `sort`, `dir`, `page`) e de Estoque (`branch`, `scope`, `warehouse`, `page`) eram memória React — F5, deep link, voltar/avançar e reabertura perdiam todo o contexto; o retorno ao hub descartava os filtros da família.
- **Estratégia:** a URL passou a ser a fonte recuperável, no padrão canônico já usado pelo portal (`window.location.search` + `popstate`, mesmo mecanismo de `useConsoleSearchParams`). Owner local único: `reportQueryParams.ts` (`features/closing/`) — nomes estáveis `SETTLEMENT_PARAMS`/`STOCK_PARAMS`, `parse*` com allowlists/validação, `serialize*` e o hook `useReportQuerySync`.
- **Páginas contextuais:** cada uma serializa os campos brutos (não o valor em debounce) na query da própria rota com `replace: true` — sem poluir o histórico; a hidratação acontece na montagem e em `popstate` externo (o guard «serialize ≠ search» impede que o replace próprio sobrescreva um valor inválido em edição). O fingerprint esperado impede o reset de página ao restaurar campos debounced.
- **Hub/retorno:** `backToReports` carrega os params da família aberta para `?tab=reports&report={família}&{filtros}`; `openReport` só os repassa quando `report=` corresponde à família aberta — `page`/`nature` de Baixas nunca vazam para Estoque.
- **Validação/segurança:** enums com allowlist (`side`, `sort`, `dir`, `branch`, `scope`), `page` ≥ 1, datas `YYYY-MM-DD` com `start ≤ end` e **dentro da competência da rota** — par inválido ou de outro mês cai no intervalo da rota, nunca consulta outra competência. A competência de Estoque não é serializável: permanece travada na rota. Nenhum dado financeiro/token na URL; autorização continua na BFF.
- **Legado:** modo legado (`reportContext` ausente) não ativa a sincronização — comportamento idêntico ao anterior.
- **Testes:** +20 casos — helper 10 (defaults, round-trip, par fora da competência, enums/página inválidos, `pickFamilyParams` sem vazamento), Baixas 4 (F5/deep link restaura e consulta com os valores, datas de outro mês descartadas + URL normalizada, serialização ao editar, back/forward reidrata página), Estoque 4 (idem + filtro inválido → default + competência nunca serializada), página 3 (voltar preserva filtros no hub, reabertura repassa, família diferente abre limpa).


## 27. Incremento aprovado pelo PO — relatórios reais, conciliação e simplificação do frontend (27/10/2026)

**PRODUCT_APPROVED | DESIGN_TARGET | IMPLEMENTATION_GATE_PENDING.** O PO aprovou prosseguir com as melhorias de Relatórios e divergências e **conectar as fontes canônicas para obter dados e análises efetivos**, sem esconder indisponibilidades. Este registro não afirma que os contratos de P3 já estejam ligados às consultas period-keyed, nem autoriza criar uma fórmula ou fonte paralela.

### 27.1 Sintoma observado e hipóteses, sem diagnóstico presumido
Em setembro/2026, as capturas do PO mostram a consulta operacional `stock-inventory` disponível (SB9, 7.929 itens, 2 filiais, total histórico apresentado), enquanto a conciliação P3 acusa `ENTRADAS_SAIDAS`, `P7` e `H02` indisponíveis. **São fluxos/produtores distintos**: disponibilidade de SB9 não prova equivalência ao P7 oficial (MATR460), nem prova que evidência P3 foi registrada/validada. A causa pode envolver resolução de fontes, associação de competência, contrato de captura, execução, qualificação ou estado de reconciliação; investigar código+payload sanitizado+logs antes de decidir. `UNAVAILABLE` não é divergência comprovada; zero de divergências só após cobertura suficiente.

### 27.2 Melhorias de UX aprovadas para refinamento
1. **Atenção compacta e acionável:** agrupar situações por relatório/origem; evitar cards repetidos de R05/R03/R08 com `Ver detalhes` + `Abrir relatório` simultâneos. Ação principal contextual **Abrir relatório**; informação diagnóstica e ação específica dentro da página; expansão secundária apenas se necessária.
2. **Cabeçalho sem duplicação:** nas páginas contextuais P7 e Baixas, reduzir redundância de dois heroes grandes; manter um título do relatório, contexto da competência e breadcrumb/voltar.
3. **Qualidade dos dados clara:** distingir fonte indisponível, consulta operacional disponível, paridade oficial não homologada, conferência não realizada, evidência não registrada e divergência provada. Explicar `natureza não identificada`/filial faltante em Baixas, preservando valores reais e sem fabricar vínculo.
4. **Tabelas como padrão:** preservar DataTableSection do `@delpi/plugin-ui`, colunas alinhadas, formatação PT-BR, paginação e filtros da URL; não regredir para linhas/cartões com texto concatenado.
5. **Resultados e correção orientados à ação:** na página contextual indicar fonte, data de consulta/competência, valor comparável, diferença comprovada, causa apenas quando homologada e instrução para correção manual no TOTVS; sem escrita ERP.
6. **Matriz R01–R15** secundária em disclosure; PDF contextual somente com produtor homologado. Três abas e DRE por último.

### 27.3 Plano de reconciliação de fontes (preflight READ-ONLY)
- Revalidar HEAD/git status, instruções oficiais, .cursor aplicável, owners, RQ/AC e gates, Plano 113, doc 112, doc 83 (crosswalk Ciclo 2), registros Ciclo 1/2, TÉO (AS-IS) e vídeo de Estoques/Custos 30/09/2026. Buscar evidência de cada alegação; não deduzir conteúdo do vídeo sem inspeção.
- Traçar **BFF P3**: `GET /closing/competences/{period}/p3`, estado/registro de cada domínio `ENTRADAS_SAIDAS/P7/H02`, producer, armazenamento, snapshot, cutoff, critérios de disponibilidade, autor, data, bloqueios e API de captura. Traçar separadamente `GET /closing/stock-inventory?period` (SB9) e consultas de baixas SE5. Localizar produtor canônico de P7 oficial e H02, se houver; search miss != ausência.
- Testar somente leitura com perfil autorizado e payload/log **sanitizado** de 2026-09: disponibilidade, origem, competência, snapshot, mensagens de erro, proveniência, critérios de aceite. Nenhum POST/SQL write para simular dados.
- Matriz obrigatória por R01–R15: **necessidade da analista → relatório/arquivo → operação atual → owner → produtor/API/SQL → campos e total → comparabilidade → divergência/correção → documento de evidência → status**. Registrar a paridade oficial FINR190/MATR460 como `TEST_NOT_RUN` até confronto real.

### 27.4 Checkpoints e gates
**CP1 INVENTORY READ-ONLY** traçado de producers/consumers, gap de P3, dados reais autorizados, Ciclos 1/2/vídeo, caminhos existentes de integração e componentes plugin-ui. Entrega: diagnóstico causal com evidência e matriz de dependências.
**CP2 DESIGN/CONTRACT** definir estados UX, tabelas e mínima evolução de contrato necessária; separar integrações já autorizadas de novas. Em caso de owner, cálculo, persistência, integração, permissão, contrato breaking ou PDF novos: `DECISION_REQUIRED`, não implementar sem gate.
**CP3 FRONTEND** implementar apenas refinamentos de apresentação aprovados e integrações sustentadas por contrato, mantendo URL/F5/back-forward, temas, mobile, teclado, BFF-only e fail-closed.
**CP4 BACKEND/INTEGRATION** após gate, integrar fontes via owner canônico, sem inferir equivalência SB9=P7, sem calcular divergência no browser, sem sobrescrever evidência histórica.
**CP5 VERIFY** testes positivos/sibling/negativos, competência 2026-09 e outra, source missing != zero, proveniência, paridade quando aplicável, smoke autenticado; build e deploy local primeiro; produção somente pelo operador/gates.
**CP6 DOCS/CLARA** atualizar docs 23/30/94/112/113/README, Ajuda; republicar corpus CLARA apenas com afirmações de runtime comprovadas e testar retrieval.

**Ação imediata:** iniciar CP1 read-only; não publicar alterações de serviço ou mexer em registros financeiros antes do diagnóstico e gate. Não excluir legado; página DRE segue última fase.


## 28. Priorização PO — pausa de integração dos relatórios e próxima frente de UX documental (27/10/2026)

**DECISÃO DE SEQUENCIAMENTO — PRODUCT_APPROVED / PLANNED.** A investigação e conexão das fontes reais dos relatórios, conciliadores P3, P7 oficial e H02, documentada em §27, **fica expressamente para uma próxima rodada**. Não disparar CP1 nem alteração de BFF/API/ERP neste momento; preservar a documentação e os critérios de evidência existentes. Isto não cancela §27.

**Frente atual: DEFINIR O VISUAL DA PÁGINA DE CADASTRO/CONFIGURAÇÃO DE DOCUMENTOS.** Retomar o requisito aprovado no início deste plano: gerir o catálogo mestre dos tipos de documentos/PDFs exigidos para encaminhamento à Contabilidade/DRE em **página administrativa dedicada**, substituindo o modal de criação/edição; não confundir com o upload de arquivo na aba operacional Documentos e interações. Acessível somente a `controllership-finance.manage` ou autoridade efetiva equivalente do Super Admin, com AuthZ final na BFF.

**Invariantes já aprovados para a proposta visual:**
- Listagem de documentos configurados; adicionar e editar em páginas completas, com breadcrumb e retorno à lista preservando filtros e foco.
- Nome/descrição/finalidade, exigência ou destino DRE, vigência inicial e final, casos excepcionais, status e histórico/proveniência conforme contratos efetivos. Não inventar campos como se já estivessem persistidos.
- Nova exigência vale a partir da referência definida; exclusão/retirada prospectiva não altera snapshot histórico do fechamento encerrado; não exigir cadastro mestre para abrir o mês.
- UX PT-BR simples, desktop/mobile, claro/escuro, teclado/foco, Ajuda sincronizada, `@delpi/plugin-ui` first e reutilização do padrão de Administração de outros Portais.
- Não adicionar quarta aba operacional; não criar permission nova; não remover modal/legado antes de inventário e gate de implementação.

**Próximo checkpoint:** inventário READ-ONLY do fluxo administrativo atual, modal e rotas, catálogo/schema/contracts, permissões efetivas, componentes e páginas equivalentes do plugin-ui; desenhar listagem + formulário de criação/edição para aprovação visual do PO. Só depois preparar implementação page-by-page. A atualização de conhecimento da CLARA deverá refletir esta priorização documental na próxima ingestão autorizada; não declarar o visual como implementado.

### 28.1 Registro de implementação — UX-012 catálogo de documentos (28/10/2026)

**IMPLEMENTADO — menor diff frontend autorizado; zero contrato/persistência nova.** O catálogo mestre «Documentos do fechamento» foi implementado sobre o modelo de checklist versionado existente (CP3 encerrou sem `DECISION_REQUIRED`):

- **Rotas:** `closing/admin/documents` (listagem), `closing/admin/documents/new` e `closing/admin/documents/{itemKey}` (páginas completas — nenhum modal para cadastro/edição), view `documents_admin`, entrada de hub restrita a `manage`.
- **Listagem derivada (`documentCatalog.ts`):** cada `item_key` vira uma linha com janelas de vigência calculadas da timeline de versões publicadas (`effective_from_period` como fronteira; versão vencedora por intervalo) — vigência inicial/final, situação vigente/futuro/encerrado, exigência e destino. Item presente apenas em DRAFT/REVIEW aparece como «futuro» + pendente.
- **Gravação por orquestração do contrato atômico:** salvar cria DRAFT clonando a configuração publicada mais recente, aplica o delta do documento (inserção ou edição por `item_key`), submete a revisão e publica com `effective_from_period` escolhido — sempre prospectivo, snapshots congelados. «Exigido até» publica segunda versão de remoção no período seguinte; «Encerrar exigência» publica somente a remoção. `draft_already_open` vira banner honesto com orientação (não sobrescreve trabalho alheio); encerrar o último item do checklist é recusado (backend exige ≥1 item).
- **Navegação:** filtros da listagem (`q`, `status`, `dest`) serializados na URL pelo mesmo `useReportQuerySync` do RW01; a página de formulário carrega a query da listagem e devolve no retorno — F5/deep link/voltar-avançar restauram contexto.
- **Segurança:** todas as operações nos endpoints `/admin/checklist-templates*` (MANAGE na BFF); nenhuma permissão nova; 403 → banner seguro.
- **Não implementado nesta rodada:** página exclusiva de documentos DRE/contabilidade recebidos (gate separado), catálogo de tipo-documento com vigência start/end nativa (não existe contrato — a vigência permanece derivada de versões), depreciação do modal legado (mantido até autorização expressa), e a investigação de fontes reais dos relatórios (§27 — próxima rodada).

### 28.2 Registro de rework — UX-012-RW01 integridade de vigências e publicação governada (28/10/2026)

**Parecer do GPT Arquiteto:** REWORK (integridade funcional). Classificação CP3: **B — contrato parcialmente suficiente**: a composição das versões e os cenários de falha foram corrigidos no frontend; a atomicidade multi-versão e o encerramento da última exigência exigem evolução da BFF → `DECISION_REQUIRED-1` e `DECISION_REQUIRED-2` abaixo.

**Inventário de garantias (evidência — `closing_checklist_repository.py`):**

- `resolve_published_version(period)`: `status=PUBLISHED AND effective_from <= period ORDER BY effective_from DESC, version DESC` — a vigente NÃO é a versão de maior número; em empate de `effective_from` vence a versão maior.
- `create_draft_version` clona os itens da versão de maior NÚMERO (que pode ser REVIEW ou INACTIVE) — inofensivo porque `update_draft_items` substitui o conjunto inteiro; a base semântica correta continua sendo o vencedor do boundary.
- `publish_version` aceita qualquer `effective_from` YYYY-MM (sem checagem de futuro nem de ordem) e exige ≥1 item — versões podem ser publicadas fora de ordem cronológica com resolução determinística.
- Índice parcial garante um único DRAFT por template → `draft_already_open` em corrida; `update_draft_items` é transacional com OCC `revision` (`stale_revision`); eventos `DRAFT_CREATED`/`DRAFT_UPDATED`/`VERSION_PUBLISHED` registram `actor_subject` (UUID do Core — não exposto ao MFE).
- `open_competence`: sem versão vigente, a competência abre com `template_version_id NULL` e snapshot vazio — abertura legítima sem exigências (§10/DR-C1); snapshots de competências abertas/encerradas são cópias congeladas, nunca reescritas por publicações.

**Defeitos corrigidos (menor diff — `documentCatalog.ts`):**

1. **Base incorreta (RW01-B):** a orquestração UX-012 usava a versão publicada de maior número como base — incorreto quando a última versão é uma remoção futura ou de competência posterior. Agora a base de cada publicação é a versão VENCEDORA no boundary (`winnerAt`, espelhando `eff DESC, version DESC`).
2. **Exigência morria no boundary seguinte (RW01-B):** versões são conjuntos absolutos — inserir/editar um item no meio da timeline sem propagá-lo aos boundaries futuros encerrava a exigência silenciosamente no próximo boundary já publicado. `planDocumentSave` propaga o item a todo boundary em `[from, until]` e publica a remoção em `until+1` calculada contra o estado PÓS-inserção.
3. **Desempate de vigência (RW01-C):** a derivação ordenava apenas por `effective_from`; corrigida para `(effective_from, version)` — mesmo desempate do backend.
4. **Publicação não recuperável (RW01-A):** falha intermediária deixava DRAFT/REVIEW órfão e travava o retry em `draft_already_open`. `ensurePublishedVersion` retoma versão aberta cujos itens sejam IGUAIS ao alvo (igualdade de conteúdo — não depende de identidade do ator); versão aberta com conteúdo divergente vira `catalog_draft_conflict` honesto, nunca sobrescrevendo trabalho de outro administrador.
5. **Sucesso parcial silencioso:** cada passo é idempotente (configuração já vigente no boundary → skip); falha intermediária sempre propaga erro — nunca informa sucesso integral; retry converge sem duplicar versões.

**Matriz de cenários coberta (`documentCatalog.test.ts`, 24 testes):** inclusão futura; propagação multi-boundary (A/B/C com janelas sobrepostas); término em `until+1`; edição substituindo configuração futura; janela descontínua/reativação; empate de `effective_from` (maior versão vence); publicações fora de ordem cronológica; no-op idempotente; retry sem duplicar; REVIEW igual retomado; DRAFT divergente → conflito; falha intermediária → erro; último item → recusa explícita; remoção já vigente → no-op.

**DECISION_REQUIRED-1 — operação transacional de configuração documental.** Problema: "início + término" e a propagação a boundaries futuros são N publicações independentes — o contrato não oferece transação multi-versão; falha intermediária pode deixar a JANELA parcialmente propagada (cada versão individualmente consistente, retry converge). Evidência: ciclo DRAFT→update→REVIEW→PUBLISH por boundary em `ensurePublishedVersion`. Owner: `controllership-finance-api` (rotas/serviço de checklist admin). Contrato atual: `/admin/checklist-templates*` atômico por versão. Alternativas: (a) endpoint único `POST /admin/checklist-templates/{id}/document-config` recebendo `{item, effective_from, effective_until}` e gerando as versões em UMA transação server-side — recomendado; (b) manter orquestração idempotente do MFE (estado atual — aceitável operacionalmente, não elimina janela parcial transitória); (c) saga/compensação — descartada (complexidade sem ganho). Impacto: contrato novo aditivo, sem migration; rollback = remover chamada. Segurança: mesma capability MANAGE; auditoria já cobre as versões geradas.

**DECISION_REQUIRED-2 — checklist vazio / última exigência.** Problema: PO aprovou fechamento sem documentos, e abertura sem qualquer versão publicada já produz snapshot vazio (PROVEN); porém ENCERRAR a última exigência de um template já publicado não é representável — `publish` exige ≥1 item e `inactivate` não zera (versões anteriores continuam vencendo). Hoje a UI recusa com `catalog_last_item_end`. Conflito com o TARGET aprovado. Alternativas: (a) permitir publicação de versão com 0 itens + `resolve_published_version` retornando checklist vazio — simples, mas semântica "sem exigências" precisa distinguir "sem template" de "template vazio"; (b) flag `requirements_disabled` no template publicável prospectivamente — recomendado (preserva distinção sem checklist/ checklist vazio); (c) documento-sentinela — descartado (dado fictício). Owner: contrato/persistência do checklist BFF; possível migration (coluna ou valor de status). Gate de aprovação pendente — não implementado.

**Concorrência entre administradores:** serialização parcial pelo índice único de DRAFT (segundo admin recebe `draft_already_open`); OCC `revision` protege edição do rascunho; o plano rebusca versões frescas no início de cada save — a janela residual de corrida (publicação alheia entre fetch e publish) resulta apenas em versão adicional na timeline, nunca em exigência reescrita, pois versões publicadas são imutáveis.

### 28.3 Gate documental DR-1/DR-2 — GATE-013 (28/10/2026, READ-ONLY)

**PROPOSTA — nenhum runtime alterado.** O gate produziu o documento 114
(`114-contrato-proposto-document-config-dr1-dr2-gate013.md`) com:

- **Inventário de consumers:** `resolve_published_version` é consumido
  APENAS por `open_competence`; todo runtime (P2/P5/validações/pacotes/
  CLARA) lê o snapshot `competence_checklist_item` — mudanças de template
  nunca reescrevem competência aberta.
- **DR-1 (aprovado conceitualmente):** `PUT /admin/checklist-templates/
  {id}/documents/{item_key}/requirement` — uma transação com `FOR UPDATE`
  que publica todas as versões do plano de vigência (propagação a
  boundaries + remoção em until+1), idempotente (`no_changes`), com OCC
  `base_version`, auditoria por versão + evento resumo e `422
  retroactive_effective_period`.
- **DR-2 (sem decisão PO):** comparativo A (versão publicada com 0 itens —
  zero migration, distinção preservada por `template_version_id` NOT NULL)
  vs B (flag `requirements_disabled` — invasiva). Recomendação técnica:
  **Alternativa A**, com `allow_empty` explícito para evitar publicação
  vazia acidental.
- **Próximo gate:** revisão arquitetural + decisão PO de DR-2 →
  autorização de implementação.

### 28.4 Registro — GATE-014 fechamento contratual DR-1/DR-2 (28/10/2026, READ-ONLY)

**PROPOSTA consolidada no doc 114 §8 — nenhum runtime alterado.**

- **Writers/locks:** matriz completa em doc 114 §8.1; `SELECT FOR UPDATE`
  no template sozinho não basta — os writers legados de
  publicação/inativação passam a adquirir o mesmo lock (mudança interna,
  sem contrato novo).
- **REVIEW:** estágio de conferência aprovado em V010, SEM segregação de
  funções (mesmo MANAGE submete e publica; devolução exige motivo).
  Recomendada alternativa A: transição DRAFT→REVIEW→PUBLISHED auditada
  dentro da transação única — trilha idêntica ao fluxo manual.
- **Idempotência:** header `Idempotency-Key` obrigatório + tabela
  `document_requirement_operation` (UNIQUE template_id+key, request_hash,
  result) — padrão canônico V004; mesma chave+payload divergente → 409
  `idempotency_conflict`; replay → resultado armazenado.
- **OCC:** `base_version` = MAX(version) → 409 `stale_revision`.
- **Competências abertas:** recomendado rejeitar janela que intersecte
  competência aberta (`422 window_covers_open_competence`); corretivo
  permanece o item excepcional por competência — contratos não misturados.
- **DR-2:** alternativa A (versão publicada com 0 itens) provada
  compatível com todos os consumers de snapshot (V015 já produz snapshot
  vazio idêntico); proteção `allow_empty` explícito; distinção
  sem-template (NULL) vs checklist-vazio preservada na auditoria.
- **Decisões pendentes D1–D5** no doc 114 §8.8.

### 28.5 Registro de implementação — GATE-015 comando transacional DR-1/DR-2 (28/10/2026, PROVEN)

Contrato §8.6 do doc 114 implementado sob D1–D5 (§9). **Runtime alterado e
verificado localmente; produção não deployada** (gate separado pendente).

- **Endpoint:** `PUT /admin/checklist-templates/{id}/documents/{key}/requirement`
  — um comando aplica cadastro, edição prospectiva, término, encerramento do
  último documento (`allow_empty`), reativação e publicação de checklist
  vazio, ou nada. O MFE deixou de orquestrar DRAFT→REVIEW→PUBLISHED por
  boundary (RW01) e passou a emitir chamada única com `base_version` +
  `Idempotency-Key`.
- **Migration V017** (`document_requirement_operation`): idempotência por
  chave + request_hash, resultado persistido na mesma transação das versões.
- **Serialização:** lock FOR UPDATE no template compartilhado pelo comando
  novo e pelos writers legados (`publish_version`, `inactivate_version`,
  `create_draft_version`, `open_competence` — este resolve a versão dentro
  da transação após travar os templates; corrida publicação×abertura coberta
  por D3).
- **Governança:** REVIEW auditado por versão
  (`DRAFT_CREATED→SUBMITTED→PUBLISHED`) + `DOCUMENT_CONFIG_APPLIED`;
  autorização MANAGE backend fail-closed; `stale_revision`/`idempotency_conflict`/
  `busy` → 409; `window_covers_open_competence`/`empty_resulting_checklist`/
  `retroactive_effective_period` → 422.
- **Evidências:** backend 689 testes PG verde; MFE 337 testes; smoke
  autenticado local com ciclo completo + auditoria conferida. Detalhe no
  doc 114 §10; ACs no ledger 23.
- **Não realizado:** deploy produtivo (requer gate CP10 próprio).

### 28.6 Registro de deploy — GATE-016 produção (28/10/2026)

- **Correção:** guarda D3 (`window_covers_open_competence`) estendida aos
  writers legados `publish_version`/`inactivate_version` — commit
  `bc335e7f7f` (backend 692 testes verde).
- **Deploy canônico:** pull ff-only em `srv-api` + `up-prod-sequential.sh
  --build controllership-finance-api controllership-finance`; V017 aplicada
  na subida; API healthy; MFE bundle novo confirmado.
- **Smoke prod autenticado não destrutivo:** 401 sem token, 403 sem
  permissão CF, 200 com MANAGE (`admin/checklist-templates`, versions).
  Escrita prod: TEST_NOT_RUN — reservada ao PO.
- **Pendência material:** draft v1 (53 itens reais) aberto em produção
  bloqueia o comando documental via `catalog_draft_conflict` até publicação
  prospectiva (`effective_from ≥ 2026-10`; `2026-09` aberta rejeita por D3).
  Resolução pela UI pelo PO. Detalhe no doc 114 §11.

### 28.7 GATE-017 — inventário do rascunho v1 (28/10/2026)

- Rascunho v1 (53 itens CK-E/F) = **seed V002** de inicialização — PROVEN
  por migration + zero eventos de auditoria + nunca modificado.
- Zero dependências operacionais (0 snapshots, 0 refs de competência,
  única versão do catálogo). Elegível para descarte **exceto** por não
  existir mecanismo oficial.
- `DECISION_REQUIRED — descarte governado de versão não publicada`:
  proposta `DELETE …/versions/{version}` (DRAFT-only, OCC, audit
  VERSION_DISCARDED) registrada no doc 114 §12.3. Execução aguarda
  decisão do PO.

### 28.8 GATE-017 — encerramento executado (28/10/2026)

- PO autorizou a evolução: `DELETE …/versions/{v}` DRAFT-only
  (`df43536acd`; backend 704 testes, MFE com «Descartar»).
- Descarte prod realizado via endpoint: `VERSION_DISCARDED` auditado;
  catálogo vazio (0 versões); competência 2026-09 intacta.
- Fluxo documental desbloqueado — primeiro cadastro real pelo PO.


## 28.9 UX-013 — Refinamento visual transversal do cadastro documental (solicitação PO, 28/10/2026)

**Estado: PLANNED / DESIGN FIRST — nenhuma mudança runtime neste registro.** Evidência: capturas autenticadas do PO em produção nas telas Início, Administração do checklist, cadastro, listagem, edição e modal de eventos/auditoria após primeiro cadastro manual (Relatório P7 bloco H; v1 publicada vigente desde 2026-11). O objetivo é evoluir o acabamento e a consistência visual, **não alterar a publicação, vigência, item_key, snapshot, permissões ou contratos**. O primeiro cadastro manual aparece nas capturas; não confundir screenshot com prova de todos os cenários de backend.

**Problemas vistos nas capturas (OBSERVED, sem inferir API):**
1. Inputs, textareas, selects e month-picker do formulário parecem controles nativos/estilização local, sem assinatura visual unificada do kit; selects abrem menu nativo. Inspecionar exports reais do **Blueprint UI / @delpi/plugin-ui** (nomenclatura do PO; kit técnico vigente é @delpi/plugin-ui) e utilizar apenas componentes homologados, com labels, help, disabled/error, foco e teclado.
2. Cards extensos Identificação/Exigência/Vigência e Situação atual apresentam separação vertical insuficiente; o formulário é excessivamente largo e cada field ocupa uma linha em desktop. Melhorar spacing/gap interno e entre cards, grid responsivo de campos de comprimento adequado e largura legível, sem criar layout kit paralelo.
3. Ações Salvar/Cancelar, Adicionar documento, Versões e auditoria, Criar versão rascunho e ações de tabela têm hierarquia visual fraca. Usar ActionButton/ícones do kit com CTA primário evidente, secundárias/ghost e danger somente para ações destrutivas; estados loading/disabled/focus e feedback.
4. Auditoria usa diálogo/lista de eventos pouco diferenciados. Inventariar **componente Media / media object, timeline, Activity/Interaction** efetivamente exportado pelo kit antes de escolher. Reutilizar o componente disponível mais apropriado para ícone/autor/data/evento e cronologia. Se não existir, registrar gap no reuse map e DECISION_REQUIRED para criação/expansão do kit — proibido componente paralelo inventado no Portal.
5. Cards da home Início e blocos administrativos carecem de diferenciação/ícones; verificar PageHero, SectionCard, InteractiveDataCard, EmptyState, IconButton, Tooltip/Help, StatusBadge disponíveis. Refinar somente páginas desta jornada para evitar redesign transversal sem gate.
6. Breadcrumbs e títulos de criar/editar devem explicitar hierarquia e ser consistentes com o chrome dos outros Portais; evitar header duplicado. Listagem deve melhorar densidade, estados vazios, badge 'Futuro', ações por linha e feedback de edição, sem prometer funcionalidades inexistentes.
7. Preservar tema claro/escuro usando tokens do kit, contraste WCAG, hover/focus visível, tab-order, screen-reader labels, mobile/tablet/desktop e zoom; sem cores hardcoded ou CSS exclusivo divergente.

**Escopo:** `DocumentsAdminPage.tsx`, `DocumentConfigFormPage.tsx`, `ChecklistAdminPage.tsx`, modal eventos, entradas contextuais na home, CSS local estritamente necessário, `helpTooltips.ts`, testes. Manter as rotas existentes e os três tabs do fechamento; deep routes administrativas não criam aba.

**Gates:** UX-013-CP1 inventariar exports e consumidores de Blueprint UI/@delpi/plugin-ui + plano visual comparativo screenshots; CP2 wireframe/mapa campo→componente real + revisão docs 112/30, selecionar melhorias sem novos contratos; CP3 implementar page-by-page com menor diff após gate transversal de UI; CP4 testes RTL/Vitest, lint, typecheck, build, keyboard/a11y, mobile/dark/light, snapshots comparativos; CP5 deploy local e homologação; CP6 produção somente com autorização específica e smoke autenticado, Help e docs sincronizados. Sem mudanças BFF/schema/migrations/permissões.

**RQ/AC iniciais:**
- RQ-UX013-01 kit-first: controles de entrada (incl. selects, textarea, mês) e ícones usam export real do @delpi/plugin-ui, sem duplicação; ausência vira inventário, não invenção.
- RQ-UX013-02 spacing: cards separados visivelmente, grids responsivos legíveis e alinhamento adequado; mobile sem overflow.
- RQ-UX013-03 ações: CTA primário destacado, variantes corretas, feedback de erro/loading e confirmação danger governada.
- RQ-UX013-04 histórico/eventos: representação visual cronológica com componente de media/interação/timeline **se comprovadamente existir no kit**; autor, tipo, data e versão acessíveis, sem nova fonte de dados.
- RQ-UX013-05 listagem/home: estados e ícones consistentes, affordance e navegação preservadas, filtros URL/F5 e auditoria intactos.
- RQ-UX013-06 regressão: sem alteração de request/response nem da lógica DR1/DR2/D3/D4/D5; MANAGE backend, snapshots, vigências e idempotência preservados.
- RQ-UX013-07 DoD: claro/escuro, teclado, foco, leitor de tela, 320px→desktop, zoom 200%, Ajuda e comparação visual com as capturas.

**Ordem recomendada:** 1) formulário cadastro/edição; 2) listagem; 3) Administração do checklist + eventos; 4) home/atalhos; revisão visual PO a cada página. Não incorporar integração dos relatórios do §27 nesta rodada.

**Execução (28/10/2026):** todos os controles de entrada migraram para exports reais do kit via adaptador `cf` — `CfTextField`/`CfTextAreaField`/`CfSelectField`/`CfDateField` (novos bindings em `controllershipFinanceUi.ts`) e `CfTimeline` para eventos/histórico com tons semânticos; grid responsivo `cf-form-grid` em Exigência/Vigência/diálogo de item; CTA primário (`variant="primary"`) em Salvar/Adicionar documento/Criar versão rascunho; gatilhos destrutivos com `cf-action-btn--danger` (ghost + cor semântica); `VERSION_DISCARDED` rotulado e badge `DISCARDED` mapeado. Evidências: `tsc` ✓, eslint escopo ✓, 337 testes ✓, `vite build` ✓, screenshots autenticados locais (claro/escuro/mobile, overflow 0). Zero alteração de BFF/contrato/dados. ~~Produção: aguardando autorização específica (CP6).~~

**Deploy produção (28/10/2026, gate UX013-PROD-014):** MFE reconstruído pelo fluxo canônico (`git pull` → `up-prod-sequential.sh --build controllership-finance`) no SHA `1b59fdc895`; bundle `App-B5Ynp8Kk.js` servido via gateway (remoteEntry 200, BFF healthy, zero migrations/BFF). Smoke autenticado não destrutivo com identidade dedicada `devin-smoke-g16` (grant temporário revogado; usuário desabilitado após o smoke): listagem com o documento real do PO (Relatório P7 bloco H, Futuro 11/2026), formulário Novo documento com campos do kit em grid, SelectControl abre por mouse e teclado (Escape fecha, foco retorna), modal de eventos renderiza `CfTimeline` com tons semânticos sobre os eventos reais da v1, edição abre preenchida com histórico. Único 404 observado: `viewer-photo` pré-existente e não relacionado. Homologação visual final pelo PO: pendente.


## 28.10 UX-013-RW01 — Espaçamento e ritmo visual do catálogo (28/10/2026)

**PLANNED/TARGET — evidência: screenshots PO de produção pós UX013-PROD-014.** Não é mudança de runtime. O reuso dos controles do kit foi aceito tecnicamente, mas a composição ainda apresenta cards encostados, ação do cabeçalho colada ao subtítulo/lista de filtros, barras de ações próximas de cards adjacentes e vários campos de edição com densidade desigual. O objetivo é um passe de **spacing/visual rhythm** que não altere contrato, dados, ações ou lógica.

**Evidências visíveis e alvo:** (a) ChecklistAdmin: container principal, ações do topo e card Versões; separação entre card Versões e card Itens, inclusive quando tabela expande; (b) DocumentsAdmin: título/subtítulo → CTA → filtros → tabela precisam de respiros consistentes; (c) DocumentConfigForm: Situação atual → Identificação → Exigência → Vigência → ações → Histórico; seções não devem tocar, e labels devem manter distância clara do controle; (d) botões Salvar/Cancelar/Encerrar não encostam na seção seguinte; botões de ação têm gap consistente; (e) modal Timeline tem padding e ritmo entre eventos, sem perder verticalidade e foco.

**Gate CP1:** comparar DOM, CSS local e factories/layout tokens reais de `@delpi/plugin-ui`; mapear qual componente gerencia espaçamento (SectionCard, layout wrapper, forms, ActionButton, DataTableSection); diagnosticar se margin collapse, ausência de gap no pai ou estilos de kit causam aproximação. Proibido sobrescrever CSS global por seletor amplo; preferir gap de container e tokens de design system. 

**Gate CP2:** wireframe/spacing matrix: distância pequena dentro de grupos e entre label/control, média entre grupos de campos e botões, maior entre cards/seções; valores concretos somente após conferir tokens do kit. Manter leitura compacta, sem aumentar desnecessariamente altura da página. 

**Gate CP3:** minimal frontend diff page-by-page: (1) checklist admin; (2) listagem; (3) criação/edição; (4) timeline. Tokens e componentes do kit primeiro, CSS local escopado apenas para gaps não cobertos. Não alterar BFF, migrations, permissions ou estados. 

**RQ/AC:** UX013-RW01-01 separação visível entre cards em todas as telas; -02 hierarquia entre título/subtítulo/CTAs/filtros/grid; -03 espaço consistente entre labels, controles, linhas e ações; -04 timeline legível; -05 responsivo 320/390/768/desktop, claro/escuro/zoom 200%, sem overflow; -06 regressão zero no fluxo MANAGE, filtros URL, edição, histórico, botões e formulários; -07 evidência screenshot antes/depois, testes, lint, typecheck e build. Local primeiro, produção apenas com autorização de deploy especifica.

**Execução (28/10/2026, UX-013-RW01 — PROVEN/deploy local):** causa raiz `cf-checklist-page`/`__content`/`cf-closing-layout` sem nenhuma regra CSS (filhos colados); `__body` do card do kit é `min-width:0` sem gap; `table-section` tem `margin-bottom` sem `margin-top`. Correção por layout de página com tokens `--cf-*` existentes (escala 8px lead → 16px em card → 24px entre blocos): `.cf-checklist-page__content` flex-column `gap: var(--cf-section-gap)`; `.cf-lead-stack` (título+subtítulo, 8px) e `.cf-card-stack` (ações→tabela em card, 16px) como wrappers próprios — zero CSS de internals do kit; `margin-bottom:0` em `.cf-table-section` dentro de `__content` (margem própria somava ao gap). JSX mínimo: 2 wrappers em `ChecklistAdminPage`, 1 em `DocumentsAdminPage`; `DocumentConfigFormPage` sem alteração. Evidências: tsc/eslint/`vite build` (`App-prx-zmVR.js`) verdes; 337 testes em runs limpos (1 flake pré-existente de foto de avatar não relacionado — race entre `waitFor` do mock-call e `data-author-src` no DOM); screenshots autenticados desktop/tablet/390/320, claro/escuro, zoom 200% com `overflowX=0`; container local `delpi-controllership-finance` reconstruído e verificado. Produção: pendente de autorização específica.


## 28.11 UX-014 — Identidade humana nos eventos de auditoria (solicitação PO, 28/10/2026)

**PLANNED / CONTRACT GATE BEFORE RUNTIME.** Captura PO da timeline de auditoria do checklist exibe UUID cru após `v1`; inspeção do HEAD também encontrou `event.actor_subject` diretamente em `ChecklistAdminPage.tsx` e `DocumentConfigFormPage.tsx`. **Objetivo aprovado pelo PO:** em TODOS os componentes de auditoria do Portal Controladoria & Finanças, apresentar **avatar, nome e e-mail do ator** em vez do UUID como identidade principal. Preservar UUID como referência técnica auditável, nunca substituir/apagar o `actor_subject` persistido.

**Inventário obrigatório READ-ONLY:** procurar todas as views, timelines, listas, tabelas, detalhes, popovers e exportações de auditoria do MFE que mostram `actor_subject`/`created_by`/`updated_by`/`published_by` ou IDs; identificar producer, BFF DTO, consumers, Core identity/effective permission boundary, disponibilidade de foto/nome/email, avatar `CfUnifiedAvatar`/`@delpi/plugin-ui` e padrão existente em outros Portais. Search miss não comprova ausência. Não inferir identidade pelo UUID nem consultar o Core direto do browser.

**Contrato alvo e segurança:** a BFF poderá enriquecer uma lista de atores com dados públicos de exibição fornecidos por contrato autorizado do **Core**; definir owner/endpoint, campos, batch/cache, permissão de leitura, política de visibilidade do email, escopos, erros e observabilidade; nunca importar domain alheio nem consultar banco do Core. Havendo necessidade de novo contrato ou exposição de PII não previamente autorizada, apresentar `DECISION_REQUIRED` antes de implementar. Não acrescentar permissões do Portal. Preservar trilha original e eventos históricos.

**UI desejada:** componente do kit com `avatar + Nome completo + email` e evento/versão/data; sem avatar disponível → fallback canônico de iniciais; ator removido/desconhecido → fallback honesto 'Usuário não identificado' / 'Identidade indisponível', UUID apenas detalhe técnico autorizado (não nome); loading, avatar error, acessibilidade alt/foco, mobile, light/dark, sem N+1 no frontend. Não criar componentes paralelos se o kit oferece avatar/media.

**RQ/AC propostos:** UX014-01 inventário exaustivo de auditorias e contratos; UX014-02 identidade via Core→BFF autenticada/escopada; UX014-03 avatar/nome/email em todas as superfícies elegíveis, sem UUID cru como apresentação principal; UX014-04 actor histórico/inativo/deletado e falhas com fallback sem dados inventados; UX014-05 proteção PII, RBAC/access+manage conforme recurso, fail-closed; UX014-06 batch/cache/ausência de N+1 e sem regressão de auditoria; UX014-07 testes de contrato/RTL/integração e QA de responsive/keyboard/light/dark, smoke autenticado; UX014-08 Help/documentação e commit/deploy somente após gates. **Status TARGET/TO_INVENTORY, runtime TEST_NOT_RUN.**

**Ordem:** CP1 inventário de todas as superfícies; CP2 contrato Core/BFF e decisão transversal; CP3 kit-first UI; CP4 implementação mínima autorizada; CP5 testes; CP6 deploy local; CP7 produção mediante autorização; docs/CLARA só conforme evidência. Não misturar UX014 com UX013-RW01 de spacing nem com integração de relatórios §27.


**CP1 — Inventário executado (28/10/2026, READ-ONLY, PROVEN):**

Superfícies renderizando `actor_subject` cru (UUID):

| Superfície | Linha | Nível | Estado |
|---|---|---|---|
| `ChecklistAdminPage` modal Eventos | :1026 | MANAGE | UUID cru |
| `DocumentConfigFormPage` card Histórico | :859 | MANAGE | UUID cru |
| `MonthlyOverviewPanel` eventos | :345 | ACCESS | UUID cru |
| `PendenciesPage` diálogo Histórico | :454 | ACCESS | UUID cru |
| `DocumentDetailPanel` timeline | :305-308 | ACCESS | RESOLVIDO — `useParticipantProfiles` (contrato document-scoped) |
| `DocumentConversationPanel` | :197 | ACCESS | RESOLVIDO — mesmo contrato |

`created_by`/`updated_by`/`published_by` existem em tipos de `adminApi`/`catalogsApi`/`packagesApi` mas não são renderizados em nenhuma página.

Contratos existentes (verificados na fonte):
- Core `POST /me/directory/users/lookup` (`require_auth`, bearer do caller): `id`/`name`/`email` (mascarado por default; `reveal_email=true` expõe SMTP real — usado por perfis de portal/SMTP); **inativos são omitidos** da resposta; `app` opcional devolve `has_app_access`.
- Core S2S `GET /integrations/person-profiles/{id}/photo` + `POST /integrations/person-profiles/lookup` (`has_photo`) via `CORE_API_INTEGRATIONS_SERVICE_TOKEN`.
- BFF `POST /closing/competences/{period}/documents/{id}/participants/lookup` + `GET .../participants/{uid}/avatar` — **document-scoped**: só resolve participantes com vínculo canônico ao documento (autor U9, ator U8, uploader), anti-enumeração fail-closed.
- BFF `/viewer-photo` — somente o próprio viewer.

**Gap contratual (PROVEN):** nenhum contrato autorizado resolve identidades de atores administrativos/de auditoria fora do vínculo documental. Cobrir exige novo contrato (rota BFF de atores ou enriquecimento dos payloads de eventos) e expõe PII (nome/foto/email) a escopo mais amplo → **DECISION_REQUIRED apresentado ao PO; runtime interrompido antes de implementação** (decisão no relatório UX-014).


## 28.12 UX-015 — Navegação administrativa em cascata versão → documentos → detalhe (PO, 28/10/2026)

**TARGET / DECISÃO UX DO PO.** Capturas de produção da Administração exibem lista de Versões e, após acionar Itens, uma segunda tabela expandida na mesma página; histórico ainda abre modal. O PO requer navegação em **páginas completas**, em cascata, para compreender contexto, versão, documentos e ação de edição. Escopo restrito ao frontend com reuso kit-first e sem mudança dos contratos DR1–DR2.

**Fluxo:** `/closing/admin` lista versões → selecionar vN abre `/closing/admin/versions/{version}` com metadados, estado, vigência e lista de itens da versão → selecionar item abre `/closing/admin/versions/{version}/documents/{itemKey}` mostrando dados **daquela versão** (read-only se publicada/inativa, sem mutar snapshot). Ações de edição: DRAFT pode usar o update OCC existente; PUBLISHED/INACTIVE não é editável e oferece ação clara 'Editar exigência futura' que navega ao formulário administrativo governado `/closing/admin/documents/{itemKey}` com competência prospectiva e indicação explícita de que cria nova versão. Histórico/auditoria deve ter página de timeline contextual (não modal), mantendo versão, ator, data; para item_key histórico ausente na configuração corrente, mostrar histórico read-only. Rotas finais e parâmetros ainda requerem inventário no HEAD, evitar colidir com rotas existentes.

**UX:** breadcrumbs Início → Administração do checklist → Versão vN → Documento; link voltar preserva contexto, filtros/scroll/foco quando aplicável; CTA primário por intenção e danger com confirmação; StatusBadge/SectionCard/DataTableSection/PagePath/Timeline/UnifiedAvatar do @delpi/plugin-ui; spacing hierárquico, cards não colados, empty/error/loading, dark/light, mobile/teclado/zoom200, Ajuda sincronizada. Não duplicar dados entre página de catálogo mestre e visão histórica de versão.

**Gates:** CP0 HEAD/status/docs/cursor; CP1 inventário de rotas, componentes, chamadas e permissões, media/timeline e fallback de ator; CP2 wireframe/contrato visual e gate transversal explícito; CP3 implementação page-by-page rota de versão, lista de itens, detalhe, página eventos, integração com catálogo prospectivo; CP4 testes (deep-link/F5/back-forward, filtros, RBAC, versão DRAFT/PUBLISHED/INACTIVE, OCC, histórico, mobilidade, acessibilidade); CP5 deploy local e screenshots; CP6 deploy produtivo **autorizado pelo PO nesta rodada apenas se gates e testes PASS e sem decisão material nova** via fluxo canônico Git/SSH; smoke autenticado não destrutivo, rollback. Nenhum endpoint/migration/DB mutation de produção por teste; não cadastrar ou editar documentos reais. Caso falte contrato ou haja boundary novo: DECISION_REQUIRED e parar antes de runtime afetado.

**RQ/AC UX015-01** seleção de versão abre página própria; **-02** lista documentos da versão selecionada, não apenas os vigentes hoje; **-03** detalhe por versão é fiel e read-only quando publicada/inativa; **-04** edição prospectiva mantém DR1/D3/OCC, nenhuma mutação histórica; **-05** timeline página contextual, identidade humana somente quando contrato Core/BFF de UX014 estiver comprovado; **-06** navegação em cascata e retorno/F5/deep-link; **-07** acessibilidade/responsividade e kit-first; **-08** regressão, testes, deploy local/produtivo e smoke real com status. UX014 identidade humana e UX013-RW01 spacing continuam independentes; incorporar apenas melhoria de spacing local estritamente necessária.


**Execução (28/10/2026, PROVEN local):** contrato de navegação confirmado conforme spec — `closing/admin` lista só versões; `closing/admin/versions/{n}` (view `checklist_version`) traz metadados + itens daquele snapshot via `getTemplateVersion` e ações por estado; `closing/admin/versions/{n}/documents/{itemKey}` (`checklist_version_document`) é read-only com «Editar exigência futura» → catálogo governado `closing/admin/documents/{itemKey}`; `closing/admin/events` e `closing/admin/versions/{n}/events` (`checklist_admin_events`) movem o histórico do modal para página `CfTimeline` com recorte `?version=` da BFF. `checklistAdminShared.tsx` virou o owner compartilhado de constantes, ações de versão + diálogos e `ChecklistItemFormDialog`, consumido pela lista e pelo detalhe; `pluginRoutes` ganhou os padrões e builders `checklistAdminVersionPath`/`checklistAdminVersionDocumentPath`/`checklistAdminEventsPath`. Breadcrumb `CfPagePath` por nível; deep link/F5/back-forward via `popstate`. Edição de itens somente em DRAFT com update atômico + OCC `revision`; PUBLISHED/INACTIVE somente leitura; `actor_subject` cru mantido (UX-014 segue em DECISION_REQUIRED). Evidências: tsc/eslint ✓; **360 testes** (rotas + 4 páginas do escopo); `vite build` (`App-Cq3zaL3w.js`); deploy local reconstruído; smoke autenticado **12/12 PASS** (lista sem expansão, versão, documento read-only, histórico em página, deep link, back/forward, versão inexistente→404, DRAFT com ações, mobile 390 `overflowX=0`); capturas claro/escuro/tablet/320/zoom200 sem overflow (`Temp/ux015-shots`). Zero alteração BFF/migrations/permissões/dados. Deploy produtivo: autorizado nesta rodada — registrado no relatório final.



## 28.13 UX-015-RW01 — implementação governada do redesign da cascata (28/10/2026)

**PO aprovou a direção visual e pediu implementação + deploy final em produção sob gates. TARGET, não implementado neste registro.** Wireframes e critérios detalhados em doc 112 §51. Manter UX-015 (Admin → Versão → Documento → Histórico), sem voltar a tabela expansível nem modal. Diagnóstico das capturas: lista vertical de pares label/valor em cards largos com excesso de vazio, metadados pouco escaneáveis, ações no rodapé. Solução: header hierárquico, resumo compacto (somente dados reais), cards em grid read-only 2–3 colunas, contexto de versão condensado e ação de edição futura no topo, timeline em página, gaps/tokens homologados.

**Gate 0/1:** HEAD/status, instruções, .cursor, wireframes 112 §51, reuse 30, ledger 23; inspecionar `ChecklistVersionPage`, `ChecklistVersionDocumentPage`, `ChecklistAdminEventsPage`, `ChecklistAdminPage`, suas APIs/DTOs e testes; inventário dos exports kit e do CSS existente; nenhum contrato novo sem DECISION_REQUIRED. **Gate 2:** fechar mapa campo→componente/layout/tokens e wireframe responsivo com owner e AC, somente então alterar runtime. **Gate 3:** page-by-page versão, documento, histórico, administração; menor diff frontend sem modificar backend, migrations, permissions ou dados. **Gate 4:** testes, QA screenshots antes/depois local autenticado/viewport, teclado/foco e light/dark/zoom200; preservar edição DRAFT por OCC, histórico immutable e edição prospectiva pelo cadastro mestre. **Gate 5/6:** commit, deploy local e, com gates PASS e sem decisão material nova, deploy PROD AUTORIZADO pelo PO nesta solicitação somente para MFE; script canônico Git/SSH, BFF untouched, smoke autenticado não destrutivo, rollback, evidência. Se credencial smoke ausente, não improvisar grants/segredos: AC smoke TEST_NOT_RUN, reportar residual. Integração avatar/email UX-014 permanece separada e depende de contrato Core/BFF.

**RQ/AC:** UX015-RW01-01..09 conforme doc 112 §51.6; PASS somente com provas em código, testes e screenshots; ausência de smoke não vira PASS.


**Execução (28/10/2026, PROVEN local):** redesign implementado conforme doc 112 §51 — causa raiz era `cf-detail-list` sem regra CSS (lista vertical estreita); virou o grid semântico read-only do portal. Versão: `CfMetricStrip` com 3 tiles do DTO + fatos secundários + ações junto ao resumo + `DataTableSection` como banda única. Documento: badges e ações no header («Editar exigência futura» sempre prospectiva), Identificação/Exigência em grid, contexto em linha compacta. Histórico: subtítulo de escopo. CSS scoped novo: `cf-detail-list` grid, `cf-detail-list__full`, `cf-lead-row`, `cf-lead-badges`, `cf-version-context` — tokens `--cf-*`, zero internals do kit, zero `!important`. Evidências: tsc/eslint ✓; **360 testes**; `vite build` `App-GXSC05Nq.js`; smoke autenticado **12/12**; capturas desktop/tablet/390/320 × claro/escuro/zoom200 com `overflowX=0` (`Temp\ux015-shots`). Rotas/contratos/permissões imutados; zero escrita. Deploy produtivo executado via fluxo canônico; smoke autenticado condicionado a identidade smoke autorizada (ver relatório — AC-09).


## 28.14 UX-015-RW02 — rework estrutural obrigatório (PO, 28/10/2026)

**VEREDITO VISUAL PO: REWORK.** Capturas pós RW01 comprovam persistência de excesso de wrappers/cards aninhados em Administração e Versão, desperdício de largura/altura, UUID de autor cru, ações 'Abrir' redundantes e listagem sem ordenação e alternância tabela/cards. Não tratar como espaçamento cosmético nem considerar UX-015-RW01 aceite visualmente.

**Decisão de UX:** Administração deve possuir cabeçalho em PT-BR, ações com ícones/variantes semânticas e uma única superfície de listagem; remover o card intermediário entre container da página e DataTableSection, evitando card dentro de card dentro de card. Identificadores técnicos `monthly-closing-checklist` não aparecem no título principal (podem ficar em detalhe técnico autorizado). A página de Versão deve seguir igual princípio: resumo compacto, uma listagem de documentos sem wrappers redundantes. Linhas inteiras clicáveis abrem versão/documento; remover botão redundante 'Abrir', mas manter ações destrutivas separadas (stopPropagation), foco/Enter/Espaço e affordance acessível. Tabelas DEVEM oferecer ordenação por colunas aplicáveis e alternância **Tabela/Cards** utilizando recursos reais de `@delpi/plugin-ui`, preservando URLs/deep-link, state e filtros. Listagem deve preencher o espaço vertical disponível de forma flexível, **sem fabricar linhas** nem comprometer mobile, footer, viewport ou paginação. Não confundir 'closed' técnico e checklist com rótulos UX PT-BR; revisar toda copy do escopo.

**Identidade humana transversal UX-014:** na Versão, História e qualquer componente de auditoria do Portal, substituir UUID cru visível por avatar, nome e e-mail conforme contrato autorizado Core→BFF; preservar actor_subject apenas em trilha auditável. **DEPENDÊNCIA MATERIAL:** se a BFF não dispuser de contrato de identidade, iniciar inventário/contrato, retornar DECISION_REQUIRED e não inventar integração, nome ou consulta browser→Core. Não marcar UX014 PASS sem identity integration real. Separar ajuste frontend seguro do novo contrato que demande gate.

**DoD visual:** screenshots e revisão DOM antes/depois com contagem de containers aninhados, evidence de uma superfície principal por página, tabela/card toggle real, ordenação asc/desc por coluna, click row/navegação teclado, prevenção de ativação destrutiva, altura flexível e comportamento em dataset 0/1/50/100, dark/light, 320/390/768/desktop e zoom 200%; smoke local/prod autorizado, zero mutação de dados reais, regressão 360 testes (ou baseline HEAD comprovado). Usuário deve perceber diferença estrutural notável, não alteração de margin isolada.

**Gates:** CP0 HEAD/status/authority; CP1 kit inventory DataTableSection/table-card-toggle/row click/sort/height and avatar/media identities; CP2 design/contratos, owner e decisão de identidade se precisar BFF; CP3 implementação page-by-page Admin→Version→Document→Events; CP4 testes UX/a11y/regressões; CP5 screenshot comparativo e homologação local; CP6 deploy produção somente depois de gates e sem decisão material nova, autorização PO de deploy deve ser confirmada nesta rodada específica. Estado PLANNED/TARGET; runtime não alterado por este registro.


#### Execução UX-015-RW02 (28/10/2026) — frontend-only

**Inventário do kit (PROVEN):** `DataTableSection`/`DataTable` já suportam nativamente tudo o exigido — `column.sortable`+`sortValue` (sort client-side asc/desc), `viewLayoutPreferencesKey`+`renderCard` (toggle Tabela/Cards persistido, default cards ≤768px), `onRowClick` (tabIndex/Enter/Espaço), `rowClick:"stop"` por coluna (isolamento destrutivo), `columnPreferencesKey`, `headerActions`, `getSearchText`. `createDashboardDataRecordCard` produz card-anchor navegável (`CfDataRecordCard` adicionado ao catálogo cf). Gap honesto: kit não expõe sort-bar no modo Cards — a ordenação definida na tabela aplica-se também aos cards.

**Administração (`ChecklistAdminPage`):** removido o `CfSectionCard` intermediário — uma única superfície `DataTableSection` (título «Versões · {nome do template}», sem o código técnico). Ações governadas no `headerActions` com ícones (`FilePlus2`/`History`/`FileText`) e variante `danger` nas destrutivas. Colunas ordenáveis, toggle Cards, busca, clique de linha → versão; coluna «Ações» mantém apenas as ações por estado com `rowClick:"stop"`; botão «Abrir versão» removido. Em modo Cards o `DataRecordCard` é o anchor e as ações ficam em faixa própria (sem interativo aninhado).

**Versão (`ChecklistVersionPage`):** resumo compacto preservado; «Publicada por» nunca exibe UUID — fallback «Identidade não disponível» com o subject apenas em `title` (diagnóstico) e na trilha de auditoria («Ator (id):» nos eventos). Documentos em superfície única com sort/toggle/clique; ações de edição DRAFT migraram para `headerActions` da tabela; sem «Abrir».

**Identidade UX-014 — DECISION_REQUIRED:** o único contrato BFF de identidade é document-scoped (`POST .../participants/lookup`, restringido a participantes do documento; `/viewer-photo` só o próprio usuário). Não existe contrato autorizado para resolver atores administrativos (`published_by`, `actor_subject`) — requer nova rota BFF (ex.: proxy do `/me/directory/users/lookup` do Core com bearer do caller) sujeita a gate de contrato/PII. Frontend entrega o fallback honesto sem UUID; nenhum backend/contrato foi alterado.

**Evidência:** 365/365 testes (novos: sort, toggle cards, row-click, isolamento destrutivo, fallback de identidade); tsc/eslint limpos no escopo (erro preexistente `ProfilePage.tsx` fora do escopo); build `App-D376ypA0.js` (expose `__federation_expose_App-0ucqmrGp.js`) — deployado `bed4993c05` em produção com remoteEntry 200 e BFF healthy; smoke autenticado local 13/13 (superfície única, sort asc/desc, cards, nav linha/card, destrutiva isolada, sem UUID, deep link, mobile); 6 capturas dark/tablet/320 `overflowX=0`. Zero mudança de rotas/contratos/permissões/migrations.


## 28.15 UX-016 — Hero e tabela flexível, duas páginas irmãs (decisão visual PO)

**APPROVED DESIGN / TARGET:** wireframe aprovado pelo PO documentado integralmente em 112 §53. Escopo: `ChecklistAdminPage` e `ChecklistVersionPage`, wrappers de layout e reuse do DataTableSection. Administração remove coluna Ações/Inativar; linha/card abre versão. Ação de Inativar com ícone/danger e confirmação existe somente na página da versão. Hero agrupa título, métricas, ações, pesquisa, toggle Tabela/Cards, Colunas; tabela abaixo ocupa altura útil restante (flex min-height apropriado, sem registros inventados); ambas seguem a mesma estrutura visual e tokens light/dark.

**Gate:** CP0 HEAD/status/instruções/.cursor/docs; CP1 inventário da API real do kit (headerActions, filtros, table/cards, sort, columns, layout/height) e contratos; CP2 wireframe responsivo e mapa concreto de componentes sem duplicar barras; CP3 implementar Admin, testar, implementar Versão, testar; CP4 regressão, UX QA e screenshots comparativos com dados 0/1/50/100; CP5 local; CP6 produção SOMENTE após autorização específica e sem drift/decisão material, smoke autenticado governado ou TEST_NOT_RUN; CP7 docs, Help e evidência. Integração de identidade UX-014 continua gate de contrato separado. Nenhuma mudança BFF/DB/permissões.

**Execução (UX-016):** IMPLEMENTADO. Evolução mínima do kit: `DataTableSection.toolbarPortalTarget` (portal da toolbar nativa para o hero, mesma instância/estado) + `tableLayout="scroll"` (wrap `--scroll` flexível do kit). `ChecklistAdminPage` e `ChecklistVersionPage` usam `CfPageHero` + `cf-flex-listing` irmão com a cadeia `dashboard-page--fill` aplicada às duas views no `PluginShell`. Admin sem coluna Ações/Inativar; Inativar danger+ícone só no detalhe; hero intrínseco (`flex:0 0 auto`), listagem única que cresce e rola internamente com paginação ancorada. Testes: MFE 367/367, plugin-ui data 167/167 (inclui `toolbarPortal` 3/3); smoke local autenticado 19/19; QA visual light/dark/768/390/320/zoom200 sem overflow. Registro de AC: doc 23 UX016-01..09. UX-014 segue `DECISION_REQUIRED` (sem contrato Core→BFF de identidade administrativa).

**Execução (UX-016-RW01):** IMPLEMENTADO. Help contextual transversal com recursos já homologados do kit — `headerHint` por coluna, `searchHint` na toolbar e `hintedLabel` (HelpTooltip) em métricas/campos somente leitura — com textos no catálogo `helpTooltips.ts`; cobertura em 10 superfícies (Admin, Versão, Documento, Documentos, Catálogos, Checklist da competência, Estoque, Baixas, Minhas tarefas, formulário de configuração). Paginação inteligente na fonte compartilhada: `DataTableSection.hidePaginationWhenSinglePage` (opt-in retrocompatível) ativada por padrão no wrapper `cfDataTableUi` — rodapé só aparece com >1 página efetiva; seletor de page size preservado. Zero mudança em BFF/contratos/dados.


## 29. DRE-ACCESS-018 — Área de Fechamentos Recebidos e Revisão Documental da DRE (inventário READ-ONLY + gate de arquitetura)

**Data:** 29/10/2026. **Origem:** brief `CF-PROC0072-DRE-ACCESS-018` (PO). **Modalidade:** inventário read-only + desenho funcional + gate de contratos. `IMPLEMENTATION_AUTHORIZED=NO` — nenhum endpoint, migration, página runtime ou deploy antes do gate. Wireframes dos quatro níveis: doc 112 §54. Matriz RQ/AC: ledger 23 «Área DRE».

### 29.1 Owner, boundary, producers, consumers

| Papel | Valor |
|---|---|
| Owner funcional | Controladoria (produtor das entregas) + PO PROC-0072 |
| Owner técnico do contrato | `controllership-finance-api` (BFF) + Core (effective permissions/grants) |
| Boundary | Área restrita de **consulta** dentro da Central de Fechamento — sem upload, sem validação P2, sem aceite/revisão P5, sem relatórios TOTVS/divergências/estoque/admin (doc 91 §1, doc 112 §16.1) |
| Producers | `closing_package`/`closing_package_version` (snapshot de composição), `closing_document`/`document_version` (arquivos), `document_message`, `audit_event`, `closing_notification_event`, `closing_review_assignment` |
| Consumers | MFE `controllership-finance` (quatro páginas doc 112 §54), Core (permissions, identidade, notificações), CLARA (sem superfície DRE nesta fase) |

### 29.2 Inventário de contratos existentes (CP1 — evidência de código)

| Capacidade | Evidência | Estado |
|---|---|---|
| Pacotes por área destinatária | `closing_package` UNIQUE(competence_id, recipient_area), CHECK CONTABIL\|FISCAL (V008) | PROVEN |
| Versão de pacote imutável com composição | `closing_package_version` DRAFT→FINALIZED→SUBMITTED, `content` JSONB com `items[]`{item_key,state,document_version_id} + resumos P3/P4 (V008; `_composition_snapshot`) | PROVEN |
| Visibilidade de pacote por assignment | `_visible_areas`: manage vê tudo; demais veem só pacotes com `closing_review_assignment` ativo (REVIEWER/COORDINATOR) — sibling nunca vaza (404) | PROVEN |
| Elegibilidade por grupo Core | `REVIEW_ELIGIBILITY` (catálogo P6) + verificação de grupo Core, fail-closed | PROVEN |
| Decisões/esclarecimentos append-only | `closing_review_decision` por área/versão; `closing_clarification` OPEN→RESOLVED; rejeição terminal | PROVEN |
| Documentos versionados | `closing_document` ATTACHED/CANCELLED + `document_version` + `document_version_id` no snapshot | PROVEN |
| Download auditado | `resolve_download`: scope de filial + storage + `DOCUMENT_DOWNLOADED` auditado (autorizado/negado/falha) | PROVEN |
| Mensagens documentais | `document_message` V016 — **CHECK `audience='INTERNAL'` somente** | PROVEN com limite material |
| Effective permissions | `controllership-finance.access` + `.manage` apenas; `principal_type='user'`; Core indisponível → 503 fail-closed; manifesto/teste estrutural pinam exatamente duas permissions | PROVEN |
| Competências/itens por área | `GET /closing/competences`, `/items?recipient_area=` | PROVEN |
| Notificações | `closing_notification_event` outbox → Core notifications para assignments | PROVEN (somente assignments P5) |
| Kit UI | `DataTableSection`(+toolbarPortalTarget/tableLayout/hidePaginationWhenSinglePage/headerHint/searchHint), `CfPageHero`, `ResizableColumns`, `createDashboardMessageThread`, `createDashboardMentionComposer`, `createDashboardRoomConversationShell`, `createDashboardAttachmentPreviewStrip`, `useFilePreviewLoader`/`FilePreview`, `CfTimeline`, `HelpTooltip` | PROVEN (exports no HEAD) |
| Superfícies MFE reutilizáveis | `DocumentDetailPanel` (metadados+versões+preview+download+timeline+conversa), `DocumentConversationPanel`, `PackagesPage`, `MonthlyDocumentsPanel` — orientadas à Controladoria | PROVEN componentes; contrato DRE pendente |

### 29.3 Gaps materiais encontrados (CP1→CP3)

1. **Sem ato de liberação ao destinatário.** `list_documents`/`get_document`/`resolve_download` autorizam por competência + `branch_scope` apenas; **não verificam** que o documento/versão consta do snapshot de uma `closing_package_version` liberada à área do solicitante. Hoje qualquer usuário `.access` baixa qualquer documento da competência — correto para a Controladoria, **insuficiente para destinatário restrito**. Não há campo/tabela `released`/`delivery` para consulta DRE.
2. **Sem vínculo «destinatário de consulta».** `closing_review_assignment` modela REVIEWER/COORDINATOR (revisão P5), não «quem da Contabilidade/DRE pode consultar». `recipient_area` é atributo do pacote, não entitlement de pessoa.
3. **Audiência de mensagens fechada em INTERNAL.** `document_message.audience CHECK ('INTERNAL')` impede conversa visível ao destinatário sem evolução de contrato+migration.
4. **Sem máquina de estados de solicitação de ajuste.** `closing_clarification` é P5 (versão de pacote, áreas revisoras) — não cobre «pedido de correção do destinatário → resposta → confirmação de atendimento» por documento.
5. **Permissões congeladas.** Opção B do doc 91 (`controllership-finance.closing-documents.read`) é direção aprovada mas **deferida** (`DEFERRED_IMPLEMENTATION_BY_PO`); manifesto/teste estrutural pinam duas permissions; entrada restrita no launcher exige decisão transversal.
6. **Projeção restrita ausente.** `get_package`/`list_packages` expõem `content` com resumos internos P3/P4 — incompatível com o boundary DRE; precisa de read-model próprio.

### 29.4 Respostas às perguntas de segurança (CP3)

| Pergunta | Resposta com evidência |
|---|---|
| Como o Core distingue destinatários DRE? | **Hoje: não distingue.** Somente `.access`/`.manage`. Sem vínculo destinatário → `DECISION_REQUIRED` |
| Como a BFF resolve effective permissions? | Middleware Core → `authorized_user`; indisponibilidade = 503; `manage ≠ access` | PROVEN |
| Como o pacote registra o público autorizado? | `recipient_area` + assignments de **revisão**; não há registro de audiência de **consulta** | GAP |
| Impedir acesso a anexos não liberados | Inexistente — leitura de documento não consulta pacote/snapshot | GAP crítico |
| IDOR por competência/package_id/document_id | Competência+filial fail-closed (404). Troca de `document_id` por `.access` é permitida hoje — para DRE seria vazamento | GAP para novo público |
| Previews/downloads protegidos | Download: stream autenticado + auditoria PROVEN; falta vínculo liberação→download | PROVEN + GAP |
| Auditoria de ações de revisão | `audit_event` append-only + `closing_review_decision` | PROVEN |
| Separação envio/revisão/aceite | Distinta em P5 (submitter manage, reviewer assigned, decisões por área); falta papel «destinatário de consulta» | GAP |

### 29.5 Contrato de acesso proposto (candidato — gate)

**`D-DRE-ACCESS-01 — DECISION_REQUIRED.`**

| Alt. | Desenho | Impacto | Recomendação |
|---|---|---|---|
| A | Terceira capability `controllership-finance.closing-documents.read` (Opção B, doc 91) + papel `RECIPIENT` em `closing_review_assignment` (CHECK novo) | Exceção ao freeze: manifesto, Core grants/launcher, teste estrutural, entrada restrita; migration de CHECK | **Recomendada** — direção de produto já aprovada (doc 91 §1, não reabrir); role reutiliza mecânica de visibilidade/auditoria provada sem RBAC paralelo |
| B | Reusar `.access` + regra «assignment RECIPIENT» | `.access` guarda todas as rotas → precisaria negar o restante por scope; risco de liberação indevida; doc 91 §3 proíbe ampliar `.access` por conveniência | Rejeitada (viola boundary) |
| C | Grupo Core sem permission nova, rotas sob `.access` | Mesmo problema de B | Rejeitada |

**`D-DRE-RELEASE-01 — DECISION_REQUIRED.`** Estado que libera o documento ao destinatário: (A) liberação = `closing_package_version.status='SUBMITTED'` (snapshot congelado; read-model deriva `document_version_id` de `content.items`); (B) ato dedicado `release_to_recipient` por item/pacote. **Recomendação:** A na V1 — snapshot SUBMITTED já é imutável, auditado e representa «pacote enviado»; B como evolução se o PO quiser liberação granular. A projeção deve expor `items[].document_version_id` e **não** `p3_reconciliation`/`p4_pendency_counts`.

**`D-DRE-PROJECTION-01 — DECISION_REQUIRED.`** Endpoints de leitura restrita (read-model): `GET /closing/received-closings` (N1), `GET /closing/received-closings/{period}/{package_id}` (N2), `GET .../documents/{document_id}` + `.../download` (N3). Mínimo: reusar `_document_in_scope` + verificação «document_version_id ∈ content.items da versão SUBMITTED do pacote visível ao ator» + auditoria `DOCUMENT_DOWNLOADED` com contexto recipient.

**`D-DRE-COLLAB-01 — DECISION_REQUIRED.`** Ajuste/comentário DRE: (A) `document_message.audience += 'RECIPIENT'` + tabela `document_adjustment_request` (OPEN→ANSWERED→CONFIRMED, imutável); (B) adaptar `closing_clarification` a documento. **Recomendação:** A — clarification é de pacote/área revisor; reuso criaria semântica ambígua. Resposta NÃO encerra a solicitação (regra no service; encerramento = ação de validação do destinatário).

**Pendentes herdados:** D-DRE-MANIFEST-01 (=ACCESS-01), D-DRE-NOTIFY-01, D-DRE-HISTORY-01, D-DRE-ENTRY-01, D-DRE-COMPOSER-01 (texto-only), UX-014 (identidade humana).

### 29.6 Sequência objetiva de implementação (pós-gate)

1. Gate transversal: ratificar capability Opção B + papel RECIPIENT + entrada restrita (Core/manifest/launcher/guards).
2. BFF: projeção read-model N1–N3 + verificação de liberação + download auditado + testes positive/sibling/negative (IDOR, 401/403/404, Core-down).
3. BFF: `document_adjustment_request` + audiência RECIPIENT em `document_message` + resposta/encerramento + notificações.
4. MFE: quatro páginas do doc 112 §54 com kit homologado + Help + testes RTL.
5. Deploy local → smoke autenticado → produção somente com autorização PO e smoke governado.

### 29.7 Plano de testes

Rotas BFF (mock+PG): listagem só de entregas autorizadas; competência sem pacote → `[]`; pacote multi-PDF; pacote zero docs liberados; versões de PDF (só liberada); download autorizado/negado/inexistente; solicitação criada/respondida/não-encerrada/encerrada; IDOR (trocar period/package/document); 401 sem token; 403 sem capability; 404 cross-recipient; Core indisponível → fail-closed. MFE: quatro páginas 0/1/N registros, filtros/URL/F5/back, sort, cards, paginação inteligente, help, mobile 320/390/768, claro/escuro, zoom 200%. Contrato: DTOs de projeção sem campos internos (p3/p4, internals de auditoria).

### 29.8 Deploy e rollback

**Deploy:** somente após gate + autorização PO. Ordem: migration(s) → BFF → grants Core/capability → manifesto/MFE. A área permanece inacessível sem grant — rollout por grant Core, não por flag de código. **Rollback:** revogar grant/capability no Core → revert manifesto/MFE → revert BFF; migrations aditivas permanecem (imutáveis); rollback lógico = revogação de grants, nunca delete destrutivo.

### 29.9 Status de execução — DRE-ACCESS-019 (2026-10-27)

Sequência §29.6 executada: capability `closing-documents.read`, projeção BFF `/closing/received-documents` (deliveries/documentos/download auditado/mensagens `SHARED`/solicitações de ajuste), audiência `SHARED` + `document_adjustment_request` (V018) e modo destinatário no MFE com rota `closing/documents`. Implementação, desvios de contrato e evidências: [doc 115](./115-dre-access-019-documentos-recebidos-gate-91-implementacao.md). Itens 7–8 de §2 e checkpoint 6 passam de TARGET a IMPLEMENTED nos limites descritos no doc 115.

### 29.10 Status de execução — DRE-ACCESS-019-RW02 (2026-10-28)

Migração governada da capability de entrada (decisão PO): `closing-documents.read` → `controllership-finance.access.dre`, separando acesso interno, gestão e público DRE. Fluxo alvo: Portal raiz → **Home DRE** → «Fechamento Mensal» → Documentos e interações. Manifesto: 4 permissions (legada marcada DEPRECATED, mantida até homologação), 13 rotas — `closing/documents` canônico sob `access.dre`, `home` (Home DRE, `showInMenu`) e alias compat `received-documents` sob a legada. BFF aceita ambas no boundary DRE e reporta `accessDre` distinto em `/viewer-context`; nenhum endpoint interno passa a aceitar `access.dre`. Entrada resolvida pela convenção `resolveAuthorizedEntryPath` (RW01) — sem evolução material do contrato Core, `DECISION_REQUIRED` não acionado. Importação do manifesto e grant ao papel DRE ficam com o PO (ordem e verificações no doc 115 §10).

### 29.11 Status de execução — DRE-ACCESS-019-RW03 (2026-10-28)

Home DRE padronizada no padrão da Home interna e **remoção definitiva** da legada `closing-documents.read`, após evidência de migração no Core produtivo (`access.dre` importada na v0.1.3, papel DRE provisionado com 1 usuário real, legada com zero grants — doc 115 §11). Manifesto v0.1.4: **3 permissions/12 rotas**. `DreHomePage` removida — a `HomePage` compartilhada projeta `HUB_SECTIONS` por capability (`access`/`manage`/`accessDre`); a seção `closing_dre` («Central de Fechamento» → «Fechamento Mensal» → Documentos e interações) só aparece para `access.dre`. Top bar dinâmica por capability («Início» para ambos os públicos) e paleta restrita às rotas autorizadas. BFF aceita **somente** `access.dre` no boundary documental; `/viewer-context` reporta `{access, manage, accessDre}`; alias `received-documents` descontinuado (`not_found`); usuário somente-legado passa a ser negado. Descontinuação produtiva ocorre no registro da v0.1.4 pelo PO — o `PluginPermissionSyncService.sync_module` remove permissions/rotas ausentes (mecanismo oficial, sem SQL direto, sem perda de auditoria).

### 29.12 Status de execução — DRE-ACCESS-019-RW04 (2026-10-28, REWORK da RW03)

Correção arquitetural por decisão do PO: **UMA HomePage, UM basePath, UMA top bar, UM catálogo** — a diferença entre públicos é somente o conteúdo autorizado. A separação `home`/`dre_home` da RW03 foi removida na origem:

- **Portal:** `resolveAuthorizedEntryPath` → **`hasAuthorizedAppEntry`** — no basePath exato, quem detém ≥1 rota autorizada monta o MFE (não há mais redirect para sub-rota). Contrato de uma permission por rota e `ProtectedRoute` inalterados; sem ampliação — o MFE já era montado de qualquer forma e a BFF segue autoridade.
- **MFE:** view `dre_home` eliminada (tipo, mapa de rotas, nav, branches); `/home` virou compat de entrada do launcher DRE que canonicaliza no basePath; `HomePage` perdeu o prop `homeView`; top bar passou a um único «Início» com `requiredCaps: [access, accessDre]`; hero por audiência continua projetado por capability (não por view).
- **Manifesto v0.1.5:** 3 permissions/12 rotas — `/home` segue `access.dre`+`showInMenu` como entrada autorizada do launcher (redirect, não página).
- **Rede de segurança** do viewer somente-DRE agora retorna a `home` (não mais a `dre_home`).

Deploy rebuilda `portal` + `controllership-finance`; BFF sem mudança.

### 29.13 Registro — CONSOLIDATION-002, base canônica do processo (2026-10-29)

Execução documental `CF-PROC0072-ANALYSIS-CONSOLIDATION-002` entregue: [Documento 118 — base canônica do fechamento mensal](./118-base-canonica-processo-fechamento-mensal-proc0072.md) consolida modelo operacional OPS-01..17, evidências com proveniência, regras DR-01..16, resolução das 10 questões do doc 117, contradições reconciliadas, AS-IS × TARGET e prontidão de contratos (§16.B). **Próxima evolução sob este plano:** os Checkpoints 2–5 usam o doc 118 como fonte de verdade do processo; contratos `DESIGN_READY` (RQ-ANL-02/03/04/05/08, ledger 23 revisado) aguardam gate de implementação do doc 93 — nenhum runtime foi autorizado por esta consolidação.
