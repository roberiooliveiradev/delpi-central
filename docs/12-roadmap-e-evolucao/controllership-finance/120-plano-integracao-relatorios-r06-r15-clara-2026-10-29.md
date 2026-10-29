# Plano de continuidade — integrações de relatórios e CLARA (29/10/2026)

> **Estado:** TARGET/PLANNED; plano autorizado para preparação e gates, **não** autorização de runtime. **Autoridade:** doc 118 (processo), doc 85 (BR), doc 83/84 (provas), doc 113 (fluxo), HEAD (implementação), TÉO (AS-IS). Revisão de roadmap não equivale a homologação de relatórios nem publicação do corpus CLARA.

## 1. Baseline (verificar novamente no HEAD antes da execução)

- **R01/R02:** consultas de baixas financeiras operacionais existentes; R02 permanece com lacuna do produtor custom E1. Não confundir consulta SE5 com equivalência oficial.
- **R03/P7:** consulta operacional com escopos `all_products` e `mp_pi_pa`; CSV/PDF; paridade MATR460 pendente (E2).
- **R05/MATR320:** consulta operacional e CSV/PDF; paridade oficial pendente.
- **R08/MATR989/H02:** consulta operacional e CSV/PDF; paridade oficial pendente (E8).
- **Conciliação analítica:** composição de saldos SB9 classificada `IDENTITY_ONLY`; não comprova paridade entre emissões independentes nem conclui P3.
- **P3 governado:** registro e validação próprios, não dependentes de cadastro documental; análises, filtros e exportações são independentes da superfície Documentos e interações.
- **Frontend:** REWORK-013 é somente refinamento pontual de cartões, indicadores, matriz, navegação e Help; PDF terá verificação final separada. Não presumir entrega do 013 antes do relatório e SHA.

## 2. Sequência recomendada dos próximos gates

| Ordem | Pacote | Escopo operacional proposto | Reuso e evidências | Condição de entrada / bloqueio |
|---|---|---|---|---|
| 014 | R06 CPV/Kardex + R07 INVENT | Consulta por competência/filial/produto/armazém; movimentos, resumos, investigação de custos e inventário; exportação só após contrato | MATR910, regras BR-R06/BR-R07 e DR-09/DR-10, `matr910_dlp.prx`, SD1/SD2/SD3, saldo SB9 anterior; CPV existente `REUSE_PARTIAL` | Gate transversal: owner, grão, filtros, custos, `as_of`, produtores/consumidores, authz e comparação com artefatos `cpv 09 26 matriz.xlsb`/`Invent.xlsb`. Não equiparar paridade histórica a G6 |
| 015 | R10 Centro de Custo + R11 NF a desconsiderar | Consultas analíticas separadas, sem exclusões automáticas em relatórios vizinhos | EDAPP/SD1/SD2; DR-11/DR-12; view CC `REUSE_PARTIAL` | E10 (classificação manual Direto/Ind/Adm) e E11 (finalidade/exclusões) verificados; não inventar classificação |
| 016 | R09 Faturamento × MOD | Faturamento, tempos, horas e custos por filial com proveniência e ausências explícitas | DLP204; SD2/SHY/SG2/SH1/SBZ; DR-13 | E9 (SP/producer), lacunas dos tempos/custos e G5 `INCONCLUSIVE`; sem custo zero substituto |
| 017 | R12 estado de custos + R15 cutoff | Painel READ de MATA320/MATA300/MATA330/MATA280, `MV_ULMES`/SB9 por filial; nada de executar ERP | doc 118 OPS-01..04, doc 85 BR-R12/R15; T03/owner canônico | Confirmar contrato existente de estado e proveniência; sem execução de rotinas/write no Portal |
| Depois | R04, R13, R14 | Consumo por OP e fontes financeiras/externas | R04 produtor/artefato ausente; R13 bancos/aplicações; R14 importação/câmbio | `DECISION_REQUIRED` se owner, fonte, contrato ou integração externa não estiver decidido |

**Cada pacote exige:** HEAD + git status, instructions/.cursor, inspeção dos contratos e producers/consumers atuais, owner+RQ/AC, gate documental e de segurança antes de runtime, implementação mínima page-by-page, testes, smoke, evidências, SHA e revisão GPT. Nada está autorizado a instalar nova permissão por relatório; somente `controllership-finance.access`, `controllership-finance.manage` e `controllership-finance.access.dre` (esta apenas documentos DRE autorizados).

## 3. Análises transversais vinculadas

1. CPV e evolução de custo por produto/filial, com divergências e encadeamento de movimentos (R06).
2. Inventário/ajustes de estoque, sem exclusão ou retificação automática (R07).
3. Despesas por centro de custo e tratamento explícito das classificações manuais (R10).
4. NF a desconsiderar como seleção investigativa, sem propagação de exclusão implícita (R11).
5. Faturamento versus mão de obra direta, custos e tempos não disponíveis como nulos explícitos (R09).
6. Estado de fechamento de custo, virada e cutoff por filial (R12/R15).
7. Paridade independente das emissões oficiais MATR320/MATR460/MATR989: frente de homologação distinta do controle `IDENTITY_ONLY`; comparar mesmo período, filial, escopo, versão e `as_of`.

## 4. CLARA — atualização de conhecimento e responsabilidades

**Verificação READ de 29/10/2026:** `get_catalog` informa corpus `5d546360-ab37-410c-80e8-e1a5748ed56e`, publicado em **27/10/2026 09:11:19 -03**, com 56 fontes e 1.713 itens. É anterior aos REWORK-010/011/012 e a este plano. **Corpus atualizado: NÃO COMPROVADO / sincronização PENDING.** As ferramentas CLARA disponíveis nesta sessão são de leitura, análise e operações governadas do fechamento; nenhuma ferramenta de refresh/publicação do corpus foi exposta.

**Handoff ao owner do pipeline CLARA:** incluir este documento, doc 118/113/119 e evidências técnicas atuais no processo oficial de ingestão; gerar versão/hash novos; publicar por caminho governado; verificar `get_catalog` + `list_knowledge_sources` + buscas com citações após a publicação. Não atualizar hashes/versões à mão e não afirmar que a CLARA já sabe do plano antes dessa prova.

**Diretrizes funcionais para CLARA após publicação:** explicar a fila 014→017 e os bloqueios; diferenciar `consulta operacional`, `paridade oficial`, `conciliação analítica IDENTITY_ONLY` e `P3 governado`; não recalcular divergência na CLARA (usar owner/BFF READ); não associar análise/exportação a documento cadastrado; não executar Protheus; exigir evidências e permissão efetiva nas leituras. Para novas consultas, fonte de runtime = tools READ, conhecimento = corpus com `citation_locator` e classificação de evidência.

## 5. Próximo passo autorizado

**Próximo gate proposto:** `CF-PROC0072-R06-R07-CONTRACT-GATE-014` — READ/VERIFY do reuso MATR910 e CPV existente, contratos, grão, `as_of`, autorizações, provas dos XLSB e RQ/AC; entregar gate documental, não scaffold/runtime automático. Em paralelo, encaminhar refresh CLARA ao owner. A homologação humana G6 continua `PENDING` quando não executada.
