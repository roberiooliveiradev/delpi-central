# EVA / Portal Engenharia — Routing Study Workspace V2 — Visual Contract

**Estado:** `TARGET / OWNER-DIRECTED / NOT_IMPLEMENTED_BY_THIS_DOCUMENT`  
**Decisão de produto:** 2026-11-17 (nova decisão posterior ao visual V1 de três abas internas).  
**Owner da experiência:** Portal Engenharia. **UI compartilhada:** `@delpi/plugin-ui`. **Fonte oficial:** Domain APIs/API-DELPI. **Motor existente:** domínio determinístico Engenharia/EVA. **Aprovação de alterações de processo:** Engenharia.
**Contexto:** a aba principal **Roteiro** permanece na Ficha do Produto; **remover as três abas internas** `Operações / Balanceamento / Análise visual`. Convergir para **UMA página scrollável**, reunindo consulta, configuração, cálculo, comparação e gráficos.  
**Referência histórica visual:** [PNG aprovado para V1, seis estados, dois temas](./references/routing-all-tabs-dark-light-approved.png). Reutilizar sua linguagem de cards/cores/compactação, **não sua navegação em três abas**: a decisão V2 prevalece exclusivamente nesse ponto.  
**Fonte de dados de exemplo:** capturas reais enviadas na conversa do produto 90260146, operação EMBALAR / CT-19 / 0,06 min/peça (observação de UI, não prova independente do ERP).  
**Precedência:** autoridades de segurança/arquitetura/domínio > contrato de API > decisões V2 de composição > imagem e contratos V1 para linguagem visual > Doc 126 histórico. Nunca usar valores ilustrativos como dado oficial.

## 1. Objetivo UX

Um único fluxo, dentro da aba Roteiro da Ficha do Produto:

`Contexto do roteiro → Indicadores → Operações oficiais → Condições produtivas → Organização da linha → Resultado do estudo → Cenários → Análise visual → Limitações/provenance`.

- Sem terceira top bar, sem alternância entre seções para completar o trabalho.
- Uma única rolagem vertical da página; evitar scroll interno de contêineres, salvo listas/visualizações de grande volume com acessibilidade e justificativa.
- O usuário pode analisar rapidamente o roteiro **ou** configurar um arranjo hipotético de postos.
- Estados vazios não devem reservar grandes cartões de gráficos e resultados sem informação.
- A UI não deve sugerir que CT equivale a posto físico nem que uma SIMULATION altera o roteiro oficial.

## 2. Wireframe estrutural V2 (desktop)

```text
PORTAL / FICHA DO PRODUTO / ROTEIRO                 [navegação principal EXISTENTE]
+-----------------------------------------------------------------------------+
| Roteiro de fabricação        Filial [01 v]      Estágio [principal v]        |
| {produto} · Operações e análises de processo                                 |
+-----------------------------------------------------------------------------+
 [Operações] [CTs] [Recursos] [Tempo padrão]              quatro KPI cards
+-----------------------------------------------------------------------------+
| Operações do estágio                                 [n operações]           |
| [01] EMBALAR                  CT-19 · 0,06 min/peça             [expandir]     |
|   [detalhes técnicos sob demanda, componentes]                              |
| [02] ...                                                                    |
+-----------------------------------------------------------------------------+
              gap 20–24px
+-----------------------------------------------------------------------------+
| Estudo de balanceamento                             [Rascunho de sessão]    |
| Condições de produção: [Demanda] [Turno] [Pausas]                            |
| Resumo: [Tempo produtivo] [Prévia takt]                                     |
| Organização da linha: (•) Análise rápida ( ) Configurar postos              |
|   se configurar: cards Posto 01, Posto 02..., operações vinculadas, ordem   |
| [Adicionar posto]             [Novo cenário] [Limpar estudo] [Calcular]      |
+-----------------------------------------------------------------------------+
              gap 20–24px
+-----------------------------------------------------------------------------+
| Resultados e cenários (somente quando aplicável)                             |
| [Takt] [Conteúdo] [Postos teóricos] [Gargalo] [Restrições/limitações]        |
| Cenário A × Cenário B... (identificados por parâmetros e versão do roteiro)  |
+-----------------------------------------------------------------------------+
              gap 20–24px
+-----------------------------------------------------------------------------+
| Análise visual                                                              |
| [Tempos por operação] [Tempo × takt quando calculado]                       |
| [Distribuição simulada, só se suportada e disponível]                       |
+-----------------------------------------------------------------------------+
  Fonte e classificação próximas dos dados: OFFICIAL/OBSERVED, PROVIDED,
  CALCULATED, SIMULATION, UNKNOWN; alterações de processo não são publicadas.
```

Os valores do wireframe são **ilustrativos** e nunca substituem dados oficiais.

## 3. Composição e dimensões de referência

| Área | Composição obrigatória | Densidade |
|---|---|---|
| Contexto | Cabeçalho **sem altura mínima artificial**, título/subtítulo à esquerda, **selects funcionais** à direita | Compacto, não um terceiro hero |
| Indicadores | 4 KPI cards nativos com dados do estágio | 4 colunas desktop; 2 tablet/mobile quando legível; 1 em 320px quando necessário |
| Operações | Lista vertical de **cards expansíveis**, não tabela principal | Chip nº, título, CT + tempo, chevron; expandir detalhes presentes |
| Estudo | Um card de seção para parâmetros + organização (subcards discretos) | Condições 3 campos, resumo de 2 métricas; avançado progressivo |
| Postos | Cards individuais nomeados, com nº, operações atribuídas, CT/recurso, hipótese de capacidade | Múltiplos cards; botões adicionar/remover/reordenar; controles reais |
| Ações | Calcular ação principal; Novo cenário e Limpar secundários | Limpar exige confirmação explícita; salvar automático é status, não botão enganoso |
| Resultados | Cards por métrica + informação de base e limites | Exibir só depois de cálculo válido; sem falsos resultados oficiais |
| Gráficos | Renderers canônicos do Plugin UI, plot e títulos temáticos | Evitar cards gigantes vazios; 1 operação pode usar indicador compacto |

**Espaçamento-alvo** (preferir tokens Plugin UI, números como referência para QA): entre seções 20–24px; KPI cards 12–16px; padding de cards 16–20px; entre operações 8–12px; título→conteúdo 12–16px; entre campos 12–16px. Testar compressão e consistência dos gaps, sem codificar valores arbitrários se tokens nativos existem.

## 4. Configuração da linha — sem confundir conceitos

- **Operação:** etapa oficial do roteiro; identificada por chave estável que inclua produto/nível/operação/recurso conforme contrato de domínio.
- **CT:** centro de trabalho cadastrado no roteiro; pode agrupar atividades/recursos, **não é prova de um posto físico**.
- **Recurso:** equipamento/recurso vinculado na fonte, não prova de disponibilidade simultânea.
- **Posto hipotético:** estação ou posição definida pelo usuário para um estudo, com nome editável, ordem, operações atribuídas, CTs/recursos associados e capacidade/operadores se informados.
- **Paralelismo:** número de posições/equipamentos paralelos proposto; não inferir da quantidade de CTs.
- **Sequência proposta dos postos:** organização da hipótese, diferente da sequência oficial de operação e sujeita a precedência e restrições.

### 4.1 Análise rápida

Selecionada por padrão; consome roteiro e parâmetros simples (demanda, minutos produtivos, lote/num_stations apenas se explicitamente informados). Não presume quantidade real de postos nem equipes.

### 4.2 Configurar postos — TARGET

A UI progressiva deve oferecer, após validação do contrato:
- Adicionar, renomear, duplicar como hipótese e excluir postos.
- Vincular múltiplas **operações oficiais** a um posto via multisseleção; não oferecer operação inventada.
- Vincular CTs/recursos presentes no roteiro; alertar sobre associação inconsistente.
- Ordenar postos (botões subir/descer sempre disponíveis; drag-and-drop apenas com alternativa teclado).
- Ajustar operadores/posições paralelas, lote e hipóteses de capacidade **sem tratá-los como dados oficiais**.
- Precedência, conflito de recursos, estágio e simultaneidade não são presumidos. Mostrar bloqueios/avisos em vez de prometer viabilidade.

**GATE DE ARQUITETURA:** o motor atual `routing.line_balance` não está comprovado como solucionador de alocação explícita por posto, sequência e paralelismo. Essa UI pode persistir uma hipótese **DRAFT LOCAL**, porém NÃO pode executar ou exibir resultado como cálculo de viabilidade da configuração avançada sem contrato e motor validados pelo owner. Extensão de bounded contract/authority → `ARCHITECTURE_DECISION_REQUIRED` via Coordination.

## 5. Resultados, cenários e análise visual

- Resultado de `POST /v1/products/{code}/line-balance` existente, quando suportado, identificado como `CALCULATED`/qualificação real; ecoar parâmetros e revisão/provenance.
- Conteúdo de trabalho, mínimo teórico, gargalos e eficiência só quando o backend os retornar de forma compatível; `minimum theoretical stations` não equivale a dimensionamento aprovado.
- Cenários com identificadores locais A/B/C... (limites existentes não alterados sem contrato); comparar apenas parâmetros e resultados correspondentes, sem recomputar algoritmo no MFE.
- Alterações de demanda/filial/estágio/postos invalidam associação dos resultados anteriores ou exibem `STALE`, nunca exibem CALCULATED atual indevidamente.
- Gráficos de tempo podem ler roteiro oficial; tempo × takt depende de cenário; distribuição hipotética depende de resultado suportado.
- Sem cenário: feedback pequeno e ação evidente; não exibir 3 painéis grandes vazios.
- Tooltip/legendas/eixos em dark/light corretos; conversão min→s **somente na visualização**, com unidade explícita.

## 6. Responsividade e navegação

- Desktop: contexto inline, quatro KPIs, operações largura total, estudo em subcards, gráficos em grid compacto.
- Tablet: KPIs 2×2, filtros reorganizados, subcards em coluna se necessário.
- Mobile 390/320px: título e filtros em pilha, cards de operações full width, campos e postos em coluna, ações sem overflow, gráficos ajustados ou resumo.
- **Apenas duas camadas de navegação preexistentes:** Portal e Ficha do Produto. Remover tabs internas do Roteiro; sem navegação visual paralela.
- Scroll deve manter contexto compreensível; opcional índice discreto de seções **somente se comprovadamente útil** e sem reinstaurar terceira top bar.

## 7. Acessibilidade, temas e preservação

- Usar exports públicos reais do Plugin UI pela façade Engineering. Cards expansíveis com `aria-expanded`, role/teclado, foco.
- Inputs com labels/unidades; multiselect acessível e sem duplicar componentes nativos.
- Mensagem de alteração salva no navegador deve ser honesta; não indicar sincronização com servidor.
- Respeitar tokens claro/escuro; sem cabeçalho com espaço vazio; sem plots brancos no dark ou título preto.
- Preservar `GET routing`, `POST line-balance`, permissões, paginação, BOM, dedup, limites, proteções e histórico.
- Contrato de armazenamento e limpeza está em [routing-study-session-state-contract.md](./routing-study-session-state-contract.md); matriz V2 em [routing-study-v2-acceptance.md](./routing-study-v2-acceptance.md).

## 8. Estados UX mínimos

`initial`, `routing_loading`, `routing_empty`, `routing_forbidden`, `routing_unavailable`, `quick_draft`, `advanced_draft`, `auto_saved`, `restored`, `restore_invalid`, `stale_reference`, `calculating`, `result`, `scenario_comparison`, `clear_confirmation`, `cleared`; dark/light; desktop/390/320; authorized/forbidden.

**Status:** somente design/contrato; nenhuma tela, rota, storage ou motor foi implementado por este documento.
