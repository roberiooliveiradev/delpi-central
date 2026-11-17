# GLPI #1606 — Fundo transparente em gráficos, KPIs e tabelas do TV Dashboard

**Solicitante:** TI / TV GR – Rio Bananal/ES  
**Data:** 17/11/2026  
**Status:** Implementado em branch isolada, aguardando PR, testes de integração, merge e publicação.

## Problema

Ao sobrepor gráficos a um template visual personalizado no TV Dashboard, o fundo branco cobre a arte da tela. A cor de fundo não possuía opção simples e evidente de transparência nas propriedades visuais. No caso de gráficos, apenas retirar o preenchimento da moldura deixava a área interna de plotagem branca, porque são camadas independentes.

## Implementação

### Gráficos (`chart_view`)

- **Formatar / Aparência → Fundo do gráfico:** opções **Normal (fundo padrão)** e **Transparente (sem preenchimento)**. Também disponível nas propriedades da parte **Moldura do gráfico / Área de plotagem**.
- O modo transparente atualiza em conjunto **`chartOptions.backgroundColor`**, **`chartParts.chartArea.style.fill`** e **`chartParts.plotArea.style.fill`** com `transparent`.
- O botão **Sem preenchimento** da moldura na faixa **Forma** aplica a mesma correção às duas camadas, evitando plot branco residual.
- Preserva eixos, série, legenda, rótulos, título, cor das barras/linhas, dimensões, contorno e configurações de interação.
- **Normal** volta à cor de superfície padrão. Cores personalizadas de moldura podem ser escolhidas novamente pelos controles já existentes.
- O mesmo contrato de `chartParts` é utilizado pelo editor e renderizador da apresentação publicada, inclusive gráficos sem pontos e velocímetros.

### KPIs (`kpi_view`)

- No inspetor de KPI, **Fundo do KPI → Normal / Transparente**; o preenchimento do card também permite **Sem fundo** no seletor de cor.
- A autoridade de renderização continua em `kpiParts.card.style.fill`, espelhada em `kpiOptions.backgroundColor`. Textos, valores, sinais e regras condicionais permanecem intactos.

### Tabelas (`table_view`)

- No inspetor de tabela, **Fundo da tabela → Normal / Transparente** e opção **Sem fundo** no preenchimento da moldura e de células individuais.
- A autoridade é `tableParts.frame.style.fill`. A classe `delpi-ui-config-table--transparent-background` força transparência visual no frame, título, cabeçalho, células e bandas de linhas no editor e na TV publicada.
- As cores anteriores do cabeçalho, das células e dos destaques **continuam salvas**; ao voltar para Normal são novamente utilizadas. O modo transparente altera apenas as superfícies de fundo e não apaga o texto.

## Compatibilidade e segurança

- Sem alterações em API DELPI, TV Dashboard API, modelos de dados, rotas ou cálculos.
- Sem migração de banco. Alteração opt-in, sem impacto em telas existentes que não ativarem transparência.
- Nenhuma programação ou slide existente será alterado automaticamente.
- O renderizador do player aplica o mesmo preenchimento a `chartParts`/`kpiParts`/`tableParts`, sem configurações específicas por ambiente.
- Opacidade de texto/séries não é afetada. Para templates escuros, orientar o usuário a ajustar a **cor do texto/eixos** separadamente para contraste adequado.

## Checklist de validação

1. Executar `cd plugins/tv-dashboard && npm run ci`, verificando lint, TypeScript e build.
2. Executar teste unitário `src/utils/visualBackgroundTransparency.test.ts`.
3. Criar um gráfico de colunas sobre um template azul-marinho, selecionar **Transparente**; verificar se são visíveis os elementos do template atrás da moldura **e da plotagem**, sem perder barras, grade, eixos ou legenda.
4. Usar um gráfico sem dados; confirmar que não nasce um fundo branco residual.
5. Aplicar transparência num KPI e numa tabela com linhas alternadas; verificar texto, cabeçalho, células e linhas com fundo transparente.
6. Desativar transparência e conferir o retorno do fundo padrão/estilos, sem descaracterizar o layout.
7. Salvar, recarregar a tela, abrir prévia e publicar temporariamente em HML. Comparar preview com o player em 16:9 e com o editor.
8. Verificar o gráfico de evolução mensal do GR Rio Bananal após publicação, sem alterar o painel real antes do aceite.

## Deploy proposto (após CI e merge)

Alterações concentradas em `plugins/tv-dashboard`, `plugins/tv-dashboard-presentation` e `plugins/plugin-ui`. O Compose `tv-dashboard` é construído a partir do contexto `../plugins`; para usar também os novos estilos do kit, recompilar em sequência:

```bash
cd /home/operador/projetos/delpi-central
git switch main
git pull --ff-only origin main
bash infra/scripts/up-prod-sequential.sh --build plugin-ui tv-dashboard
```

Não é necessário deploy de `api-delpi` ou `tv-dashboard-api`.

**Aceite:** o usuário escolhe **Transparente** nas propriedades do gráfico e vê seu template atrás de toda a área visual, com o mesmo efeito após salvar e publicar.
