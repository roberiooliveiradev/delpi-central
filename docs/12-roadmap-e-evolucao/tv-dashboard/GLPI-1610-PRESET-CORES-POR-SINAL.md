# GLPI #1610 | TV Dashboard: preset de cores por sinal nas colunas

**Data:** 17/11/2026 · **Produto:** TV Dashboard (editor + renderizador compartilhado) · **Situação:** implementado em PR, aguardando merge/deploy e validação do solicitante.

## Contexto

O gráfico de colunas **GR Diário · Evolução mensal das divergências de estoque** já tem origem zero para valores positivos e negativos (PR #248). O solicitante pediu uma **pré-seleção no menu Alterar cores**, além das existentes, que pinte as colunas conforme o **sinal**: perdas (negativas) em vermelho, ganhos (positivas) em verde e zero em cinza neutro. A regra deve permanecer independente da posição do item na série e do tamanho da perda/ganho. Não é um gradiente nem uma comparação com meta.

## Contrato do preset

| Valor | Cor | Significado |
|---|---|---|
| `value < 0` | `#dc2626` | Negativo |
| `value > 0` | `#16a34a` | Positivo |
| `value === 0` | `#94a3b8` | Zero |
| `null`, `undefined`, `NaN` | sem cor semântica | Lacuna não recebe valor fictício |

- **Ativação:** TV Dashboard → selecionar um gráfico de **Colunas** ou **Barras horizontais** → **Alterar cores** → **Escalas (melhor / pior)** → **Negativo / positivo** (swatches vermelho/cinza/verde), ou marcar **Colorir pelo sinal (− vermelho / + verde)**.
- **Desativação:** desmarcar **Colorir pelo sinal** ou selecionar outra paleta. Ao desmarcar, preservam-se as cores anteriores do gráfico; a opção não modifica a fonte de dados, o valor nem a ordem dos itens.
- **Persistência:** `chartOptions.colorScale.mode = "by_sign"` e `paletteId = "sign-negative-positive"`. O código já suporta os outros modos `off`, `by_value` e `by_goal`, que continuam válidos.
- **Escopo:** gráficos `bar` e `horizontal_bar`, inclusive agrupados/multissérie (aplicação individual a cada barra). Gráficos de linha, área, velocímetro e empilhados permanecem sem esse preset específico nesta entrega.
- **Legenda:** quando habilitada, acompanha as categorias de sinal presentes nos dados com as mesmas cores usadas pelo gráfico, sem criar falsos vínculos de seleção com outras séries. Se só houver negativos, mostra apenas **Negativo**; se houver positivos/negativos/zero, mostra os três.
- **Compatibilidade:** sem seleção do novo preset, o layout, a cor e a geometria das barras permanecem como antes; sem efeitos em gráficos já publicados. A opção não interfere na origem zero implementada na PR #248.
- **Segurança:** apenas frontend, sem modificação de rotas, bancos, regras de negócio do Protheus ou API do TV Dashboard.

## Implementação

- `plugins/plugin-ui/src/components/charts/seriesChartOptions.ts`: novo modo e cores semânticas compartilhadas (`SIGN_SCALE_COLORS` / `resolveSignScaleColor`).
- `plugins/plugin-ui/src/components/charts/seriesChart/ChartSeriesBar.tsx`: determinação de cor por sinal **antes** da paleta por categoria; funciona em série única e multissérie.
- `plugins/plugin-ui/src/components/charts/seriesChart/ChartPlotAreaGroup.tsx`: propaga `colorScale` também aos grupos de barras.
- `plugins/plugin-ui/src/components/charts/seriesChartLegendItems.ts` e `seriesChart/ChartLegend.tsx`: legenda semântica correspondente à renderização, sem seleção de séries inexistentes.
- `plugins/tv-dashboard/src/content/chartStyleRecipes.ts`: preset semântico e round-trip (ativar/desativar) preservando paletas anteriores.
- `plugins/tv-dashboard/src/components/ChartColorsStylesMenu.tsx`: opção de pré-seleção no menu existente de paletas.
- `ChartSelectionFloatToolbar.tsx` e `selectionSections/ChartDesignSections.tsx`: habilitação contextual apenas em colunas/barras horizontais.
- Testes UI em `ChartColorsStylesMenu.test.tsx` e `chartStyleRecipes.test.ts`, testes de paint em `ChartSeriesBar.test.tsx`, teste de semântica em `seriesChartLegendItems.test.ts`.
- Workflow `tv-dashboard-visual-quality.yml` executa as regressões para esta PR.

## Roteiro de validação

1. Abra a programação do GR Diário e selecione o gráfico de evolução mensal das divergências (colunas).
2. No menu **Alterar cores**, selecione **Negativo / positivo**. Confirme perdas vermelhas, ganhos verdes e, quando houver, zeros cinza.
3. Verifique as alturas e o alinhamento em zero, inclusive em escalas com valores negativos altos e ganhos baixos.
4. Ative a legenda: devem aparecer os termos e cores correspondentes aos sinais presentes.
5. Desative e reative o preset: a seleção anterior de cores deve continuar disponível, sem cor semântica forçada ao desativar.
6. Salve a tela, atualize editor e TV publicada, e confirme que as cores persistem no bloco.
7. Teste uma tabela/barra multissérie com valores positivos e negativos simultâneos; a cor deve ser individual, não apenas por série.
8. Confirme que gráficos sem o preset, inclusive linhas, continuam inalterados.

## Deploy após merge

```bash
cd /home/operador/projetos/delpi-central
git switch main
git pull --ff-only origin main
bash infra/scripts/up-prod-sequential.sh --build plugin-ui tv-dashboard
```

**Observação:** Não encerrar o chamado #1610 sem confirmação da validação em produção.
