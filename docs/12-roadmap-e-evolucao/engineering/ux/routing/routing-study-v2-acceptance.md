# EVA / Portal Engenharia — Routing Study Workspace V2 — Acceptance Matrix

**Status:** `TARGET / TEST_NOT_RUN` — critérios futuros, não provas de implementação.  
**Data:** 2026-11-17.  
**Escopo:** scroll único, composição Plugin UI, estudo rápido, postos hipotéticos, persistência da sessão e limpeza, sem reabrir motor oficial.

| RQ | Verificação | Resultado exigido |
|---|---|---|
| V2-01 | Navegação | Somente tabs globais da Ficha; remover `Operações/Balanceamento/Análise visual` internas; todas áreas no scroll |
| V2-02 | Cabeçalho | Título, produto, filial, estágio compactos, sem altura artificial ou faixa vazia |
| V2-03 | Indicadores | Quatro KPI cards temáticos, gap coerente e dados de estágio |
| V2-04 | Operações | Cards expansíveis com 01/descrição/CT/tempo, detalhes e componentes; sem tabela principal |
| V2-05 | Espaçamento | Gaps referenciais de 20–24px entre seções; cards 12–16px; tokens prevalecem; sem dupla borda colada |
| V2-06 | Fluxo de estudo | Condições → organização da linha → resultado → gráficos na mesma página |
| V2-07 | Linguagem | CT, recurso, operação e posto hipotético apresentados como conceitos distintos |
| V2-08 | Análise rápida | Não presume postos físicos, cálculo somente do contrato backend existente |
| V2-09 | Configuração avançada | Adicionar/remover/renomear/ordenar postos hipotéticos, operações oficiais multisselecionáveis, CTs/recursos baseados na fonte |
| V2-10 | Limites de simulação | Não declarar viabilidade de distribuição manual sem motor/contrato autorizado |
| V2-11 | Refresh | Rascunho recuperado da mesma aba após refresh, com estado e mensagem honesta |
| V2-12 | Contexto | Não misturar produto/filial/estágio/principal; revalidar autorização e fonte |
| V2-13 | Persistência | Sem JWT/segredos/PII; schema/limites/erros de sessionStorage tratados |
| V2-14 | Limpeza | Botão Limpar com confirmação; cancela ou remove só draft atual; dados oficiais permanecem |
| V2-15 | Novo cenário | Cria cenário separado e preserva o anterior, com parâmetros visíveis |
| V2-16 | Invalidação | Resultado antigo stale ao mudar parâmetros/roteiro ou contexto |
| V2-17 | Gráficos | Tempos oficiais disponíveis; takt e distribuição somente quando suportados; sem 3 painéis vazios enormes |
| V2-18 | Tema | Dark/light com plot, texto, input, cards e tooltip consistentes |
| V2-19 | Responsividade | 1440px/1024px/390px/320px sem overflow, cards/filtros reorganizados |
| V2-20 | Acessibilidade | Teclado, aria-expanded, confirmação dialog, multiselect e ordenação por botões |
| V2-21 | Regressão | GET/POST existentes, BOM/dedup/authz/paginação/cenários preservados |
| V2-22 | Gate de arquitetura | Nova alocação/postos explícitos só após inventário/contrato/owner; registrar `ARCHITECTURE_DECISION_REQUIRED` quando aplicável |
| V2-23 | Verify | Auditoria independente do código + DOM e screenshots; não apenas import do kit |
| V2-24 | Publicação | HML→PROD somente após gates governados e visual reproduzível; smoke autenticado real não substituído por HTTP 200/401 |

## Cenários visuais obrigatórios

1. Desktop dark: cabeçalho + KPIs + operação expandida + início do estudo visíveis em scroll.
2. Desktop light: mesma estrutura e contraste.
3. Estudo preenchido: cálculo rápido e resumo, seguida de resultados e gráficos válidos.
4. Advanced: dois ou mais postos, multisseleção real e ordenação local.
5. Refresh: estudo preenchido antes e depois da recarga, status `Recuperado`.
6. Novo cenário A/B: versões de inputs e resultados corretamente identificadas.
7. Limpar: diálogo de confirmação e estado zerado, roteiro preservado.
8. Mobile 390/320: cards e inputs acessíveis.
9. Sem cenário: não mostrar distribuição ou comparador como resultado calculado.
10. Roteiro alterado/sem permissão: sem restauro que contorne segurança.

## Gates

- **G0:** contrato visual e regra de sessão inventariados; capabilities suportadas vs TARGET separadas; arquitetura deliberada.
- **G1:** composição visual com kit oficial em navegador real, dark/light/mobile; Verify com comparação.
- **G2:** estado temporário e testes E2E de refresh/limpar/context switch.
- **G3:** integração do cálculo rápido sem copiar domínio; avançado não enganoso.
- **G4:** regressão + segurança + acessibilidade + independent verifier com evidências.
- **G5:** HML autenticado; depois PROD autorizado, smoke autenticado e aceite visual.

**Status de execução:** `TEST_NOT_RUN` em todos os RQ nesta documentação. O V2 é especificação; não significa runtime implementado.

## Resultado resumido

Um usuário autorizado abre a Ficha do Produto → Roteiro, consulta operação, define demanda, decide análise rápida ou estudo hipotético de postos, vê resultados claramente classificados, atualiza a página sem perder rascunho da mesma sessão, pode comparar cenários e usar `Limpar estudo` para começar de novo. Tudo numa página scrollável e sem modificar o ERP.
