# Yamazumi V4 — especificação de primeira capacidade

**Status:** TARGET para Studio; V3 do Portal Engenharia é base existente. Yamazumi é método visual, não solver de linha.

## Contextos suportados pretendidos
1. Produto oficial (rota autorizada, sem mutação da fonte).
2. Processo manual (operações digitadas, `PROVIDED/DRAFT_LOCAL`).
3. Estudo misto: operação oficial preservada e elemento hipotético com origem visível. Não reclassificar operação hipotética como oficial.

## Elementos
- **Operation Palette:** catálogo de operações disponíveis, filtro/busca, tempo, categoria, origem, CT/recurso apenas se presentes.
- **Station Board:** postos renomeáveis, reordenáveis, adicionáveis; atribuição exclusiva por ID; botões de mover e opção drag-and-drop acessível; seção `Não atribuídas`.
- **Yamazumi Chart:** colunas empilhadas por posto, linha de takt, eixo min/s, legenda categórica, tooltip acessível, aviso de valores UNKNOWN.
- **Scenario Bar:** A/B e cenários compatíveis, salvar nesta aba, comparar, limpar com confirmação.
- **Operation Table:** mesma coleção base, edição manual com validação, selecionar/atribuir posto e destaque sincronizado com gráfico.

## Invariantes funcionais
- Fonte oficial e tempo oficial imutáveis; overlay manual com `PROVIDED` e `DRAFT_LOCAL`.
- Uma operação atribuída a somente um posto, a menos que exista política explícita de divisão/replicação em novo contrato.
- Valor ausente não conta como zero; cargas parciais mostram `UNKNOWN` e operação sem tempo.
- `setup_hours` não vira tempo por peça sem `batch_size` validado; escolher explicitamente o que a barra agrega.
- Sobre-takt informa excesso matemático, **não** conclusões sobre máquinas, pessoas ou precedência.
- Não inferir paralelismo ao aumentar operadorCount.
- Estudo com uma operação agregada só exibe barra agregada; orientar criação explícita de elementos para detalhamento.
- Sem takt, gráfico mostra carga mas não linha artificial nem afirma `viável`.

## Fluxos interativos
**Adicionar operação manual:** Inserir linha com descrição e tempo fornecidos → validar → refletir imediatamente nas duas views; a análise oficial permanece preservada.  
**Mover operação:** Escolher origem e destino → confirmar integridade dos IDs → atualizar cenário local → recalcular apresentação (soma aritmética, sem solver) → invalidar resultados externos anteriores.  
**Editar elemento:** Pode detalhar uma operação quando o usuário tiver dados próprios; elementos e somas devem declarar se total substitui ou é decomposição do tempo oficial para evitar dupla contagem.  
**Comparar A/B:** Only same source, context, revision, tempo base e período; caso contrário `not comparable`, sem percentual fictício.

## Tooltip mínimo
Posto, operação/elemento, tempo com unidade, categoria, origem, fonte/revisão quando houver, cenário e limitações. Texto alternativo/table view fornece leitura sem hover.

## Exports
CSV/XLSX/PDF: parâmetros, estudo, tarefas e postos, provenance, notas, warnings, método/versão; label `DRAFT / SIMULATION` nos resultados de edição.

## Cenários de QA críticos
0 postos; posto sem operações; operação desconhecida; operação sem tempo; uma única operação; duas operações com mesmo código mas recurso diferente; mesma tarefa em dois postos; posto > takt; mudança de filial/estágio; mudança de dado oficial; F5; storage bloqueado; importação futura; teclado; dark/light e layouts 1440/1024/390/320.
