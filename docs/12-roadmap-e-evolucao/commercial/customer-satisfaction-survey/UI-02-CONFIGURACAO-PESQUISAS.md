# Página 02 — Configuração de Pesquisas e Campanhas

> **Estado:** ESPECIFICAÇÃO DE UI / WIREFRAME PROPOSTO — **NÃO IMPLEMENTADO**. Entrega 1. Ref observada: `main` / `c135a9823e054ce1234f73eee627548043737264` em 11/11/2026; confirmar HEAD/branch/working tree antes de implementar. Owner visual: `plugins/commercial` ou `plugins/public-hub` conforme indicado. Autoridade de regra e dados: `commercial-api`.
>
> **Fontes:** [índice mestre](./REQUIREMENTS-INDEX.md), [contrato da primeira entrega](./SURVEY-FIRST-RELEASE-CONTRACT.md), [plano de frontend](./FRONTEND-FIRST-RELEASE-PLAN.md) e plano Word integral; código existente: \`plugins/commercial/src/features/home/HomePage.tsx\`, \`features/administration/AdministrationHomePage.tsx\`, \`features/analytics/AnalyticsOtdPage.tsx\`.

**Regra visual obrigatória:** reaproveitar exclusivamente componentes de `@delpi/plugin-ui/index` e wrappers/compostos já usados no Portal, sem implementar novo componente visual nativo da página. Layout semântico e ligação de dados React são permitidos; se uma necessidade realmente não estiver coberta, registrar lacuna e passar pelo Abstraction Gate antes de alterar o PluginUI. Não criar CSS/kit de design paralelo.

## 1. Objetivo e navegação

Criar campanhas e selecionar clientes existentes no TOTVS para que o usuário possa **copiar e enviar manualmente** convites; acompanhar pendentes/respondidos e consultar respostas individuais autorizadas. A página é interna ao MFE, exclusivamente para `commercial.marketing` OU `commercial.manage`. `commercial.access` não deve ver operações de gestão.

**Rotas de UI previstas:** `/apps/commercial/satisfaction-surveys` (lista/configuração) e `/apps/commercial/satisfaction-surveys/{campaignId}` (detalhe como continuação da mesma área). Entrada por ação/aba Configuração da página de resultados, não outro MFE; a gestão pode voltar a Resultados sem perder contexto básico.

## 2. Wireframe A — lista e criação

```text
┌───────────────────────────────────────────────────────────────────────────┐
│ Marketing / Pesquisa de satisfação                                        │
│ Configuração das pesquisas                             [Ver resultados]   │
├───────────────────────────────────────────────────────────────────────────┤
│ CAMPANHAS                                                    [+ Nova]     │
│ [Pesquisar campanha] [Situação: todas ▼] [Ano ▼] [Limpar]                 │
│                                                                           │
│ Nome / período           Situação       Participantes  Respostas   Ação   │
│ Satisfação 2026/2        Aberta         100            72          Abrir  │
│ Satisfação 2026/1        Encerrada       90            70          Abrir  │
│ Satisfação 2025/2        Encerrada       80            74          Abrir  │
│                                               [Página 1 de N]             │
└───────────────────────────────────────────────────────────────────────────┘
                                     │
                         clique [+ Nova campanha]
                                     ▼
                  ┌─ Dialog oficial do PluginUI ─────────┐
                  │ Nome da campanha                     │
                  │ [________________________]           │
                  │ Início [data/hora]   Fim [data/hora]  │
                  │ Questionário oficial fixo (15)       │
                  │ [Cancelar]               [Criar]     │
                  └──────────────────────────────────────┘
```

Números das linhas **ilustrativos**; não codificar no frontend. Situação vem do backend, derivada da janela. “Participantes” significa cadastrados na campanha, não convites efetivamente enviados; o sistema não comprova contato.

## 3. Wireframe B — detalhe de campanha

```text
┌───────────────────────────────────────────────────────────────────────────┐
│ Marketing / Configuração / Satisfação 2026/2                             │
│ Satisfação 2026/2 · [Aberta]      [Editar datas]*  [Ver resultados]       │
│ Janela: DD/MM/AAAA a DD/MM/AAAA                                          │
├───────────────────────────────────────────────────────────────────────────┤
│ [Participantes]   [Respostas]                                             │
├───────────────────────────────────────────────────────────────────────────┤
│ PARTICIPANTES         cadastrados: 100  respondidos: 72   pendentes: 28  │
│ [Buscar cliente TOTVS (código, nome)]        [Adicionar à campanha]      │
│ [Buscar na lista] [Pendente / Respondido ▼]                              │
│                                                                           │
│ Cliente (código+loja)       Contato/e-mail     Respondeu    Ações         │
│ Empresa A — 001/01         contato opcional   Pendente    [Copiar link]  │
│ Empresa B — 002/01         contato opcional   Respondido  [Copiar link]  │
│                                                      [Copiar mensagem]  │
├───────────────────────────────────────────────────────────────────────────┤
│ RESPOSTAS (somente gestão)                                                 │
│ [Empresa ▼] [Tabela: satisfação geral, NPS, data] [Abrir leitura]         │
└───────────────────────────────────────────────────────────────────────────┘

*Editar datas apenas segundo regras do backend, sem invalidar respostas.
```

## 4. Mapa real de componentes

| Região/ação | Componente existente | Arquivo/padrão |
|---|---|---|
| Hero, breadcrumbs e voltar | `CommercialPageHero`, `CommercialPagePath`, `CommercialActionButton` | `commercialUi.ts` |
| Seção de campanhas e participantes | `SectionCard`/`CommercialSectionCard` | PluginUI/Portal Comercial |
| Seções do detalhe | `CommercialUnderlineNav` | Wrapper PluginUI no Comercial |
| Tabela de campanhas, participantes e respostas | `CommercialDataTable`, `CommercialPagination` | `commercialUi.ts`, exemplo `AnalyticsOtdPage.tsx` |
| Busca de cliente/campanha | `CommercialTextField`, `CommercialFilterBarShell` | `commercialUi.ts` |
| Data e filtros | `CommercialDateField`, `CommercialSelectField`, `CommercialMultiSelectField` | `commercialUi.ts` |
| Nome/contato/e-mail ajustável | `CommercialTextField`, `CommercialDetailFieldGrid` | `commercialUi.ts` |
| Criar/editar campanha | `CommercialHostDialog`, `CommercialActionButton` | Modal host-contained do PluginUI |
| Leitura da resposta | `CommercialHostDrawer` + `CommercialDetailCard` | Painel oficial, sem editor |
| Status | `CommercialStatusBadge` | Wrapper PluginUI; não usar status `enviado` |
| Cópia link/mensagem | `CommercialActionButton` + API nativa de clipboard como comportamento | Visual 100% kit; sem botão HTML estilizado custom |
| Feedback | `CommercialStateBanner`, `CommercialLoadingCard`, `EmptyState` | Portal Comercial |

**Não reutilizar** componentes de `commercial.tasks` como mecanismo para a pesquisa nesta entrega. Na entrega 2 serão avaliados somente se respeitarem isolamento e ownership; o plano de ação continua obrigatório no produto completo.

## 5. Estados, validações e regras de interação

### Criar campanha
- Nome, início e fim; formulário oficial com perguntas **fixas e não editáveis**.
- Erro de datas, conflito e falha de rede aparecem no diálogo sem gerar campanha local falsa; fechar/navegar somente após sucesso de persistência.
- `Agendada`, `Aberta`, `Encerrada` são estados derivados no backend; não deixar o usuário mudar uma flag manual de “ativa”.
- Edição de datas deve respeitar imutabilidade das respostas e validações do backend.

### Selecionar participante
- Busca usa `commercial-api` (BFF já existente) e a fonte TOTVS; seleção conserva `customer_code+customer_store`, inclusive códigos com zeros iniciais.
- Ao incluir duplicado, carregar participante já existente e **preservar o mesmo token**; nunca gerar link no browser.
- O e-mail/contato copiado do ERP é informação auxiliar ajustável só neste convite; não editar cadastro TOTVS nem exigir e-mail para copiar link.

### Copiar convite
- **Copiar link** solicita ao backend o mesmo URL estável e copia; **Copiar mensagem** usa o URL e um texto curto aprovado, sem disparar nada.
- Toast/estado de sucesso só após confirmação da cópia; falha de clipboard oferece seleção/cópia manual. Não incluir `Enviar e-mail`, `Reenviar`, `WhatsApp direto`, `Entregue`, `Enviado`, disparo em lote ou contador de tentativas.
- Recópia não indica que houve contato com o cliente; mostrar **Pendente/Respondido** com base na submissão.

### Consultar respostas
- Resposta individual é somente leitura; notas, NPS, 10 dimensões e até três comentários, data e vínculo empresa. Nada de `Editar`, `Excluir` ou “Responder em nome do cliente”.
- Nenhuma página ou componente público recebe dados de outros participantes.

## 6. APIs, permissões e fluxo

| Interação | REST planejado | Requer |
|---|---|---|
| Listar/criar/abrir/editar campanha | `GET/POST /satisfaction-surveys/campaigns`, `GET/PATCH /satisfaction-surveys/campaigns/{id}` | Gestão |
| Busca cliente | `GET /customers/search` existente; via BFF | Autorização da operação e validação no backend |
| Listar/adicionar participantes | `GET/POST /satisfaction-surveys/campaigns/{id}/recipients` | Gestão |
| Ajustar contato | `PATCH /satisfaction-surveys/campaigns/{id}/recipients/{recipientId}` | Gestão |
| Copiar mesmo link | `GET /satisfaction-surveys/campaigns/{id}/recipients/{recipientId}/link` | Gestão; resposta sensível |
| Listar/detalhar respostas | `GET /satisfaction-surveys/campaigns/{id}/responses`, `GET /satisfaction-surveys/responses/{id}` | Gestão |
| Enviar e-mail | **INEXISTENTE nesta experiência** | Usuário usa seu canal fora do Portal |

`commercial.marketing` será registrado durante implementação, junto com RBAC do frontend/host, backend e CAIO. **Não** inventar `commercial.survey.write` ou outros códigos.

## 7. Responsividade, testes e critérios de aceite

- Desktop: tabela com paginação e colunas essenciais; tablet/mobile: filtros reorganizados com kit e tabela rolável/adaptativa do PluginUI; ações acessíveis pelo teclado e rótulos claros.
- Estado vazio inicial oferece `Nova campanha`, sem dados fictícios; acesso negado tem mensagem específica; falha de consulta não se apresenta como `0 participantes`.
- O link não aparece em logs, navegação indevida ou analytics; Clipboard é ação explícita.
- Testar via UI e backend: criação, datas, duplicidade, edição controlada, pares TOTVS, link estável, cópia sem envio, pendência, restrição de acesso, leitura imutável e responsividade.
- Testar `read`/`execute` no CAIO com os mesmos casos de uso e limites de autorização; teste REST/CAIO na **mesma etapa**. Conferir HEAD, arquivos, mudanças, residual search, outcome e gaps em execution report.

**Entrega 2:** classificação e plano de ação **não aparecem agora**, mas estão previstos e obrigatórios segundo o [Word/índice](./REQUIREMENTS-INDEX.md). Não antecipar telas de ações nesta página enquanto a pesquisa não estiver entregue.