# Documento 90 — Crosswalk E2E PROC-0072 · TÉO → RQ/AC → capacidades → páginas Portal

**Data:** 2026-10-24. **Rodada:** CF-C3-PROC0072-ENDTOEND-CROSSWALK-001.  
**Produto:** Portal Controladoria & Finanças. **Primeira funcionalidade:** Central de Fechamento. **Processo:** PROC-0072.  
**Base GitHub inspecionada:** main 7237b92a5d5a00f473672b7f03a6b4bcf85386b0 (revalidar HEAD para novos gates).  
**TÉO:** consulta READ ao processo, contexto/decomposição, 43 documentos catalogados e excerpts disponibilizados de 05/06.1/06.2/07/30/31/31.1–31.19/33/34. O TÉO retorna textos truncados nos documentos longos; este crosswalk indica esse limite e usa [doc 19](./19-rastreabilidade-teo.md) para IDs e proveniência.  
**Natureza:** DOCUMENTATION_ONLY. Não houve leitura/escrita operacional Protheus, execução de testes ou alteração de runtime. **IMPLEMENTATION_AUTHORIZED=NO nesta rodada.**

## 0. Resultado e interpretação correta de escopo

O PROC-0072 não é somente consulta de SB9/SE5. Seu AS-IS é **abertura da competência e checklist → produção/coleta dos entregáveis → conferência/conciliação e tratamento de divergências → cutoff/sacramentação Protheus → consolidação e encaminhamento → esclarecimentos e conclusão mensal**. O TO-BE aprovado é um **workflow completo** com automações progressivas, documentos externos e PDFs, validação humana, versionamento, pendências, pacotes/revisão humana, auditoria, administração e integração com a Minha DELPI.

**P1–P6 são a funcionalidade completa, não apenas telas opcionais.** As decisões C3-D01=A, D02=A, D03=B, D04=B, D05=A, D06=A ([88](./88-ciclo3-r01-inventario-contratos-e-pacote-decisoes.md), [89](./89-ciclo3-decisoes-aprovadas-e-gate-documental-r02.md)) delimitam **somente a primeira fatia read-only de escopo/design**, e não revogam as decisões anteriores do TÉO 31/33 ou do [contrato canônico P5, doc 37](./37-p5-submissao-e-revisao-no-portal.md). Diferenciar “V1 funcional P1–P6” de “primeira fatia C3 read-only”; interpretar um como substituto do outro configura EXECUTION_DRIFT documental.

**Ciclo 2 = descoberta técnica das fontes e dos 15 entregáveis**; **Ciclo 3 = alinhamento de contratos, páginas e automação do workflow completo**. A medição C2 permanece 47/60 coleta, 55/90 auditoria, 0/15 com G6 humano.

## 1. Authority e fontes

| Tema | Fonte verificável | Uso correto |
|---|---|---|
| Processo, evidências e handoffs | TÉO PROC-0072: docs 04/05/06/06.1/06.2/07/30 + contexto do processo; [GitHub 02](./02-proc-0072-as-is-e-baseline.md) | Authority de AS-IS, proveniência e objetivo da melhoria |
| TO-BE, decisões e readiness | TÉO docs 31, 31.1–31.19, 33 e 34 (identificadores em [doc 19](./19-rastreabilidade-teo.md)) | TO-BE funcional aprovado; pendências de binding técnico não reabrem decisão por preferência |
| P1–P6 e RQ/AC | [GitHub 08](./08-p1-cockpit-da-competencia.md), [09](./09-p2-checklist-e-documentos.md), [10](./10-p3-estoque-cutoff-e-conciliacao.md), [11](./11-p4-classificacoes-e-pendencias.md), [12](./12-p5-pacote-finalizacao-e-envio.md), [13](./13-p6-administracao-e-configuracao.md), [23](./23-ledger-rq-ac-testes.md), [37](./37-p5-submissao-e-revisao-no-portal.md) | Contratos funcionais TARGET; RQ/AC detalhados no ledger; documentado não é implementado |
| Relatórios e produtores | [47](./47-t01-report-column-audit-tracker-v1.md), [80](./80-ciclo2-registro-vivo-investigacao-devin.md), [82](./82-ciclo2-handoff-pacote-evidencias-owners.md), [85](./85-ciclo2-catalogo-regras-negocio-r01-r15.md), [86](./86-ciclo2-relatorio-final-consolidado-e-handoff.md) | Paridade e residual C2, não aceites P2/P5 |
| Contratos/código existentes | [88](./88-ciclo3-r01-inventario-contratos-e-pacote-decisoes.md); MFE src/app/pluginRoutes.ts e src/features/closing/StockInventoryPage.tsx e FinancialSettlementsPage.tsx conferidos no HEAD | CODE_PRESENT, não RUNTIME_VERIFIED; rotas existentes não comprovam workflow P1–P6 |
| UI, segurança e padrões | [24](./24-inicio-e-navegacao-principal.md), [30](./30-plugin-ui-reuse-map.md), ADRs, instruções oficiais e regras .cursor aplicáveis | @delpi/plugin-ui first; Core = permission authority; MFE chama apenas BFF |

## 2. Crosswalk AS-IS → capacidades TO-BE → outcome

| Etapa do PROC-0072 | Capacidade do Portal | Authority | Aceite/outcome esperado |
|---|---|---|---|
| Abertura e checklist | P1 contexto e três eixos; P2 checklist por competência, originado da versão publicada por P6 | TÉO 31/31.1/31.17; GitHub 08/09/13/23 | Snapshot da versão vigente, itens aplicáveis, responsáveis, sem alterar competência aberta ao publicar template novo |
| Geração, coleta e automação | P2 itens, resultados de APIs autorizadas e documentos externos; P4 exceções | TÉO 05/07/30/31.1–31.13; GitHub 09/11/47/85 | Dados estruturados com proveniência; PDF/anexo ATTACHED != ACCEPTED quando exige validação |
| Conferência e divergências | P2 validador, rejeição/replacement; P3 paridade E/S–P7–H02; P4 classificação/humano | TÉO 06.2/31.3/31.4/31.14/31.15; GitHub 09/10/11/15.1/23 | Paridade EXATA R$0,00; qualquer centavo não zero = divergência; pendência e decisão auditadas |
| Cutoff e sacramentação | P3 confirmação do corte, revalidação e estado externo STOCK_CLOSED | TÉO 31.14; GitHub 10/23; produtor Protheus E5/T03 | Portal não executa a virada no ERP na V1; READY_TO_CLOSE != STOCK_CLOSED; sem fallback local silencioso |
| Consolidação e submissão | P5 gera PackageVersion por destinatário, separa Finalizar e Enviar para análise | TÉO 31.16/33; GitHub 12/23/37 | Finalizar não submete; submeter dentro da Minha DELPI não conclui competência nem transporta PDF por e-mail |
| Aceites, esclarecimentos e conclusão | P5 revisores autorizados por área/versão, complementos, rejeição terminal formal, conclusão; tarefas e notificações | TÉO 31.16/31.17; GitHub 12/23/27/37 | Pacotes aplicáveis submetidos, aceite humano real por pacote e cada área obrigatória existente, nenhuma clarification aberta e nenhuma rejeição terminal |

**Invariante da conciliação:** DIVERGENCIA = ENTRADAS_SAIDAS − P7 − H02. PARIDADE_OK apenas se R$0,00 (TÉO 06.2; [GitHub 15.1](./15.1-p3-criterios-paridade-monetaria.md)). R$0,01, −R$0,01 ou qualquer outro valor não zero é divergência, inclusive antes de eventual critério de prontidão.

## 3. Matriz P1–P6 — processo, RQ/AC, código e gaps

| Página | TÉO TO-BE | RQ/AC GitHub | Capacidade existente no HEAD | Lacuna / owner / status |
|---|---|---|---|---|
| **P1 Cockpit** | 31, 31.1, 31.2, 31.18 | [08](./08-p1-cockpit-da-competencia.md), [23](./23-ledger-rq-ac-testes.md): **RQ-P1-01..07** (competência, três eixos independentes, blockers, source, histórico, ajuda) | MFE Home + viewer-context; **Home não é P1**; /closing cockpit não consta do pluginRoutes inspecionado | Composition state P2/P3/P5, eventos e blockers: Portal CF + api-delpi/Core; TARGET/TO_INVENTORY; IMP-08/P1 NO_GO |
| **P2 Checklist e Documentos** | 31.1/31.2 e **31.3–31.13** | [09](./09-p2-checklist-e-documentos.md), [23](./23-ledger-rq-ac-testes.md): **RQ-P2-01..12**, detalhes TÉO 31.x a reconciliar por ID | Nenhuma página P2 nem contrato de upload/validação confirmado nas rotas CF existentes | Template/snapshot, arquivo/versão, item, validator, audit, notifications; Portal CF + Controladoria + storage/Core owners; TARGET/CONTRACT_PENDING |
| **P3 Estoque, cutoff e conciliação** | 31.14/06.2 | [10](./10-p3-estoque-cutoff-e-conciliacao.md), [15.1](./15.1-p3-criterios-paridade-monetaria.md), [23](./23-ledger-rq-ac-testes.md): **RQ-P3-01..10, RQ-P3-08A, AC-P3-PARITY-01..07** | StockInventoryPage + BFF/api-delpi SB9 operacional; **consulta SB9 não é P7 oficial MATR460, nem a P3 completa** | Cutoff, revalidação, E/S–P7–H02, freshness e STOCK_CLOSED canônico: ERP/api-delpi+Controladoria; REUSE_PARTIAL/TARGET, STOP T03 |
| **P4 Classificações e Pendências** | 31.15 | [11](./11-p4-classificacoes-e-pendencias.md), [23](./23-ledger-rq-ac-testes.md): **RQ-P4-01..08** | Views de CC/indicadores adjacentes são REUSE_PARTIAL; não demonstram workflow P4 | Estados da pendência, ownership, sugestão IA, confirmação humana, audit; Portal CF/owners; TARGET |
| **P5 Pacote e Revisão** | 31.16, 33 Q18–Q26, 31.18 | [12](./12-p5-pacote-finalizacao-e-envio.md), [23](./23-ledger-rq-ac-testes.md): **RQ-P5-01..12, AREA-01..06, TERM-01..03, F..J**; [37](./37-p5-submissao-e-revisao-no-portal.md): **C2/P5-A..J/DEC-01..04** | Nenhuma PackageVersion, submissão/review ou página P5 demonstrada na fatia atual | Domínio de pacotes/versões/recebedores, Core eligibility T05, OCC, audit, tasks, notificações T02; Portal CF + Core; TARGET/PHYSICAL_BINDINGS_TO_INVENTORY |
| **P6 Administração** | 31.17, 31.18, 31.12.1 | [13](./13-p6-administracao-e-configuracao.md), [28](./28-administracao.md), [23](./23-ledger-rq-ac-testes.md): **RQ-P6-01..10** | Sem página P6 de configuração do processo no pluginRoutes atual; Core RBAC não substitui P6 | Template DRAFT/REVIEW/PUBLISH/EFFECTIVE_FROM, catálogos, motivos/roles e snapshot; Portal CF MANAGE com scope, Core RBAC owner; TARGET |

**Estados da execução:** páginas Home, FinancialSettlementsPage e StockInventoryPage e rotas de MFE constam do código; BFF e api-delpi foram inventariadas no [doc 88](./88-ciclo3-r01-inventario-contratos-e-pacote-decisoes.md). Isso é CODE_PRESENT. Nenhum smoke foi executado aqui: TEST_NOT_RUN/RUNTIME_VERIFIED não declarado.

## 4. P2 — subfluxos de PDFs, extratos, aceite documental e exceções

| Subfluxo / TÉO | RQ/AC | Regra vigente / próximo binding |
|---|---|---|
| Template por competência e tipos de item — 31.2/31.17 | RQ-P2-01/02; RQ-P6-01/02 | Snapshot na abertura, REQUIRED/CONDITIONAL/N/A; publicar depois não muda aberto; persistência e catálogo TARGET |
| Extratos, aplicações, SWIFT, câmbio e documentos externos — AS-IS 05/07, R13/R14 | RQ-P2-02/03/12; R13/R14 doc 47 | Responsável entrega evidência externa; Controladoria ou validador elegível confere no Portal; upload, formato, roles E05 e ownership a inventariar; não inventar SQL para PDF |
| Anexo e validação — 31.3 | RQ-P2-03/04/05 | ATTACHED != ACCEPTED; rejeição não apaga versão, motivo estruturado, replacement não herda aceite; validator/registro auditável TARGET |
| Multi-anexo — 31.4 | RQ-P2-06 | PER_ATTACHMENT ou WHOLE_SET configurável por tipo; validação no backend TARGET |
| Reversão de rejeição — 31.7/31.8 | RQ-P2-10/11 | Só validador elegível, sem replacement posterior; notifica os destinatários originais; **não** confundir com aceite P5 irreversível |
| Itens excepcionais — 31.9/31.10 | RQ-P2-07/09 | ACCESS com scope cria item da competência e ajusta atributos antes de execução; sem alterar mestre |
| Cancelamento e revisão estrutural — 31.11/31.12/31.12.1/31.13 | RQ-P2-08/09 | CANCELLED só antes de evento material, sem delete; após execução ACCESS solicita revisão, MANAGE pode aprovar inclusive própria solicitação no scope, preservando histórico |
| Notificações e idade — 31.5/31.6 | RQ-P2-11; T02 | Notificação canônica Minha DELPI, e-mail via capacidade existente; **SEM SLA, overdue ou escalonamento**; pending_since/idade factual |
| Validação humana e segurança | RQ-P2-03..06/09 e AC do ledger 23 | Validador/area/owner sob scope e regra; só access/manage, nunca permission code por PDF/documento |
| Gaps de granularidade TO-BE | TÉO 31.13 exibe **RQ-P2-039**; ledger 23 resume **RQ-P2-01..12** | **TO_INVENTORY:** reconciliar RQs/ACs detalhados dos documentos TÉO 31.3–31.13 com ledger 23 antes do brief P2; não inventar correspondência literal |

**Não confundir aceites:** P2 = aceite da evidência de um item; P5 = aceite da PackageVersion por revisor/área; G6 do Ciclo 2 = aceite funcional dos relatórios analisados; MONTHLY_CLOSING_COMPLETED = conclusão da competência após regra C2 do P5.

## 5. Regras críticas P3/P4/P5/P6 e distinções

| Regra | Authority/RQ/AC | Consequência |
|---|---|---|
| Cutoff e revalidação | TÉO 31.14; RQ-P3-01/02/04..09 | Cutoff por humano, fontes frescas, revalidação ao mudar input; zero pré-cutoff não fecha |
| Paridade monetária exata | TÉO 06.2; AC-P3-PARITY-01..07 | Somente R$0,00 pós-cutoff/revalidação; qualquer diferença ou source_missing impede READY_TO_CLOSE |
| Sacramentação | RQ-P3-07/08/08A | Portal P3 não escreve Protheus na V1; STOCK_CLOSED vem do owner/ERP se existir, sem fallback manual |
| IA/classificação | TÉO 31.15; RQ-P4-01/02 | IA sugere; confirmação humana autorizada; P4 não corrige ERP diretamente V1 |
| Pendências | RQ-P4-03..07 | State machine fechada; claim/reassign; DISMISSED motivado; sem SLA fictício |
| Finalização | TÉO 31.16; RQ-P5-01/02/03 | PackageVersion imutável; Finalizar não Envia; reabrir antes de submissão preserva versão anterior |
| Enviar para análise | [37](./37-p5-submissao-e-revisao-no-portal.md), RQ-P5-04..08 | **Portal-first:** submetida a revisores autenticados Minha DELPI, e-mail apenas avisa/link, sem pacote anexo; notificar != business state |
| Aceite humano P5 | RQ-P5-09/10/12, AREA-01..06, TERM-01..03, F..J, doc 37 | Áreas obrigatórias e PackageVersion vigente; nova versão exige novos aceites; elegibilidade via Core ACCESS+scope+regra; aceite P5 irreversível no V1 |
| C2 — conclusão mensal | doc 37 C2/P5-A/D-FINAL-02, RQ-P5-12 e AREA-05 | Todos os pacotes aplicáveis submetidos, aceite humano real por pacote e cada área obrigatória existente, nenhuma clarification aberta/rejeição terminal; conjunto vazio não aprova automaticamente nem cria trava extra de envio |
| Administração | TÉO 31.17, RQ-P6-01..10 | DRAFT→REVIEW→PUBLISH→EFFECTIVE_FROM, catálogos e snapshots; MANAGE efetivo + escopo; Core mantém identidade/RBAC |

**Resolução da aparente divergência Q22:** TÉO 31.16/33 registra o canal de envio como pendente em 05/10; o contrato **posterior e específico** [doc 37](./37-p5-submissao-e-revisao-no-portal.md) aprovou o P5 portal-first. E04/T04 continuam inventários quando aplicáveis; **não** tornam anexo de e-mail uma obrigação da V1.

## 6. Crosswalk R01–R15 — base dos relatórios/automação por página

| R-ID | Producer / evidência C2 | Uso na Central | Gate/lacuna |
|---|---|---|---|
| R01 | FINR190, SE5 baixar a pagar | P2 entrega automatizável, P5 pacote; deep page financeira já no MFE | G1–G5 PASS, G6 PENDING |
| R02 | DLP06R01 custom, SE5 baixar a receber | P2/P5, deep page financeira | G4 PENDING E1; G5 PASS |
| R03 | MATR460 P7 / Bloco H | P3 conciliação e P2 evidência; não equiparar ao SB9 operacional | G4/G5 PENDING E2 |
| R04 | MATR860 consumo por OP | P2 Produção e P4 exceções | G1–G4 PENDING, G5 TEST_NOT_RUN |
| R05 | MATR320 Entradas/Saídas | P3 paridade E/S–P7–H02, P2/P5 | G1–G5 PASS; contrato P3 não inferido |
| R06 | MATR910 Kardex/CPV 01 | P3 conferência P2 documento | G1–G5 PASS; RPO/params E7; CPV vivo REUSE_PARTIAL |
| R07 | MATR910 Inventários/Kardex 99 | P3/P2 | G1–G5 PASS; E7 |
| R08 | MATR989 Material em Processo H02 | P3 H02, P2 documento | G1–G5 PASS empiricamente; E8 |
| R09 | DLP204 Faturamento × MOD | P2/P4 custos/classificação | G5 INCONCLUSIVE; E9 |
| R10 | EDAPP SD1 Notas por CC | P2/P4/P5 | G1–G5 PASS; E10 |
| R11 | EDAPP SD2 NF a desconsiderar | P2/P4/P5 | G1–G5 PASS; E11 |
| R12 | MATA320/MATA300/MATA330/Análise | P3 readiness, P1 estado | G4 PASS; G5 INCONCLUSIVE; E12 |
| R13 | Extratos/aplicações externas | **P2 upload e validação de PDFs**, P5 pacote/review | G1 PASS, G2–G4 PENDING, G5 TEST_NOT_RUN |
| R14 | Importações/SWIFT/câmbio/ACSI | **P2 documentos externos**, P4 exceções, P5 | G1–G4 PENDING, G5 TEST_NOT_RUN |
| R15 | MATA330→MATA280→SB9, cutoff | P3 e P1; P5 depende de estado | G3/G4 PASS, G5 INCONCLUSIVE; E5 writer interno ainda pendente |

Os dados R01–R15 são **insumos** de processos P1–P6; as regras do doc 85 e testes por relatório permanecem fonte canônica. Nenhum relatório é promovido a G6 pela existência de paridade.

## 7. Automação e componentes atuais — distinção de CODE_PRESENT e TARGET

| Capacidade | Evidência no HEAD / doc 88 | Classificação para o workflow |
|---|---|---|
| Home e navegação inicial | MFE pluginRoutes.ts e Home existentes | CODE_PRESENT, **não é cockpit P1** |
| Estoque histórico | MFE StockInventoryPage + BFF stock-inventory + api-delpi SB9, segundo doc 88 | REUSE_CONFIRMED para consulta operacional, **não relatório P7 oficial nem P3 completa** |
| Baixas financeiras | MFE FinancialSettlementsPage + BFF settlements/summary + api-delpi SE5, doc 88 | REUSE_CONFIRMED para consulta; não entrega/validação de arquivo P2 |
| Outros relatórios R03–R15 | Inventário de producers/paridades no Ciclo 2 | REUSE_PARTIAL / TO_INVENTORY; não afirmar automação integral |
| Anexo, aceite de PDF e correção | TÉO 31.3–31.13 + GitHub P2 | TARGET: não comprovado na fatia atual |
| Conciliação tripla e cutoff | TÉO 06.2/31.14 + GitHub P3 | TARGET de workflow; fontes/estado T03 pendentes |
| Classificação e apoio IA | TÉO 30/31.15 + GitHub P4 | TARGET; sugestão IA nunca aprova sozinha |
| PackageVersion, revisão e envio | TÉO 31.16 + GitHub doc 37 | TARGET, sem endpoint/persistência P5 comprovados na fatia atual |
| Notificações e projeção Minhas tarefas | GitHub 26/27/37, Core/plataforma a inventariar | REUSE_PARTIAL / TO_INVENTORY; notificação não é aceite |
| Sacramentação Protheus automática | R12/R15 do C2 | **FORA DA V1 P3 em escrita**; Portal não dispara reabertura/fechamento implícito |

**Segurança:** só controllership-finance.access e controllership-finance.manage. Effective permissions via Core; backend fail-closed por capability AND ownership/vínculo AND resource_scope AND business_rule; filial/área/validador/reviewer são escopos de recurso, não permissions. MFE consome BFF própria; api-delpi detém regras TOTVS; sem import de domain/application alheio e sem banco do vizinho como API.

## 8. Páginas comuns e superfícies de apoio

| Superfície | GitHub/RQs | Papel no fechamento | Runtime CF |
|---|---|---|---|
| Início | [32](./32-inicio-home.md), RQ-HOME-01..09 | ponto de entrada e navegação | CODE_PRESENT |
| Visão geral | [25](./25-visao-geral-indicadores-financeiros.md), RQ-OVW-01..10 | visão analítica do produto multi-macroprocesso | TARGET |
| Sala de interação | [26](./26-sala-de-interacao.md), RQ-ROOM-01..12 | colaboração contextual; mensagem não muda estado P2/P5 por si | TARGET |
| Minhas tarefas | [27](./27-minhas-tarefas.md), RQ-TASK-01..12 | projeções self-only de validações/revisões P5 | TARGET |
| Administração | [28](./28-administracao.md), RQ-ADM-01..12 | P6 templates, catálogos e versão, não Core RBAC | TARGET |
| Ajuda | [29](./29-ajuda.md), RQ-HELP-01..11 | documentar somente features já disponíveis, sincronizada no gate | TARGET página; help contextual já nas deep pages |
| Página de usuário | [31](./31-pagina-do-usuario.md) | deep route, sem item na topbar | TARGET |

Topbar canônica [24](./24-inicio-e-navegacao-principal.md): Início, Visão geral, Sala de interação, Minhas tarefas, Administração e Ajuda. P1–P6 ficam no contexto da Central de Fechamento. @delpi/plugin-ui first ([30](./30-plugin-ui-reuse-map.md)).

## 9. Registro de lacunas verificáveis (sem reabrir produto)

| ID | Gap / bloqueio | Owner | Próxima evidência/gate |
|---|---|---|---|
| XW-01 | “V1” de docs C3 read-only ambígua versus V1 funcional P1–P6 | PO + arquitetura | Etiquetar por fatia; não reinterpretar C3-D01 como cancelamento de P2/P5. Prioridade futura de slices exige decisão se houver escolha material |
| XW-02 | IDs RQ/AC detalhados P2 no TÉO, ex. RQ-P2-039, sem correspondência literal 1:1 demonstrada no ledger 23 | Controladoria/produto + TI | TO_INVENTORY do texto integral TÉO 31.3–31.13 para brief P2; não inventar IDs |
| XW-03 | Fonte/storage/versionamento/anexo, validator scopes, roles E05 e motivos E06 | Portal CF + Core/Controladoria/owner storage | CONTRATO FÍSICO P2 a inventariar; testes negative/replacement/sibling |
| XW-04 | Cutoff, canon STOCK_CLOSED T03 e escritor SB9/MV_ULMES E5 | TI/ERP/api-delpi + Controladoria | Gate P3 quando owner fornecer contrato/outcome; não bloquear consulta SB9 existente |
| XW-05 | Elegibilidade reviewer Core T05, áreas por PackageVersion, coordinator binding | Core + Portal CF | Fail-closed, contrato S2S e tests de scope/área antes de implementar review |
| XW-06 | Modelo físico PackageVersion, recipients, estados/eventos, OCC, audit e clarifications | Portal CF + arquitetura | DECISION_REQUIRED se houver escolha real de persistência/contrato; não scaffolding |
| XW-07 | T02 Notifications; E04/T04 quando houver envio externo adicional | Core + Portal CF | Submissão portal-first já aprovada no doc 37; e-mail é só notificação |
| XW-08 | E1–E12 do Ciclo 2, R04/R13/R14 externos sem fonte; E01–E06/T01–T05 de implementação são **famílias distintas** | Owners nomeados em docs 17/82 e TÉO 34 | Inventários específicos por página; não converter search miss em ausência |
| XW-09 | Testes/smoke e contrato de página P1/P2/P3/P4/P5/P6 | PO + arquitetura + times owners | CODE_PRESENT != RUNTIME_VERIFIED; gate transversal + page-by-page obrigatório |
| XW-10 | P2 aceite de item, P5 aceite de pacote, G6 de relatório e conclusão mensal usados como sinônimos | Product + Controladoria | Quatro outcomes distintos e auditáveis; proibir colapso de estados |

## 10. Critérios de aceite da reconciliação e próximo gate

Este crosswalk cobre **produto completo, P1–P6, páginas comuns, R01–R15, principais RQ/AC e cadeia AS-IS→TO-BE→implementação**; não recria todos os 100 BRs/75 testes: estes permanecem vinculados pelos docs 85/23. Resíduos de RQ detalhado TÉO e contratos físicos estão identificados com owner.

Para briefs futuros, exigir matriz por página: **etapa PROC-0072 → autoridade TÉO → RQ/AC GitHub → fonte/produtor e contexto owner → contrato real ou TARGET → AuthZ → teste/erro → Help → gate**.

**Recomendação de encaminhamento:** manter a fatia read-only C3-D01..D06 como incremento inicial já aprovado para design; recolocar P2 (documentos e aceites) e P5 (pacote/submissão/review) como capacidades essenciais do backlog da Central de Fechamento, não como backlog de produto futuro indeterminado. Definir ordenação e autorização de runtime dos slices por decisão/gate explícitos. Nenhuma mudança de escopo original ou decisão de framework/persistência/endpoints foi feita aqui.

**Classificação da entrega documental:** ACCEPT_WITH_RESIDUAL — alinhamento E2E demonstrado; XW-02 e bindings físicos continuam TO_INVENTORY; sem G6 ou PASS de runtime inferido. **IMPLEMENTATION_AUTHORIZED=NO para esta rodada.**
