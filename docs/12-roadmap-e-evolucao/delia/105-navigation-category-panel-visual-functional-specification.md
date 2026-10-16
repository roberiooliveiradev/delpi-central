# 105 — DÉLIA | NavigationCategoryPanel — Painel expansível

**Data:** 2026-10-16  
**Status:** `PRODUCT_UX_SPEC / PLANNED / NOT_IMPLEMENTED`. **Documentação somente**: sem frontend, backend, dados mock de produção, deploy, mudança de fase ou aceite.  
**Produto:** DÉLIA standalone. `plugin-ui` é owner de apresentação compartilhada; `plugins/delia` compõe o produto e seu estado. O Portal continua host/navegação global; Core resolve autorização; APIs de domínio são autoridade final; MCP/A2A não conferem permissão.  
**Reancoragem obrigatória antes de executar:** HEAD/git status e .cursor/Project Instructions → 16 → 50 → 17 → 49 → 51 → 52 → 21 → 20 → 25 → arquitetura técnica → product spec → documentos temáticos → ledger; evidência conflitante exige `EXECUTION_DRIFT` ou `ARCHITECTURE_DECISION_REQUIRED`.  
**Base verificada nesta documentação:** GitHub `main` `e7159c86756ba05f885cf0ccdbfe6fb2faecb54b`. Não presumir que será o HEAD de implementação.  
**Gates universais:** `read != write`, `draft != send`, `PREPARE != ACT`, `discovery != approval`, `model output != FACT`, `JWT != live AuthZ`; layout não concede authority.  

**Master:** [103](./103-delia-navigation-sidebar-master-product-ux-specification.md).

## Objetivo e composição

Painel adjacente ao rail que apresenta **apenas a categoria selecionada**, com cabeçalho, ações válidas, lista e rodapé contextual. Não é uma página independente, nem modal permanente nem segundo host. Trocar o conteúdo não deve destruir o `ConversationWorkspace`.

```text
┌───────────────────────────┐
│ Conversas            [‹]  │
│ [+ Nova conversa]          │
│ [⌕ Pesquisar]              │
│ ───────────────────────── │
│ Fixadas                   │
│ Recentes                  │
│ Anteriores                │
│                           │
│ [Opções autorizadas]      │
└───────────────────────────┘
```

## Design

Largura candidata 248–288px desktop, altura do container host, `min-height:0`; cabeçalho fixo ~52–60px, rolagem só no corpo, rodapé alinhado à base se houver ação contextual. Padding 16–20px, space rhythm 8px, borda hairline; não criar recorte escuro/cinza como cartão secundário. Header com label curto, ação de recolher ghost à direita, somente **um** toggle compartilhado com rail (visual migratório quando abre/fecha, nunca duplicado). Tipografia pequena/moderada, ícones 16–18px.

## Estados

`closed`: largura zero e rail íntegro, sem conteúdo tabulável escondido; `open`: conteúdo carregado quando legitimamente disponível; `loading`: skeleton após fetch real, respeitar tamanho; `empty`: resultado de consulta real, sem placeholder histórico inventado; `unavailable`: copy curta quando falta contrato; `forbidden`: não renderizar metadata; `error`: erro tipado + retry contratado; `overlay`: painel sobre conversa em compact com backdrop e focus management.

## Interações

Categoria ativa determina título/renderer e eventuais ações. Seleção troca apenas apresentação; não revoga decisões nem reseta draft. Expandir não aciona API. Ao fechar, foco volta ao rail selecionado/toggle; ao selecionar outra categoria, preservar posição de scroll por categoria opcional **em estado transitório** (não usar storage ad hoc). Listas longas podem paginar/virtualizar após contrato real. Não esconder item ativo atrás de cabeçalho sticky. Empty states por categoria específicos, curtos e sem prometer capacidade.

## Responsividade

Amplo: rail + painel ocupam largura e o centro preserva sua largura útil. Médio: painel pode sobrepor centro sem remount; mobile/Companion Dock: drawer apenas quando aberto, rail entrypoint reduzido/oculto se necessário. A largura que ativa overlay será validada pela dimensão real do host. Nunca criar `width:100vw` ou `height:100vh` dentro do Portal.

## Ownership/contratos

O kit `plugin-ui` apresenta shell, heading, loading, no-results e callback; a DÉLIA seleciona categoria e fornece projeções autorizadas. `EXISTING_EQUIVALENT=YES` para sidebar/shell e primitives; `REUSE_DECISION=EXTEND`, `TO_INVENTORY` para drawer/resizer. Se há contrato de lista real, exibir; se não há, renderizar unavailable e nunca gerar objeto fake.

## Critérios transversais de qualidade

- **Design system:** usar tokens, typografia, `IconButton`, feedback e superfícies do `plugin-ui`; ícones Lucide, sem cores hardcoded como identidade; no claro e escuro, ícone ghost transparente em repouso, hover tonal, foco visível, estados pressed/selected distinguíveis.
- **Responsividade:** medir container do Portal, não assumir viewport global. Cobrir página ≥1440, 1280, 1024, 768, 420, 375, 320px, zoom 200%, além do Companion Dock; não renderizar lista legível em rail estreito.
- **Movimento:** transição curta 180–240ms conforme tokens existentes; `prefers-reduced-motion` instantâneo; nunca remount do `ConversationWorkspace` nem perda de draft ao selecionar categoria.
- **Acessibilidade:** landmarks únicos, labels de ícones e hints por teclado, `aria-current` para navegação, `aria-expanded`/`aria-controls` para expansão, ordem de Tab previsível, Escape apenas em overlays, restauração de foco, contraste e screen reader.
- **Sem falso runtime:** nada de nomes de conversas, projetos, agentes, plugins, datas, métricas ou permissão inferidos. Loading só com requisição real; vazio = resultado autorizado real, indisponível = contrato inexistente, proibido = sem revelação de recursos.
- **Segurança:** nenhum item visual executa domínio, MCP, ferramenta, automação ou write por clique sem fluxo autorizado. Dados externos são não confiáveis; labels/snippets renderizados como texto inerte.
- **Validação:** testes de props/callbacks/estados e negativos de AuthZ, QA page/dock light/dark, check de exports/federação, prova de generalização em cenários de navegação e revisão independente no SHA executado. `TEST_NOT_RUN` não equivale a PASS.


