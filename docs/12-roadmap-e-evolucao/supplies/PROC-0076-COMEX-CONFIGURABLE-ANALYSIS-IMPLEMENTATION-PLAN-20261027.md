# PROC-0076 — Plano de implementação: catálogo SB1, NCMs e análises Comex configuráveis

> **Estado:** `PLANNED` — proposta de implementação, **não autorização para executar**. **Data:** 2026-10-27. **Baseline documental:** main `23613bd1f1e43ca9804fa389c7b540b6abc183b5`. **Owner de coordenação:** Portal Suprimentos. Implementação page-by-page e GATE-FEATURE vigente continuam obrigatórios.
>
> **Objetivo:** permitir que usuários autorizados de Suprimentos selecionem produtos/matérias-primas reais da DELPI, consultem suas NCMs já cadastradas no Protheus, escolham um conjunto para análise de comércio exterior e salvem visualizações pessoais, mantendo a autoridade fiscal e o Comex Stat/MDIC nos seus owners.

## 1. Evidências e premissas classificadas

| Evidência | Estado | Fonte / limitação |
|---|---|---|
| SB1010 dispõe de `B1_COD`, `B1_DESC`, `B1_TIPO`, `B1_GRUPO`, `B1_POSIPI`, `B1_EX_NCM`, `B1_UM`, `B1_SUBGRUP` | `PROVEN` | Consulta autorizada DAVI ao dicionário Protheus, `list_protheus_table_columns(SB1010)`. `B1_POSIPI` é texto de tamanho 10 no dicionário; validar formato antes de tratar como NCM de 8 dígitos |
| Tipos MP, PI e PA são representados por `B1_TIPO` (2 caracteres) | `PROVEN` quanto à capacidade do campo e ao contrato da rota de estoque de segurança; frequências e preenchimento reais `TO_INVENTORY` | DAVI + `api-delpi/app/interface/http/routes/product_routes.py` |
| A `api-delpi` consulta `SB1.B1_POSIPI AS ncm_ipi_position` | `PROVEN` no repositório | `api-delpi/app/infrastructure/persistence/totvs/product_repositories/product_repository.py` |
| `GET /search`, `GET /{code}` e `GET /{code}/summary` existem no router de produtos | `PROVEN` no código | `api-delpi/app/interface/http/routes/product_routes.py`; paths relativos ao router, validar prefixo completo |
| Busca de produtos via DAVI retornou total de 55.341 registros | `PROVEN` para projeção consultada, **não** população MP/PI/PA | DAVI `search_products`, página 1, 3 itens; retorno truncado |
| `GET /search` não mostrou filtro `product_type` na assinatura inspecionada; `GET /{code}` admite `view` | `PROVEN` no trecho atual; efeito de projeção `TO_INVENTORY` | Código no HEAD; verificar DTO/ACL e permissões |
| NCMs preenchidas/válidas na SB1010, vínculo com SYD e tabela oficial vigente | `TO_INVENTORY` | Não inferir qualidade a partir do dicionário |
| Comex Stat MDIC contém dados mensais por NCM; feed atual não possui NCM homologada | `PROVEN` em contrato/evidências anteriores para estado pendente; runtime futuro exige revalidação | PROC-0076 R5 |
| Usuários com acesso poderão criar e salvar análises pessoais | `TARGET` | Decisão de produto; requer contrato e AuthZ server-side |

**Invariante:** a NCM cadastrada no ERP é uma *candidata à análise*, não prova automática de classificação fiscal vigente ou equivalência comercial. Nunca transformar classificação em dado mestre editável pelo Portal.

## 2. Experiência alvo e escopo do MVP

Uma **única perspectiva Comex** na página de Inteligência de Mercado. Não adicionar rota nova sem contrato; não criar construtor genérico de BI.

1. Filtro de **tipo de produto**: MP, PI, PA (ou tipos adicionais somente se comprovados e autorizados).
2. Busca paginada de produtos reais: código, descrição, tipo, grupo, UM; seleção múltipla com chips legíveis e pesquisa incremental.
3. Mostrar para cada item **NCM de origem `B1_POSIPI`** com estado: ausente, malformada, divergente, candidata, homologada, rejeitada. Usuário entende o motivo de não elegibilidade.
4. Agrupar por **matéria-prima/família de análise** configurável, distinta de `B1_GRUPO` e `B1_TIPO`; a seleção de produto é um meio de resolver NCMs e não garante que o usuário deva analisar cada SKU separadamente.
5. Multiselect de famílias ou produtos → deduplicação de NCMs homologadas → consultas internas ao histórico Comex por período, com indicadores **FOB (US$), peso (kg/t) e FOB/massa (US$/t indicativo)**, país de origem somente quando contrato permitir.
6. Série por NCM/família e consolidado **somente onde semântica permitir**; média ponderada = soma FOB / soma massa em toneladas, nunca média simples de médias. NCM compartilhada por duas famílias não pode ser duplicada no total.
7. Salvar visualização pessoal: nome, filtros, seleção e modo (gráfico/tabela), sem copiar dados externos em settings; permitir abrir/editar/excluir **apenas a própria visualização**, no escopo de unidade/recurso e capacidade efetiva.
8. Estado sem NCM ou fonte indisponível é claro, não expõe zero sintético nem envia requisição externa a cada clique.

**Fora do MVP:** escrita TOTVS/SB1, correção fiscal automática, cadastro livre de NCM sem validação, CRUD universal de dashboards, fontes novas, novos indicadores estratégicos, ajustes em outras páginas, redistribuição dos dados.

## 3. Ownership e contratos

```text
Keycloak (identidade) → Core API (permissions efetivas)
MFE plugins/supplies (UX, kit-first)
   → supplies-api (Flask; AuthZ, catálogo composto, visualizações salvas)
      → api-delpi (owner SQL SB1010, tipos e classificação fiscal ERP)
      → external-data-api (owner ingestão MDIC, dados por NCM e competências)
```

- **api-delpi**: investigar reuso de busca e detalhe atuais; se insuficientes, adicionar **endpoint semântico paginado** para seleção de produtos MP/PI/PA e NCM cadastral, com filters allowlisted, projeção minimizada, paginação e AuthZ. Não promover SQL nem chamada direta da MFE ao Protheus.
- **external-data-api**: catálogo de NCMs e origem/metodologia da série MDIC; homologação de NCMs e allowlist do feed sob seu modelo governado de source rights, com revisão de contrato e ownership. Evitar misturar dados TOTVS próprios do `supplies-api` no schema `external_data`.
- **supplies-api**: compõe catálogo de produtos, status de homologação e dados Comex, autoriza por capability AND unit_scope AND resource_scope/ownership AND business_rule; persiste **apenas** grupos/seleções/visualizações próprios do Portal, após verificar migrations e schema `supplies`. Não espelhar SB1 nem observações TOTVS.
- **plugins/supplies**: filtros, seleção, cards, gráfico, tabela, estados e Help; priorizar componentes do `@delpi/plugin-ui`.
- **Fiscal/Compras**: Compras seleciona famílias relevantes, Fiscal valida classificação e abrangência, Suprimentos homologa uso da NCM na análise. Uma visualização pessoal pode usar **somente NCMs aprovadas**; não requer aprovação individual por gráfico.

**RBAC:** não criar permission por botão, tela, endpoint ou CRUD. Reutilizar capacidades existentes ou submeter mudança à Core como contrato transversal somente se o inventário mostrar necessidade. `view-all` nunca amplia unidade.

## 4. Sequência e gates

### S0 — Inventário e contrato (somente READ)

**OWNER:** Architecture + `api-delpi` + `supplies-api` + Integrações.

- Rebaseline HEAD/status, authorities e regras `.cursor`; verificar página autorizada e gate atual.
- Consultar DAVI e as projeções reais: `B1_TIPO` MP/PI/PA, `B1_POSIPI` nulo/preenchido, grupos, duplicidades de NCM, exclusões `D_E_L_E_T_`, filiais e permissões; aplicar paginação e delimitar escopo. Não enumerar dados sem autorização.
- Confirmar prefixo/contrato/OpenAPI de `GET /search`, `GET /{code}`; testar se `ncm_ipi_position` é emitido pelo DTO nas `views` atuais.
- Identificar schemas/owners para catálogo de homologação, grupos configuráveis e visuais pessoais. Não presumir onde armazenar a homologação sem contrato.
- Inspecionar feed Comex, fonte, downloads, limites, rate controls, disponibilidade e direito de armazenamento; definir método de atualização mensal, sem chamadas MDIC por interação.
- Produzir inventário de dados e `RQ/AC`, contrato HTTP, matriz de owners e rollback. **STOP** em `EXECUTION_DRIFT`.

**GATE-S0:** `PASS` apenas com dicionário+amostra autorizada+DTO+AuthZ+fonte verificados. Nenhum código nesta etapa.

### S1 — Contrato de catálogo do Protheus

**OWNER:** `api-delpi`. Reusar rotas existentes quando suficiente, senão diff mínimo para endpoint semântico:
- busca paginada, filtros por tipo MP/PI/PA, grupo, descrição/código, projeção de NCM quando autorizada;
- preservar código, descrição, tipo, grupo, unidade, origem da classificação e filial quando aplicável;
- validação formal de NCM de 8 dígitos e status explícito, **sem alterar** `B1_POSIPI`;
- positive/sibling/negative, paginação/limit, permissão e regressão das rotas antigas.

**GATE-S1:** contrato/owner aprovado, testes API e AuthZ `PASS`; não afirmar sucesso de consulta via rota equivalente mas distinta.

### S2 — Catálogo e governança das NCMs

**OWNERS:** Fiscal + Compras + `external-data-api` (NCM allowlist da integração) + `supplies-api` (configuração própria).
- proposta → validação fiscal → homologação por Suprimentos → ativação do código no feed; auditoria com responsável, evidência e data.
- Normalização e deduplicação de NCMs; histórico de vigência e divergências da tabela oficial, se houver fonte aprovada.
- **Sem registros NCM homologados por enquanto.** Iniciar com 3–5 famílias reais selecionadas por Compras; cadastro exemplo não autoriza ingestão.
- Provar estado de fonte MDIC, contrato de ingestão e indicadores FOB/peso/FOB por tonelada.

**GATE-S2:** pelo menos uma NCM real homologada, testes de allowlist, owner, fonte e rollback aprovados antes de ingressar dados Comex em produção.

### S3 — Composição BFF e visualizações salvas

**OWNER:** `supplies-api`:
- contratos de busca/seleção/filtros/visuais salvos (a fechar em S0); service de composição com api-delpi e external-data-api;
- esquema de estado próprio e migration aditiva **somente após** autoridade do schema;
- persistir visuais por identidade, unidade e ownership; sanitizar filtros e índices, limites de seleção e de períodos, prevenir abuso e cross-unit leakage;
- cache de resultados agregados por NCM, período e granularidade conforme direitos, sem armazenar TOTVS.

**GATE-S3:** AuthZ fail-closed e coverage positive/sibling/negative, API compatível, testes PG e S2S.

### S4 — Experiência na página Comex

**OWNER:** `plugins/supplies`:
- multiselect de materiais/famílias, busca paginada, filtros/seleções acessíveis e URL/F5;
- UX de pendência/ausência/homologação, loading/error/403/404, KPIs e gráfico/tabela/export;
- salvar/abrir/editar/excluir visualizações pessoais somente quando contrato S3 estiver aprovado;
- sem gráficos que misturem NCMs incompatíveis sem metodologia; labels e fontes contextualizadas;
- Help/glossário sincronizados, responsivo claro/escuro, teclado/foco.

**GATE-S4:** testes, typecheck/build, visual desktop/mobile e sem regressão de Metais/PTAX/IPP.

### S5 — Ingestão oficial e aceitação federada

**OWNER:** `external-data-api` + Release/Infra:
- carga histórica controlada de NCMs homologadas, preferencialmente arquivos oficiais para grandes volumes e incremental mensal;
- health e egress TLS, checksum/dedup, sem fetch upstream por clique; preservar provenance, competência, update time;
- smoke de NCM real: entrada no catálogo → valores do MDIC → BFF → visual/exports, negativos 401/403/404/422;
- smoke federado autenticado, URL/F5, desktop/mobile, dark/light, rollback e SHA.

**GATE-FEATURE:** `PASS` apenas com dados reais, contratos, AuthZ e navegador comprovados; caso contrário `INCONCLUSIVE`, sem inferir aceite por testes verdes.

## 5. Critérios de aceite rastreáveis

| AC | Critério |
|---|---|
| AC-01 | Tipos MP/PI/PA e preenchimento de NCM inventariados por leitura autorizada |
| AC-02 | Busca de produtos paginada reaproveita contrato `api-delpi` correto |
| AC-03 | `B1_POSIPI` é exposto com status de qualidade sem alteração do ERP |
| AC-04 | Catálogo de famílias/seleções não confunde tipo, grupo, NCM ou SKU |
| AC-05 | Fiscal valida NCM, Compras prioriza, Suprimentos homologa uso |
| AC-06 | NCMs duplicadas deduplicadas; ausência/invalidez sinalizada |
| AC-07 | Multiselect pesquisa/seleciona material com responsividade e a11y |
| AC-08 | Só NCM homologada chega ao feed MDIC |
| AC-09 | FOB, massa e valor indicativo por tonelada têm metodologia explícita |
| AC-10 | Agregações não duplicam NCM nem calculam média simples de médias |
| AC-11 | Usuário salva visual pessoal e reabre filtros/estado corretamente |
| AC-12 | Ownership e unidade impedem acesso/edição de visuais alheios |
| AC-13 | Core effective permissions/AuthZ S2S e fail-closed preservados |
| AC-14 | Estados pending/empty/partial/error/403/404 acessíveis, sem fake data |
| AC-15 | URL/F5, gráficos, tabelas e exportações coerentes |
| AC-16 | Sem regressão Metais, PTAX, IPP; sem LME não homologada |
| AC-17 | Testes positivos, sibling, negativos, PG, build, smoke federado |
| AC-18 | Help/docs/ADRs, rollback, SHAs e evidência atualizados |

Estados por AC: `PASS | FAIL | PENDING | INCONCLUSIVE | TEST_NOT_RUN`.

## 6. Riscos e decisões pendentes

| Risco / decisão | Estado | Tratamento |
|---|---|---|
| `B1_POSIPI` preenchido mas NCM desatualizada/inválida | `TO_INVENTORY` | Verificar formato, vigência e validação Fiscal; não editar ERP |
| `GET /search` não possui filtro por tipo | `PROVEN` no contrato inspecionado | S0 decide extensão mínima em `api-delpi` |
| Pesquisa transversal pode retornar SKUs em volume alto | `PROVEN` para busca paginada | Busca incremental, paginação, limites e controle de carga |
| NCM pode classificar vários tipos de produto | `TARGET` | Usuário vê proveniência e ressalva de representatividade |
| MDIC feed sem NCM e com disponibilidade externa variável | `PENDING` | S0 verifica fonte, S2 homologa, S5 ingere |
| Escolha do owner do catálogo de homologação entre serviços | `TO_INVENTORY` | Fixar em S0 com ADR se necessário; nunca bancos cruzados |
| Visualizações pessoais dependem de escopo de unidade/ownership | `PLANNED` | S3 contratual + Core permissions |
| Tela Comex já existe e está em estado pendente | `PROVEN` nas capturas | Evoluir somente a perspectiva existente, sem abrir nova página |

## 7. Condição para começar a implementação

**Autorizado agora apenas planejar/documentar.** A execução de S1–S5 depende de:

1. S0/GATE de inventário e contratos fechado;
2. confirmação de owner de NCM allowlist e configurações;
3. decisão de Compras/Fiscal sobre os primeiros materiais;
4. comprovação da fonte MDIC e das permissões;
5. autorização explícita de implementação do PO conforme governança do Portal.

**Próximo passo recomendado:** emitir brief de Cursor **S0 READ-only** para concluir inventário da SB1010, DTOs e contratos Comex, sem código, migrations ou deploy.

## 8. Referências

- [README da documentação de Suprimentos](./README.md)
- [Guia das perspectivas e validação Comex](./PROC-0076-GUIA-PERSPECTIVAS-E-VALIDACAO-COMEX-20261027.md) — PR #119, confirmar incorporação ao main
- [Contrato de comportamento UX R4](./PROC-0076-R4-UX-BEHAVIOR-CONTRACT.md)
- [Evidências de R5](../shared-integrations/PROC-0076-R5-METALCHARTS-IMPLEMENTATION-AND-EVIDENCE-20261027.md)
