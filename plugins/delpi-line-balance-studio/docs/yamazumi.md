# Yamazumi — primeira implementação greenfield

**Status:** TARGET / NOT_IMPLEMENTED. Não reutilizar código do Yamazumi da Engenharia.

## Modo de uso
Criar estudo com ou sem produto, editar operações em tabela (descrição, tempo, categoria e origem), atribuir a postos por seleção/arrastar, visualização imediata de carga por posto e takt. Clicar em uma barra seleciona operação na tabela, e vice-versa. Atribuir uma operação a outro posto só altera cenário `DRAFT/SIMULATION`.

## Componentes originais propostos
`OperationGrid`, `StationBoard`, `YamazumiView`, `ScenarioSwitcher`, `MethodPicker`; controles genéricos do Plugin UI, não clones de componentes existentes em outros portais.

## Comportamento
- Barras empilhadas só por categorias efetivamente fornecidas ou observadas; se apenas tempo total, barra única rotulada `Agregado — composição desconhecida`.
- Linha de takt somente com dados de demanda e disponibilidade válidos; acima do takt = alerta matemático, não prova de inviabilidade física.
- Tempo ausente = UNKNOWN, tarefa não atribuída destacada, posto vazio sem carga fictícia.
- Proibir contagem duplicada e divisão/replicação automática; mais operadores ≠ tempo automaticamente dividido.
- Operações criadas manualmente são PROVIDED; operações oficiais permanecem OBSERVED e imutáveis na fonte.
- Cenários comparáveis somente com contexto/período/revisão compatíveis.
- Exportações com modo, hipóteses, operações, unidade, limitações e proveniência; sem alegar publicação.

## Aceite
Criar 3 operações manuais → criar 2 postos → atribuir por clique → gráfico reflete carga → mudar por tabela → gráfico sincroniza → Novo cenário mantém original → F5 recupera no escopo autorizado → Limpar confirma. Repetir em light/dark, 1440/1024/390/320 e teclado.
