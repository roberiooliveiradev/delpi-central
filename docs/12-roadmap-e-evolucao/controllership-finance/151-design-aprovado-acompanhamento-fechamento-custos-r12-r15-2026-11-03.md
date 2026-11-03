# 151 — Design aprovado pelo PO: Acompanhamento do fechamento de custos (R12/R15)

**Produto:** Portal Controladoria & Finanças | **Processo:** PROC-0072 | **Data da aprovação visual:** 03/11/2026
**Status:** `TARGET / VISUAL_APPROVED_BY_PO`; **runtime:** `NOT_IMPLEMENTED_UNTIL_GATE`; **paridade/homologação humana:** não comprovada.
**Fonte visual:** mockup aprovado expressamente pelo PO na conversa em 03/11/2026 (“é exatamente esse visual que quero”), gerado a partir da captura da tela atual R12/R15. **Este documento é a especificação textual fiel do mockup aprovado.** O arquivo bitmap não foi anexado ao repositório neste commit; não presumir que exista asset de imagem versionado.
**Arquivo vigente:** `plugins/controllership-finance/src/features/closing/CostClosingStatePage.tsx`.
**Contrato vigente:** `plugins/controllership-finance/src/api/costClosingStateApi.ts` e BFF `GET /closing/competences/{period}/cost-closing-state`.
**Relação:** Documento 150 CF-UX-023/035; nova ficha de implementação CF-UX-051 definida abaixo.

## 1. Decisão visual vinculante do PO

Transformar a atual listagem técnica “Estado de fechamento e cutoff — R12/R15” numa **visão de acompanhamento simples, legível e inteiramente em português**, conforme mockup aprovado. Não alterar, inferir ou executar rotinas TOTVS. Esta aprovação **é de design da tela**, não equivale a decisão de mover a página para a Visão geral (CF-UX-035 ainda `DECISION_REQUIRED`).

### Estrutura exata de cima para baixo

1. **Hero compacto:** título primário **“Acompanhamento do fechamento”**, subtítulo **“Resumo dos sinais encontrados no sistema para apoiar a conferência do fechamento por filial.”**. Na faixa de contexto, uma indicação discreta de que é **“Visão de apoio”**; o código `R12/R15` pode ficar apenas como metadado técnico secundário ou no Help (não ser parte do título). À direita, última atualização real e botão **“Atualizar consulta”** com ícone de atualizar do `@delpi/plugin-ui`; não duplicar refresh. Preservar competência contextual na navegação/breadcrumb existente.
2. **Cartão explicativo “Como interpretar esta tela”**, com ícone de informação e três mensagens em português:
   - “Esta tela mostra sinais encontrados no sistema para apoiar a análise do fechamento.”
   - “Ela não confirma sozinha que o fechamento foi concluído.”
   - “A validação final depende da conferência da equipe responsável.”
   Texto legível e sintético, sem expor detalhes internos de SQL/ERP no corpo principal.
3. **Duas colunas de cartões por filial no desktop**, lado a lado para filial 01 e 02 (ou tantas filiais quantas o contrato trouxer, sem hardcode). Uma coluna só em mobile, ordem estável. Cabeçalho de cada cartão: ícone pertinente, **“Filial 01”**, resumo auxiliar **“3 de 5 verificações com evidência”** `APENAS` quando calculado de dados reais dessa filial, e um estado neutro/âmbar **“Acompanhamento parcial”**. **Não tratar 3/5 como percentual de execução do fechamento nem usar cor verde global de “concluído”.**
4. **Cinco linhas por filial**, cada uma com ícone discreto, título de negócio, explicação curta e badge alinhado à direita:
   
   | Campo do contrato | Nome em tela | Explicação aprovada | Status de referência no mockup |
   |---|---|---|---|
   | `snapshot` | **Posição de estoque do fechamento** | “Com base nos registros do sistema.” | **Encontrado** quando `available` |
   | `cutoff_marker` | **Referência do último fechamento** | “Data e referência registradas no sistema.” | **Encontrada** quando `observed` |
   | `cost_evidence` | **Lançamentos de custo** | “Registros de custos identificados.” | **Encontrados** quando `observed` |
   | `wizard_lifecycle` | **Andamento do processo** | “Situação do fechamento no sistema.” | **Sem informação** quando `unavailable` |
   | `human_acceptance` | **Validação da equipe** | “Confirmação da equipe responsável.” | **Pendente de informação** quando `not_informed` |

   Os três primeiros badges verdes significam apenas **evidência técnica encontrada**, nunca aprovação. Os dois últimos são neutro/cinza e âmbar, respectivamente. Outras combinações de estado devem ser mapeadas honestamente para texto e cor (ex.: `missing`, `partial`, `not_advanced`), sem estados inventados.
5. **Rodapé discreto de origem:** “Base consultada: posição de DD/MM/AAAA · visão de apoio ao fechamento”, data real `referenceDate`, com Help acessível para proveniência e limitações técnicas. Não exibir bruto `technical_markers`, `snapshot`, `SB9010`, `MV_ULMES`, `TTAT`, `wizard`, `cutoff`, `UTC` no texto principal. Dados técnicos continuam acessíveis no Help/detalhes para auditoria.
6. **Erros, carregamento e vazio:** usar `CfLoadingCard`, `CfQueryErrorBanner`, `CfEmptyState` já existentes. Não mostrar “3 de 5” sem resposta ou somar `not_informed` como verificado.

### Referência textual de layout

```text
[Acompanhamento do fechamento]                  [Atualizado ...] [↻ Atualizar consulta]
Resumo dos sinais encontrados no sistema...

[ i  Como interpretar esta tela
     • Esta tela mostra sinais encontrados...
     • Ela não confirma sozinha...
     • A validação final depende da equipe... ]

┌─ Filial 01 ───────────────────────┐  ┌─ Filial 02 ───────────────────────┐
│ 3 de 5 verificações com evidência │  │ 3 de 5 verificações com evidência │
│ [Acompanhamento parcial]          │  │ [Acompanhamento parcial]          │
│ Posição de estoque    [Encontrado]│  │ Posição de estoque    [Encontrado]│
│ Referência fechamento [Encontrada]│  │ Referência fechamento [Encontrada]│
│ Lançamentos de custo  [Encontrados]│ │ Lançamentos de custo  [Encontrados]│
│ Andamento do processo [Sem informação]│ ...                             │
│ Validação da equipe [Pendente de informação]│ ...                          │
└───────────────────────────────────┘  └───────────────────────────────────┘

Base consultada: posição de 30/09/2026 · visão de apoio ao fechamento
```

**Composição:** cards espaçosos e hierarquia clara, ícones consistentes, separadores leves entre linhas, fundo dark/light com a mesma árvore, badges contrastantes. Evitar a tabela técnica atual em bullets com códigos do ERP e o bloco longo de limitações acima das filiais. Não criar novo chrome/hero/grid se o plugin-ui possui componentes equivalentes.

## 2. Semântica e cautelas contratuais

- A tela **não executa** `MATA320`, `MATA300`, `MATA330`, `MATA280` nem homologa o fechamento. É somente **read-only**.
- Status `available/observed` representa presença de indícios, não conclusão do fechamento, resultado correto do processamento ou validação humana.
- **Resumo “3 de 5”** deve ser calculado contando exclusivamente os nós de fato marcados com evidência (`available` / `observed`) no payload por filial. Outros estados são pendentes/não informados, não erros automaticamente. O rótulo “Acompanhamento parcial” só deve ser adotado se suportado pela classificação honesta dos cinco nós; não criar progress bar de execução.
- **`human_acceptance=not_informed`** não significa reprovação nem atraso real. Badge deve informar ausência de confirmação (“Pendente de informação” ou “Não informada”); evitar apresentar “Pendente” isolado como fato de atraso.
- O contrato atual possui cinco nós e `limitations[]`; as limitações devem ficar acessíveis em Help/expansão clara, sem desaparecer. Não inferir a execução de rotina, autorizar alteração de estado ou escrever no Protheus.
- Filiais e datas são dinâmicas conforme contrato e competência; não fixar `01`, `02`, `30/09/2026`, `3/5` em JSX.
- A instância R12/R15 **permanece na rota atual** até decisão formal de realocação CF-UX-035. Não alterar catálogo, rotas e deep links por inferência.

## 3. Reuso, contrato, segurança e escopo

- Reusar `ClosingHero`, `CfSectionCard`, `CfStatusBadge`, `CfTitleWithHelp`, feedback/loading, ícones e layout existentes via `@delpi/plugin-ui` / `controllershipFinanceUi`. Verificar props e limites reais do kit.
- Reusar `getCostClosingState(period)`; **nenhuma API nova, nenhuma mudança de BFF/produtor, nenhum SQL, nenhum novo permission code, nenhum gateway paralelo**. Se a apresentação exigir um campo não presente (ex.: data específica de cada marcador), apresentar `DECISION_REQUIRED` antes de ampliar contrato.
- Preservar ACL existente: `controllership-finance.access` e `controllership-finance.manage` apenas; effective permissions e resource scope no backend; frontend não autoriza.
- Formatos, ícones e labels PT-BR em todos os elementos visíveis, inclusive Help. Identificadores técnicos somente em metadados ou detalhes auditáveis.
- Preservar breadcrumb contextual, navegação, foco, teclado, leitores de tela, responsividade e tema.

## 4. Plano de execução e critérios de aceite

**Etapa 0:** HEAD + git status + instruções oficiais/.cursor + Doc 150 + Doc 151 + contratos + testes, WIP e owner; baseline visual.

**Etapa 1:** refatorar apenas composição/presentação de `CostClosingStatePage.tsx` e estilos/Help estritamente necessários, sem mudar domínio. Renderizar hero/explicação/cards por filial/cinco verificações/rodapé e estados de falha/empty/loading.

**Etapa 2:** testes unitários e de componente para cinco nós, mapping por estado, resumo, 0 e N filiais, competências, ausência de evidência e erros. `human_acceptance` não vira aprovação inferida. Testar responsividade, dark/light, aria, foco, navegação e refresh.

**Etapa 3:** teste real via CLARA `read(report.cost_closing_state)` se ferramenta suportar; comparar 2026-09 filial 01/02 com BFF e renderização do Portal autenticado; guardar screenshots antes/depois, sem confundir teste de CLARA com prova visual.

**Etapa 4:** typecheck, vitest, build, regressões, commit/push `main` e deploy controlado quando gates de segurança e release estiverem satisfeitos, com rollback documentado e SHA de serviço comprovado. Atualizar docs 150/151 e Help no mesmo ciclo.

**DoD:** design visual semelhante ao mockup aprovado em todos os blocos; textos de negócio em PT-BR; dados/status honestos; cinco verificações completas por filial; sem rotinas SQL nem novas APIs; visual desktop/mobile e claro/escuro; sucesso real de dados, autorização, build/testes, screenshots e deploy verificado. Sem sessão autenticada: `TEST_NOT_RUN` para smoke visual; nunca `PASS` inferido.

## 5. Decisão de navegação — ainda separada

**CF-UX-035 / DECISION_REQUIRED:** manter em catálogo/grupo técnico ou mover para Visão geral da competência. O design aprovado **não decide isso automaticamente**. Implementar a tela aprovada na rota atual e preservar seu acesso. Se o PO aprovar explicitamente a mudança de local, fazer gate de migração/navegação com consumer inventory, Help e compatibilidade de deep links; não remover o relatório antigo por conta própria.

**Artefato de aceite:** Documento 151 e a referência visual aprovada pelo PO nesta conversa. **Classificação:** `VISUAL_APPROVED` (design), `IMPLEMENTATION_PENDING` (runtime).
