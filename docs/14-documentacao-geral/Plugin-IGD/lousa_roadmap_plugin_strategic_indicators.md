# Roadmap — Plugin Strategic Indicators

## Visão geral
Este roadmap organiza o desenvolvimento do plugin **Strategic Indicators** em etapas incrementais, priorizando:

- alinhamento funcional
- fundação técnica do microfrontend
- entrega rápida de valor executivo
- aprofundamento analítico gradual
- governança final do plugin dentro da MinhaDelpi

A lógica de execução é:

1. alinhar contrato do produto
2. subir fundação técnica e visual
3. entregar visão executiva
4. aprofundar drill-down e análise
5. adicionar tendências e alertas
6. concluir governança, segurança e hardening

---

## Fase 0 — Alinhamento funcional e contrato do produto

### Objetivo
Fechar o escopo oficial do plugin antes de iniciar a implementação.

### Entregáveis
- nome final do plugin
- definição oficial das telas do MVP
- catálogo inicial de indicadores
- definição de cálculo do IGD no sistema
- definição dos departamentos e pesos oficiais
- definição das fontes de dados por indicador
- definição dos perfis de acesso

### Decisões que precisam ficar fechadas
- quais indicadores entram no MVP
- quais campos cada indicador precisa ter
- se a meta será mensal, anual ou ambas
- se o cálculo da nota será feito no backend ou em camada analítica dedicada
- se o modo apresentação entra no MVP 1 ou MVP 2

### Critério de conclusão
- escopo aprovado
- nomenclatura aprovada
- mapa de telas aprovado
- permissões iniciais aprovadas

---

## Fase 1 — Fundação técnica do plugin

### Objetivo
Criar a estrutura mínima do microfrontend e deixá-lo plugável na MinhaDelpi.

### Entregáveis de frontend
- criação do projeto `strategic-indicators`
- configuração Vite + React
- configuração de Module Federation
- `main.tsx`, `bootstrap.tsx`, `App.tsx`
- roteamento interno do plugin
- layout base do plugin
- integração com tokens do portal

### Entregáveis de governança
- criação do `delpi.manifest.json`
- definição de `id`, `basePath`, `entry`
- cadastro das permissões iniciais
- rotas do plugin definidas

### Entregáveis de integração
- plugin servindo em `/apps/strategic-indicators`
- `remoteEntry.js` em `/apps/strategic-indicators/assets/remoteEntry.js`

### Critério de conclusão
- plugin sobe isoladamente
- portal consegue carregar o microfrontend
- manifesto está aderente ao contrato oficial
- menu do portal consegue exibir o plugin via rota governada

---

## Fase 2 — Fundação visual e design system do módulo

### Objetivo
Transformar o wireframe em interface real reutilizável.

### Entregáveis
- shell visual do plugin
- grid base
- `FilterBar`
- `StatusBadge`
- `IgdHeroCard`
- `DepartmentCard`
- componentes de tabela
- componentes de empty, loading e error state
- suporte a light/dark mode com os tokens existentes

### Resultado esperado
Ao final dessa fase, o plugin ainda pode operar com mock, mas já terá:
- linguagem visual consistente
- responsividade
- hierarquia visual pronta
- base para acelerar todas as telas

### Critério de conclusão
- tela inicial com layout real funcionando
- componentes reutilizáveis prontos
- padrão visual aprovado

---

## Fase 3 — MVP 1: Visão Executiva

### Objetivo
Entregar a primeira tela útil para demonstração interna.

### Escopo
- tela `/apps/strategic-indicators`
- hero do IGD
- faixa de classificação
- cards dos departamentos
- gráfico de contribuição por área
- gráfico de tendência do IGD
- bloco de alertas rápidos
- filtros de período e unidade

### Backend/API
Endpoint consolidado mínimo sugerido:

```text
GET /apps/api-delpi/strategic-indicators/executive-summary
```

### O endpoint deve retornar
- competência
- valor do IGD
- classificação
- variação
- lista de departamentos com nota, peso, contribuição e tendência
- alertas resumidos

### Critério de conclusão
- plugin entrega valor executivo real
- reunião interna já consegue usar a tela principal
- dados saem do mock e entram em API real

---

## Fase 4 — MVP 2: Departamentos e drill-down

### Objetivo
Permitir leitura analítica por área.

### Escopo de frontend
- `/departments`
- `/departments/:departmentId`
- tabela comparativa de departamentos
- histórico do IDD
- detalhamento dos indicadores da área
- resumo gerencial lateral

### Backend/API
Endpoints mínimos sugeridos:

```text
GET /apps/api-delpi/strategic-indicators/departments
GET /apps/api-delpi/strategic-indicators/departments/{departmentId}
```

### O que a API deve devolver
- nota do IDD
- peso
- contribuição ponderada
- variação
- indicadores da área
- meta, realizado, nota, gap, tendência

### Critério de conclusão
- o usuário consegue sair do “todo” e entender a causa
- drill-down por departamento está funcional
- navegação principal do plugin fica completa

---

## Fase 5 — MVP 3: Indicadores analíticos

### Objetivo
Criar a visão operacional e analítica completa.

### Escopo
- tela `/indicators`
- filtros avançados
- busca textual
- ordenação
- tabela completa de indicadores
- painel lateral de detalhe
- exportação inicial CSV/XLSX

### Backend/API
Endpoint sugerido:

```text
GET /apps/api-delpi/strategic-indicators/indicators
```

### Suporte de filtros esperado
- período
- unidade
- departamento
- status
- criticidade
- busca textual

### Critério de conclusão
- o plugin deixa de ser só painel executivo
- passa a servir também para análise operacional

---

## Fase 6 — Tendências e visão temporal

### Objetivo
Adicionar leitura histórica e comportamento ao longo do tempo.

### Escopo
- tela `/trends`
- série histórica do IGD
- série histórica dos IDDs
- heatmap mensal por departamento
- ranking de melhora e piora

### Backend/API
Endpoint sugerido:

```text
GET /apps/api-delpi/strategic-indicators/trends
```

### Critério de conclusão
- o plugin responde não só “quanto está”, mas também “como está evoluindo”

---

## Fase 7 — Alertas e priorização gerencial

### Objetivo
Traduzir leitura analítica em foco de ação.

### Escopo
- tela `/alerts`
- indicadores críticos
- recorrência
- impacto estimado no IGD
- ranking de severidade
- agrupamento por área

### Backend/API
Endpoint sugerido:

```text
GET /apps/api-delpi/strategic-indicators/alerts
```

### Critério de conclusão
- o plugin passa a apoiar decisão, não só monitoramento

---

## Fase 8 — Modo apresentação

### Objetivo
Criar a experiência própria para reunião mensal.

### Escopo
- tela `/presentation`
- fullscreen
- tipografia ampliada
- simplificação visual
- navegação entre blocos
- exportação para PDF/imagem em evolução posterior

### Critério de conclusão
- a reunião mensal pode ser feita diretamente no plugin

---

## Fase 9 — Configuração e governança do painel

### Objetivo
Dar autonomia controlada para administrar o módulo.

### Escopo
- tela `/settings`
- pesos por departamento
- catálogo de indicadores
- metas por competência
- regras de exibição
- ativação/inativação de indicadores
- permissões de administração

### Permissão principal
```text
strategic-indicators.settings.manage
```

### Critério de conclusão
- a manutenção do painel deixa de depender de ajuste manual em código para mudanças simples

---

## Fase 10 — Registro final, segurança e hardening

### Objetivo
Fechar o plugin como produto governado da MinhaDelpi.

### Entregáveis
- manifesto final validado
- registro do plugin na Core
- revisão de permissões
- validação JWT no backend
- testes por perfil
- logs estruturados
- tratamento de erros padronizado
- healthcheck
- revisão de cache e publicação do `remoteEntry.js`

### Critério de conclusão
- plugin pronto para uso oficial no ecossistema

---

## Sequência prática recomendada

1. Fase 0 — Alinhamento
2. Fase 1 — Fundação técnica
3. Fase 2 — Fundação visual
4. Fase 3 — Visão Executiva
5. Fase 4 — Departamentos
6. Fase 5 — Indicadores
7. Fase 6 — Tendências
8. Fase 7 — Alertas
9. Fase 8 — Presentation
10. Fase 9 — Configuração
11. Fase 10 — Hardening e registro final

---

## Melhor recorte de entregas

### MVP 1
- Fase 0
- Fase 1
- Fase 2
- Fase 3

**Entrega:**
- plugin carregando na MinhaDelpi
- visão executiva do IGD funcionando

### MVP 2
- Fase 4
- Fase 5

**Entrega:**
- drill-down por departamento
- análise detalhada por indicador

### Release gerencial
- Fase 6
- Fase 7
- Fase 8

**Entrega:**
- tendências
- alertas
- modo apresentação

### Release corporativa final
- Fase 9
- Fase 10

**Entrega:**
- governança
- administração
- hardening
- operação oficial

---

## Riscos principais a evitar

- começar pela tela mais complexa e não pela fundação
- misturar regra de negócio no frontend
- deixar cálculo de indicador espalhado na UI
- criar permissões genéricas demais
- subir microfrontend sem manifesto validado
- ignorar o padrão oficial de `remoteEntry.js`
- acoplar o plugin a dados fixos ou fórmulas hardcoded
- deixar settings sem proteção de permissão

---

## Checklist resumido por etapa

### Fundação
- [ ] projeto do plugin criado
- [ ] federation configurado
- [ ] manifesto criado
- [ ] rotas definidas
- [ ] permissões definidas

### MVP executivo
- [ ] visão executiva implementada
- [ ] API de resumo pronta
- [ ] filtros básicos funcionando

### Drill-down
- [ ] comparação de departamentos
- [ ] detalhe do departamento
- [ ] indicadores analíticos

### Gestão
- [ ] tendências
- [ ] alertas
- [ ] modo apresentação

### Governança
- [ ] settings
- [ ] manifesto final
- [ ] registro do plugin
- [ ] revisão de segurança
- [ ] testes finais

---

## Recomendação prática

A melhor forma de começar é executar juntas:

- Fase 1
- Fase 2
- Fase 3

Isso entrega rapidamente:
- plugin real dentro da MinhaDelpi
- interface com cara de produto
- visão executiva funcional

Depois seguir para:
- Fase 4
- Fase 5

Assim o plugin ganha profundidade analítica sem perder velocidade de entrega.

