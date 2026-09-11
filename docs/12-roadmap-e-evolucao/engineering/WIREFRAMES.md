# Portal de Engenharia — wireframes

> **Status:** referência de UX para planejamento.  
> **Implementação:** não autorizada por este documento.

## 1. Princípios de navegação

A navegação principal segue o padrão dos portais maduros da Minha DELPI, com TopBar persistente e poucas jornadas de alto valor.

### Ordem travada da TopBar

```text
Início | Visão geral | Sala de interação | Minhas tarefas | LMPs | Ajuda
```

**Produtos não entra na TopBar.** Produtos e demais capacidades especializadas ficam na vitrine de ferramentas e em deep links contextuais.

## 2. Shell do portal

```text
+==================================================================================+
| Portal de Engenharia                                               [avatar] Nome |
|----------------------------------------------------------------------------------|
| Início | Visão geral | Sala de interação | Minhas tarefas | LMPs | Ajuda          |
+==================================================================================+
| conteúdo da rota                                                                  |
+==================================================================================+
```

A implementação deve reutilizar os factories/componentes do `@delpi/plugin-ui` equivalentes aos usados em Comercial/Suprimentos, com façade `engineeringUi.ts` e prefixo próprio do módulo.

## 3. WF-01 — Início

**Objetivo:** responder “o que importa para mim agora?” e concentrar acesso às ferramentas.

```text
+----------------------------------------------------------------------------------+
| Início                                                                            |
| Bom dia, <usuário>. Aqui está o que precisa da sua atenção.                      |
+----------------------------------------------------------------------------------+
| [ Minhas tarefas 07 ] [ LMPs críticas 03 ] [ Menções 02 ] [ Indicador-chave ]    |
+----------------------------------------------------------------------------------+
| MINHAS PRIORIDADES                                                                |
|  [!] LMP 123456 atrasada                         [Abrir]                           |
|  [ ] Solicitação MP aguardando análise          [Abrir]                           |
|  [@] Menção em Produto 90262957                  [Abrir sala]                      |
+----------------------------------------------------------------------------------+
| FERRAMENTAS                                                                       |
| [ Produtos ] [ Controle de MP ] [ Documentos técnicos ] [ Desenhos ]              |
| [ Não conformidades ] [ TRANSFORMA+ ] [ outras ferramentas permitidas ]           |
+----------------------------------------------------------------------------------+
| ATIVIDADE RECENTE                                                                 |
| LMPs recentes · salas recentes · documentos recentes                              |
+----------------------------------------------------------------------------------+
```

### Estados

- loading com skeleton;
- sem tarefas: estado positivo, não “vazio quebrado”;
- fonte parcial indisponível: banner discreto com dados restantes preservados;
- forbidden: ferramentas sem permissão não aparecem.

## 4. WF-02 — Visão geral

**Objetivo:** responder “como está a Engenharia?”.

```text
+----------------------------------------------------------------------------------+
| Visão geral                                              [Período] [Filial/Escopo]|
| Saúde operacional e indicadores da Engenharia.                                      |
+----------------------------------------------------------------------------------+
| [ Projetos/LMP no prazo ] [ Lead time ] [ NCs ] [ TRANSFORMA+ ]                   |
+----------------------------------------------------------------------------------+
| Evolução LMPs no prazo                     | Distribuição por status               |
| [ gráfico temporal ]                       | [ gráfico ]                           |
+----------------------------------------------------------------------------------+
| Gargalos / retornos                        | TRANSFORMA+                           |
| [ gráfico / ranking ]                      | [ resumo e CTA ]                      |
+----------------------------------------------------------------------------------+
| Atenções                                                                         |
| [ cards/lista de exceções com deep links ]                                        |
+----------------------------------------------------------------------------------+
```

Indicadores estratégicos não podem ser recalculados localmente no MFE quando a fonte canônica for Strategic Indicators.

## 5. WF-03 — Sala de interação

**Objetivo:** colaboração da Engenharia, geral e contextual.

### 5.1 Sem sala selecionada

```text
+----------------------------------------------------------------------------------+
| Sala de interação                         [Pesquisar] [Minhas] [Não lidas] [Nova]  |
| Conversas da Engenharia e contextos de trabalho.                                  |
+----------------------------------------------------------------------------------+
| [avatar] Geral da Engenharia                         último trecho...       10:42  |
| [avatar] Produto 90262957                             último trecho...       09:10  |
| [avatar] LMP 123456                                  último trecho...       ontem  |
| [avatar] Projeto ABC                                 último trecho...       ontem  |
+----------------------------------------------------------------------------------+
```

### 5.2 Sala aberta

Seguir o padrão consolidado da Sala de interação do Portal Comercial: lista + thread, painel contextual “Neste chat”, um único scroller de mensagens e composer do kit.

```text
+----------------------------------------------------------------------------------+
| Sala de interação / Produto 90262957                                              |
+----------------------+-----------------------------------------------------------+
| CONVERSAS            | Produto 90262957        [participantes] [contexto]         |
|                      |-----------------------------------------------------------|
| * Produto 90262957   | mensagem ...                                              |
|   LMP 123456         |                 resposta ...                               |
|   Geral              | mensagem ...                                              |
|                      |                                                           |
|                      |-----------------------------------------------------------|
|                      | [Responder...] [anexo] [formatar]                 [Enviar] |
+----------------------+-----------------------------------------------------------+
```

### Contexto da sala

O painel “Neste chat” pode exibir:

- objeto vinculado;
- participantes;
- mensagens fixadas;
- anexos;
- deep link para Produto/LMP/Projeto/Solicitação.

Mensagem não altera status oficial do objeto de negócio.

## 6. WF-04 — Minhas tarefas

**Objetivo:** worklist pessoal agregada, sem virar novo workflow engine.

```text
+----------------------------------------------------------------------------------+
| Minhas tarefas                          [Busca] [Origem] [Prioridade] [Status]      |
| Tudo que precisa da sua atuação na Engenharia.                                    |
+----------------------------------------------------------------------------------+
| 7 pendentes | 2 atrasadas | 3 hoje                                                |
+----------------------------------------------------------------------------------+
| Prior. | Origem       | Tarefa                         | Prazo | Estado | Ação      |
| Alta   | LMP          | Revisar LMP 123456            | hoje  | ...    | [Abrir]   |
| Média  | Controle MP  | Analisar solicitação #987     | —     | ...    | [Abrir]   |
| Alta   | NC           | Responder NC-0042             | ontem | ...    | [Abrir]   |
+----------------------------------------------------------------------------------+
```

Requisitos UX:

- origem claramente identificável;
- deep link no owner real;
- filtros na URL;
- F5/back/forward preservam estado;
- ações rápidas apenas se o backend owner fornecer `allowed_actions` de forma segura;
- sem tarefa: empty state informativo.

## 7. WF-05 — LMPs

### 7.1 Lista/painel

```text
+----------------------------------------------------------------------------------+
| LMPs                                        [Busca] [Período] [Status] [Filial]    |
| Acompanhe propostas e fluxos de Engenharia.                                      |
+----------------------------------------------------------------------------------+
| [ % no prazo ] [ Lead médio ] [ Total ] [ Atrasadas ]                            |
+----------------------------------------------------------------------------------+
| [gráficos resumidos]                                                              |
+----------------------------------------------------------------------------------+
| OV/LMP | Cliente | Nível | Status | Lead | Responsável | Última mov. | Ação        |
+----------------------------------------------------------------------------------+
```

### 7.2 Detalhe de LMP

```text
+----------------------------------------------------------------------------------+
| LMP 123456 / Cliente XYZ                                      [ações permitidas]  |
| status · nível · revisão · responsável · datas                                    |
+----------------------------------------------------------------------------------+
| [Resumo] [Produtos] [Histórico] [Gantt] [NCs]                                     |
+----------------------------------------------------------------------------------+
| conteúdo da aba                                                                    |
+----------------------------------------------------------------------------------+
```

**Produtos** dentro da LMP exibem resumo e CTA para a ferramenta Produtos. Evitar reconstruir ficha 360° inteira dentro do detalhe.

### 7.3 Histórico

Timeline baseada no contrato real de eventos, com estados, tempos e transições. Filtros devem permanecer na URL quando materiais.

### 7.4 Gantt

Reusar a inteligência já existente em `dashboard-lmps`, evoluindo apenas após inventário/paridade. Não redesenhar regra de cálculo no frontend.

## 8. WF-06 — Ajuda

**Ajuda é item da TopBar.**

```text
+----------------------------------------------------------------------------------+
| Ajuda                                                                              |
| Encontre orientação sobre o Portal de Engenharia.                                 |
+----------------------------------------------------------------------------------+
| [Pesquisar na ajuda............................................................]   |
+----------------------------------------------------------------------------------+
| COMEÇAR                    | PRINCIPAIS RECURSOS                                   |
| • O que é o Portal         | • LMPs                                               |
| • Como navegar             | • Produtos                                           |
| • Minhas tarefas           | • Sala de interação                                  |
|                            | • Controle de MP                                     |
+----------------------------------------------------------------------------------+
| FERRAMENTAS                | DOCUMENTOS E DESENHOS                                 |
| • Produtos                 | • Biblioteca de desenhos                             |
| • TRANSFORMA+              | • Documentos técnicos                               |
+----------------------------------------------------------------------------------+
| GLOSSÁRIO · PERGUNTAS FREQUENTES · CONTATO/SUPORTE                                |
+----------------------------------------------------------------------------------+
```

A ajuda deve usar linguagem de negócio, nunca paths de API, operationId ou detalhes TOTVS no texto destinado ao usuário.

## 9. WF-07 — Ferramenta Produtos

**Entrada:** card na vitrine de ferramentas ou deep link contextual.

### 9.1 Pesquisa

```text
+----------------------------------------------------------------------------------+
| Produtos                                                                           |
| [ Código, descrição, referência ou part number.............................. 🔍 ]  |
+----------------------------------------------------------------------------------+
| Pesquisas rápidas: [Estrutura] [Onde é usado] [Desenho] [Estoque]                |
+----------------------------------------------------------------------------------+
| Código   | Descrição                     | Tipo | Unidade | Grupo | Ação            |
+----------------------------------------------------------------------------------+
```

### 9.2 Ficha 360°

```text
+----------------------------------------------------------------------------------+
| Produto 90262957 — DESCRIÇÃO                                                      |
| tipo · unidade · grupo                                           [Abrir sala]      |
+----------------------------------------------------------------------------------+
| [Visão geral] [Estrutura] [Onde é usado] [Desenho] [Estoque] [Fornec.] [Custos]  |
+----------------------------------------------------------------------------------+
| conteúdo da dimensão                                                              |
+----------------------------------------------------------------------------------+
```

Acesso a preço/custo deve respeitar RBAC específico; não assumir que `engineering.products.view` concede dados sensíveis.

## 10. WF-08 — Biblioteca de desenhos

```text
+----------------------------------------------------------------------------------+
| Biblioteca de desenhos                                                            |
| [Código] [Nome arquivo] [Revisão] [Tipo] [Modificado em]                          |
+----------------------------------------------------------------------------------+
| 90261040 | 90261040_R10.pdf | R10 | revisão | 2026-08-20 | [Visualizar]          |
| 90262957 | 90262957.pdf     | —   | exato   | 2026-08-19 | [Visualizar]          |
+----------------------------------------------------------------------------------+
```

### Preview

```text
+----------------------------------------------------------------------------------+
| 90261040_R10.pdf                                     [Tela cheia] [Baixar]        |
| revisão R10 · tamanho · modificação                                                 |
+----------------------------------------------------------------------------------+
|                               PDF VIEWER                                          |
|                                                                                   |
+----------------------------------------------------------------------------------+
| [Abrir produto] [Abrir sala]                                                      |
+----------------------------------------------------------------------------------+
```

O frontend nunca recebe path físico do FILESERVER.

## 11. WF-09 — Documentos técnicos

Não construir um Explorer web genérico. A UI representa **bibliotecas autorizadas**.

```text
+----------------------------------------------------------------------------------+
| Documentos técnicos                         [Pesquisar] [Biblioteca] [Tipo]         |
+----------------------------------------------------------------------------------+
| Bibliotecas: [LMPs] [Projetos] [Técnicos]                                          |
+----------------------------------------------------------------------------------+
| Nome                 | Contexto   | Tipo | Alterado | Tamanho | Ação               |
| RQ-060.docx          | LMP 123456 | docx | ...      | ...     | [Abrir/baixar]      |
| memoria-calculo.xlsx | Projeto ABC| xlsx | ...      | ...     | [Baixar]            |
+----------------------------------------------------------------------------------+
```

No MVP, preview inline deve ser limitado a formatos suportados com segurança; arquivos Office podem começar como download controlado.

## 12. WF-10 — Controle de MP

A página do Portal é um hub contextual, não uma duplicação do `my-requests`.

```text
+----------------------------------------------------------------------------------+
| Controle de matéria-prima                                                         |
| Solicite criação/alteração e acompanhe seus pedidos.                              |
+----------------------------------------------------------------------------------+
| [ + Criar matéria-prima ] [ Alterar matéria-prima ]                               |
| [ Minhas solicitações ]     [ Fila de atendimento ]†                              |
+----------------------------------------------------------------------------------+
| Resumo opcional: minhas abertas · devolvidas · concluídas                          |
+----------------------------------------------------------------------------------+
```

Cada CTA navega para a rota canônica do `my-requests`, preservando o tipo/contexto.

## 13. WF-11 — TRANSFORMA+

```text
+----------------------------------------------------------------------------------+
| TRANSFORMA+                                                                        |
| [ Ganhos ] [ Processos ativos ] [ Indicador ]                                      |
+----------------------------------------------------------------------------------+
| resumo / evolução                                                                  |
+----------------------------------------------------------------------------------+
| [Abrir Transformômetro]                                                            |
+----------------------------------------------------------------------------------+
```

Não recriar CRUD/atas/matriz do Transformômetro.

## 14. Padrões visuais obrigatórios

- façade `engineeringUi.ts` sobre `@delpi/plugin-ui`;
- `EngineeringTopBar` via factory do kit, se compatível com a API vigente;
- `PageHero`, `PagePath`, filtros, chips, cards, tabelas, empty/loading/error e helps pelo kit;
- ícones `lucide-react`;
- claro/escuro via tokens;
- mobile <= 768px em coluna única quando aplicável;
- touch target >= 44x44px;
- sem CSS `.delpi-ui-*` no MFE;
- sem `body`, `:root` global ou utilitários genéricos no CSS do MFE.

## 15. Rotas conceituais

Os paths finais devem ser validados contra manifesto/colisões antes da implementação. Direção proposta:

```text
/apps/engineering
/apps/engineering/overview
/apps/engineering/rooms
/apps/engineering/rooms/:roomId
/apps/engineering/my-tasks
/apps/engineering/lmps
/apps/engineering/lmps/:saleNumber
/apps/engineering/help
/apps/engineering/tools/products
/apps/engineering/tools/products/:code
/apps/engineering/tools/drawings
/apps/engineering/tools/documents
/apps/engineering/tools/raw-material-control
/apps/engineering/tools/transforma-plus
```

## 16. Critérios de UX

Cada página user-facing deve validar:

- rota/deep link;
- loading;
- success;
- empty;
- error/downstream error;
- forbidden;
- F5/back/forward;
- desktop;
- mobile;
- tema claro;
- tema escuro;
- teclado/foco em ações críticas;
- ajuda contextual sincronizada.
