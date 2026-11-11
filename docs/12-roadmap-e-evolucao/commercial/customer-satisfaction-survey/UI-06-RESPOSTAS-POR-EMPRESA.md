# UI-06 — Respostas por Empresa (consulta privada)

> **Estado:** decisões de UX **aprovadas visualmente em 11/11/2026**, **NÃO IMPLEMENTADO**. Separação da UI-01 e identidade visual com avatar aprovadas. Auditoria UI-07/G02 (11/11/2026, HEAD `0cde0f674bd31e494f6af3f9f688d908f24f5542`): **contrato de rota fechado** (spec); páginas/rotas ainda ausentes no código. Fonte de `hasAvatar` na projeção de respostas permanece **TO_INVENTORY** até o endpoint R12.
>
> **Owner visual:** `plugins/commercial`. **Autoridade de dados e permissão:** `commercial-api`. Origem de empresa e imagem existente: integrações oficiais do Portal/TOTVS, sem duplicar cadastro.

## 1. Escopo e navegação — decisão aprovada

Página **somente de consulta**, separada da UI-01 de [Resultados](./UI-01-RESULTADOS-PESQUISA.md) e da UI-02 de [Configuração](./UI-02-CONFIGURACAO-PESQUISAS.md). Lista empresas **respondentes e pendentes** da campanha selecionada. Resposta enviada é definitiva e consultada somente na **página própria UI-07 — Detalhes da Resposta**, sem modal nem drawer. **Não** adicionar participante, criar campanha, alterar contato, editar resposta, copiar/reenviar link ou disparar convite nesta UI; estas operações pertencem à Configuração, quando autorizadas.

**Uma única topbar principal**, sem barra duplicada nem nova área de navegação. Ações contextuais no `CommercialPageHero`: **Ver resultados**, **Configuração** e **Atualizar** (com autorização); filtros de campanha, situação, grupo e busca por cliente **dentro do mesmo Hero**, conforme fonte e permissão. `CommercialPagePath` mostra a trilha. Entradas: botão **Respostas por empresa** no Hero da UI-01, e ligação contextual da UI-02 que pode preservar a campanha escolhida.

**Contrato de rota (G02 — `CLOSED_SPEC`, não implementado):** lista em `/apps/commercial/satisfaction-survey-responses` com query `campaign_id`/`status`/`group`/`q`/`page`/`sort`/`dir`; **Ver resposta** navega para `/apps/commercial/satisfaction-survey-responses/:responseId` com `returnTo`+`returnLabel` via `commercialNavigationReturn.ts`. Detalhe e owners: [UI-07 §1.1](./UI-07-DETALHES-RESPOSTA.md#11-contrato-de-rota-e-navegação-g02--closed_spec-não-implementado).

Usuários com somente `commercial.access` não acessam esta página nem os endpoints identificados. Para consulta privada, exigir `commercial.marketing` ou `commercial.manage` efetivamente validados no backend. A simples ocultação dos botões não substitui autorização.

## 2. Identidade de empresa — padrão aprovado do Portal

**Reutilizar `CustomerAvatar` existente**, sem recriar componente, CSS de avatar ou segunda fonte de imagens:

- **Arquivo:** `plugins/commercial/src/features/customers/components/CustomerAvatar.tsx`.
- **Origem visual:** `createInitialsAvatar("cm")` de `@delpi/plugin-ui/index`; o componente controla busca de blob pela API de enriquecimento do cliente, com `AbortController` e limpeza de URL de objeto.
- **Props confirmadas:** `code`, `store`, `name`, `hasAvatar?`, `size?: "sm" | "md" | "lg"`, `refreshKey?`, `previewable?`; quando é link, `href`, `title`, `onNavigate?`.
- **Identidade canônica:** `customer_code` **e** `customer_store` (não usar nome isolado, nem assumir loja `01` para identidade desconhecida).
- **Imagem:** só requisitar se `hasAvatar` vier de fonte oficial autorizada. **TO_INVENTORY:** se a projeção de participantes/respostas disponibiliza `hasAvatar` e nome oficial ou se exige leitura de enriquecimento já existente. Quando sem imagem/metadado, **iniciais** da mesma implementação; não inventar flag nem persistir imagem na pesquisa.
- **Coluna Cliente (tabela):** avatar **`size="sm"`**, razão/nome oficial e código/loja no padrão já usado em `CustomersTable.tsx` e `OtdCustomerIdentityCell.tsx`. No celular, mesma identidade no cabeçalho do card, não um avatar alternativo.
- **Interações separadas:** avatar e nome levam à **Conta do Cliente** com `buildCustomerDetailHref` / navegação oficial e retorno contextual quando suportado; **“Ver resposta”** navega à **página UI-07** da resposta daquela empresa/campanha, sem navegar à conta. Link de avatar não deve abrir preview/lightbox quando for navegação; verificar `href`/destino autorizado. Cliente pendente não tem ação ativa de abrir resposta.

## 3. Estrutura funcional (visual em revisão)

```text
TOPBAR PRINCIPAL DO PORTAL (EXISTENTE, INALTERADA)
  Comercial / Marketing / Pesquisa / Respostas por empresa  [CommercialPagePath]

COMMERCIAL PAGE HERO COMPACTO
  Respostas por empresa                     [Ver resultados] [Configuração] [Atualizar]
  [Campanha v] [Situação: Todas/Respondidas/Pendentes v] [Grupo v]
  [Pesquisar por código, loja ou empresa]

EMPRESAS PARTICIPANTES — lista oficial
  Cliente [avatar | nome | código/loja] | Situação | Data resposta | Ver resposta
  [avatar] Empresa Alpha 001245/01       Respondida   10/12/2026    [Ver resposta]
  [avatar] Empresa Beta  002318/01       Pendente     —             —
  [avatar] Empresa Gama  003570/02       Respondida   11/12/2026    [Ver resposta]

AO ACIONAR VER RESPOSTA:
  Página completa UI-07 — Empresa / Campanha / data (não modal/drawer)
  Satisfação geral 1–5; recomendação 0–10; as 10 dimensões (1–5 ou N/A);
  três respostas abertas opcionais; somente leitura.
```

**Valores/nomes/datas ilustrativos.** Não chamar nota individual de `IGS` ou `NPS`: estes são indicadores agregados da pesquisa. Situação “Pendente” indica **sem resposta definitiva**, não comprova envio, leitura do convite ou atraso do cliente.

## 4. Mapa de componentes oficiais

| Região | Componente/padrão já existente | Observação |
|---|---|---|
| Trilha | `CommercialPagePath` | Não duplicar topbar |
| Hero, ações, filtros | `CommercialPageHero`, `CommercialActionButton`, `CommercialSelectField`, `CommercialTextField` | Ações e filtros globais pertencem ao Hero |
| Lista/tabela | `CommercialDataTable` e `DataTableColumn<T>` | Uma fonte de linhas por campanha; identidade cliente com avatar real |
| Status | `CommercialStatusBadge` | Respondida ou Pendente, conforme resposta definitiva |
| Avatar | **`CustomerAvatar`** | Componente real em `features/customers/components`; não duplicar imagem |
| Link da conta | `CommercialEntityLink`, `buildCustomerDetailHref` | Mesmo padrão de Minha Carteira/OTD |
| Mobile | `CommercialDataCardsGrid` / `CommercialInteractiveDataCard` ou modo oficial de `DataTableSection` | **PENDING:** conferir melhor integração e props reais, sem CSS paralelo |
| Detalhes da resposta | [UI-07 — página própria](./UI-07-DETALHES-RESPOSTA.md), `CommercialPageHero`, `CommercialDetailCard`, `CommercialDetailFieldGrid` | Somente leitura, navegação própria, sem drawer |
| Estados | `CommercialLoadingCard`, `CommercialEmptyState`, `CommercialStateBanner` | Sem dados ≠ erro ≠ sem permissão |

## 5. Responsividade e critérios de aceite da identidade

**Desktop:** avatar pequeno à esquerda do nome e do código/loja dentro da coluna Cliente; ação “Ver resposta” em coluna própria. **Tablet:** preservar a identidade visível e reorganizar colunas conforme largura. **Celular:** um card por empresa com `CustomerAvatar`, nome, código/loja, situação e ação separada. Somente o clique no avatar/nome navega para a Conta; a ação “Ver resposta” navega para a página UI-07. Em todos os tamanhos, se a empresa não tiver imagem, exibir iniciais do kit sem salto de layout.

Aceite: (1) avatar, nome e identidade reproduzem o padrão de `CustomersTable`/`CustomerListCard`/`OtdCustomerIdentityCell`; (2) nenhum avatar customizado; (3) com `hasAvatar=false` ou metadado indisponível, iniciais; (4) imagem só carregada se informada e autorizada; (5) código+loja preservados; (6) navegação para Conta separada da ação de resposta; (7) pendente sem página de resposta; (8) sem writes na página; (9) backend nega leitura individual ao perfil somente `commercial.access`; (10) testes de desktop/tablet/mobile, foco/teclado, zoom, regressão e autorização.

**Visual aprovado:** na UI-07, cinco pontos preenchidos/neutros para cada nota de dimensão, via `RatingDots` **CANDIDATO** do PluginUI, condicionado a Abstraction Gate; ver [UI-07](./UI-07-DETALHES-RESPOSTA.md).

**Status real:** aprovação de especificação, não prova de código da nova página, rota, integração de avatar ou API. Antes de implementar: revalidar HEAD, branch e working tree, inspecionar consumidor e fonte de `hasAvatar`, conferir contratos de permissão e teste, fazer menor diff e verificar resultado.
