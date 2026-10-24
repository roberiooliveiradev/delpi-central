# Documento 93 — Roadmap executivo E2E da Central de Fechamento, com checkpoints reais

**Data de rebaseline:** 2026-10-24 · **Processo:** PROC-0072 — Gestão do Fechamento Mensal da Controladoria  
**Produto:** Portal Controladoria & Finanças · **Primeira funcionalidade:** Central de Fechamento  
**Referência remota analisada:** `8ecce3f836d9963fa7485089200afdf8edd32f43` (main antes deste documento; revalidar HEAD em cada entrega). **Git status de worktree local:** INCONCLUSIVE via conector GitHub; executor deve registrar a situação real.  
**Natureza:** `EXECUTION_ROADMAP / REBASELINE_DOCUMENTAL / DESIGN_GATE_OPEN`. **Não há autorização de implementar nenhum slice novo: `IMPLEMENTATION_AUTHORIZED=NO`.**  
**Owner de decisão de produto:** PO/Controladoria. **Owners técnicos:** Portal CF/BFF, Core/Plugin System, api-delpi/TI-Protheus, demais contextos, conforme [21](./21-boundaries-produtos-e-owners.md). Nenhum novo owner foi atribuído por suposição.

> **Regra de navegação:** Este **é o roteiro executivo vigente da Central de Fechamento** para dependências, próximos passos e checkpoints pós-Ciclos 1–3. O [39 — roadmap V1 de base](./39-roadmap-mestre-implementacao-v1.md) permanece como plano **histórico de sequenciamento de todo o Portal**; [40 — dependências/IMP](./40-matriz-dependencias-e-slices-v1.md), [41 — testes/gates](./41-estrategia-validacao-e-gates-implementacao-v1.md), [42 — playbook](./42-playbook-brief-cursor-execution-report-v1.md) e [43 — rollout](./43-rollout-operacao-e-handoff-v1.md) seguem normativos para critérios que não conflitem. README é o painel de estado. Não existem dois roadmaps de execução concorrentes.

## 1. O que reavaliamos e por que o plano antigo não pode ser seguido literalmente

**O roadmap existia** nos docs 39–43, publicado em 16/10/2026, mas sua fila R1→R2→R3→R4 não incorporava:
- **Ciclo 1:** levantamento de **19 arquivos de planilhas/PDFs e gravação**, checklist Eletrônico/Físico/Planilha1 e aceites documentais com residual ([59](./59-ciclo1-checklist-abas-e-entregaveis-sanitizado.md), [76](./76-ciclo1-fechamento-documental.md), [79](./79-ciclo1-aceite-formal-po.md)); **verde = item esperado para envio naquele contexto, não entregue nem aceito**; a lista não é 1:1 com R01–R15. Matriz + filial ativas da empresa de componentes foram informadas pelo PO; contexto industrial legado não vira entrega obrigatória.
- **Ciclo 2:** quinze grupos de investigação R01–R15, não quinze páginas nem necessariamente quinze relatórios unitários; 47/60 coleta, 55/90 auditoria e **0/15 com G6 humano**, conforme [47](./47-t01-report-column-audit-tracker-v1.md)/[86](./86-ciclo2-relatorio-final-consolidado-e-handoff.md). O catálogo de 100 regras e 75 testes ([85](./85-ciclo2-catalogo-regras-negocio-r01-r15.md)) é fundamento de automação, não prova de runtime.
- **Ciclo 3:** inventário de código existente ([88](./88-ciclo3-r01-inventario-contratos-e-pacote-decisoes.md)), escopo read-only D01..D06 ([89](./89-ciclo3-decisoes-aprovadas-e-gate-documental-r02.md)), crosswalk E2E TÉO/RQ/AC/P1–P6 ([90](./90-ciclo3-crosswalk-end-to-end-proc0072-teo-rq-ac-portal.md)) e handoff P2 ([92](./92-ciclo3-consolidacao-e-handoff-continuacao-p2.md)).
- **Decisão posterior do PO:** Contabilidade/DRE receberá permission e página restrita de histórico/download **em fase futura**, sem aceite na primeira versão ([91](./91-ciclo3-contabilidade-acesso-documentos-historicos-gate.md) seção 8). Não implementar agora, nem usar `access` geral como atalho.

**O objetivo funcional comprovado pelo TÉO (31/31.1–31.19/33) e GitHub docs 08–13/23/37:** abrir competência, manter checklist configurável, coletar/automatizar relatórios TOTVS e documentos externos, anexar, validar/rejeitar com histórico, conciliar/cutoff, resolver pendências, montar/versionar/disponibilizar pacotes por destinatário, dar visibilidade, tratar esclarecimentos e concluir de forma auditável. **A mesma Joici pode anexar e validar quando autorizada para ambas as ações, sem validação automática.**

**Rebaseline de sequenciamento:** em vez de implementar todas as páginas comuns antes do workflow, primeiro **provar o reuso que já existe** e fechar a fundação de checklist/snapshot P6→P2; então liberar os slices P2, integrações de relatórios e P5/P3/P4 conforme suas dependências; P1/visões/tarefas tornam-se úteis conforme os produtores reais existem. Páginas comuns seguem roadmap, mas não bloqueiam arbitrariamente a prova do fluxo central. Isso é **proposta de ordem técnica por dependência**, não GO de implementação ou alteração de decisão de produto.

## 2. Auditoria do que já existe no HEAD — duas páginas e contratos

| Código e rota existentes | Contrato real / limite | R-ID(s) e destino no TO-BE | Classificação correta | Evidência a produzir no checkpoint |
|---|---|---|---|---|
| MFE `FinancialSettlementsPage.tsx` + API client e BFF `GET /closing/financial-settlements`, `/summary` → api-delpi `/financeiro/settlements/*` | Consulta operacional por período, payable/receivable, filtros, totais não oficiais/qualidade e paginação. **Não emite FINR190/DLP06R01 oficial nem prepara evidência validada P2.** | R01/R02 → item P2 (captura/relatório) e posterior P5; pode permanecer deep view operacional. | **CODE_PRESENT / REUSE_PARTIAL_FOR_PROCESS**; G6 ambos PENDING; R02 G4 PENDING E1 | Testar com usuário humano real e scope, correspondência do retorno com fonte e período/filial, amostra de documento original por G5, erros/siblings e limite de classificação; não fingir export/paridade |
| MFE `StockInventoryPage.tsx` + BFF `GET /closing/stock-inventory` → api-delpi `/financeiro/stock-inventory` | Snapshot operacional `SB9/SB1` por `B9_DATA`, recortes `all_products/mp_pi_pa`, filial/armazém, status `source_missing/incomplete`. **DTO `officialP7=false` e `parityStatus=TEST_NOT_RUN`; não é MATR460/P7 oficial**. | R03 + parte de R15 → visual auxiliar P3/P1, não prova do P7, paridade, cutoff ou sacramentação. | **CODE_PRESENT / REUSE_PARTIAL_FOR_PROCESS**; R03 G4/G5 pendente | Validar origem e competência reais, estados sem snapshot, regra de filial como filtro, contraste com PDFs P7 e divergências, AuthZ e S2S; provar limitação antes de UX nova |
| Home MFE e viewer-context BFF | Entrada e identidade; não é cockpit P1 nem workflow P2/P5. | Hub do Portal → futura Central | **CODE_PRESENT / NOT_P1** | Deep links e catálogo visível apenas quando rotas realmente autorizadas/funcionais |

**Inspeção HEAD feita nesta reavaliação:** `plugins/controllership-finance/src/app/pluginRoutes.ts` mapeia somente `home`, `financial_settlements`, `stock_inventory`; manifesto `controllership-finance.manifest.json` tem root + 2 deep routes e permissions atuais `.access/.manage`; BFF `closing_routes.py` + `viewer_context_routes.py`; consumidores MFE; arquivos de testes em MFE, BFF e api-delpi. A suíte existente cobre, entre outros, filtros/estados, source_missing, S2S, 403/scope_unavailable e 503. **Os testes foram lidos, mas não executados nesta rodada.** `TEST_NOT_RUN` neste SHA para execução nova, `RUNTIME_VERIFIED=INCONCLUSIVE` para experiência ponta a ponta. Não usar dois endpoints/telas como percentual implementado da Central.

**Checkpoint CP01 anti-overclaim:** separar as duas perguntas: (A) `consulta operacional funcional e segura?` e (B) `relatório oficial/entregável da Joici automatizado e homologado?`. (A) exige smoke/autorização/estado de fonte reais; (B) exige mapeamento item do checklist, arquivo/layout/parâmetros, paridade G5 e aceite funcional G6 quando aplicável. **PASS(A) não implica PASS(B).** Preservar páginas; só integrar, relabelar, reposicionar ou depreciar com decisão/evidência de consumidores.

## 3. Modelo de checklists e fontes — o que guia todas as etapas

**Entidade funcional de planejamento (não schema aprovado):** uma linha do checklist por competência deve ter `item_id/identificador de origem`, finalidade, aba Eletrônico/Físico, filial/unidade quando aplicável, `recipient`, pessoa/área responsável por produzir/anexar, origem TOTVS/externo/misto, formato/attachment role, applicability REQUIRED/CONDITIONAL/OPTIONAL governada pelo template P6, prazo somente se regra comprovada, regra de satisfação/validação, aprovador elegível, `source contract`, vínculo R-ID(s) se houver, estado, versões, event/audit e evidência de aceite.

A aba `Planilha1` do Ciclo 1 é vocabulário/catálogo candidato, **não** uma terceira tela ou estado de entrega. Não transformar célula não verde em N/A automaticamente. O template e obrigatoriedade são versionados; P2 mantém snapshot da competência aberta.

**Uma única visão de rastreabilidade por item:**  
`ITEM_CHECKLIST → R01..R15 OU EXTERNAL → owner da fonte → contrato real ou arquivo externo → coleta/automação → evidência/versão → validador humano → destinatário P5 → versão de pacote → status comprovado → RQ/AC → teste → gate`.

**Separações obrigatórias:** `ATTACHED != VALIDATED` (P2); `FINR190/P7 official != consulta SE5/SB9`; `STOCK_CLOSED != PACKAGE_FINALIZED != PACKAGE_SUBMITTED_FOR_REVIEW != MONTHLY_CLOSING_COMPLETED`; **P2 aceite de documento, G6 aceite funcional de relatório, P5 review por área e conclusão mensal são eventos diferentes**.

## 4. Grafo direto de entregas (dependências, não calendário inventado)

```text
C00 autoridade / checklist / contratos / gates + CP01 prova das páginas existentes
  └─ C02 P6 mínimo: template/versão/snapshot e catálogo governado [IMP-13 subset]
      └─ C03 P2 checklist por competência [IMP-09a]
          ├─ C04 P2 anexos externos/versões/storage [IMP-09b]
          │   └─ C05 P2 validação, rejeição, substituição, auditoria [IMP-09c]
          ├─ C06 catálogo de automação: R01..R15 por item/gates G1..G6 [Rxx batch]
          │   ├─ C07 P3 cutoff e conciliação E/S − P7 − H02 [IMP-10]
          │   └─ C08 P4 pendências/classificação e decisão humana [IMP-11]
          └───────────────┬───────────────────────────────────────┘
                          v
                C09 P5 pacotes/PackageVersion [IMP-12a]
                          |
                C10 P5 disponibilização, regras de análise e conclusão [IMP-12b-d]
                          |
                C11 P1 cockpit + tarefas/visões + P6 UI completa [IMP-08, IMP-01..07, IMP-13]
                          |
                C12 E2E multi-competência, segurança, operação, rollout [IMP-INT]
                          |
                CF-FUTURE Contabilidade/DRE: nova permission + página de histórico/download [doc 91]
```

**Grafo lógico, não waterfall rígido:** C06/C07/C08 podem correr paralelos às etapas P2 quando contratos/slices independentes comprovarem; o **cockpit P1** pode ter incremento honesto de leitura depois de C03/C06, mas **nunca** exibir fechamento concluído antes dos produtores P2/P3/P5. C10 e C12 dependem de regra de conclusão P5 reconciliada. Página futura de DRE tem gate próprio e não será incluída incidentalmente na C09/C10.

## 5. Trilhos executáveis — cada checkpoint mede resultado observável

**Legenda:** CP = evidência de checkpoint; `PENDING` = não fechado; `TEST_NOT_RUN` = sem testes executados nesta revisão. Nenhum CP recebe PASS apenas por existir documento ou código.

| Trilho / gate | Construção ou revisão por menor fatia | Pré-condições e owners | Checkpoint que autoriza sair da etapa | Estado 24/10 |
|---|---|---|---|---|
| **C00 / CP00 — Rebaseline** (sem runtime) | Congelar escopo E2E, inventário das 3 abas do checklist e R01–R15; matriz `item→owner→arquivo/fonte→destinatário→regra→RQ/AC`, revalidar docs TÉO completos e code map | TÉO AS-IS e TO-BE, docs 03/59/79/90/92; Product/Controladoria e arquitetura | **100% dos itens do checklist em escopo têm registro ou pendência explícita**, não “percentual de implementação”; links para fonte, owners e lacunas, HEAD/status do executor, contratos e decisão do próximo slice | **PENDING** — matrizes conceituais prontas, 1:1 ainda TO_INVENTORY |
| **C01 / CP01 — Auditoria duas páginas** (sem alterar por padrão) | Provar finance settlements e stock inventory como consultas reais, escopo, erros, indicadores, contratos e destino no P2/P3; medir delta contra entregáveis | MFE/BFF/api-delpi/Core; docs 48/49/51/52/88; Controladoria para paridade oficial | Testes rodados + smoke real autorizado de 2 perfis/competências quando aplicável, respostas com status verídico, nenhum acesso indevido, planilha de equivalência R01/R02/R03 `OPERACIONAL vs OFICIAL`, G5/G6 sem promoção inferida | **INCONCLUSIVE / TEST_NOT_RUN nesta revisão** |
| **C02 / CP02 — P6 contrato mínimo** (documentar→GO específico→implementar) | Template/versionamento de checklist, catálogo de requisitos/roles/recipients e snapshot da competência que P2 consome | Core effective permissions, owner P6, E01/E05/E06/T05; docs 13/17/23; DEC-04 | Publicação não altera competências abertas; teste de edição concorrente/stale revision, scope MANAGE, versão prospectiva, histórico; contrato físico e owner aprovados | **PENDING / TARGET** |
| **C03 / CP03 — P2 leitura e operação da competência** | Lista de itens, obrigatoriedade, responsável, origem e estado, detalhe, filtros/deep links, completude parcial sem inventar aprovação | CP00, CP02; docs 09/23/59/90; Portal CF | Criar/consultar duas competências com snapshots diferentes, REQUIRED não vira N/A, sem criar admin/config genérica; evidência de lista e estados + negative auth + F5 + Help | **PENDING / TARGET** |
| **C04 / CP04 — P2 anexos e documentos** | Upload de extratos, PDFs, XLS/artefatos permitidos, metadados de origem, multi-anexo e versão, preview/download autorizados e auditáveis | CP03, storage/plataforma real inventariado e owner aprovado, E05, security/retention/OCC | Arquivo permanece após recreate/mudança controlada; hash/metadados e versões referenciáveis; leitura não autorizada negada em URL direta; `ATTACHED` não vira VALIDATED; arquivo rejeitado preservado | **PENDING / TARGET** |
| **C05 / CP05 — P2 validação pela Controladoria** | Validator elegível aceita/rejeita com motivo, replacement, revisão, requisitos e histórico; Joici pode ser uploader **e** validator mediante autorização independente por ação | CP04, E06/T05, RQ-P2-03..11, docs 09/23, detailed TÉO 31.3–31.13 | Caso mesmo ator anexa e valida gera **dois eventos**, sem autoaceite; segundo validador sem scope negado; substituição volta a pendente; PER_ATTACHMENT/WHOLE_SET e siblings testados | **PENDING / TARGET** |
| **C06 / CP06 — Automação dos relatórios** | Producer contracts/queries governados por lote R-ID, geração de resultado estruturado e evidência versionada para checklist, manual enquanto fonte incerta | CP00/03/05 onde necessário; api-delpi owner TOTVS, Controladoria G6, E1–E12 C2 | **Por R-ID**: G1–G6 rastreados, parâmetros/competência/filial, comparação com arquivo oficial/validação de externalidade, auditoria de divergências, prova READ reprodutível + aceite G6. Passar Rxx não passa irmãos | **R01..R15 C2: 47/60,55/90,0/15**; runtime C06 **NOT_STARTED** |
| **C07 / CP07 — P3 estoque/cutoff/conciliação** | Evidências de R05/R03/R08 e estado externo, corte humano, revalidação, indicadores de divergência | T03 ERP/STOCK_CLOSED e fontes oficiais P7/H02/E/S; docs 10/15.1/82 | Paridade exata R$0,00 após cutoff e revalidação; R$0,01 ou −R$0,01 bloqueia; source_missing/zero pré-cutoff não fecha; Portal não escreve sacramentação ERP; owner valida estado | **PENDING / STOP T03/E2/E5** |
| **C08 / CP08 — P4 classificações e pendências** | Captura de divergências, origem, responsável, classificação sugerida, decisão humana, justificativa e audit | P2/P3 sources; T01/T05, owners CC/ERP; docs 11/23 | Atribuição/reatribuição auditada, sibling independente, sugestão IA não vira decisão, não escreve correção Protheus; negativo de scope e de regra | **PENDING / TARGET** |
| **C09 / CP09 — P5 composição e finalização** | Seleção de entregáveis validados por destinatário, PackageVersion imutável, finalização ≠ envio; versão histórica | P2 completo para material requerido, P6 catálogo recipients, CP02; docs 12/23/37 | Duas versões e dois destinatários; edição de versão finalizada proibida, snapshot legível sem contaminação de sibling; evidência de versão e conteúdos reais | **PENDING / TARGET** |
| **C10 / CP10 — P5 disponibilização/review/conclusão** | Enviar para análise in-portal, notificação, review/clarification se aplicável, conclusão mensal; **DRE read-only sem aceite na primeira versão** | CP09, Core T05/owner, regra C2 doc 37, decisão PO doc 91, destinatários/áreas e estados | Sem e-mail anexo, falha notificação não desfaz negócio; revisão humana auditada onde aplicável; sem aprovador não gera aceite por vacuidade; conclusão somente se invariantes **reconciliados e aprovados**. **STOP: reconciliar P5 C2 antes de alterar outcome** | **PENDING / DECISION_REQUIRED para conflito de conclusão** |
| **C11 / CP11 — Cockpit e superfície integrada** | P1 agrega estados separados de P2/P3/P4/P5 com fontes reais; Home, Minhas tarefas, Visão geral, Sala, Administração e Ajuda progridem conforme produtores | CP03/05/07/09/10 para estados dependentes; plugin-ui, Core e owners, docs 08/24–32 | Cockpit não equipara estoque fechado a pacote enviado; tarefas self-only, links autorizados, ausência de source sem falso verde; tema/mobile/teclado/foco/Help; páginas comuns só com capability real | **PENDING; Home CODE_PRESENT** |
| **C12 / CP12 — Integração e operação** | Caminho E2E de duas competências, duas filiais quando aplicáveis, múltiplos destinatários, versões e atores; regressão/observabilidade | CP02–11 pertinentes aprovados, contratos/owners, docs 41/43 | E2E positivo, sibling e negativo em SHA final; persistência sob restart, autorização real, rollback, deploy/smoke sob GO separado, aceite da Controladoria no cenário-alvo | **TEST_NOT_RUN / RELEASE_NOT_AUTHORIZED** |
| **CF-FUTURE / CP-F** | Permissão específica e página de documentos históricos da Contabilidade/DRE, leitura/download sem aceite | Decisão opção B **aprovada** mas **implementação adiada**, doc 91; contratos P5/arquivo, manifest/Core/guard/BFF | Usuário permission-only navega na entrada restrita, vê/baixa somente pacotes seus por histórico; sem aceite/rejeição; outros pacotes/rotas negados por HTTP BFF e Portal; rollback do novo grant | **DEFERRED_BY_PO / NO_RUNTIME** |

### Integração dos R01–R15 no trilho C06 (batch sugerido, não prazos)

| Lote | Itens | Estratégia / stop |
|---|---|---|
| **B0 — reuso existente** | R01/R02 consultas SE5; R03 SB9 operacional | CP01 primeiro; não chamar de FINR190/DLP06R01/MATR460 oficial, nem liberar exportação antes de paridade e autorização |
| **B1 — fontes oficiais investigadas** | R05 Entradas/Saídas, R06 CPV/Kardex01, R07 Inventários/Kardex99, R08 H02, R10 CC, R11 NF desconsiderar | Cada item precisa de binding, parâmetros/semântica owner, prova de output e G6; não abrir 6 endpoints/relatórios numa única PR |
| **B2 — fontes com residual crítico** | R03 P7 oficial, R04 Consumo OP, R09 Faturamento × MOD, R12 wizard, R15 cutoff/SB9 | E2/E9/E12/E5 e fontes/owners; separar leitura/consulta de processamento e escrita TOTVS, sem executar MATA280 |
| **B3 — externos/mistos** | R13 extratos bancários e aplicações, R14 importações/câmbio/SWIFT/ACSI | **P2 upload/validação** pode ser o contrato de captura do documento, sem inventar tabela SQL ou automação inexistente; proof é arquivo íntegro + aceite conforme regra |
| **Todos** | R01–R15 | Para cada filho de R-ID usar \`item_checklist_id | owner | source | parameters | evidence_G1..G6 | producer_contract | consumer_P2/P3/P5 | git_SHA\`. Não mudar denominador do tracker C2 sem \`scope_change\` formal. |

## 6. Gates de engenharia com provas que mudam o estado

**Todo trilho segue, nesta ordem; executar nada se pré-requisito falhar.**

| Gate | Pode avançar somente quando | Evidência aceita | FAIL / STOP |
|---|---|---|---|
| **A — INTENT/OWNER** | RQ/AC, source TÉO→GitHub, competência/filial, owner, ator, autorização, resultado de negócio e não-objetivos identificados | doc/linha, owner, decisão vigente, base HEAD e `git status` executado | owner ausente; scope ou interpretação de checklist deduzida; decisão material não aprovada |
| **B — CONTRACT/DESIGN** | Producer/consumer, BFF/DTO, persistência e storage quando preciso, resource scope/AuthZ, estados/erros e Help propostos e aprovados | contract gate com impactos backward compat, testes planned positive+sibling+negative e links | adivinhar fonte/tabela/permission/framework; browser chamar api-delpi; violar documento 37 |
| **C — AUTHORITY FOR RUNTIME** | Gate transversal explícito + autorização **separada** para aquele slice/page pelo PO, e guardrails do HEAD atuais | `IMPLEMENTATION_AUTHORIZED=YES / SCOPE=<slice>` com SHA, data, owner e baseline; autorização específica não libera outros slices | sem GO, interromper no documental; não criar scaffold ou migration especulativa |
| **D — VERIFIED CODE** | Diff mínimo no owner canônico; testes de domínio/aplicação, contrato, BFF/AuthZ, UI e Help no mesmo PR | logs de comandos/resultados em SHA final, teste de recurso irmão, erro/forbidden, acessibilidade, build MFE federado | mock só prova mock; atualizar snapshot para mascarar regressão; CI isolado não prova objetivo |
| **E — BUSINESS OUTCOME** | Postcondition aferida com dados e artefatos comparáveis, leitura posterior, validação humana quando exige | arquivo/metadata/versão auditáveis, relatórios comparação G5 + aceite G6, transições reais P2/P5 conforme slice | 200, status HTTP, tela, spinner ou SQL rows sozinhos; smoke não executado = INCONCLUSIVE |
| **F — RELEASE/ROLLBACK** | Owners e operações aprovaram rollout, observabilidade, backup/retenção/rollback e smoke ambiente real | ticket/go-live separado, evidência de autorização e degradação de Core/storage/S2S | merge/deploy técnico não é aceite do processo; rollback impossível ou volume perde arquivos |

**Régua de qualidade fixa:** `PROVEN|TO_INVENTORY|PLANNED|TARGET` para evidência de fato; `PASS|FAIL|PENDING|INCONCLUSIVE|TEST_NOT_RUN|STALE_EVIDENCE` para gates; `ACCEPT|ACCEPT_WITH_RESIDUAL|REWORK|EXECUTION_DRIFT|INCONCLUSIVE` para GPT REVIEW. Cada checkpoint registra `BASE_SHA | HEAD_FINAL | owner | BR/RQ/AC | fonte/contrato | teste/comando/log | positive | sibling | negative | smoke | business_outcome | residual | reviewer | approval | NEXT`. Não marcar PASS com testes só encontrados no repositório.

## 7. Cenários E2E obrigatórios antes de chamar "aplicação completa"

1. **Checklist real:** duas competências, template vigente e novo; Eletrônico/Físico com aplicabilidade correta por matriz/filial; célula verde representa esperado, não entregue; item externo sem fonte não vira N/A silenciosamente.
2. **Automação e evidência:** consulta real de R01/R02 (ou outro Rxx com owner/gate), output com parâmetros/proveniência e versão; resultado diferente do documento oficial identificado como parcial; não promover G6 sem Controladoria.
3. **PDF/extrato manual:** Joici anexa, documento fica pendente quando requer validação; Joici, se elegível, executa validação como ação separada; versão rejeitada preservada, replacement retoma avaliação, WHOLE_SET/PER_ATTACHMENT respeitados.
4. **Conciliação:** P3 cruza E/S, P7 e H02 por mesmo período/corte com fontes válidas; R$0,00 pós-cutoff OK, R$0,01 negativo e erro fonte bloqueiam; nenhuma rotina de sacramentação executada pelo Portal.
5. **Pacote:** dois recipients e duas PackageVersions; finalizar não submete; pacote imutável; arquivos e validadores corretos, dados de sibling isolados; notificação não torna pacote aprovado.
6. **Revisão/conclusão:** testar somente após reconciliação contratual de C2: nenhum revisor humano elegível não aprova por vacuidade, área não aceita mantém pendente, histórico de mudança imutável e coordenador formal confirma eventual terminal.
7. **Segurança:** token sem capability, `manage` isolado, Core indisponível, 403 scope, recurso sibling, arquivo baixado fora de autorização, leitura retroativa de versão indevida e acesso por URL direta; MFE não é autoridade.
8. **Histórico Contabilidade FUTURO:** permission e página adiadas; quando liberadas, usuário acessa a entrada restrita, consulta/baixa somente material liberado e **não registra aceite**, com auditoria e validade histórica.
9. **UX/operacional:** light/dark na mesma árvore, desktop/mobile, teclado/foco, manual atualizado na mesma mudança, persistência de anexos após restart, S2S/503 honestos, monitoramento/rollback.

**Não definir SLA, percentuais de economia, velocidade-alvo ou datas inventadas.** O baseline AS-IS 960 minutos/mês do TÉO é `INFORMED`, não benchmark medido ou ROI realizado; ganhos só após instrumentação aprovada.

## 8. Regra de priorização e decisão aberta

**Prioridade por dependência para a próxima execução documental:**
1. `CF-C3-E2E-CP00-CP01-REBASELINE-VERIFY-001`: revalidar duas páginas/contratos/testes + checklist C1 em nível de item, distinguir gaps Rxx e owner, preencher CP00/CP01 (não programar).
2. `CF-C3-P2-DOCUMENTS-CHECKLIST-READINESS-001` (doc 92): fechar mapeamento RQ detalhado TÉO 31.3–31.13, contratos P6/P2, storage e validator scope.
3. GPT REVIEW; decisão/gate de contratos e menor sub-slice P6/P2; **solicitar** autorização runtime explícita após condições satisfeitas.
4. Avançar conforme grafo e medir cada CP; não voltar à antiga fila common-first se isso impedir o processo central sem evidência causal.

**DECISION_REQUIRED na hora apropriada, não resolvido por preferência neste roadmap:**
- Exata regra de `MONTHLY_CLOSING_COMPLETED` frente ao contrato P5 C2 (aceites humanos por pacote/área) e decisão de DRE/Contabilidade **somente consultar/baixar na V1**. DRE não é reviewer; não cancelar outros aceites sem decisão de negócio.
- Owner/storage e persistência/retention de P2/P5, contrato de snapshot P6, T05 elegibilidade Core, T03 `STOCK_CLOSED`, E1–E12 das fontes, eventual mudança material de fronteira/contrato. Onde houver contrato atual inequívoco, aplicá-lo sem nova decisão.
- Permission e página da Contabilidade: **produto aprovado, implantação expressamente adiada**. Código técnico sugerido no doc 91 é candidato, não string autorizada no manifesto.

## 9. Critério de conclusão do roadmap e responsabilidades

**Não declarar a aplicação "completa" por criação de páginas.** Registrar duas visões independentes:
- **COVERAGE DOCUMENTAL:** cada item esperado do checklist mapeado a regra de aquisição (automático/manual), P2 validation, P5 package, owner e RQ/AC ou pendência explícita; R01–R15 com gates preservados.
- **COVERAGE OPERACIONAL:** fluxo real por competência comprovado em CP02–CP12, autorização e isolamento, upload persistente, documentos validados, cálculos/conferências válidos, pacotes imutáveis e destinatários corretos. **Entrega de histórico para Contabilidade continua obrigatória para a visão de produto completo**, embora esteja DEFERRED por decisão do PO; não publicar status `FULL_SCOPE_COMPLETE` enquanto CF-FUTURE não for concluído ou formalmente retirado do escopo por decisão posterior.

**Ownership de gate:** Controladoria/PO aceita conteúdo/decisão de negócio; Core aceita o desenho de RBAC/effective permissions e grants quando aplicável; TI Protheus/api-delpi comprovam fonte/semântica ERP; Portal CF comprova BFF, orquestração, ACL de recurso e P2/P5; qualidade/release validam smoke, UX, observabilidade e rollback. Names concretos/atribuição formal permanecem TO_INVENTORY onde não identificados.

**Veredito documental desta revisão:** `ACCEPT_WITH_RESIDUAL` — roadmap existente localizado e rebaselined por descobertas, duas páginas classificadas corretamente, trilhos e outcomes definidos; **nenhum checkpoint de runtime foi executado**, CP00/01 PENDING/INCONCLUSIVE, decisões de fechamento e contratos físicos remanescentes explicitados. **IMPLEMENTATION_AUTHORIZED=NO.**

**Próxima ação inequívoca:** executar o brief CP00/CP01 acima (READ/VERIFY/REPORT) e alimentar este roadmap com evidência fresca; depois o gate P2 do doc 92. Nenhuma permissão/rota de Contabilidade deve ser criada neste momento.
