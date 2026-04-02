# Etapa 1 — Fundação técnica do plugin Strategic Indicators

## Status da etapa
Concluída

## Objetivo da etapa
Criar a base técnica mínima do plugin para que ele exista como microfrontend federado plugável na MinhaDelpi, com manifesto inicial, rotas definidas e estrutura pronta para integração com o portal.

---

## Referência da etapa no roadmap
Esta etapa corresponde à **Fase 1 — Fundação técnica do plugin**.

Objetivos previstos no roadmap:
- criação do projeto `strategic-indicators`
- configuração Vite + React
- configuração de Module Federation
- `main.tsx`, `bootstrap.tsx`, `App.tsx`
- roteamento interno do plugin
- layout base do plugin
- integração com tokens do portal
- criação do `delpi.manifest.json`
- definição de `id`, `basePath`, `entry`
- cadastro das permissões iniciais
- definição das rotas do plugin
- plugin servindo em `/apps/strategic-indicators`
- `remoteEntry.js` em `/apps/strategic-indicators/assets/remoteEntry.js`

---

## Lista oficial do que deve ser feito nesta etapa

### 1. Fechar os identificadores técnicos do plugin
- confirmar `id`
- confirmar `name`
- confirmar `basePath`
- confirmar `entry`
- confirmar `serviceName` do backend

### 2. Fechar o contrato inicial de navegação
- consolidar rotas do plugin
- consolidar permissões por rota
- definir quais rotas entram no menu e quais ficam ocultas

### 3. Fechar o manifesto inicial
- validar `schemaVersion`
- validar `type`
- validar `ui.renderMode`
- validar permissões
- validar rotas
- validar bloco `backend`

### 4. Definir a estrutura técnica do frontend
- estrutura de pastas
- páginas iniciais
- componentes base previstos
- separação `ui / state / data / routes / bootstrap`

### 5. Definir os arquivos mínimos da fundação federada
- `main.tsx`
- `bootstrap.tsx`
- `App.tsx`
- `vite.config.ts`
- `package.json`
- `index.css`
- `delpi.manifest.json`

### 6. Definir os critérios de validação da etapa
- como saber que o plugin sobe isolado
- como saber que o portal consegue carregá-lo
- como saber que o manifesto está aderente ao contrato
- como saber que o entry público está correto

---

## Decisões consolidadas nesta etapa

### Identidade do plugin
- `id`: `strategic-indicators`
- `name`: `Strategic Indicators`
- `type`: `microfrontend`
- `basePath`: `/apps/strategic-indicators`
- `entry`: `/apps/strategic-indicators/assets/remoteEntry.js`
- `ui.renderMode`: `federated`

### Backend declarado no manifesto
- `serviceName`: `api-delpi`
- `baseUrl`: `/apps/api-delpi/strategic-indicators`
- `validateJwt`: `true`
- `issuer`: `https://www.minhadelpi.com.br/auth`
- `audience`: `delpi-central`

### Rotas previstas
- `/apps/strategic-indicators`
- `/apps/strategic-indicators/departments`
- `/apps/strategic-indicators/departments/:departmentId`
- `/apps/strategic-indicators/indicators`
- `/apps/strategic-indicators/trends`
- `/apps/strategic-indicators/alerts`
- `/apps/strategic-indicators/presentation`
- `/apps/strategic-indicators/settings`

### Permissões previstas
- `strategic-indicators.view`
- `strategic-indicators.departments.view`
- `strategic-indicators.indicators.view`
- `strategic-indicators.trends.view`
- `strategic-indicators.alerts.view`
- `strategic-indicators.presentation.view`
- `strategic-indicators.settings.manage`

---

## Estrutura técnica proposta do frontend

```text
plugins/strategic-indicators/
  src/
    ui/
      pages/
        ExecutiveDashboardPage.tsx
        DepartmentsPage.tsx
        DepartmentDetailsPage.tsx
        IndicatorsPage.tsx
        TrendsPage.tsx
        AlertsPage.tsx
        PresentationPage.tsx
        SettingsPage.tsx
      components/
        IgdHeroCard.tsx
        DepartmentCard.tsx
        DepartmentTable.tsx
        IndicatorTable.tsx
        TrendChart.tsx
        ContributionChart.tsx
        AlertList.tsx
        StatusBadge.tsx
        FilterBar.tsx
    state/
      hooks/
        useExecutiveDashboard.ts
        useDepartments.ts
        useDepartmentDetails.ts
        useIndicators.ts
        useTrends.ts
        useAlerts.ts
      store/
        strategicIndicatorsFiltersStore.ts
    data/
      api/
        strategicIndicatorsApi.ts
      adapters/
        executiveDashboardAdapter.ts
        departmentsAdapter.ts
        indicatorsAdapter.ts
      mappers/
        statusMapper.ts
        chartMapper.ts
    routes/
      index.tsx
    bootstrap/
      bootstrap.tsx
    App.tsx
    main.tsx
    index.css
  vite.config.ts
  package.json
  delpi.manifest.json
```

---

## Arquivos mínimos obrigatórios da fundação

### `main.tsx`
Responsável por importar o bootstrap dinamicamente.

### `bootstrap.tsx`
Responsável por expor `mount(el, props)` e `unmount(el)`.

### `App.tsx`
Responsável por renderizar a raiz do plugin.

### `vite.config.ts`
Responsável por configurar React, Federation, `filename: remoteEntry.js` e `base` do plugin.

### `package.json`
Responsável por dependências e scripts do plugin.

### `index.css`
Responsável por tokens locais e estilos base do módulo.

### `delpi.manifest.json`
Responsável pelo contrato de registro do plugin na plataforma.

---

## Critérios de validação da etapa

A etapa foi considerada correta porque:

- o plugin teve identidade técnica fechada
- o manifesto inicial ficou coerente com o contrato oficial
- as rotas foram definidas
- as permissões foram definidas
- a estrutura do projeto foi definida
- os arquivos mínimos obrigatórios da fundação foram criados
- o plugin foi publicado como microfrontend federado
- o portal conseguiu carregar o plugin em `/apps/strategic-indicators`

## Resultado validado em execução

### Evidência funcional
O plugin abriu corretamente dentro do portal em:

```text
/apps/strategic-indicators
```

### Resultado observado
A tela exibiu corretamente:
- marca MinhaDelpi
- título `Strategic Indicators`
- badge `Plugin em fundação`
- card `Microfrontend carregado com sucesso`

### Conclusão técnica
A fundação do microfrontend foi validada com sucesso, o que confirma que:
- o host conseguiu carregar o remote
- a integração federada está funcional
- o `remoteEntry.js` está utilizável pelo portal
- a estrutura mínima do plugin está correta

## Estado atual da infraestrutura

O usuário já preparou a infraestrutura Docker para incluir o serviço `strategic-indicators` no `docker-compose`, com:

- build em `../plugins/strategic-indicators`
- volume do plugin montado em `/app`
- serviço incluído no `gateway` via `depends_on`
- integração com a rede `delpi-network`

Também foram disponibilizados arquivos de referência do plugin `dashboard-lmps`, que servem como padrão funcional para a fundação federada:

- `vite.config.ts`
- `bootstrap.tsx`
- `App.tsx`
- `main.tsx`

---

## Encerramento oficial da etapa

A **Fase 1 — Fundação técnica do plugin Strategic Indicators** foi concluída com sucesso.

### O que foi entregue
- estrutura inicial do plugin criada
- dependências instaladas
- `vite.config.ts` configurado para Federation
- `main.tsx` criado
- `bootstrap.tsx` criado
- `App.tsx` criado
- `index.css` criado
- manifesto inicial definido
- serviço Docker do plugin preparado
- plugin carregando corretamente no portal

### Ajustes realizados durante a etapa
- correção do stack de dependências para compatibilidade com o host
- correção do Dockerfile para o padrão funcional
- correção do problema de runtime do microfrontend
- correção de tipagem local do TypeScript

### Próxima etapa do roadmap
A próxima etapa é:

**Fase 2 — Fundação visual e design system do módulo**

Objetivo da próxima etapa:
- transformar a fundação atual em layout real reutilizável
- criar shell visual do plugin
- criar componentes base
- preparar a tela para evoluir da fundação para a visão executiva

