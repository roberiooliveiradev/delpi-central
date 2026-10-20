# 48 — DESIGN TARGET | Rotas de Baixas R01/R02 — PROC-0072

> 20/10/2026 — DOCUMENTATION / PROPOSED / DECISION_REQUIRED. **Sem GO de runtime**. Fonte: TÉO PROC-0072, docs 03/21/45/46/47, resultados DAVI em 20/10/2026; vídeo analisado indiretamente pelo NotebookLM, não homologado. FINSV010/FINR190 padrão TOTVS não prova equivalência da customização DELPI `_F190C`.

## 1. Objetivo e arquitetura

Disponibilizar leitura de eventos efetivos de **baixas a pagar (R01)** e **baixas a receber (R02)**, com filtros, resumo e tabela de detalhe para conferência por competência. Os cinco arquivos relatados por Joici (Pagar XLS/PDF data/PDF natureza; Receber XLS/PDF data) são **saídas informadas verbalmente**, não exportações observadas. A primeira etapa proposta é JSON read-only; exportação fica em gate separado.

- **api-delpi**: owner da consulta, joins e regras financeiras Protheus (Clean Architecture, ports/adapters). Contrato tipado dedicado; nunca usar `POST /data/sql` como API produtiva do Portal.
- **controllership-finance-api**: BFF owner de composição do Portal, authorization por effective permissions Core **AND** resource_scope/ownership **AND** business rule; fail closed. `access` para leitura; não criar novas permissions.
- **MFE**: consome exclusivamente `/apps/controllership-finance-api`; nenhuma consulta direta a api-delpi.
- **Boundaries**: este projeto de rotas não autoriza a página P1, competência persistida ou exportações. Doc 45 §15 mantém P1 NO-GO.

## 2. Inventário físico e evidências de chave

| Função | Tabela | Colunas documentadas (candidatas para DTO) |
|---|---|---|
| Fato de baixa a pagar | `FK2010` | `FK2_IDFK2, FK2_IDDOC, FK2_DATA, FK2_VALOR, FK2_MOEDA, FK2_NATURE, FK2_TPDOC, FK2_RECPAG, FK2_SEQ, FK2_FILIAL, FK2_HISTOR` |
| Fato de baixa a receber | `FK1010` | `FK1_IDFK1, FK1_IDDOC, FK1_DATA, FK1_VALOR, FK1_MOEDA, FK1_NATURE, FK1_TPDOC, FK1_RECPAG, FK1_SEQ, FK1_FILIAL, FK1_HISTOR` |
| Ponte para título | `FK7010` | `FK7_IDDOC, FK7_ALIAS, FK7_FILTIT, FK7_PREFIX, FK7_NUM, FK7_PARCEL, FK7_TIPO, FK7_CLIFOR, FK7_LOJA, FK7_FILIAL` |
| Título a pagar | `SE2010` | `E2_PREFIXO, E2_NUM, E2_PARCELA, E2_TIPO, E2_FORNECE, E2_LOJA, E2_NOMFOR, E2_EMISSAO, E2_VENCTO, E2_VALOR, E2_FILIAL` |
| Título a receber | `SE1010` | `E1_PREFIXO, E1_NUM, E1_PARCELA, E1_TIPO, E1_CLIENTE, E1_LOJA, E1_NOMCLI, E1_EMISSAO, E1_VENCTO, E1_VALOR, E1_FILIAL` |
| Natureza | `SED010` | `ED_CODIGO, ED_DESCRIC, ED_FILIAL` |
| Motivo | `F7G010` | `F7G_SIGLA, F7G_DESCRI` |
| Rastreamento | `FKA010` | `FKA_IDPROC, FKA_IDORIG, FKA_TABORI, FKA_FILIAL` |
| Banco | `FK5010` | `FK5_IDMOV, FK5_DATA, FK5_VALOR, FK5_BANCO` |
| CNPJ / identificação legal | `SA1010/SA2010` | **TO_INVENTORY** — campo, necessidade e projeção restrita não confirmados |

**Provas SQL READ (20/10):** FK2 8.969 eventos e FK1 5.578 a partir de 2026-01-01; `EXISTS(FK7)` FK2 8.911, FK1 5.578; `EXISTS(FK7→SE2)` 8.911, `EXISTS(FK7→SE1)` 5.578. FK2 58 sem ponte FK7 e 49 sem natureza SED. FK7→SE1 histórico 12 sem título nos filtros usados. `FKA_IDORIG` isolado não comprova join de negócio: exigir `FKA_TABORI` + contexto. Índices SIX não são constraints DB. Filial vazia nas linhas de amostra demanda política de compartilhamento; **não assumir `branch=01/02`**. Probes não provam paridade com `_F190C`.

## 3. Rotas candidatas — ainda não congeladas

| Owner | Método/path TARGET PROPOSED | Função |
|---|---|---|
| api-delpi | `GET /financeiro/baixas/pagar` | Detalhes paginados de eventos FK2 |
| api-delpi | `GET /financeiro/baixas/receber` | Detalhes paginados de eventos FK1 |
| api-delpi | `GET /financeiro/baixas/resumo` | Totais por lado/moeda/natureza e métricas de qualidade |
| CF BFF | `GET /closing/financial-settlements` | Fachada com `side=payable\|receivable` |
| CF BFF | `GET /closing/financial-settlements/summary` | Resumo com escopo resolvido no Core |
| CF BFF | `GET /closing/financial-settlements/exports` | **DEFERRED** — não implementar neste slice |

A BFF jamais faz SELECT SQL diretamente. Conectar via client/adapter HTTP tipado, autorizado S2S, com contratos e tratamento de erros. Api-delpi mantém owner dos relacionamentos TOTVS. Padrão técnico existente inspecionado: `api-delpi/app/interface/http/routes/financeiro/inadimplencia_router.py` e `despesas_centro_custo_router.py` (FastAPI APIRouter, composition/use case, DTO e gates). Antes da implementação, confirmar padrão vigente no HEAD, producer/consumer e contratos OpenAPI.

## 4. Parâmetros sugeridos

| Parâmetro | Regra candidata |
|---|---|
| `start_date`, `end_date` | Obrigatórios `YYYY-MM-DD`, intervalo inclusivo para eventos `FKx_DATA`; limites máximos e timezone a decidir |
| `side` | `payable` ou `receivable` somente na BFF |
| `company_code` / `branch_code` | Obrigatórios conforme scope resolvido, **mapeamento empresa 01/03/04 vs Protheus TO_INVENTORY** |
| `nature_code` | Filtro opcional por natureza, caso homologada |
| `sort_by` | `settlement_date\|nature`, com desempate estável pelo ID do evento |
| `sort_dir` | `asc\|desc` |
| `page`, `page_size` | Paginação controlada; teto deve seguir padrões da plataforma |
| `competence` | Contexto apenas quando existir contrato de competência aprovado; não tratar texto do deep link como scope |

Sem fallback para período ilimitado, sem perda silenciosa de filtros de filial, sem aceitar `principal_type=service` como usuário humano na BFF. `D_E_L_E_T_=''` aplicado a todos os objetos Protheus; timestamps/frescor/erro tipados.

## 5. Campos do relatório JSON (TARGET CANDIDATE)

| Campo do contrato | Fonte candidata | Exibição | Risco |
|---|---|---|---|
| `settlementId` | `FK1_IDFK1/FK2_IDFK2` | ID interno oculto | PROVEN source |
| `settlementDate` | `FK1_DATA/FK2_DATA` | Data baixa | PROVEN source |
| `settlementAmount` | `FK1_VALOR/FK2_VALOR` | Valor evento | PROVEN source |
| `currencyCode` | `FKx_MOEDA` | Moeda (não somar moedas distintas) | Mapeamento display pendente |
| `natureCode`, `natureDescription` | `FKx_NATURE` + `SED` | Código/natureza | 49 exceções FK2 observadas |
| `documentNumber`, `prefix`, `installment`, `documentType` | `FK7` + `SE1/SE2` | Título | Prova de existência, join cardinality pending |
| `partyCode`, `partyStore`, `partyName` | `FK7` / `SE1/SE2` | Cliente/fornecedor | Dados de terceiros; scope + minimização |
| `partyTaxId` | cadastro SA1/SA2 | CNPJ para Aliança | TO_INVENTORY/PII — não expor por padrão |
| `issueDate`, `dueDate` | `SE1/SE2` | Emissão/vencimento | Necessidade no relatório a confirmar |
| `history`, `movementType` | `FK1/FK2` | Histórico/tipo | Códigos exigem dicionário |
| `bankReference` | `FK5/FKA` | Detalhe bancário | DEFERRED até semântica validada |
| `linkStatus` | regra de integridade | `resolved\|missing_document\|missing_nature\|unresolved_scope` (valores propostos) | Nunca suprimir gap automaticamente |

Linha base = **um evento FK1/FK2**, nunca somar `E1/E2_VALOR` como evento de baixa. `EXISTS` prova que registro relacionado existe, não define JOIN final. Não multiplicar valores por vínculo FKA ou por várias naturezas.

### Envelope ilustrativo — não é schema congelado

```json
{
  "report": "payable_settlements",
  "period": {"startDate": "YYYY-MM-DD", "endDate": "YYYY-MM-DD"},
  "scope": {"companyCode": null, "branchCode": null, "resolution": "pending"},
  "status": "partial",
  "totalsByCurrency": [],
  "quality": {"missingDocumentCount": null, "missingNatureCount": null},
  "pagination": {"page": 1, "pageSize": 50, "totalItems": null},
  "items": [{
    "settlementId": "<technical-id>",
    "settlementDate": "YYYY-MM-DD",
    "settlementAmount": "0.00",
    "currencyCode": "<ERP-code>",
    "natureCode": null,
    "documentNumber": null,
    "partyName": null,
    "linkStatus": "unresolved"
  }]
}
```

Valores monetários como strings decimais; agrupamentos por moeda. `status=partial` não pode ser fabricado: calculado de evidência real, e `HTTP 200` não equivale a relatório completo. Se o scope não resolver, **retornar erro de autorização**, não linhas com `resolution=pending` em runtime.

## 6. Apresentação sugerida para o consumidor

Tela do Portal (após gate de página) com abas **Baixas a Pagar** e **Baixas a Receber**, cabeçalho período/competência/empresa-filial explícitos, filtros data/natureza, cartões de quantidade/total por moeda/pendências documentais, tabela de **Data | Documento | Parcela | Cliente ou Fornecedor | Natureza | Valor | Moeda | Situação do vínculo**, ordenação e paginação. Estado loading/empty/partial/failed e aviso de fonte; exportação **indisponível até homologação**. UX PT-BR, mesmo chrome `@delpi/plugin-ui`, Help sincronizada e navegação por teclado. Não apresentar como FINR190 reproduzido até prova de paridade.

## 7. RQ/AC propostos

| ID | Critério objetivo |
|---|---|
| RQ-SET-01 | Separar fato pago/recebido de título em aberto e preservar ID de cada baixa |
| RQ-SET-02 | Expor somente campos de apresentação autorizados com data, valor, moeda, natureza e documento enriquecido |
| RQ-SET-03 | Filtros e paginação estáveis, datas validadas, sem carga aberta |
| RQ-SET-04 | Contar links não resolvidos e explicar exceções (58 sem FK7 e 49 sem SED no recorte auditado) |
| RQ-SET-05 | Autorização Core effective permissions + ownership + scope, fail closed; nenhuma permission por relatório |
| RQ-SET-06 | Paridade de contagem e centavos por moeda, período, empresa e variantes com saídas reais da `_F190C` |
| RQ-SET-07 | No data vs falha upstream vs dados parciais distintos, sem PASS inferido |
| RQ-SET-08 | Excel/PDF e CNPJ somente em gate futuro de layout, privacidade e integração contábil |

Testes requeridos (TEST_NOT_RUN): positivo por lado/intervalo, sibling por competência/filial, negativo sem ACCESS/sem scope/Core 503, principal de serviço, data inválida e intervalo amplo, títulos sem FK7/natureza, múltiplas moedas, filial compartilhada, joins sem duplicação, paginação determinística, upstream timeout, OpenAPI/DTO/BFF contract tests, smoke real, paridade PDF/XLS somente depois.

## 8. DECISION_REQUIRED e gates

1. **D1 — Endpoints/boundary**: proposta separada api-delpi + fachada BFF unificada; owner precisa confirmar nomes/contrato e consumidores.
2. **D2 — Faseamento**: recomendar JSON read-only primeiro; PDF/XLS como entrega posterior (não substitui os cinco arquivos da Aliança).
3. **D3 — Escopo**: empresa 01/03/04 vs filial 01/02, compartilhamento e contrato Core T05. **STOP** sem resolução.
4. **D4 — Semântica de exceções**: tipos BA/ES/VL/CP, 58 sem FK7, 49 sem natureza: inclusão/omissão exige decisão owner financeiro, não automatizar.
5. **D5 — Fidelidade ao legado**: confirmar código ADVPL da `_F190C` ou cinco arquivos reais sanitizados, colunas, filtros e campos CNPJ. Sem isso declarar relatório novo TARGET, jamais substituto validado.

**Status:** `DESIGN_DRAFT=READY_FOR_PO_REVIEW`; `ENDPOINTS/DTO=TARGET_PROPOSED`; `R01/R02_G4=PENDING`; `G5=TEST_NOT_RUN`; `G6=PENDING`; `IMPLEMENTATION_AUTHORIZED=NO`; `RUNTIME_CHANGED=NO`; `IMP-08/P1=NO_GO`.

**Plano após decisão e GO expresso:** revalidar HEAD/working tree, .cursor aplicável, framework/consumers; congelar DTO/OpenAPI; implementar producer na api-delpi com mínima diff, testes; integrar BFF com escopo Core; validar contratos e resultset; gate MFE/Help posterior; paridade com exportações; evidência + revisão + SHA. Nunca scaffold de arquitetura paralela por conveniência.

## 9. Decisões do PO — 20/10/2026 (sobrepõem propostas anteriores nos itens indicados)

**D1 APPROVED — padrões:** novas rotas em inglês, padronizadas e isoladas no contexto financeiro de baixas da api-delpi. Pode reutilizar padrões estruturais de inadimplência/despesas, sem misturar ownership/dados/DTOs de outro Portal. Naming final ainda requer conferência com o HEAD antes de congelar caminhos.

**D2 APPROVED — ordem e UI:** primeira entrega API JSON read-only com testes/validações; depois BFF própria do Portal; depois frontend visual. **Sem exportação Excel/PDF**, inclusive como meta de entrega deste recorte. A UI visual apresenta informações do novo contrato.

**D3 APPROVED como invariante de produto, não como implementação de mapeamento:** isolamento por filial (01, 02 e demais autorizadas/existentes); uma coluna de filial vazia não significa escopo global. **MAPPING/ENFORCEMENT=PENDING**: owner ERP/Core deve provar tabela compartilhada, regra filial origem/título, chave empresa↔filial e escopo autorizado. Sem isso, não executar endpoint que exponha dados de outras filiais. Se necessidade de decisão material persistir, retornar DECISION_REQUIRED.

**D4 PENDING:** seleção de tipos BA/ES/VL/CP e totais oficiais precisa evidência/decisão do owner financeiro. Primeira versão pode ter campo de tipo e qualidade, mas não pode presumir significado/inclusão oficial. Não promover um relatório financeiro oficial que some movimentos sem classificação aceita.

**D5 DEFERRED:** ausência de fonte _F190C/cinco arquivos **não bloqueia novo relatório operacional visual**. Paridade com legado opcional futura, fora do aceite do primeiro backend. A descrição do produto não deve alegar equivalência.

**GATE revisado:** `PRODUCT_DIRECTION=APPROVED`; `EXPORTS=OUT_OF_SCOPE`; `ROUTINE_PARITY=DEFERRED`; `D3_ENFORCEMENT=TO_INVENTORY`; `D4_CLASSIFICATION=DECISION_REQUIRED`; `ENDPOINT_CONTRACT=TARGET_PROPOSED`; `IMPLEMENTATION_AUTHORIZED=NO` até contrato e controles transversais efetivamente fechados. Uma autorização genérica para começar backend não dispensa fail-closed por recurso/filial ou definição de totais por tipo.

**Próximo cursor gate:** revalidar HEAD/status, .cursor, contratos de API, prova de scope/filial e semântica D4; propor subset mínimo com detalhes por baixa sem totais oficiais até aceitação do owner. Então solicitar GO explícito para runtime api-delpi somente.

## 10. Probe DAVI — distribuição de filiais nas fontes financeiras (20/10/2026)

**EXECUTADO / SQL READ via DAVI**: GROUP BY da filial, incluindo somente D_E_L_E_T_=''. Resultado exaustivo de grupos retornados no ambiente consultado:

| Fonte | Coluna | Grupo retornado | Quantidade |
|---|---|---|---:|
| SE2010 | E2_FILIAL | vazio | 120377 |
| SE1010 | E1_FILIAL | vazio | 115558 |
| FK2010 | FK2_FILIAL | vazio | 128057 |
| FK1010 | FK1_FILIAL | vazio | 108849 |
| FK7010 WHERE FK7_ALIAS='SE1' | FK7_FILTIT | vazio | 114634 |
| FK7010 WHERE FK7_ALIAS='SE2' | FK7_FILTIT | vazio | 96454 |

**Achado crítico / EXECUTION_DRIFT da hipótese de campo portador:** COALESCE(FK7_FILTIT, E1_FILIAL/E2_FILIAL) não discrimina filial; todas as opções amostradas e agora agregadas são vazias. Isso **não prova** que o ERP não possua separação empresarial: pode depender de schema/base, compartilhamento do Protheus, contexto de empresa, outro atributo ou política. NÃO aplicar branch=all ou interpretar vazio como filial 01. Filial/empresa autorizadas devem vir de fonte e contexto comprovados, com fail-closed.

**D3 ENFORCEMENT=BLOCKED** até localizar portador físico ou contexto de conexão/empresa, verificar domínio de todas as filiais e contrato de autorização. Não implementar acesso por filial, nem autorizar rotas com dados financeiros indiscriminados. **D-PERM=DECISION_REQUIRED**: permissões api-delpi requerem aprovação/contrato próprios e não ampliam os dois codes do Portal. D4 mantém classificação oficial PENDING. **GO_RUNTIME=NO**, apesar de paridade _F190C deferida para nova consulta visual.

**Próximo inventário delimitado:** owner ERP/infra e api-delpi verifiquem o contexto de conexão do SQL Server, bancos/esquemas por empresa, regra de compartilhamento SX2 e código de extração dos relatórios financeiros existentes. Reapresentar como matriz empresa de negócio → tenant/base/schema/contexto → filial autorizada → query scope, com testes cross-branch positivos e negativos. Se separação não estiver representável em dados ou contexto, STOP e solicitação de decisão de arquitetura.

## 11. Decisão D3.1 — filial nullable sem inventar scope (20/10/2026)

**Manifestação expressa do PO:** continuar o desenvolvimento das rotas JSON da api-delpi, manter a informação de filial no contrato mesmo quando não preenchida pela fonte; adiar o tratamento de preenchimento/visualização confiável de filial. **Não autoriza interpretar vazio como acesso a todas as filiais**, tampouco aprova bypass de autorização entre filiais.

### Contrato de representação — APPROVED

- O campo de resposta `branchCode: string | null` é obrigatório no schema e **nullable**. Na falta de identificação confiável, retornar `null`, nunca `"01"`, `"02"`, `"all"` ou valor inventado.
- Opcionalmente `branchResolution: "resolved" | "unresolved"` em DTO, sujeito a ajuste nos contracts do HEAD; se houver `unresolved`, a origem deve ser transparente e o UI não deve rotular a filial como conhecida.
- Manter a coluna física `*_FILIAL` intacta; nenhuma migração, preenchimento artificial, alteração na origem TOTVS ou inferência por `COALESCE` de campos que são vazios.
- A futura BFF/MFE poderá apresentar "Filial não identificada" e disabilitar filtro inconclusivo; não construir tela neste gate.
- A decisão **não revoga a segregação de filial como princípio**; resolve apenas formato de resposta e permite trabalho isolado de backend.

### Separação técnica — enforcement ainda pendente

- As probes de 20/10/2026 encontraram apenas filial vazia em `FK1,FK2,SE1,SE2,FK7_FILTIT`. Logo, nenhuma dessas colunas constitui, por si, base de autorização de recurso/filial. Distinção: `branchCode=null` **não é prova de scope autorizado**.
- Implementação de camadas **internas** e de contratos pode avançar após GO do slice: DTO, validação, consultas de leitura e testes isolados. **Publicação ou habilitação de rotas que entreguem linhas reais deve permanecer fail-closed** quando não existir escopo autorizado comprovado — a permissão HTTP isolada não o substitui.
- Em particular, não executar consulta global sob `branch=all`, não usar o bypass de `/data/sql`, não assumir que `BranchAccessGate` existente resolva compartilhamento SQL, não criar permission por filial no Portal.
- Se for demonstrado isolamento por base/schema/conexão autorizada (ou contrato explícito de dataset compartilhado para audiência autorizada), documentar prova e testes negativos cross-branch antes de habilitar rotas; caso contrário manter consultas reais inacessíveis externamente, com resultado tipado de scope indisponível.

### Produto, movimento e release

- D1: rotas técnicas em inglês e contexto separado de outras features; nomenclatura candidata `GET /financeiro/settlements/payables`, `/receivables`, `/summary`. Congelar no gate técnico.
- D2: JSON somente leitura, backend api-delpi → testes/validações → BFF do Portal → MFE visual. **Excel/PDF fora do produto desta entrega**.
- D4: `movementType` e `paymentDirection` códigos crus, sem semântica inventada. A exibição exploratória pode ser planejada, mas totais oficiais, exclusões por tipo e quaisquer filtragens financeiras canônicas exigem aceite do owner financeiro. Não reclassificar BA/ES/VL/CP.
- D5: `_F190C` é referência opcional para paridade posterior, não bloqueador do relatório visual novo.
- **Permissões**: Portal mantém somente `controllership-finance.access` e `.manage`; capability própria da api-delpi fica `DECISION_REQUIRED` até owner de segurança definir, sem criação automática em runtime.

### Gate e escopo da próxima etapa

`D3_RESPONSE_SHAPE=APPROVED`; `BRANCH_ENFORCEMENT=TO_INVENTORY/PENDING`; `PRODUCT_BACKEND_FIRST=APPROVED`; `IMPLEMENTATION_AUTHORIZED=NO` para publicar endpoints com dados reais. **Próxima etapa autorizável:** inventory + definição de contrato/API e testes em isolamento, seguida de pedido de GO explícito para implementação mínima da api-delpi. Não confundir avanço de código com aceite de segurança nem com deploy.

**Aceites mínimos:** campo filial nullable testado; sem default para filial vazia; casos de missing FK7/SED não suprimidos; nenhuma duplicação; valores como Decimal; paginação; testes de AuthZ positivo/negativo e bloqueio de scope desconhecido; nenhuma BFF/MFE/exportação. Se os controles produzirem contexto comprovadamente autorizado, reapresentar evidências para desbloqueio de exposição.

## 12. Registro de implementação — S2S backend-first (20/10/2026)

Escopo executado: `controllership-finance-api → api-delpi → Protheus`, reutilizando o padrão S2S individual OAuth2 Client Credentials da plataforma (referência: `supplies-api`, commit `633390da`). Fora do escopo e não implementado: MFE/frontend, exportação Excel/PDF, paridade `_F190C`, migrações, grants produtivos.

### Rotas implementadas

| Camada | Rota | operationId | AuthN/AuthZ |
|---|---|---|---|
| api-delpi | `GET /financeiro/settlements/payables` | `get_financeiro_settlements_payables` | `require_s2s_service` estrito (cliente `controllership-finance-api`, scope `settlements.read`) + Bearer de usuário obrigatório |
| api-delpi | `GET /financeiro/settlements/receivables` | `get_financeiro_settlements_receivables` | idem |
| api-delpi | `GET /financeiro/settlements/summary` | `get_financeiro_settlements_summary` | idem |
| BFF | `GET /closing/financial-settlements` | `get_closing_financial_settlements` | `principal_type=="user"` + `controllership-finance.access` (effective permissions via Core) |
| BFF | `GET /closing/financial-settlements/summary` | `get_closing_financial_settlements_summary` | idem |

`side=payable|receivable` na rota de detalhe da BFF. Nenhum nome físico de tabela é exposto ao navegador.

### Controles aplicados

- **D3.1**: `branchCode: string|null` — `*_FILIAL` vazio rende `null` + `branchResolution:"unresolved"`; nenhum param `branch` aceito; nenhum fallback 01/02/all.
- **Fail-closed de dataset**: `SettlementScopeResolver` (port na application, composição em `financeiro_settlements_composer`) retorna `unresolved` enquanto não existir mecanismo de escopo comprovado → rota responde 403 `scope_unavailable`. Linhas reais nunca são servidas sem escopo autorizado.
- **D4**: `movementType`/`paymentDirection` são códigos crus; `officialTotals:false` permanente; summary agrupa por `side × currencyCode × natureCode × movementType`, nunca soma cross-moeda.
- **Dados**: FK1/FK2 fatos; LEFT JOINs auditados FK7→SE1/SE2 (composto SX9) e SED; `D_E_L_E_T_=''`; valores em string decimal; `linkStatus` preserva eventos sem vínculo (`missing_document`, `missing_nature`, `missing_document_and_nature`).
- **S2S**: `Authorization`=Bearer do usuário + `X-Delpi-Service-Authorization`=JWT client-credentials próprio da BFF; `X-Delpi-Caller-App` só telemetria; token legado compartilhado nunca autoriza; sem secrets em código/docs.

### Configuração necessária (nomes apenas — valores via .env/secret store)

- BFF `controllership-finance-api`: `DELPI_API_URL`, `DELPI_API_TIMEOUT`, `DELPI_API_CALLER_APP=controllership-finance-api`, `S2S_TOKEN_URL`, `S2S_CLIENT_ID`, `S2S_CLIENT_SECRET`, `S2S_SCOPE`, `S2S_TIMEOUT_SECONDS` (credencial própria, não a de suprimentos).
- api-delpi (validator): `S2S_AUDIENCE`, `S2S_ALLOWED_CLIENTS` (incluir `controllership-finance-api`).
- Keycloak: client `controllership-finance-api` (client_credentials) com scope `settlements.read` — provisionamento owner-side.

### Arquivos principais

api-delpi: `interface/http/routes/financeiro/settlements_router.py` + `settlements_route_helpers.py`; `application/dto/financeiro_settlements/*`; `application/use_cases/financeiro_settlements/*`; `application/security/settlement_scope.py`; `domain/ports/financeiro_settlements/settlements_repository_port.py`; `infrastructure/persistence/totvs/financeiro_settlements/*`; `composition/financeiro_settlements_composer.py`; registros em `route_contract_registry.py`, `main.py`, `openapi_baseline.json`.

BFF: `controllership_finance_app/interface/http/routes/closing_routes.py`; `infrastructure/api_delpi_gateway.py`; `config.py`; `main.py`; compose dev (`DELPI_API_*`, `S2S_AUDIENCE`/`S2S_ALLOWED_CLIENTS`).

### Residuais conhecidos

- `DATA_ACCESS=BLOCKED_BY_SCOPE` por design até contrato de escopo autorizado (D3 enforcement).
- D-PERM: não criada família `financial-settlements.*` — autorização usa S2S client+scope existente + permissões do Portal na BFF; se o owner de segurança preferir capability própria na api-delpi, é troca localizada do decorator.
- D4 pendente: totais oficiais/semântica BA-ES-VL-CP exigem aceite financeiro.
- FKA/FK5 fora do contrato; `partyTaxId`/`bankReference` não expostos.
- Pré-existente no HEAD: `test_route_contract_registry_completeness` já falhava por opIds de outros módulos (supplies/protheus-rest/audit-5s/gpt) sem registro — não causado por este slice.


## 13. D3 — Audiência compartilhada autorizada pelo acesso ao Portal (decisão do PO, 20/10/2026)

**DECISÃO DE PRODUTO APROVADA:** O conjunto de baixas R01 (a pagar) e R02 (a receber) é compartilhado e read-only na versão inicial. Os usuários com concessão efetiva e explícita de `controllership-finance.access` no Core — atribuída administrativamente apenas às pessoas designadas para o Portal — podem visualizar todos os registros de baixas do conjunto compartilhado, **sem segunda lista de usuários, permission ou capability por relatório/filial**. `controllership-finance.manage` isoladamente não substitui `.access`. Não estender esta autorização a outros relatórios, produtos ou datasets.

**Boundary de confiança:** A BFF deve confirmar principal humano e effective permission atual no Core; chamada BFF→api-delpi exige S2S individual Keycloak (client `controllership-finance-api`, scope `settlements.read`) e Bearer humano delegado. Apenas token de serviço, apenas Bearer humano direto à api-delpi, headers de caller autodeclarados ou JWT claims de permissions não autorizam os dados. A política do producer deve garantir que essa rota seja utilizável exclusivamente por esse BFF com delegação verificada; se não houver prova de autorização do conjunto na chamada, fail-closed. A decisão de audiência é **de produto**; implantação do resolver requer revisão de owner segurança/dados e resultados positivos e negativos antes de deploy.

**Filial:** os campos físicos observados estão vazios e a base é única; `branchCode=null`, `branchResolution='unresolved'` no v1. Escopo aprovado corresponde ao dataset compartilhado, não à filial 01/02 nem a `branch=all`. Não criar filtro de filial fictício, não adicionar permission por filial.

**Outros limites:** JSON read-only; D4 códigos crus BA/ES/VL/CP, `officialTotals=false`; não produzir valor oficial, não editar Protheus; sem Excel/PDF, sem paridade obrigatória `_F190C`. UX PT-BR e `@delpi/plugin-ui` primeiro; tela específica de R01/R02 dentro da Central de Fechamento, sem inventar menus e páginas duplicados.

**Implementação planejada, NÃO executada por esta decisão documental:** substituir `UnresolvedSettlementScopeResolver` por contrato de escopo compartilhado somente se o producer puder provar caller S2S estrito + delegado e a BFF puder comprovar Core effective access (sem confiar em flags injetadas pelo navegador). Testar Core indisponível, access revogado, manage-only, ausência/erro de service JWT, client/scopes incorretos, tentativa de acesso direto, usuário sem auth, caminhos de resposta sem PII/segredos, tenant/caller forjado, reconciliação dos eventos e ausência de duplicações.

**GATES:** `D3_PRODUCT_AUDIENCE=APPROVED`; `D3_DATASET=SHARED_R01_R02_READ_ONLY`; `D3_EXTRA_PORTAL_PERMISSION=NONE`; `D3_ENFORCEMENT=PLANNED`; `FINANCIAL_DATA_RELEASE=NO_GO` até validação técnica, smoke aprovado e autorização explícita de deploy. Somente mudança de contrato não prova que o resolver já está seguro ou funcional.
