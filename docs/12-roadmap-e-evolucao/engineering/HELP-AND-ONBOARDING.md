# Portal de Engenharia — Ajuda e onboarding

> **Status:** contrato de conteúdo/UX para a implementação.  
> **Regra:** toda mudança user-facing avalia `feature-help-sync`; Help não é etapa opcional pós-feature.

## 1. Objetivo

A Ajuda deve permitir que um usuário entenda o Portal sem conhecer nomes de APIs, tabelas TOTVS, services ou paths internos.

Rota principal:

```text
/apps/engineering/help
```

Ajuda permanece na TopBar.

## 2. Estrutura do Manual

```text
Ajuda
├── Começar
│   ├── O que é o Portal de Engenharia
│   ├── Como navegar
│   ├── Áreas principais × Ferramentas
│   └── Como usar busca e favoritos
├── Jornadas principais
│   ├── Visão geral
│   ├── Sala de interação
│   ├── Minhas tarefas
│   └── LMPs
├── Ferramentas
│   ├── Produtos
│   ├── Biblioteca de desenhos
│   ├── Documentos técnicos
│   ├── Controle de MP
│   ├── Não conformidades
│   └── TRANSFORMA+
├── Indicadores
├── Permissões e acesso
├── FAQ
└── Glossário
```

## 3. Quero → onde

Tabela mínima:

| Quero… | Onde | Como |
|---|---|---|
| saber o que precisa da minha atenção | Início | use prioridades, tarefas e menções |
| ver a situação da Engenharia | Visão geral | consulte indicadores e tendências |
| conversar com a equipe sobre um item | Sala de interação | abra/crie uma sala contextual |
| ver o que depende de mim | Minhas tarefas | filtre por origem/estado/prioridade |
| acompanhar uma LMP | LMPs | pesquise a LMP e abra o detalhe |
| consultar estrutura/BOM de um produto | Produtos | pesquise o código e abra Estrutura |
| saber onde um item é usado | Produtos | use a dimensão Onde é usado |
| abrir o desenho de um item | Biblioteca de desenhos ou Produto | pesquise o código e visualize o PDF |
| acessar documento técnico | Documentos técnicos | escolha a biblioteca autorizada |
| criar/alterar matéria-prima | Controle de MP | o Portal leva ao fluxo canônico Minhas Solicitações |
| acompanhar TRANSFORMA+ | Ferramentas → TRANSFORMA+ | veja resumo e abra o Transformômetro |

## 4. FAQ mínima

### Qual a diferença entre Início e Visão geral?

Início é pessoal e orientado a ação/descoberta. Visão geral mostra saúde e indicadores da área.

### Qual a diferença entre Sala e Minhas tarefas?

Sala é colaboração/conversa. Minhas tarefas reúne itens que exigem ação; mensagem não altera automaticamente o status oficial de um processo.

### Por que Produtos não aparece na TopBar?

Produtos é uma ferramenta especializada, acessível pelo launcher, busca, favoritos e contexto de LMP.

### Quem pode ver uma sala?

Somente usuários autorizados pelo Portal e pela política/membership da sala. Conhecer o link/UUID não concede acesso.

### Como mencionar alguém?

O composer deve oferecer menção de usuário usando a identidade canônica. A Ajuda não deve prometer notificação offline até o contrato correspondente estar implementado.

### Onde ficaram Controle de MP e TRANSFORMA+?

Continuam com owners próprios. O Portal fornece resumo/atalho e leva o usuário ao fluxo oficial.

### O Portal altera arquivos do FILESERVER?

No MVP, não. Bibliotecas técnicas são read-only e controladas.

### Por que não vejo uma ferramenta?

A visibilidade depende das permissions efetivas e do escopo do usuário.

### O que é Nota IDD?

É o score calculado pelo Strategic Indicators conforme o indicador/meta oficial; o Portal apenas apresenta o valor recebido.

## 5. Glossário mínimo

| Termo | Definição user-facing |
|---|---|
| LMP | processo/jornada de Engenharia acompanhado no Portal; validar expansão oficial da sigla antes da copy final |
| BOM / Estrutura | composição de itens/componentes de um produto |
| Onde é usado | produtos/estruturas que utilizam o item consultado |
| Não conformidade | registro de desvio associado à jornada LMP conforme regra atual |
| Controle de MP | solicitação de criação/alteração de matéria-prima atendida pelo Minhas Solicitações |
| TRANSFORMA+ | iniciativa/processo de melhoria acompanhado pelo Transformômetro |
| IDD | nota do indicador estratégico conforme cálculo do sistema de Indicadores Estratégicos |
| Sala contextual | conversa vinculada a um objeto como Produto ou LMP |
| Ferramenta | capacidade especializada acessada pelo Portal, fora da TopBar principal |

Não inventar a expansão de siglas que não esteja confirmada no repositório/negócio.

## 6. Help contextual

Conteúdo técnico centralizado, por exemplo:

```text
plugins/engineering/src/content/helpTooltips.ts
plugins/engineering/src/content/userManualContent.ts
plugins/engineering/src/content/glossaryContent.ts
```

Nomes finais seguem o padrão real do MFE no E1.

### Padrão visual

Quando existir label/título semântico, o próprio texto é o alvo do tooltip. Evitar `?` separado.

Exemplos:

- título de KPI;
- Meta/Nota IDD;
- labels de filtros;
- seção “Ferramentas”;
- controles de Sala;
- estados/filtros de LMP.

Usar primitives/factories do `plugin-ui`.

## 7. Conteúdo por página

### Início

Explicar:

- prioridades;
- origem dos cards;
- ferramentas;
- favoritos;
- diferença Início × Overview.

### Visão geral

Explicar:

- indicador de projetos no prazo;
- ganhos TRANSFORMA+;
- meta/realizado/IDD;
- escopo consolidado;
- indicadores operacionais × estratégicos.

### Sala

Explicar:

- salas gerais/contextuais;
- participantes;
- menções;
- reações;
- anexos;
- read/unread;
- que conversa não substitui workflow.

### Minhas tarefas

Explicar origem, prioridade, prazo, deep link e limitações de ações rápidas.

### LMPs

Explicar status, lead/histórico, Gantt, produtos e NCs somente conforme semântica comprovada.

### Produtos/desenhos/documentos

Explicar diferenças entre estrutura, onde-usado, desenho e arquivo técnico; avisar sobre permissions de custos/download quando aplicável.

## 8. Onboarding

Primeiro acesso pode mostrar até 3 atalhos, sem bloquear a tela:

1. “Veja o que precisa da sua atenção” → Início;
2. “Acompanhe suas LMPs” → LMPs, se autorizado;
3. “Encontre ferramentas” → launcher/busca.

Onboarding não deve repetir a cada sessão indefinidamente. Se persistência for necessária, definir owner antes de implementar.

## 9. Busca da Ajuda

P0 pode ser client-side sobre conteúdo versionado se volume pequeno. Não criar backend/search engine sem necessidade.

Busca deve indexar labels amigáveis, sinônimos e termos do glossário.

## 10. Help e permissions

Não revelar em Help detalhes de feature que o usuário não pode acessar como se fossem disponíveis. Manual pode explicar conceitos gerais, mas CTAs/deep links devem respeitar capabilities.

## 11. Testes

- rota `/help` acessível a `engineering.access`;
- conteúdo Quero→onde cobre todas as jornadas principais;
- FAQ e glossário renderizam;
- help contextual existe nas features novas;
- nenhum `?` standalone onde há label adequado;
- keyboard/focus abre tooltip conforme kit;
- texto não contém operationId/path técnico em superfície user-facing;
- links internos respeitam basePath e RBAC.

## 12. Definition of Done de Help

Uma feature não está fechada quando a UI muda e:

- tooltip ficou desatualizado;
- Manual aponta rota antiga;
- FAQ descreve regra anterior;
- glossário usa termo incorreto;
- screenshot/wireframe promete controle inexistente.

Help faz parte do mesmo entregável da feature.
