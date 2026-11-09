# 157 — Gate documental: conciliação analítica de estoque por unidade na aba Relatórios e divergências

**Data:** 2026-11-09  
**Processo:** PROC-0072 — Fechamento Mensal da Controladoria  
**Tipo:** PO-approved UX/behavior design; **DOCUMENTATION_ONLY**. Sem runtime, migration, rotas, deploy, alteração de V2 ou alteração na CLARA por este documento.  
**HEAD de baseline consultado:** `3a2da6021bd6e71d84c3e61954209882b396579c` em `main`. `git status` de checkout local não disponível neste canal — validar no Cursor.  
**Autoridade:** instruções oficiais GPT Arquiteto + .cursor aplicáveis + docs 118, 113, 15.1, 84, 119/152, 156 e testes/código no HEAD.  
**Aprovação funcional do PO:** 2026-11-09, nesta conversa: visão inicial **Por unidade**, com **Filial 01 + Filial 02 simultâneas**, e opção **Consolidado** que substitui as duas seções por uma única visão; sem seletor individual 01/02 nesta aba.

## 1. Escopo e comportamento de produto aprovados

Na terceira aba da competência, **Relatórios e divergências**, a seção **Conciliação analítica — Entradas/Saídas − P7 − H02** deve oferecer um único controle de visão:

- `Por unidade` (default): mostrar **duas seções completas**, na mesma página e em ordem fixa **Filial 01 — Matriz** e **Filial 02**, cada uma com:
  1. `Entradas e saídas (R05)`;
  2. `Posição de estoque P7 (R03)`;
  3. `Material em processo (R08)`;
  4. `Divergência analítica`.
- `Consolidado`: mostrar **somente uma** seção, rotulada `Consolidado — Filiais 01 + 02`, com os mesmos quatro indicadores.
- Alternância `Por unidade / Consolidado` **não muda a competência**, não altera persistência P3, não combina dados no browser e não obriga clique para conferir as duas filiais.
- Os cards de relatórios acima da seção e as páginas de relatório detalhado permanecem com seus filtros/drill-downs existentes, salvo mudança explicitamente justificada e aprovada.
- O bloco `Relatórios para análise` e Help precisam manter padrão `@delpi/plugin-ui`, estados de erro/loading, keyboard/focus, desktop/mobile e dark/light.

Esta é uma **escolha funcional aprovada de apresentação**, não autorização para scaffold de API, SQL novo ou troca do motor de cálculo.

## 2. Visual textual canônico

```text
Conciliação analítica — Entradas/Saídas − P7 − H02     [Por unidade | Consolidado]

[Por unidade — padrão]
Filial 01 — Matriz                          [Situação da conferência]
  Entradas e saídas (R05)                    [valor/status/data-base]
  Posição de estoque P7 (R03)               [valor/status/data-base]
  Material em processo (R08)                [valor/status/data-base]
  Divergência analítica                      [valor ou não calculada]

Filial 02                                   [Situação da conferência]
  Entradas e saídas (R05)                    [valor/status/data-base]
  Posição de estoque P7 (R03)               [valor/status/data-base]
  Material em processo (R08)                [valor/status/data-base]
  Divergência analítica                      [valor ou não calculada]

[Consolidado — alternativa]
Consolidado — Filiais 01 + 02                [Situação da conferência]
  Entradas e saídas (R05)                    [valor/status/data-base]
  Posição de estoque P7 (R03)               [valor/status/data-base]
  Material em processo (R08)                [valor/status/data-base]
  Divergência analítica                      [valor ou não calculada]
```

## 3. Inventário real do HEAD (não inferir implementação a partir de rota)

| Camada | Evidência encontrada | Decisão mínima |
|---|---|---|
| MFE `MonthlyReportsPanel.tsx` | monta aba e `Conciliação analítica` com um único `recon` | Reorganizar **somente** esta seção com modo e renderização por unidade/consolidado. |
| MFE `useMonthlyReportSources.ts` | `stockReconciliationQueryKey(scope,{period})`; `getStockReconciliation({period})` | Hoje omite `branch`, resultando em `all`. Inventariar hook/query-caching para 01/02/all sem chaves colidirem, garantido isolamento por usuário/capability. |
| API client `stockReconciliationApi.ts` | `StockReconciliationQuery {period,branch?,reportScope?}`; default `branch=all`, `report_scope=all_products` | **Contrato já suporta branch**. Reutilizá-lo. |
| BFF `closing_routes.py` | `GET /closing/analytics/stock-reconciliation?period=&branch=all|01|02&report_scope=all_products|mp_pi_pa` | **Não criar rota nova por preferência**. Antes da implementação testar comportamento e paridade dos três branches e datas-base. |
| BFF — semântica | contrato declara `DIVERGENCIA=ENTRADAS_SAIDAS-P7-H02`; R05=closingBalance, P7=stockTotal ex-loc 99, H02=physicalTotal loc 99, com-OP fora do operando | Manter a definição exata; não usar total H02 incluindo com-OP nem somar parcelas heterogêneas. |
| BFF — limitação crítica | docstring declara `same live SB9 universe`, `parity=IDENTITY_ONLY|DIVERGENCE`, `reconciliationVerdict=INCONCLUSIVE`, e nunca `EXACT_PARITY` | Diferença zero **não comprova** paridade oficial MATR320/MATR460/MATR989 nem fechamento concluído. Não exibir PASS/verde inferido só por zero. |
| P3 governado | fechamento P3 persiste reconciliação governada separada da visão analítica | Nova UI não escreve P3 nem substitui aceite/validação humana. |

**Evidência PO/AS-IS:** transcrição da demonstração, marcas 06:31 e 12:22 sinalizam necessidade por filial; 08:33–08:50 mostram filtros por filial e escopo nos detalhes. Validar timecodes com arquivo transcrito original quando necessário; este documento não incorpora transcrição bruta, nomes pessoais ou valores financeiros confidenciais.

## 4. Invariantes e critérios de aceite (RQ/AC para inventário Cursor)

- **RQ-UX-01 / AC-01:** default `Por unidade`, ambas filiais presentes simultaneamente e identificadas; nenhuma delas escondida por seleção exclusiva de 01/02.
- **RQ-UX-02 / AC-02:** modo `Consolidado` renderiza **apenas consolidado**, sem duplicar subseções individuais; voltar para `Por unidade` retorna ambas.
- **RQ-DATA-01 / AC-03:** cada seção usa consulta da BFF com o `branch` correspondente `01`, `02` ou `all`, competência idêntica e mesmo `report_scope`; não calcular consolidado em client somando UI.
- **RQ-DATA-02 / AC-04:** a apresentação dos três operandos por seção corresponde ao payload daquele branch, incluindo `as_of`, proveniência e status independentes. `branch=all` não é proxy para dados individuais.
- **RQ-TRUTH-01 / AC-05:** `source_missing`/`incomplete`/`partially_available`/timeouts mostram estados honestos e diferença `não calculada` ou `INCONCLUSIVE`, sem zero inventado, sem PASS inferido.
- **RQ-TRUTH-02 / AC-06:** mesmo `0,00` com `IDENTITY_ONLY` permanece **INCONCLUSIVE** para paridade oficial. Não comparar grand totals históricos de relatório oficial com decomposição SB9 sem homologação de `branch`, `as_of`, `report_scope`, `warehouse`, `physicalTotal` e produtor.
- **RQ-SEC-01 / AC-07:** backend autoriza effective permissions Core + escopo; MFE segue browser→BFF; refetch e cache isolados por subject/permission/scope/branch/competência; nenhuma nova permission.
- **RQ-UX-03 / AC-08:** loading/error/empty isolados por unidade (falha f02 não apaga f01), responsive/light/dark, foco, acessibilidade, textos PT-BR e Help no mesmo gate.
- **RQ-NONREG-01 / AC-09:** preservar páginas detalhadas, respectivos filtros existentes, cards de atenção e demais funcionalidades da aba; sem alterar semântica de P3 ou pacote documental P5.
- **RQ-VERIFY-01 / AC-10:** validar com 3 fixtures independentes 01/02/all e 1 cenário de fonte parcial; medir retorno real para competência autorizada, não inferir deploy a partir de testes unitários.

## 5. Gate técnico para o Cursor (próxima etapa, NÃO executado)

1. `HEAD + git status` + project instructions + .cursor aplicáveis + README + docs pertinentes; inspecionar contratos/types/testes/hooks/caches (MFE, BFF, api-delpi) e produtor dos 3 operandos.
2. Levantar RQ/AC e diferenças em relação à proposta. Identificar se BFF `branch=01/02/all` satisfaz tudo na mesma data-base. Ler testes de rota/reconciliação e schemas de erro antes de decidir mudar contrato.
3. Classificar `PROVEN/TO_INVENTORY/TARGET`; se há decisão material de boundary, persistência, API, permissão, origem de dados, nova rota ou mudança da semântica de divergência, retornar **DECISION_REQUIRED** ao PO antes de implementar.
4. Primeiro fechar contrato/design/testes necessários e gate transversal explícito; depois implementar diff mínimo **page-by-page** no MFE; BFF somente se houver lacuna demonstrada e contrato aprovado.
5. Testes negativos 01 parcial, 02 ausente, consolidated parcial; interações teclado, mobile e claro/escuro; confirmação de que `identity_only` não vira `PASS`; testes de cache/regressão.
6. Registrar evidência real de execução, captura e status `PASS|FAIL|PENDING|INCONCLUSIVE|TEST_NOT_RUN`, smoke autorizado e residual. Não deploy sem gate.

## 6. Relatório CLARA recebido do Cursor (verificação independente do canal)

Relatório fornecido pelo executor: HEAD inicial `2bcf9aafee08b0e48cbf61cb59eb5e5273b65039`; final e implantado `3a2da6021bd6e71d84c3e61954209882b396579c`; commit glossário `aa073b71a8a6c33c541ac2da436ae684c3b99d1f`; corpus `6459c1a1-eb2d-4596-ac85-497fec0773c0` (89 fontes, 2211 itens). `doc-156` `INTERNAL_ONLY`, ficha-processo operacional `PORTAL_ACCESS`; 20 testes informados PASS; ChatGPT/MCP final `TEST_NOT_RUN` **no report**.

**Verificação realizada neste canal em 2026-11-09:** GitHub `main` mostrou `3a2da...`; documento 156 existe no `main`. CLARA `knowledge.search` retornou efetivamente corpus `6459c1a1...` com 89 fontes/2211 itens, incluindo ficha-processo com glossário e fluxo `recipient_area=CONTABIL`; **PASS para recuperação semântica dessa consulta específica via MCP**. Os 20 testes locais, scripts produtivos e smoke E2E de todos os caminhos **não foram reexecutados por este revisor**; não elevar evidência reportada a prova própria.

## 7. Pendências e resultado

- **Design UX/PO:** APPROVED no escopo deste documento, sem autorização automática de implementação.
- **BFF compatível com `branch`:** contrato **PROVEN no HEAD**; paridade oficial por filial e comportamento live **TO_INVENTORY**.
- **Nova implementação:** `PLANNED`, `TEST_NOT_RUN`.
- **Conhecimento CLARA:** recuperação do glossário **PASS no canal MCP desta conversa**, não equivalência a smoke autenticado de Portal/deploy.
- **Residual de segurança:** freeze original de 2 permissions vs `access.dre` no HEAD/documentação 156; não alterar permissões aqui.
- **Envio documental:** checklist V2 com 14 itens `CONTABIL` é assunto separado da conciliação analítica; não publicar/alterar V2 neste gate.

**Próximo passo:** enviar ao GPT Arquiteto o Execution Report do Cursor relativo ao glossário (agora recebido), depois aprovar escopo técnico e executar etapa de inventário/implementação visual em gate separado.
