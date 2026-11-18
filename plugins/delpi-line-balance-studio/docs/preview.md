# Contrato da interface reutilizável e da demo

| Requisito | Aceite |
| --- | --- |
| RQ-LBS-06 · Interface independente | AC-LBS-06 · Um host registra o elemento `delpi-line-balance-studio` e fornece um `ManualStudyInput` pela propriedade `study`. O host pode observar `study-change` com o DTO atualizado. |
| RQ-LBS-07 · Estudo manual e Yamazumi | AC-LBS-07 · Operações e postos editáveis, atribuição por seletor ou arrastar, total conhecido por posto e indicação explícita para tempos desconhecidos. Tabela e gráfico refletem o mesmo cenário. |
| RQ-LBS-08 · Condições de produção | AC-LBS-08 · Turno por relógio ou duração, múltiplas pausas, demanda e lote, validação pelo contrato existente e referência de takt da simulação somente com turno válido e demanda positiva. |
| RQ-LBS-11 · Plugin UI | AC-LBS-11 · Studio e demo usam os controles públicos do Plugin UI, com tema do host, navegação por teclado e edição de tempos fracionários. |
| RQ-LBS-09 · Demo Pages | AC-LBS-09 · Layout usável no desktop e no celular, build estático com fixture fictícia, sem containers, credenciais ou acesso a fonte oficial. |

O Studio é responsável pelo rascunho e pela projeção visual. A interface recebe um DTO local validável e emite uma cópia nas alterações locais. O host continua responsável por persistência, identidade, permissões e APIs oficiais. A demo usa estado em memória. A referência de takt divide o tempo líquido pela demanda informada. Cargas com tempos desconhecidos são parciais e não permitem concluir viabilidade. O M5 visual não aplica solvers, precedências ou restrições de engenharia.

A integração importa `registerLineBalanceStudio` de `@delpi/line-balance-studio/ui`. Depois de registrar o elemento, o host define `element.study = input`. O evento `study-change` propaga `detail.study`, com o mesmo formato de entrada, inclusive durante a correção de condições inválidas.

## Controles compartilhados e inventário

O Studio compõe o `PageHeader`, `SectionCard`, `SimpleKpiCard`, `StateBox`, `StatusBadge`, `DataTable`, `StackedColumnChart` e os controles públicos de `@delpi/plugin-ui`. O `ModernSelectControl` usa o mecanismo compartilhado de seleção com a apresentação da Minha DELPI. O rascunho, as atribuições, as cargas e o takt continuam no Studio.

Inventário em `784d7047a6fb`, por busca literal de `FormSelectControl` em arquivos TSX de aplicação, com testes, catálogo e o próprio Studio excluídos:

| Consumidor direto | Arquivos |
| --- | ---: |
| Painel de TV (`tv-dashboard`) | 28 |
| CIPA (`cipa`) | 3 |
| Comitê de Ética (`comite-etica-conduta`) | 2 |
| Production Pulse (`production-pulse`) | 1 |
| Plugin UI (editor de cores de série, correção PRC e barra de texto rico) | 3 |

A variante anterior continua disponível para esses consumidores. Sua retirada depende da migração dos usos diretos e da confirmação das superfícies que importam controles do kit por federação.
