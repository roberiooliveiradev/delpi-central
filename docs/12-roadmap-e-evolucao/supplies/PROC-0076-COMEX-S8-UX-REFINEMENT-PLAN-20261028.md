# PROC-0076.COMEX.S8 — Plano de refinamento visual e de experiência

> **Data:** 2026-10-28 · **Status:** `PLANNED` / proposta UX · **Authority:** produto/UX subordinado às instruções oficiais, regras `.cursor`, ADRs, contratos e código no HEAD.
>
> **Página:** `/apps/supplies/market-intelligence?view=indicators&indicator=comex`. **Escopo:** perspectiva Comex existente em `plugins/supplies`. **Não autoriza implementação, mudança de contratos, migration, deploy nem ativação MDIC.**
>
> **Evidência visual:** duas capturas de produção em tema escuro fornecidas pelo PO em 2026-10-28, uma em **Consultar NCM** e outra em **Produtos DELPI**. Este registro descreve observações visuais, não reproduz anexos no Git nem comprova mobile, tema claro ou teclado.

## 1. Contexto e problema de produto

Após S7, o catálogo NCM é compartilhado e a adição é idempotente; o usuário pode buscar produtos SB1010 ou informar NCM diretamente. Contudo, a experiência mostra **espaço vazio excessivo**, especialmente em Produtos DELPI; catálogo disposto horizontalmente sem hierarquia; mistura visual de pesquisa, cadastro, escolha, administração e visuais salvos; e painel de resultados distante da seleção atual.

As capturas mostram também registros com descrições de teste (`smoke S7`, `SMOKE cobre`) e um código `99999999` inativo. **Não excluir nem alterar dados/auditoria automaticamente:** identificar origem, ownership e política de fixtures antes de decidir ocultação/limpeza. Há botão **Selecionar** em entradas inativas: isso requer distinção entre seleção contextual e aptidão a participar de consultas MDIC.

**Decisão UX:** não adicionar funcionalidades; reorganizar o que já foi construído. Evitar reabrir S0–S7 ou criar um segundo BI.

## 2. Layout-alvo

### Desktop (duas colunas + resultado integral)

| Coluna esquerda — Encontrar materiais/NCMs | Coluna direita — Minha análise |
|---|---|
| Alternador **Produtos DELPI / Consultar NCM** | Contagem e lista/chips de **NCMs selecionadas** |
| Campo de busca largo, com Enter e ação contextual | Estados por NCM: **cadastrada / em revisão / habilitada / inativa / sem dados** |
| Em produtos: filtro **Todos / MP / PI / PA** | Visualizações pessoais: escolher, nomear, salvar/atualizar/excluir |
| Em NCM: digitar código de oito dígitos e adicionar/selecionar | Remoção e limpar seleção, com confirmação apenas se houver perda material |
| **Resultados paginados em lista ou tabela compacta**: código, descrição, tipo/NCM/status, ação | Resumo de aptidão: selecionadas, aptas a consultar e sem dados |

**Abaixo, em largura total:** **Importações — Comex Stat (MDIC)** com toolbar de gráfico/tabela/comparação conforme contrato, KPIs somente com dados reais, cobertura, fonte, competência e mensagens de estado adequadas.

**Administração do catálogo:** área secundária recolhida, acessível sob `supplies.manage` efetiva e escopo; não colocar inativação ou homologação ao lado de cada ação de seleção comum.

**Tablet/mobile:** empilhar colunas (busca → seleção → resultados), não criar rolagem horizontal ou botões fora da área visível; reutilizar breakpoints e componentes reais do `@delpi/plugin-ui`.

### Comportamento contextual

- **Produto:** pesquisar por código/descrição e exibir lista paginada; mostrar NCM real `B1_POSIPI` e sinalizar ausência, formato inválido ou estado de governança. Não inferir NCM pela descrição.
- **NCM direta:** aceitar código com máscara/pontuação compatível; ao encontrar registro compartilhado, ação **Selecionar**; se não existir, **Adicionar** idempotente, sem homologação automática. Não expor workflow técnico ao usuário comum.
- **Seleção atual:** chips com remoção clara, múltiplas NCMs sem duplicação, limite vigente (20), estados e aptidão para dados; seleção visual não implica direito de ingestão ou valor no gráfico.
- **Visualizações salvas:** propriedade pessoal/ownership permanece, com seleção reaplicável e URL/F5 coerente.
- **Resultado:** mensagens distintas para (a) nada selecionado, (b) selecionadas sem NCM habilitada, (c) NCM habilitada sem observações na janela, (d) fonte indisponível ou feed OFF, (e) erro AuthZ/HTTP. Não afirmar “nenhuma NCM do catálogo está habilitada” se apenas a seleção atual estiver vazia.
- **Export/compare:** desabilitar contextual e explicar indisponibilidade, sem export vazio que pareça análise real.
- **Fonte:** Comex é estatística mensal por NCM; FOB, kg/t, média ponderada FOB/massa; sem cotação spot ou dado sintético.

## 3. Entregas planejadas

### S8.1 — Estrutura e hierarquia visual

**Owner:** `plugins/supplies`. Inventariar o layout atual, componentes `@delpi/plugin-ui` e CSS isolado. Implementar composição duas colunas em desktop, lista paginada no lugar da linha horizontal, resumo de seleção e visualizações na lateral, painel de resultados logo abaixo. Preservar contratos de `supplies-api`, `api-delpi` e `external-data-api`.

**Gate:** screenshots desktop escuro/claro com largura representativa, sem regressão em Produtos DELPI e Consultar NCM; sem overflow.

### S8.2 — Ações e estados sem ambiguidade

**Owner:** MFE, BFF somente se um contrato real exigir (inventário antes de editar). Ações contextuais **Adicionar** versus **Selecionar**, feedback idempotente, chips, estado da NCM, empty states precisos, administração apartada. Não dar **Selecionar** com significado de “habilitar MDIC”.

**Gate:** testes de busca, seleção múltipla, dedup, NCM válida/inválida/inativa, usuário sem `manage`, fonte OFF, salvamento/recuperação e URL/F5; positivos/sibling/negativos de AuthZ no backend se houver alteração.

### S8.3 — QA visual e documentação

**Owner:** MFE + QA/Release. Testar desktop/tablet/mobile, claro/escuro, teclado/foco, Help, impressão/exportações quando aplicável; capturas comparativas antes/depois, testes/build e smoke federado autenticado se o deploy for autorizado.

**Gate:** `PASS` somente com evidência autenticada; ambiente/browser indisponível = `INCONCLUSIVE`. Atualizar guia, Help e ledger PROC-0076 com SHAs e resultados.

## 4. RQ/AC

| AC | Critério de aceite |
|---|---|
| S8-AC-01 | Página tem hierarquia legível e não mantém grande espaço vazio artificial |
| S8-AC-02 | Duas colunas no desktop e uma no mobile, sem overflow |
| S8-AC-03 | Produtos DELPI pesquisáveis com resultados paginados, tipo e NCM visível |
| S8-AC-04 | NCM direta permite **Adicionar** ou **Selecionar** com regra idempotente |
| S8-AC-05 | Catálogo compartilhado legível em linhas/tabela, sem ação dispersa |
| S8-AC-06 | Resumo da seleção distingue NCM cadastrada, apta e sem dados |
| S8-AC-07 | NCM inativa não ativa feed nem se apresenta como apta por engano |
| S8-AC-08 | Visualizações pessoais preservam ownership, salvar/abrir/editar/excluir |
| S8-AC-09 | Administração só com effective `supplies.manage` e escopos vigentes |
| S8-AC-10 | Empty states diferentes para seleção vazia, não homologada, sem observação e falha da fonte |
| S8-AC-11 | Indicadores somente com dados reais; metodologia FOB/massa explícita |
| S8-AC-12 | URL/F5, seleção múltipla, exportações e comparação coerentes |
| S8-AC-13 | Desktop/tablet/mobile, temas claro/escuro, teclado, foco, labels e contraste |
| S8-AC-14 | Reuso do kit, CSS isolado, identificadores técnicos em inglês |
| S8-AC-15 | Help/manual atualizados e regressão Metais/PTAX/IPP preservada |
| S8-AC-16 | Smoke federado e evidências visuais após deploy, sem inferir PASS |

Estados `PASS | FAIL | PENDING | INCONCLUSIVE | TEST_NOT_RUN`; revisão arquitetural `ACCEPT | ACCEPT_WITH_RESIDUAL | REWORK | EXECUTION_DRIFT | INCONCLUSIVE`.

## 5. Restrições e riscos

- **Sem mudanças de RBAC:** Core determina permissões efetivas; BFF autoriza fail-closed com unidade, recurso e regra de negócio. MFE esconde controles, mas não autoriza.
- **Sem escrita TOTVS:** SB1010 permanece owner `api-delpi`; NCM no Protheus não é homologação automática.
- **Sem ativar MDIC:** `comex-monthly` e NCM allowlist mantêm gates de fonte e homologação; dados reais ainda `PENDING`.
- **Sem novos componentes genéricos antes do kit.**
- **Dados de smoke:** `TO_INVENTORY` quanto à necessidade de limpar/ocultar registros específicos; não remover auditoria nem criar regra ad hoc por texto “SMOKE”.
- **Concessão temporária de smoke:** revisão do usuário de teste e permissions Core é residual de segurança distinto, a confirmar por inspeção de estado vigente.
- **Documentos PR #119/#120:** consultar situação real, não tratar branch não mergeada como authority do `main`. Reconciliar se necessário.
- **Nenhuma página nova:** fluxo dentro da perspectiva Comex; manter demais perspectivas intactas.

## 6. Preflight e relatório esperado ao Cursor

Antes de executar S8.1: HEAD, `git status`, authorities, regras `.cursor`, README e `IMPLEMENTATION-PLAN.md`, contratos do Comex S6/S7, owner, componentes/props do kit, testes e página autorizada. Se aparecer conflito de contrato/owner, `EXECUTION_DRIFT` e parar fatia afetada.

Relatório por etapa: `BASE HEAD, FINAL HEAD, STATUS, FACTS PROVEN, TO_INVENTORY, EXECUTION_DRIFT, FILES INSPECTED/CHANGED, CONTRACT IMPACT, TESTS, SECURITY CHECKS, RQ/AC COVERAGE, RESIDUAL SEARCH, POSTCONDITION/OUTCOME, UNRESOLVED, NEXT STEP`.

**Próximo passo:** após revisão/merge deste plano e autorização expressa do PO, iniciar brief **S8.1** voltado a layout e composição, com menor diff MFE; não ativar MDIC nem mexer em dados de teste preventivamente.
