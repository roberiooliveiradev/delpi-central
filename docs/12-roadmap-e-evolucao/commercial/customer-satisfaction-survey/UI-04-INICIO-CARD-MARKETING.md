# Ponto de entrada A — Card Marketing no Início do Portal

> **Estado:** ESPECIFICAÇÃO DE UI / WIREFRAME PROPOSTO — **NÃO IMPLEMENTADO**. Entrega 1. Ref observada: `main` / `c135a9823e054ce1234f73eee627548043737264` em 11/11/2026; confirmar HEAD/branch/working tree antes de implementar. Owner visual: `plugins/commercial` ou `plugins/public-hub` conforme indicado. Autoridade de regra e dados: `commercial-api`.
>
> **Fontes:** [índice mestre](./REQUIREMENTS-INDEX.md), [contrato da primeira entrega](./SURVEY-FIRST-RELEASE-CONTRACT.md), [plano de frontend](./FRONTEND-FIRST-RELEASE-PLAN.md) e plano Word integral; código existente: `plugins/commercial/src/features/home/HomePage.tsx`, `content/pluginRouteCatalog.ts`, `content/hubRouteIcons.tsx`.

**Regra visual obrigatória:** reaproveitar exclusivamente componentes de `@delpi/plugin-ui/index` e wrappers/compostos já usados no Portal, sem implementar novo componente visual nativo da página. Layout semântico e ligação de dados React são permitidos; se uma necessidade realmente não estiver coberta, registrar lacuna e passar pelo Abstraction Gate antes de alterar o PluginUI. Não criar CSS/kit de design paralelo.

## 1. Finalidade e decisão

A página **Início já existe** e mostra os cards Operação, Gestão à vista, Documentos, Ajuda e Administração. Acrescentar **um card Marketing** ao catálogo **Caminhos e funcionalidades**, seguindo o mesmo componente e mesmo grid; incluir **um link** “Pesquisa de satisfação do cliente” que abre diretamente os resultados. Não criar página “Painel Marketing”, novo MFE ou item fixo de topbar. O card permanece extensível a futuras capabilities, sem antecipar links sem implementação.

**Observação de acesso:** Marketing é nome da área, **não um filtro que exclui Comercial com `commercial.access`**. O link para resultados agregados pode aparecer a `commercial.access` e gestores; links exclusivos de configuração só aparecem a gestores na página de resultados/configuração, com autorização reforçada no backend.

## 2. Wireframe do card na grade existente

```text
┌─ Caminhos e funcionalidades ──────────────────────────────────────────┐
│ [Operação] [Gestão à vista] [Documentos] [Ajuda] [Administração]     │
│                                                                     │
│ ┌─ Marketing ────────────────────────────────────────────────────┐   │
│ │ [ícone existente] Marketing                                    │   │
│ │ Satisfação dos clientes e relacionamento.                      │   │
│ │ Pesquisa de satisfação do cliente                       ☆      │   │
│ └────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

A posição final é resolvida pelo **grid responsivo existente**; não definir CSS fixo para uma sexta coluna no desktop. Busca de caminhos, favoritos, últimos acessos e paleta de comandos devem continuar funcionando com a nova entrada.

## 3. Mapeamento de componentes e código

| Visual/ação | Componente existente / origem | Alteração esperada |
|---|---|---|
| Caixa “Caminhos e funcionalidades” | `SectionCard` do PluginUI; `HomePage.tsx` | Sem nova caixa |
| Card Marketing | `CommercialSectionRouteCard` → `createDashboardSectionRouteCard` do PluginUI | Acrescentar definição ao catálogo |
| Ícone/descrição | `SECTION_ICONS` em `HomePage.tsx`; `lucide-react` já usado nos outros cards | Adicionar mapping `marketing` usando ícone da coleção existente |
| Link e estrela/favoritos | `HubRouteDef`, `mapSectionRoutes`, `CommercialRecentAccessStrip`/favoritos existentes | Novo route id/capability e viewId |
| Busca | `CommercialCatalogSearchBar`, `collectSearchHits` | Termos: marketing, satisfação, pesquisa, cliente |
| Navegação | `navigatePluginView`, `pluginRoutes.ts` | Reutilizar roteador; destino Resultados |

**Arquivos concretos:** `src/content/pluginRouteCatalog.ts` (`HubSectionId`, `HUB_SECTIONS`, `HubCapability`), `src/features/home/HomePage.tsx` (`SECTION_ICONS` e capacidades), `src/app/pluginRoutes.ts` (view id), `src/content/hubRouteIcons.tsx`, testes de catálogo/favoritos/rotas. A nova capability de entrada deve ser derivada do RBAC oficial, **não** inferida somente do nome do card.

## 4. Estados e critérios de aceite

- Com `commercial.access`: card visível e link para resultados gerais, sem ação de configuração.
- Com `commercial.marketing` ou `commercial.manage`: link para resultados e, dentro da página, ação Configuração.
- Usuário sem acesso a indicadores não recebe link; favoritos previamente gravados não podem ser utilizados como autorização.
- Card funciona em grid responsivo, busca, favoritos, recents, Ctrl+K e navegação voltar.
- Nenhum texto de campanha, resposta, dado privado ou token é carregado no Início; é **somente navegação**.
- Reuso estrito de `CommercialSectionRouteCard`; nenhum componente visual novo. Testes estruturais/funcionais de permissões e roteamento.

## 5. Aprovação final do solicitante — composição do card (13/11/2026)

**APROVADO:** acrescentar somente **um card Marketing** na seção existente **Caminhos e funcionalidades** do Início, com título **Marketing**, descrição curta **Satisfação dos clientes e relacionamento** e **uma única entrada** **Pesquisa de satisfação do cliente** que navega à **UI-01 Resultados gerais**, sem pré-selecionar campanha. Manter os mesmos padrões de card do catálogo, ícone oficial, favoritos/estrela, grid responsivo, busca, acessos recentes, atalhos e navegação do Portal. **Não** criar página Painel Marketing, nova topbar, outro MFE, indicadores no card ou links adicionais não implementados.

**Acesso:** `commercial.access` pode acessar os resultados agregados; ações de gestão/configuração da campanha aparecem somente dentro das páginas autorizadas para `commercial.marketing` ou `commercial.manage`, sob verificação efetiva da API. Card é entrada de navegação, jamais prova de autorização.

**Design e implementação:** `CommercialSectionRouteCard`/`createDashboardSectionRouteCard` e grid oficial. Posição final, tamanhos, colunas, fonte, padding, margens, gap e breakpoints vêm do PluginUI e CSS real; **TO_INVENTORY** dos valores e seletores específicos, sem fixar dimensão arbitrária nem criar CSS paralelo. Verificar comportamento desktop/tablet/celular, favoritos, busca e acesso por teclado. **Status:** composição visual **APROVADA**, implementação e testes **PENDING**.
