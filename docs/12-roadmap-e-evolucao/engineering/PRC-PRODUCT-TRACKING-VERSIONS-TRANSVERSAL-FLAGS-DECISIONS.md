# PRC — Registro de produtos acompanhados, versões confirmadas e flags transversais

> **FONTE CANÔNICA ATUAL — 2026-11-13:** [Regras de produto, inconsistências e plano central PRC-TRACK](./PRC-TRACK-CANONICAL-PRODUCT-RULES-AND-EXECUTION-PLAN.md). Este documento é referência histórica/setorial: em caso de divergência sobre no-op, V1, snapshot PRC, REOPEN, RESOLVED/REMOVED, flags durante solicitação, conclusão, permissões ou critérios de aceite, **o plano central prevalece**. Trechos legados contraditórios estão **SUPERSEDED**, não são perguntas abertas nem instruções para implementar. Regras UX não conflitantes continuam válidas. `G1_ARCHITECTURE_DECISION_REQUIRED / TEST_NOT_RUN`.


> **REGRA FINAL DO PO — ADR-04 (2026-11-13; substitui todas as interpretações anteriores):** a bandeira é única por produto/alvo e propaga-se às revisões enquanto **OPEN**. Se **RESOLVED durante V4**, aparece em **V4 como RESOLVED** (verde), mas **não aparece em V5 em diante**. Se **REMOVED durante V4**, **não aparece nem em V4 nem nas posteriores**. V3 preserva OPEN nos dois cenários. O evento registra `revisionContext=V4`, instante, autor e operação; resolução/remoção não cria versão técnica. A ficha corrente da V4 reflete imediatamente resolução/remoção; versões anteriores preservam seu estado. Histórico de eventos continua auditável, inclusive após desaparecimento da bandeira. **A revisão de resolução é a revisão vigente quando ocorre a ação, e não uma revisão nova.** Se houver reabertura, definir contrato separado, não supor comportamento retroativo. Especificação de persistência/projeção ainda depende de Coordination.

> **ATUALIZAÇÃO PO — 2026-11-13:** [Deliberações G1 do PO](./PRC-TRACK-G1-PO-DECISIONS-2026-11-13.md) **substituem** regras conflitantes deste baseline: (a) acompanhar campos registrados pela Engineering API, com proveniência/cobertura a definir em contrato; (b) **no-op não gera Vn**; (c) propagação visual de flag única por produto/alvo a cada versão sem clones de identidade; (d) HML API funcional antes do novo frontend. Demais disposições permanecem sujeitas a Coordination. Documento antigo preservado para rastreabilidade.

> **Data:** 2026-11-12  
> **Natureza:** decisões funcionais do Product Owner consolidadas em conversa; desenho técnico TARGET e gaps TO_INVENTORY.  
> **Status:** BUSINESS_RULES_DEFINED / ARCHITECTURE_DECISION_REQUIRED para confirmar ownership, contratos e mudanças persistentes. **Não autoriza migration, deploy ou implementação.**  
> **Owner proposto:** domínio PRC da Engineering API, sujeito a ratificação pela Coordination.  
> **Escopo:** somente evoluções processadas por solicitações PRC de criação/alteração; não é auditoria geral do TOTVS.

## 1. Intenção e limites

A Engenharia quer consultar o histórico de produtos que passaram por suas solicitações, incluindo quantas versões acompanhadas foram produzidas, quais campos/vínculos mudaram, de qual solicitação vieram e quais flags técnicas permaneceram abertas ou foram resolvidas ao longo do tempo.

- **TOTVS:** autoridade do cadastro oficial e dos valores consultados.
- **Engineering API / PRC:** autoridade proposta sobre o histórico de acompanhamento gerado por seus próprios workflows, não sobre o cadastro mestre TOTVS.
- **Solicitação:** registra o processo, correções, aprovações, flags e verificações.
- **Versão acompanhada:** snapshot do estado oficial observado na conclusão validada, vinculado à solicitação; não é sinônimo de revisão nativa do TOTVS.
- **Flag:** sinalização técnica persistente, com identidade própria e alvo de produto/campo/vínculo; atravessa versões sem duplicação.

**Fora do escopo:** monitorar, bloquear, reconstruir ou atribuir modificações feitas diretamente no TOTVS. Se um snapshot oficial observado contiver diferenças externas, elas não devem ser apresentadas como mudanças causadas pela PRC; o diff atribuído à Engenharia deriva da solicitação e de sua verificação.

## 2. Regras de negócio decididas

| ID | Regra |
|---|---|
| PRC-TRACK-01 | Somente o fluxo de conclusão autorizado de uma solicitação PRC de criação/alteração pode disparar registro de versão acompanhada. |
| PRC-TRACK-02 | Criação exige o código oficial informado/validado pelo fluxo PRC existente; alteração exige verificação campo a campo das mudanças no TOTVS, conforme os contratos existentes. Falha ou divergência bloqueia a conclusão e a versão. |
| PRC-TRACK-03 | Após conclusão validada, consultar a fonte oficial e registrar os atributos/vínculos efetivamente observáveis, com cobertura e proveniência. Não completar campos ausentes com valores presumidos do draft. |
| PRC-TRACK-04 | Identidade do produto acompanhado: fonte oficial + código oficial estável; usar identidade interna de acompanhamento e não assumir que o código isolado é globalmente único. |
| PRC-TRACK-05 | Se já houver produto acompanhado, publicar nova revisão imutável; se não houver, iniciar acompanhamento com V1, inclusive quando a primeira PRC observada for de **alteração**. |
| PRC-TRACK-06 | Baseline anterior eventualmente capturado é referência observada, não versão fictícia do histórico. V1 significa primeira versão **acompanhada pela Engenharia**, não nascimento do produto no ERP. |
| PRC-TRACK-07 | Numeração sequencial por produto acompanhado; revisão publicada é imutável e possui solicitação de origem, evidência oficial, snapshot, diff, timestamps e esquema versionado. |
| PRC-TRACK-08 | Devolução, rejeição, correções intermediárias e verificação falha não criam versão consolidada. Reexecução idempotente da mesma conclusão não duplica revisão. |
| PRC-TRACK-09 | Conclusões concorrentes do mesmo produto exigem serialização/CAS e revalidação; uma solicitação não pode sobrescrever silenciosamente atributos confirmados por outra. |
| PRC-TRACK-10 | O histórico de solicitações é distinto do histórico de versões do produto; não transformar cada edição intermediária em versão. |
| PRC-FLAG-01 | A flag é transversal ao produto: um único registro lógico permanece associado ao alvo técnico entre V3, V4, V5 etc., até transição autorizada de estado. Não copiar flags por versão. |
| PRC-FLAG-02 | Alvos: campo técnico (FIELD/path) ou vínculo fornecedor-produto (SUPPLIER_LINK + identidade estável do vínculo + atributo, p.ex. partNumber/catalogNumber). |
| PRC-FLAG-03 | Uma alteração posterior do campo não resolve automaticamente a flag; o responsável autorizado deve resolver/cancelar com trilha auditável. |
| PRC-FLAG-04 | Preservar eventos de criação, atualização, resolução, reabertura e exclusão lógica/cancelamento conforme contrato vigente; nunca apagar histórico para limpar a tela. |
| PRC-FLAG-05 | Consultar separadamente **flags atuais** do produto e **estado histórico** das flags na data/corte de uma versão. Resolução futura não reescreve o passado. |
| PRC-FLAG-06 | Uma flag de fornecedor não existe em versões anteriores à existência do alvo; se o vínculo for removido, preservar histórico e sinalizar alvo inativo, sem transferir automaticamente a outro fornecedor. |
| PRC-FLAG-07 | Em criação ainda sem código oficial, flags podem nascer no contexto da solicitação e devem ser vinculadas à identidade oficial confirmada sem perder ID e trilha. |
| PRC-FLAG-08 | Flags de solicitações anteriores podem continuar visíveis no produto e em solicitações posteriores, segundo autorização e alvo, sem serem recriadas. |
| PRC-FLAG-09 | Regra de uma flag OPEN por alvo deve ser conciliada com unicidade atual por solicitação antes de mudar schema; não presumir equivalência. |

### Semântica de publicação CONFIRMED

O gatilho funcional é a **conclusão PRC que já passou pelas validações oficiais**. O registro histórico deve usar a leitura oficial disponível após essa conclusão, respeitando atomicidade, falha recuperável e idempotência. Um HTTP 200 isolado não substitui as validações existentes. Não criar um segundo mecanismo de aprovação nem tentar controlar alterações externas no ERP.

Para criação: exigir identidade/código oficial validado. Para alteração: preservar a verificação campo a campo e operações de fornecedor já existentes. Se a leitura necessária ao snapshot falhar após a conclusão, registrar pendência recuperável de materialização histórica, **não** fabricar versão e **não** desfazer indevidamente a conclusão já efetivada. A política exata de retry e atomicidade é decisão de contrato/implementação.

Uma conclusão confirmada sem mudança técnica efetiva deve preservar seu registro de processo; política de produzir ou não nova versão em casos no-op fica **TO_DECIDE** conforme semântica real do PRC.

## 3. Flags: identidade, tempo e conflitos

A identidade da flag não é o número da versão. A chave técnica precisa identificar produto, alvo e, no caso de fornecedor, o vínculo exato; não usar nome do fornecedor nem índice de lista. A flag mantém ID próprio e histórico de estados.

Exemplo: produto 10080025, fornecedor código F001/loja 01, atributo partNumber. V1/V2 sem vínculo: nenhuma flag nesse alvo. V3 inclui o vínculo e abre a flag. V4 altera descrição: **a mesma flag** permanece aberta. V5 altera classificação: a flag continua. Resolução após V5 não altera a fotografia histórica de V3–V5.

Distinguir:
1. **Estado atual:** flags OPEN/RESOLVED e alvo atual do produto.
2. **Estado em uma versão:** flags existentes e seu estado no instante/corte daquela versão, reconstruídos por eventos auditáveis ou projeção histórica equivalente.
3. **Contexto de origem:** solicitação/revisão na qual a flag nasceu, sem limitar sua duração àquela solicitação.

Se o campo/Part Number for alterado, a flag permanece até revisão explícita. Se o fornecedor for removido, não excluir a flag nem afirmar que seu alvo segue ativo. Definir ação governada de resolução/cancelamento e motivo. Se a flag for criada antes de haver código oficial, sua vinculação posterior precisa ser idempotente e auditável.

**Ponto de compatibilidade importante:** o contrato D16 atual permite flags mutáveis após conclusão/rejeição e usa `FIELD`, `SUPPLIER_LINK`, `OPEN`, `RESOLVED` e soft-delete. Sua `targetKey` é única **por solicitação**, não necessariamente por produto. Portanto, a transversalidade entre solicitações/versões é uma **evolução TARGET**, não comportamento comprovado. Não substituir esse modelo sem migração, compatibilidade, auditoria e decisão de owner. `GENERAL` é legado, sem novas criações contextuais.

## 4. Inventário já identificado no repositório (evidência de código, não runtime)

- `api-delpi/migrations/plugins/engineering/V012__product_registration_core.sql` já define `engineering.product_registration_records` (chave única `official_source, official_product_code`), `product_registration_revisions` (snapshot, changes, request_id, official_evidence_id, revision_number), `product_registration_verifications` e eventos append-only. **Não criar tabelas duplicadas antes de inventariar persistência/uso real.**
- `engineering-api/engineering_app/domain/product_registration/flags.py` define alvos `FIELD` e `SUPPLIER_LINK`; identidade de vínculo por `supplierCode` + `store` e atributo `partNumber`/`catalogNumber`; `FLAG_MUTATION_AFTER_TERMINAL=True`; `OPEN`/`RESOLVED`; soft-delete auditável; `GENERAL` legado.
- `engineering-api/engineering_app/domain/product_registration/baseline.py` expõe baseline oficial com `fields[path]={value, officialField, present}`, `links`, `linksComplete`, `fingerprint` e proveniência. Não interpretar `present=false` como valor vazio confirmado.
- Os contratos atuais de criação, alteração, verificação e conclusão precisam ser auditados no service/repository antes de afirmar que toda conclusão já materializa revisão, ou que todo atributo do snapshot está confirmado.

Classificação: estruturas e contratos citados **PROVEN no código**; sua aplicação em banco/deploy e cobertura E2E **TO_INVENTORY**. Transversalidade de flags e consulta histórica de produto **TARGET**.

## 5. Modelo lógico preferencial (sujeito ao Abstraction Gate)

Reutilizar prioritariamente `product_registration_records` e `product_registration_revisions` existentes para identidade e snapshots imutáveis. Reutilizar verificações e ledger PRC para evidências e causalidade. Para flags, avaliar evolução do modelo D16 com identidade de produto/alvo, vínculo opcional à solicitação de origem e histórico de transições, sem duplicar registro por revisão. Uma projeção de flags atuais pode ser derivada do ledger; escolher persistência adicional apenas se houver requisito real.

Invariantes de banco/serviço a validar: unicidade (fonte,código); (record_id,revision_number); idempotência por confirmação/solicitação; CAS/lock de versão; integridade da evidência; autorização de leitura por produto e escrita de flags; audit trail; transação local e publicação pós-commit; backfill seguro de flags legadas e produtos já acompanhados.

Não assumir que `row_version` da solicitação, `revision_number` do produto e revisão oficial TOTVS sejam a mesma coisa.

## 6. Contratos e segurança a definir antes da implementação

Definir owners, consumers, DTOs, erros, paginação, versionamento, compatibilidade, idempotência, observabilidade e limites para:
- obter produto acompanhado por fonte+código;
- listar versões e consultar snapshot/diff de revisão específica;
- listar flags atuais e estado histórico no corte da versão;
- criar/atualizar/resolver/cancelar flag por alvo técnico com AuthZ live;
- associar flag de criação pré-código ao produto confirmado;
- registrar versão após conclusão PRC, com retry seguro.

Keycloak autentica; Core governa RBAC; Engineering API aplica autorização backend-first e por objeto; Portal e EVA apenas consomem contratos. Não incluir dados oficiais completos no WebSocket; usar invalidação e refetch autorizado. Não expor segredos, dumps ou dados sensíveis em evidências.

## 7. Casos críticos de aceite futuros

1. CREATE concluída e validada gera V1; tentativa repetida não gera V2.
2. UPDATE concluída de produto já acompanhado gera versão seguinte e diff atribuível à PRC.
3. UPDATE concluída de produto ainda não acompanhado gera V1 e baseline de entrada distinguível.
4. Falha de verificação TOTVS bloqueia conclusão/versão; leitura pós-conclusão indisponível gera pendência recuperável.
5. Concorrência de duas PRCs no mesmo produto não perde mudança nem duplica revisão.
6. Flag FIELD aberta em V3 continua a mesma em V4/V5; histórico de V3 permanece OPEN após resolução posterior.
7. Flag SUPPLIER_LINK usa fornecedor+loja+atributo; vínculo removido preserva histórico sem fingir alvo ativo.
8. Flag criada antes de código oficial é associada uma vez ao produto confirmado.
9. Flags antigas D16 seguem legíveis; migração preserva IDs, autores, estados e auditoria.
10. Usuário sem acesso não lê snapshots/flags nem muta estados; WebSocket não contorna AuthZ.
11. Nenhuma diferença externa ao escopo PRC é atribuída automaticamente à solicitação.

## 8. Pendências para Coordination (ARCHITECTURE_DECISION_REQUIRED)

- Ratificar owner e boundary da continuidade das flags por produto, hoje centradas na solicitação.
- Confirmar uso efetivo de records/revisions existentes e decidir se há lacuna real de schema.
- Definir transição de flags entre solicitação pré-código e produto confirmado; política de unicidade OPEN por alvo/produto e compatibilidade D16.
- Definir corte temporal do estado histórico, reabertura, soft-delete e alvo removido.
- Definir política no-op, concorrência, retries e recuperação de materialização pós-conclusão.
- Validar contratos de leitura TOTVS, cobertura do snapshot e verificação de fornecedor.
- Inventariar componentes de ficha técnica PRC, contratos e permissões antes do reuso; validar a UX TARGET descrita na seção 9, sem presumir backend transversal implementado.

**Nenhuma decisão acima autoriza modificar código, banco, frontend ou infraestrutura nesta fase.**

## 9. Jornada frontend consolidada — UX TARGET (2026-11-12)

### 9.1 Entrada única na ferramenta

- Preservar **Controle e Cadastro de Produtos** como uma única ferramenta/rota de entrada do Portal Engenharia, sem novo aplicativo nem segunda top bar.
- Um **hero único** contém o seletor segmentado **Solicitações | Produtos acompanhados**. Alternar o contexto troca filtros e conteúdo abaixo do hero, sem duplicar cabeçalhos ou navegação global.
- **Solicitações** preserva fila, ações, filtros, tabela/cards/kanban e fluxo PRC existentes. **Produtos acompanhados** apresenta somente produtos efetivamente registrados no acompanhamento da Engineering API, nunca o catálogo inteiro TOTVS.
- A lista de acompanhados usa padrão visual da tabela do Catálogo de Produtos, uma linha por produto (fonte + código), com descrição da versão acompanhada, número da última versão, flags abertas e última evolução conforme contratos e autorização. Não oferecer cadastro manual paralelo de produto acompanhado.
- Clicar no produto abre detalhe próprio de acompanhamento; preservar rotas/deep links do Catálogo de Produtos e das solicitações. Roteamento concreto: TO_INVENTORY/TARGET.

### 9.2 Detalhe: somente Ficha técnica e Versões

- **Hero do produto:** código oficial, descrição identificadora e identificação inequívoca da versão acompanhada. Não confundir versão de acompanhamento com revisão oficial TOTVS.
- **Ficha técnica:** reaproveitar o **padrão funcional da ficha das solicitações PRC**, não apenas a aparência. Mostrar atributos em **cards por seções técnicas** (p.ex. Identificação e classificação; Estoque e contabilidade), com **fornecedores em tabela** e seus atributos. Evitar abas próprias de fornecedores ou flags, e evitar card separado de “flags abertas”.
- **Flags integradas:** bandeira junto ao label/campo ou célula/atributo de fornecedor, com descoberta por hover **e acesso por foco/teclado/toque**. Bandeira vermelha indica acompanhamento aberto; resolvida usa semântica/legenda do componente PRC existente. Preservar o padrão atual de modal/detalhe de bandeira com título, descrição, alvo e valor contextual, sem tornar o valor técnico editável por esse modal.
- **Acompanhamento técnico:** se reutilizada, a faixa discreta de resumo/legenda já presente na solicitação pode auxiliar a localização das bandeiras; não criar um card adicional nem duplicar informações por campo.
- **Versões:** listar cronologicamente V1…Vn, data, solicitação de origem e mudanças confirmadas; permitir abrir a ficha de uma versão e comparar **quaisquer duas versões**, inclusive não consecutivas, por diferenças estruturadas de campos e vínculos. Separar eventos de flags de diferenças do cadastro oficial.
- A ficha permite selecionar uma versão. Dados técnicos exibidos são sempre o **snapshot imutável daquela versão**, com indicação explícita de consulta histórica. Não substituir silenciosamente dados antigos pelo estado atual TOTVS. Links entre versão e solicitação de origem devem ser bidirecionais quando autorizados.

### 9.3 Operação das flags a partir do produto acompanhado

- A ficha do produto **não permite editar diretamente dados técnicos oficiais ou snapshots**. Entretanto, usuários autorizados podem **criar, consultar, resolver e reabrir flags** diretamente no campo/alvo do produto, mesmo após a solicitação de origem ter sido concluída. Cancelamento/soft-delete e demais transições seguem contrato governado, com trilha auditável.
- Ação sobre flag altera o acompanhamento técnico e **não cria nova versão Vn+1** do produto. Versão nova resulta somente da conclusão PRC confirmada segundo seção 2.
- Uma flag OPEN já existente no mesmo produto/alvo deve ser **reutilizada e apresentada para tratamento**, não duplicada. Garantir unicidade no backend de forma concorrente/idempotente; frontend não é autoridade para prevenção de duplicatas.
- Flag de fornecedor deve apontar para **vínculo estável fornecedor + loja + atributo** (p.ex. partNumber), não para posição na tabela. Se o vínculo deixar de existir na versão atual, conservar trilha e evitar oferecer criação sobre alvo inexistente.
- Ao consultar a **última versão**, mostrar flags atuais nos campos correspondentes. Ao consultar **versão histórica**, mostrar as flags existentes e seus estados **no corte daquela versão**, com acesso explícito ao estado atual e ao histórico de transições. Resolução posterior não deve reescrever a bandeira histórica.
- **Regra UX proposta:** criação de flag nova somente na última versão acompanhada, após validar existência atual do alvo; em versões antigas, permitir consulta histórica e navegação para a flag atual antes de qualquer mutação. Exigir ratificação de contrato/owner para a política exata de mutações a partir de vistas históricas.
- Se o mesmo alvo estiver sinalizado em uma solicitação aberta e no produto acompanhado, apresentar a **mesma identidade lógica** da flag e refletir mudanças autorizadas em ambas as experiências; resolver conflitos por estado atual/versão de concorrência, não por sobrescrita do cliente.
- Respeitar RBAC Core, AuthZ live da Engineering API e permissão por objeto em leitura e escrita; não inferir autorização pelo hover, visibilidade do botão, JWT isolado ou socket. Em mudanças concorrentes, retornar conflito tratável e reconciliar a tela sem perder entradas do usuário.

### 9.4 Reuso técnico e limites

- Inventariar componentes reais de cards, campos sinalizáveis, tabela de fornecedores, modal, legenda e histórico das flags usados no PRC antes de extrair ou criar abstrações. Preferir reuso por contratos de apresentação; não acoplar bounded contexts nem importar lógica privada de outro aplicativo.
- Fonte de dados de **Solicitações** continua sendo os contratos PRC; fonte de **Produtos acompanhados** é o histórico versionado governado da Engineering API. O Catálogo TOTVS não se torna a fonte do histórico acompanhado.
- Contratos de leitura devem expor snapshot por versão, alvos sinalizáveis, flags no corte temporal, flags atuais e histórico de transições. Contratos de escrita devem aplicar autorização, unicidade por produto/alvo, idempotência, conflito de concorrência e auditoria.
- O estado desta seção é **TARGET funcional**, não prova de implementação. A transversalidade de flags e a materialização versionada permanecem sujeitas ao inventário e à decisão arquitetural das seções 4–8.

### 9.5 Critérios de aceite frontend futuros

1. Alternar Solicitações/Produtos acompanhados no hero não duplica top bar, não perde rotas existentes e apresenta filtros próprios.
2. Listagem de acompanhados exclui produtos sem histórico Engineering API e não duplica linha por versão.
3. Ficha usa cards técnicos e fornecedores em tabela no padrão PRC; flags aparecem nos alvos, sem card separado.
4. Hover, teclado e toque permitem acessar flag; modal reutiliza contexto, título, descrição e ações permitidas.
5. Usuário autorizado cria/trata flag no produto após encerramento da solicitação, sem alterar snapshot ou criar nova versão.
6. Flag OPEN preexistente no mesmo alvo abre tratamento da mesma flag, sem duplicação, inclusive sob concorrência.
7. Trocar V5 por V3 altera valores técnicos para o snapshot V3 e mostra flags no corte V3; estado atual é identificável separadamente.
8. Comparar V1 com V5 ou V4 com V5 mostra somente diferenças reais entre snapshots, com fornecedores identificados por vínculo.
9. Flags em fornecedores removidos permanecem consultáveis historicamente, sem aparentar vínculo ativo.
10. Usuário sem autorização não consulta/muta flags; testes cobrem conflito, acessibilidade, navegação e regressão PRC.

**Status da seção:** UX_RULES_DEFINED / TARGET; sem autorização para migration, implementação ou deploy. Mudança de owner/authority segue ARCHITECTURE_DECISION_REQUIRED.
