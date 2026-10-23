# X4.UX-R1 — Decisões de produto: cadastro assistido e conferência cadastral (2026-10-23)

> **DECISION / PO-APPROVED PRODUCT DIRECTION; IMPLEMENTATION NOT AUTHORIZED.** Registro das decisões tomadas com o Product Owner após a inspeção visual da ficha de fornecedor no Portal. Não é alteração de contrato API, autorização de provedor, aprovação DPO, mudança de fila ou autorização de gravação ERP. Antes de implementar, executar inventário e freeze RQ/AC pelos owners.

## 1. Contexto e evidência de uso

- X3.E2E backend e X4.S1/R1 frontend validados em código; X4.S2 publicou/verificou bundle e backend produtivos. O PO abriu a ficha E14 de fornecedor e apresentou capturas reais da seção `#enrichment`: campos Protheus × fonte externa, decisões, revisão e histórico.
- **Constatação UX do PO:** seção enterrada no fim de ficha extensa; o usuário precisa abrir fornecedores individualmente para descobrir quem necessita análise. Contagem de propostas `PENDING` não equivale a quantidade de **divergências acionáveis**.
- A sessão visual das capturas comprova parte da renderização desktop/tema escuro e navegação da ficha; **não prova** interações de clique, desktop completo, mobile, tema claro, teclado/foco, Help ou a íntegra do smoke de X4.S2. Preservar `INCONCLUSIVE` para critérios não testados.
- Contratos atuais mantidos: `external-data-api` consome BrasilAPI CNPJ; `supplies-api` compõe S1/S2; `api-delpi` fornece cadastro canônico SA2; writes Protheus OFF.

## 2. Decisões funcionais do PO — direção aprovada

### D-01 — Lista E13 como ponto de entrada para conferência

A lista de fornecedores existente deve apresentar **status de conferência**, quantidade de **diferenças que merecem ação** e entrada direta para revisão do fornecedor na ficha E14. Filtros para "com diferenças", "em análise", "conferido" e "não consultado" são candidatos sujeitos a contrato BFF. A ficha E14 permanece o lugar da análise detalhada. Uma nova página exclusiva de pendências **não está aprovada como solução inicial**; avaliar somente se volumes/fluxo comprovarem necessidade.

**Não inferir indicadores de todos os fornecedores a partir de chamadas BrasilAPI por linha ou de contagens genéricas de propostas.** Inventariar contrato de summary read-model servidor por fornecedor, paginação, freshness/TTL, ownership, escopo de unidade e custos. Nenhum scan automático em massa autorizado.

### D-02 — Ausência de dado externo não é divergência a tratar

Quando Protheus possui valor e a fonte externa não fornece, exibir **"Sem informação na fonte externa; cadastro interno preservado"** como informativo, sem criar ação obrigatória de aceitar/rejeitar e sem entrar na fila/contagem de diferenças acionáveis. Caso inverso (Protheus vazio e fonte externa tem valor) pode ser **complemento sugerido** se elegível. MATCH não vira pendência; PROTECTED/NOT_COMPARABLE/UNSUPPORTED são apenas informativos; diferenças reais exigem comparação de ambos os valores e eligibility validada.

**Separar explicitamente** `comparison_state`, `eligibility_state`, `decision_state` e `requires_user_attention` (campo/derivação TARGET, não existe necessariamente no contrato). Preservar auditoria e matriz S1/S2 existentes: não reclassificar enums nem apagar propostas decididas sem ADR/freeze de owner. Determinar se omissões informativas podem ser resolvidas apenas em UX/read-model ou se demandam regra de domínio para encerramento; documentar consequência sobre status da revisão.

### D-03 — Cadastro novo com preenchimento assistido

O fluxo de criação E14/`SupplierCreatePage` deve oferecer consulta externa **antes** de criar o fornecedor, sugerindo os campos disponíveis, tornando visível para cada valor a origem, o momento e se foi confirmado ou alterado manualmente. Usuário revisa dados, informa campos internos obrigatórios e confirma explicitamente a criação conforme contrato ERP/capability/write gate vigentes. A busca **não cria fornecedor**, não gera PUT, não preenche silenciosamente campos protegidos e não substitui regras Protheus; evitar duplicidade de CNPJ com consulta canônica autorizada.

**Não reutilizar automaticamente a review S2 de fornecedor existente como se já houvesse SA2 canônico para criar fornecedor.** Definir BFF prefill/preview sem persistência antecipada e field-mapping allowlist; não criar permission por botão.

### D-04 — Busca por nome → selecionar CNPJ → consulta completa automática

Na criação, permitir entrada preferencial por **CNPJ** e, como evolução desejada, **razão social/nome fantasia** (com filtros UF/município). Quando busca por nome retornar candidatos, mostrar **razão social, fantasia, CNPJ e localidade/proveniência**; a pessoa **seleciona explicitamente o estabelecimento** (não escolher o primeiro por similaridade). Em seguida, **o sistema consulta automaticamente pelo CNPJ selecionado**, através do backend, para pré-preenchimento assistido, sem exigir segundo clique ou digitação de CNPJ.

**Viabilidade ≠ contrato pronto:** BrasilAPI CNPJ já atende lookup exato; provedor de **descoberta por nome/fantasia → CNPJ** ainda é `TO_INVENTORY`, inclusive termos de uso/licenciamento/SLA, LGPD, latência, rate limits, origem e contrato de dados. Não escolher provedor ou fornecedor comercial somente por existência de website; não chamar diretamente do MFE nem iniciar criação de serviço paralelo. Reusar `external-data-api` como owner do transporte/normalização externa, `supplies-api` como owner da orquestração de cadastro e Core para permissions efetivas.

### D-05 — Proveniência obrigatória, não aprovação da fonte como autoridade

Cada sugestão deve informar fonte (terceiro), timestamp de consulta, status, e distinção `sugerido | confirmado | alterado manualmente | não disponível`. BrasilAPI/diretórios terceiros **não são fonte canônica de autorização de escrita**; Protheus continua mestre. CPF/QSA/contatos excluídos não devem ser reapresentados sem contrato LGPD novo. Sem consulta em massa ou atualização automática do Protheus.

## 3. Fronteiras e proibições

Fluxo: `plugins/supplies → supplies-api → api-delpi | external-data-api | Core`; `external-data-api → provider externo`. Core resolve effective permissions; BFF autoriza fail-closed com unit/resource/ownership. Frontend kit-first, CSS isolado, Help sincronizada. Não criar permission por ação, refazer backend aceito ou reclassificar SOURCE_MISSING automaticamente. Não habilitar POST/PUT Protheus; não modificar flag de escrita; não alterar o legado `plugins/dashboard-supplies`.

## 4. Próxima etapa solicitável — X4.UX-R1.P0 (inventário + contrato antes do código)

1. Rebase HEAD e checar `.cursor`/authorities e plano E10/E13/E14; conservar E10 gate independente.
2. Inventariar contratos DTO S1/S2 e status de revisão, regra de atenção acionável, semântica SOURCE_MISSING/CURRENT_MISSING e como fechar revisões sem falsas pendências; validar com RQ/AC e testes negativos.
3. Inventariar a lista E13 e o BFF de paginação/resumo; propor read-model de status/counters com tenant/filial/ownership, sem N+1, scans e calls externas na listagem.
4. Inventariar `SupplierCreatePage`, contratos atuais de POST/PUT Protheus, flags, duplicidade e campos homologados; propor prefill somente após confirmação e sem persistir fornecedor.
5. Inventariar opções legais/técnicas de busca por nome/fantasia e CNPJ. Critérios: licença, confiabilidade, origem, cobertura e filial, política LGPD/DPO, rate limit, custos, S2S e contrato de erro. Classificar como `TO_INVENTORY` até prova; BrasilAPI lookup CNPJ existente é `PROVEN`.
6. Definir UX wireframes/filtros/status/proveniência e separação de `diferença acionável` de informativos; mapear `route → DTO → owner → AuthZ → AC/teste`, perdas e estados de erro, dark/light, mobile, keyboard/focus, URL/F5 e Help.
7. Devolver proposta de menores fatias sequenciais (BFF/read model, prefill/criação, busca nome, UI) com gates e autorização explícita por fatia. Sem implementação ou deploy nesta P0.

**Definition of Done P0:** RQ/AC e contrato congeláveis; owner de cada capability, termos do provider verificados, dependências classificadas e plano menor diff. Resultado `READY_TO_AUTHORIZE | BLOCKED | EXECUTION_DRIFT | INCONCLUSIVE`.

## 5. Residuais existentes

- X4.S2 smoke visual ainda não fecha mobile/tema claro/teclado/foco/Help.
- Registro formal ROPA/DPO da consulta externa não concluído.
- E10/WF-15 preserva seu próprio GATE-FEATURE inconclusivo até evidência atual.
- Busca por nome, summary list e prefill novo são **TARGET**, não API implementada nem página entregue.

## 6. Referências

- [X4.P0 UX freeze](./X4-P0-SUPPLIER-ENRICHMENT-UX-INVENTORY-CONTRACT-FREEZE-20261022.md)
- [X4.S1 implementation](./X4-S1-SUPPLIER-ENRICHMENT-UI-IMPLEMENTATION-20261022.md)
- [X4.S2 runtime evidence](./X4-S2-FEDERATED-DEPLOY-RUNTIME-ACCEPTANCE-20261022.md)
- [Roadmap fornecedores](./FORNECEDORES-GESTAO-CADASTRAL-ROADMAP.md)
- [Implementation plan](./IMPLEMENTATION-PLAN.md)
- [X3 E2E closure](../shared-integrations/X3-E2E-CLOSURE-AND-X4-UI-READINESS-20261022.md)
