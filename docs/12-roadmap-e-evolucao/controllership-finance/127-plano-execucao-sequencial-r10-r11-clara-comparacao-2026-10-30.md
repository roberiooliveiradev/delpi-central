# Plano de execução sequencial — R10, R11, comparações e conhecimento CLARA

> **Estado:** PLANNED / TARGET — plano de cinco gates independentes, aprovado como sequência de trabalho pelo PO em 30/10/2026. **Este commit é somente documental:** não autoriza iniciar automaticamente nenhuma etapa, modificar runtime, publicar corpus ou executar deploy. Cada etapa será iniciada por prompt específico do PO, seguida de EXECUTION_REPORT e GPT REVIEW.
>
> **Baseline documental:** [doc 126 §§14–19](./126-gate-contratual-r10-r11-comparacao-clara-2026-10-30.md), gates 019/020; [doc 118](./118-base-canonica-processo-fechamento-mensal-proc0072.md), [doc 84](./84-ciclo2-paridade-monetaria-relatorios-oficiais.md), [doc 85](./85-ciclo2-catalogo-regras-negocio-r01-r15.md), [doc 23](./23-ledger-rq-ac-testes.md), [doc 119](./119-plano-mestre-clara-mcp-semantico-2026-10-29.md), [doc 120](./120-plano-integracao-relatorios-portal-clara-2026-10-30.md), [doc 121](./121-clara-paridade-portal-matriz-cp-2026-10-29.md).
>
> **Baseline de repositório quando criado:** `cb629c027e2d0cb54d57ac6a264619c430f95af3`; revalidar HEAD/status em cada gate. Autoria e execução futuras ainda não verificadas.

## 1. Objetivo operacional e limites aprovados

R10 e R11 devem **destacar candidatos a divergência**, mostrar documentos/códigos/produtos/centros de custo/valores, explicar evidências e orientar a localização do lançamento para **correção humana no TOTVS/Protheus**. Não executar retificação fiscal, contábil, cadastral ou de estoque pelo Portal ou CLARA; não afirmar que alerta é erro confirmado.

**R10:** separar estritamente universo de **apuração histórica** (SD1, 353 linhas, R$ 169.704,12, exclusão de MP e demais critérios do doc 84) do universo adicional de **investigação** (inclusive MP possivelmente classificada em CC inadequado). Não misturar denominadores, contagens ou valores; declarar escopo em toda resposta. Casos evidenciados: CC 0401 (1 linha, caso cabo/CT), CC 0404 (4 linhas), cinco linhas sem CC. Catálogo DV-R10-01..06 do doc 126 é TARGET, não classificador automaticamente homologado. E10a (catálogo CC→classe e exceções), E10b (persistência de revisão), consulta CTT e lista 12-vs-13 TES continuam dependências explícitas.

**R11:** universo histórico SD2 (11 linhas, R$ 97.462,71; critérios históricos no doc 84/126). Evidenciar seleção, motivos e referências ao ERP, **sem excluir automaticamente** do CPV, faturamento, DRE ou outro relatório. E11a (apuração afetada e ação corretiva) e E11b (predicado oficial generalizável) ainda sem evidência suficiente: o vídeo de 54:44 confirmou R10, **não demonstrou R11**. Não afirmar instrução de ajuste específica sem fonte.

**CLARA:** mesma identidade autorizada e contratos do Portal; leitura individual de R01–R15 na medida efetivamente implementada, comparação semântica governada na `controllership-finance-api`, usando `analyze(report_comparison)` no dispatcher MCP existente de seis ferramentas (sem nova ferramenta plana). **Sem tela genérica de comparação nem exportação comparativa** neste ciclo. Exportações individuais já contratadas são preservadas. Conhecimento R01–R15 com fichas versionadas/citações e publicação no mesmo gate da capacidade.

## 2. Regra geral: execução por gates, não em lote

Fluxo obrigatório em cada etapa: **HEAD + git status → Project Instructions → instruções oficiais → .cursor aplicável → roadmap + doc 126 + este plano → owners/contratos/código/testes → evidência → implementação mínima autorizada → testes → verificação do resultado → documentação/commit/SHA → EXECUTION_REPORT → GPT REVIEW**.

Cada gate:
- Recebe **um prompt próprio** do PO. Não iniciar o seguinte por iniciativa do executor.
- Tem `BASE_HEAD`, `FINAL_HEAD`, status, risco concorrente, owners, RQ/AC, casos de teste, evidências antes/depois, SHA e decisão.
- Preserva workstreams concorrentes (GLPI-1353, SEMANTIC, etc.); sem force push, reset destrutivo ou alteração de dados do ERP.
- Usa `PROVEN | TO_INVENTORY | PLANNED | TARGET`, `PASS | FAIL | PENDING | INCONCLUSIVE | TEST_NOT_RUN | STALE_EVIDENCE`, e parecer `ACCEPT | ACCEPT_WITH_RESIDUAL | REWORK | EXECUTION_DRIFT | INCONCLUSIVE`.
- **GATE NÃO É HOMOLOGAÇÃO:** teste unitário verde/HTTP 200/401 anônimo não substitui paridade, AuthZ positiva e aceite funcional. Se bloqueio material, retornar `DECISION_REQUIRED` e delimitar subset seguro, sem inventar regra.
- Documentação e contratos antes de runtime; transversal aprovado antes de implementar página; frontend `@delpi/plugin-ui` first, UX PT-BR, Help em mesmo gate. Não criar permission nova: `.access`, `.manage`, e `.access.dre` somente para documento DRE. Backend Core effective permissions + scope + regra, fail-closed.

## 3. Etapa 1 — R10: apuração e divergências de centro de custo

**Objetivo:** entregar consulta R10 com seleção e totalizadores históricos preservados e capacidade separada de identificar registros para revisão no Protheus.

**Entrada:** doc 126 §§2, 14–19; evidências do vídeo 44:28–54:44 e doc 56; `CC matriz.xlsb`; owner EDAPP/SD1; inventariar CTT, cadastros de produtos, códigos e serviços atuais `vw_fin_despesas_centro_custo` (REUSE_PARTIAL, seleção não equivalente).

**Execução no gate:**
1. Revalidar grão SD1, eixo `D1_DTDIGIT`, critérios de inclusão/exclusão (incluindo 12-vs-13 TES), proveniência e consistência com 353 linhas / R$ 169.704,12; validar série, item, documento, códigos e joins sem multiplicar linhas.
2. Definir contratos para **APURAÇÃO** e **INVESTIGAÇÃO** como escopos distintos, inclusive o tratamento de MP fora da seleção financeira. Totais independentes; não misturar findings e valores como se fossem base única.
3. Inventariar cadastro/consulta CTT e taxonomia CC; implementar apenas regras DV-R10 com predicado e evidência verificáveis. Ausência de CC pode ser sinalizada como candidato; `0401`, `0404` e prefixos narrados não viram regra universal por si.
4. Implementar no owner canônico a seleção e findings com explicação, `ruleId`, evidência e identificadores para localização ERP; preservar `UNCLASSIFIED`; não criar tabela de revisão sem aprovação E10b.
5. BFF proxy + AuthZ, MFE página R10 integrada às telas existentes, filtros/resumos/detalhe/estados e export **individual** conforme contrato aprovado; atualizar Help R10; registrar `read(report.cost_center_expenses)` na CLARA **no mesmo gate de runtime**.
6. Testes de contrato, cardinalidade, custos decimais, autorização, R10 universo histórico vs investigação, caso legítimo sem falso positivo, sem CC, cadastros ausentes, limites de competência, filtros, regressão e smoke autorizado.

**Bloqueios:** E10a e CTT impedem ativar detecção automática dependente de classe/validade de CC; E10b impede `REVIEWED` persistente. Implementar apenas subset `PROVEN` com estado explicativo quando necessário, mediante gate explícito. Não alterar seleção para acomodar alertas.

**Saída/aceite:** R10 disponível com dados verificáveis, escopos separados, prováveis divergências explicadas, paridade histórica (ou divergência explicitamente justificada), CLARA equivalente, Help alinhado e SHA/evidências. G6 humano oficial independente permanece pendente quando não executado.

**Handoff → Etapa 2:** contrato de findings, filtros, proveniência, status da classificação, lacunas E10, componentes reutilizáveis e dados monetários.

## 4. Etapa 2 — R11: notas fiscais a desconsiderar, sem exclusão automática

**Objetivo:** lista investigativa de NFs com critérios comprovados e instrução honesta de conferência no ERP.

**Entrada:** doc 126, `NF a desconsiderar.xlsb`, doc 84/85, owner EDAPP/SD2/SF4; baseline 11 linhas e R$ 97.462,71 em filial/período históricos. Verificar predicado TES 594, grupo 9035, CFOP, `D2_EMISSAO`, TES irmão e `F4_ESTOQUE`.

**Execução:**
1. Validar quais critérios são comprovados apenas para o artefato e quais podem ser generalizados; inspecionar dados e código e buscar evidência funcional adicional para E11a/b. Não afirmar R11 demonstrado no vídeo examinado.
2. Documentar claramente **o que 'desconsiderar' altera na análise** e a ação que a usuária toma no Protheus, **somente** quando owner/fonte resolver E11a. Enquanto pendente, apresentar indicação investigativa e não instrução fictícia de ajuste.
3. Implementar seleção e `findings[]` respaldados, com série/número/item, produto, TES/CFOP/grupo, valor, origem, apuração afetada (nulo/pendente se desconhecida), critério e documentação; diferenciar ausência de item-irmão de falha comprovada.
4. BFF + AuthZ, página R11 dentro do escopo atual do Portal, detalhes e export **individual** conforme contrato; CLARA `read(report.billing_exclusion_roster)` no mesmo pacote, Help e testes.
5. Testar 11/11, R$ 97.462,71, custo zero estrutural (não falso erro), casos fora da seleção, duplicidade de join, filiais, competências, indisponibilidade e segurança.

**Bloqueios:** E11a/b não resolvidos proíbem afirmar propósito exato/impacto downstream, expandir predicado como regra oficial ou prescrever ajuste específico. Um relatório de investigação com avisos e lacunas explícitas poderá ser entregue como subconjunto, após aceite do gate.

**Saída/aceite:** consulta R11 auditável, sem exclusão em outro relatório e sem mutação ERP; paridade histórica, CLARA/Portal com o mesmo resultado, pendências visíveis.

**Handoff → Etapa 3:** contratos individuais reais R10/R11, measures, limites e status de evidência.

## 5. Etapa 3 — Comparação transversal na BFF para a CLARA

**Objetivo:** implementar a capacidade `analyze(report_comparison)` reutilizando consultas governadas, **não** criando tela genérica nem endpoint de export comparativo.

**Execução:**
1. Inventariar `analyze`/registry e precedentes de comparação existentes; owner aprovado `controllership-finance-api`. Revalidar schema `POST /analysis/report-comparison` do doc 126 sem congelar suposições conflitantes com HEAD.
2. Implementar seleção de 2–6 sujeitos sob limites de cardinalidade, volume, paginação e timeout comprovados; todos autorizados individualmente em backend com effective permissions, scope e regra. Proibir vazamento de existência de recurso restrito.
3. Matriz de compatibilidade por par/medida/grão/eixo de data/`as_of`: `COMPARABLE`, `RELATED_REQUIRES_EXPLANATION`, `NOT_COMPARABLE`; default `INSUFFICIENT_EVIDENCE`. Deltas/% somente com unidade, seleção, sinal e base compatíveis; nenhuma reconciliação fabricada R06×CPV.
4. `PARTIAL` com `subject_error` tipado, evidência e limites de conclusão; falha de autorização não vira partial revelador; nunca zero substituto.
5. CLARA dispatcher semântico `analyze(report_comparison)` com linguagem natural para competências, filiais autorizadas, produtos e documentos; nenhum novo tool MCP público, nenhuma duplicação de cálculo no LLM.
6. Testes positivos/negativos Portal/BFF/CLARA, R06 multi-período, R06×CPV explicado, R12×R15 incompatível, documentos com chaves incompletas, scope misto 403, timeout, inputs inválidos e regressão.

**Saída/aceite:** capacidade via CLARA/BFF comprovada com dados reais autorizados, sem UI genérica/CSV/PDF comparativo; limites e explicações documentados.

**Handoff → Etapa 4:** catálogo de capabilities, tipos de measures, matriz de semântica e fontes de citações.

## 6. Etapa 4 — Fichas técnicas R01–R15 + conhecimento/corpus CLARA

**Objetivo:** consolidar o conhecimento real da Central de Fechamento para consulta, explicação de cálculos e orientação com fontes.

**Execução:**
1. Inventariar estado real de cada R01–R15 (implementado, operacional, contrato TARGET, paridade oficial PENDING), Help e corpus atual. Não afirmar que todos têm runtime.
2. Criar fichas versionadas por relatório, seguindo doc 126 §18: identificação/owner/produtor; seleção/fórmulas/filtros/grão/datas; exemplos e exceções; divergências e orientação de conferência no Protheus; limites de comparabilidade; `PROVEN|TO_INVENTORY|PLANNED|TARGET` por afirmação; citações doc/seção/código/evidence ID.
3. Incluir R10/R11 e casos do vídeo/planilhas com a ressalva de R11 não demonstrado; respeitar dados privados, sem expor documentos sensíveis indiscriminadamente no corpus.
4. Integrar fichas aos manifests/pipeline governados, checar versão/hash, recuperação citável, `get_context`/knowledge, resposta factual versus hipótese, e coerência com o catálogo MCP real. Não ensinar conhecimento somente via prompt.
5. Atualizar Help das capacidades já disponíveis; teste de perguntas de divergências, cálculos, origem, diferença MATR320/MATR910/MATR989, e respostas com fonte. Fonte indisponível → lacuna explícita.
6. Publicação do corpus condicionada a QA e autorização do próprio gate; registrar versão anterior, nova, fontes/itens e rollback. Não publicar afirmação TARGET como comportamento em produção.

**Saída/aceite:** fichas R01–R15 completas no nível de evidência disponível, corpus verificavelmente atualizado e CLARA respondendo com citações; relações de comparação documentadas.

**Handoff → Etapa 5:** hashes/versões, fonte de conhecimento, perguntas de teste e rastreabilidade.

## 7. Etapa 5 — Verificação transversal, homologação e deploy governado

**Objetivo:** consolidar integração, regressão, paridade e publicação dos componentes aprovados. **A implantação poderá ocorrer antes nesta sequência somente se um gate explicitamente aprovado estabelecer estratégia incremental e seu próprio smoke/rollback; não presumir publicação nos gates 1–4.** Na ausência dessa decisão, as etapas 1–4 devem produzir artefatos testáveis sem prometer disponibilidade produtiva antes do gate 5.

**Execução:**
1. Revalidar HEAD/status, SHAs e diff desde baseline; compatibilidade api-delpi/BFF/MFE/CLARA/corpus/Help, testes e mudanças concorrentes.
2. Executar matrizes de R10 (apuração 353 / R$169.704,12 **versus** investigação sem misturar totais), R11 (11 / R$97.462,71), R06 set/2026 sem regressão e demais relatórios afetados.
3. Testar AuthZ positiva com persona efetivamente autorizada, 401/403 negativos, multi-branch fail-closed; não criar concessões para smoke. **401 anônimo não prova caminho positivo.**
4. Testar CLARA e Portal para cada consulta R10/R11 com mesmo escopo/identidade e reproduzir comparação individual, multi-período, não comparável e parcial; testar citações corpus e Help.
5. Verificar UX desktop/mobile/teclado/foco, export **individual** aplicável e estados de erro; registrar `TEST_NOT_RUN` se não houver ambiente/persona.
6. Fechar gates A (evidência/regra), B (contratos), C (paridade), D (segurança), E (regressão), F (CLARA e corpus), G (readiness), H (smoke/rollback). Pendência material impede deploy; G6/E7 oficiais permanecem `PENDING` salvo emissão/validação reais.
7. Com autorização explícita de deploy no prompt da Etapa 5 e gates PASS: deploy oficial via SSH `operador@192.168.1.237`, rebuild mínimo dos serviços modificados, SHA/digests e versions por componente, smoke positivo e negativo, comparação antes/depois, rollback coordenado; não mexer no ERP.
8. Atualizar README, docs 23/85/120/121/126, este plano, fichas, Help e evidências com status real, commit/SHA e relatório de resíduos. Não marcar etapa concluída por docs apenas.

**Saída/aceite:** produto integrado verificado e, se autorizado/gates PASS, deploy produtivo demonstrado, sem atribuir PASS a smoke não executado.

## 8. Matriz de dependências e critérios de passagem

| Etapa | Entrada indispensável | Gate de saída para prompt seguinte |
|---|---|---|
| 1 R10 | doc 126, artefato SD1, diferenças seleção/investigação, owners | Consulta/findings explicáveis + paridade ou bloqueios E10 tipados; review GPT |
| 2 R11 | doc 126, SD2, finalidade E11 explícita ou limitada | Roster investigativo sem exclusão + evidência/limitações; review GPT |
| 3 comparação | contratos reais de R10/R11 + catálogo MCP | Compare autorizado, semântica e PARTIAL verificados; review GPT |
| 4 conhecimento | fichas/evidências dos três gates e docs 118/85 | Corpus/Help com versão, hashes e citações verificados; review GPT |
| 5 homologação/deploy | evidência 1–4, testes, autorização de produção | Gates e smoke, SHA/digests, rollback e parecer GPT |

**Risco:** etapas 1–3 envolvem capacidade end-to-end em integração, mas podem não estar em produção até a etapa 5. Diferenciar ambiente de teste de produção e verificar flags/compatibilidade; não expor rotas inacabadas como feature disponível.

## 9. Registro de progresso — atualizar após cada review

| Etapa | Estado inicial | EXECUTION_ID | SHA | Veredito GPT | Residuais |
|---|---|---|---|---|---|
| 1 — R10 | IMPLEMENTED (aguardando review) | `CF-PROC0072-R10-IMPLEMENTATION-STAGE-01` | ver EXECUTION_REPORT | PENDING | E10a, E10b, CTT histórico, TES 12-vs-13, G6 |
| 2 — R11 | IMPLEMENTED (aguardando review) | `CF-PROC0072-R11-IMPLEMENTATION-STAGE-02` | ver EXECUTION_REPORT | PENDING | E11a, E11b, paridade oficial/G6, smoke produtivo |
| 3 — Comparação | IMPLEMENTED (aguardando review) | `CF-PROC0072-CLARA-REPORT-COMPARISON-IMPLEMENTATION-STAGE-03` | ver EXECUTION_REPORT | PENDING | pares não curados → INSUFFICIENT_EVIDENCE; smoke/live/G6 |
| 4 — Conhecimento CLARA | IMPLEMENTED (aguardando review) | `CF-PROC0072-CLARA-KNOWLEDGE-R01-R15-IMPLEMENTATION-STAGE-04` | ver EXECUTION_REPORT | PENDING | corpus produtivo `PENDING_APPROVAL`; G6 |
| 5 — Homologação/deploy | PLANNED | A atribuir | — | PENDING | G6/E7 e smoke positivo |

Atualizar por **evidência**, não apenas pelo relato de execução. A aprovação ou rejeição de cada etapa é responsabilidade do review GPT/PO. Não avançar automaticamente.

## 10. Próximo movimento

**Etapa 1 executada** sob `CF-PROC0072-R10-IMPLEMENTATION-STAGE-01` — R10 implementado ponta a ponta (api-delpi `/financeiro/cost-center-expenses`, BFF `/closing/cost-center-expenses` + export, página MFE no hub de relatórios, CLARA `read(report.cost_center_expenses)`), com paridade monetária reproduzida ao vivo contra o TOTVS (353 linhas / R$ 169.704,12 / 139 documentos / 46 buckets de CC para 2026-09 filial 01 — incluindo o grupo «sem centro de custo» como no artefato). Subset implementado de divergências: DV-R10-01 (universo investigação), DV-R10-02 (CTT vigente, sem conclusão histórica), DV-R10-04, DV-R10-05 (`UNCLASSIFIED` por D-01); DV-R10-03 e DV-R10-06 declarados e bloqueados por E10a. Sem deploy, sem corpus produtivo, sem R11 — EXECUTION_REPORT entregue para GPT REVIEW.

**Etapa 2 executada** sob `CF-PROC0072-R11-IMPLEMENTATION-STAGE-02` — R11 implementado ponta a ponta (api-delpi `/financeiro/billing-exclusion-roster`, BFF `/closing/billing-exclusion-roster` + export, página MFE no hub de relatórios, CLARA `read(report.billing_exclusion_roster)`), com paridade reproduzida ao vivo contra o TOTVS **via o próprio engine** (11 linhas / R$ 97.462,71 / 11 documentos / 3 documentos sem item-irmão de estoque — 103033, 103199, 103202 — para 2026-09 filial 01, eixo `D2_EMISSAO`). Três visões com totalizadores separados e nunca somados: `candidates` (predicado histórico observado grupo 9035 ∩ TES 594), `out_of_criteria` (linhas relacionadas fora do predicado — DV-R11-04) e `all`. Subset implementado de regras: DV-R11-03 como `POSSIBLE_DIVERGENCE`; DV-R11-01 exposta como bloco de seleção; DV-R11-02 como `costStatus` explicativo (nunca divergência); DV-R11-04 como visão separada. E11a/E11b permanecem `TO_INVENTORY`/`PENDING_EVIDENCE`: nenhuma nota é excluída automaticamente de CPV, faturamento ou DRE, e o predicado não é publicado como regra oficial universal. Sem deploy, sem comparação universal — EXECUTION_REPORT entregue para GPT REVIEW.

**Etapa 3 executada** sob `CF-PROC0072-CLARA-REPORT-COMPARISON-IMPLEMENTATION-STAGE-03` — motor de comparação governado na BFF (`POST /closing/analysis/report-comparison`; domain `report_comparison/` + application `compare_use_case`), contrato tipado 2–6 sujeitos com kinds PERIOD/BRANCH/REPORT/DOCUMENT/TREND/EXPLAIN, matriz de compatibilidade semântica curada (COMPARABLE / RELATED_REQUIRES_EXPLANATION / NOT_COMPARABLE / INSUFFICIENT_EVIDENCE default), normalizações limitadas às autorizadas (delta absoluto/percentual com guarda de denominador zero; grãos só sobre agregações completas do produtor), parciais honestos sem zero implícito, fail-closed por sujeito (denied nunca vaza existência), e `analyze(report_comparison)` no dispatcher semântico chamando a MESMA rota BFF do Portal — superfície segue com seis tools. Suporte real: R01,R02,R03,R05,R06,R07,R08,R10,R11,CPV; R04/R09/R12/R15 sem contrato (`report_not_implemented`); pares não curados respondem INSUFFICIENT_EVIDENCE. 35 testes dedicados + regressão BFF verde. Sem deploy, sem tela genérica, sem exportação, sem corpus — EXECUTION_REPORT entregue para GPT REVIEW.

**Próximo prompt, somente quando o PO solicitar:** Etapa 4 — Conhecimento especializado R01–R15 da CLARA, conforme §6, após review da Etapa 3 e autorização explícita do Product Owner.

**Etapa 4 executada** sob `CF-PROC0072-CLARA-KNOWLEDGE-R01-R15-IMPLEMENTATION-STAGE-04` — 15 fichas técnicas versionadas em `docs/12-roadmap-e-evolucao/controllership-finance/fichas/` (esquema canônico doc 126 §18: identificação/fonte/regras/interpretação/operação/governança com evidência por afirmação), fichas de atenção especial R10/R11 (universos estritos, DV-R10-01..06, DV-R11-01..04, custo estrutural zero, E10a/E10b/E11a/E11b), ficha do processo PROC-0072 (GATE E — competência, pendências, fluxo Controladoria→DRE, permissões, conhecer≠consultar≠executar), matriz de inventário no README do diretório, e 17 fontes novas registradas no `corpus_manifest` (inventário explícito). Ingestão controlada executada no **ambiente local autorizado**: corpus `f9857be6` (88 fontes / 2.170 itens) — versão anterior `57109de5` preservada como rollback; **publicação produtiva do corpus permanece `PENDING_APPROVAL`** (gate separado). Recuperação citável verificada localmente com `citation_locator` por `report_id`. Help verificado e inalterado (sem superfície user-facing nova). Sem deploy, sem novos relatórios, sem mutação ERP — EXECUTION_REPORT entregue para GPT REVIEW.

**Próximo prompt, somente quando o PO solicitar:** Etapa 5 — Homologação Transversal e Deploy Governado, após review da Etapa 4 e autorização explícita do Product Owner.
