# Fornecedores — Proposta visual v1: consulta, criação, edição e revisão

**Status:** `TARGET / PLANNED` — especificação visual aprovada pelo PO em 2026-10-21 para posterior implementação; **não é código implementado nem GATE-FEATURE fechado**. Origem: captura do detalhe atual `/apps/supplies/suppliers/002469/01`, análise de UX e quatro wireframes conceptuais exibidos na conversa. O desenho visual é referência de composição; **tokens reais, kit e contratos no HEAD prevalecem**. A imagem conceitual, gerada durante a conversa, não é asset versionado neste PR; os layouts abaixo são a representação canônica textual rastreável no GitHub.

## Objetivo e âmbito

Refatorar **visualmente** os fluxos de fornecedores do MFE `plugins/supplies`: consulta, CREATE, UPDATE e revisão de alterações, reutilizando o mesmo padrão de seções e grid responsivo. A captura existente mostrou inputs de largura fixa concentrados à esquerda, áreas vazias à direita, empilhamento vertical excessivo e pouca distinção entre valores imutáveis e editáveis. Prioridade: leitura rápida, eficiência de preenchimento, revisão segura e paridade dark/light/mobile.

**Não mudar nesta entrega de especificação:** endpoint REST `:8701` → `DELPI_TST01` para homologação, contratos ou AuthZ, validação/semântica de campos, regras Protheus, persistência, tracking, código ou feature gates. Nenhuma autorização de implementar ou implantar decorre desta documentação. A implementação precisa de GO específico, inventory do HEAD e gate aplicável.

## Princípios obrigatórios

- **Kit first:** inventariar e reutilizar `@delpi/plugin-ui` (PagePath/PageHero, cards, fields, inputs, selects, badges, dialogs, buttons, tooltip, skeleton etc. **somente se existirem no HEAD**). Evitar inventar componentes compartilhados/duplicados; abstrações locais somente quando justificadas.
- MFE `plugins/supplies` somente UX e composição; `supplies-api` permanece BFF; sem acesso direto a `api-delpi`.
- CSS estritamente sob `.dashboard-supplies-portal`; não copiar CSS do legado `plugins/dashboard-supplies`; respeitar tema escuro/claro, tokens do kit, tipografia e foco.
- Todos os labels/textos em PT-BR; identificadores/componentes de código em inglês.
- Identidade Keycloak; effective permissions e escopos resolvidos no Core/backend, autorização fail-closed. UI pode ocultar ou desabilitar, **nunca** decidir permissão final. Não criar permission por botão.
- Código/loja/documento fiscal: na edição são **protegidos**, sem input disfarçado de editável; criação obedece ao contrato vigente (não presumir que `supplier_store` é sempre gerado ou sempre editável: F4.4 enviou `01`).
- Nunca marcar sucesso de persistência só porque upstream devolveu HTTP 200; exibir ACK versus confirmação conforme contrato de tracking.
- Tooltip de ajuda no texto semântico da label/título, sem ícone "(?)" redundante; acessível por hover/focus. Help sincronizada se user-facing.
- Não inferir required a partir da planilha: Gabriel informou 18 mapeamentos, mas a obrigatoriedade condicional MATA020 segue por campo.

## 1. Layout comum — desktop / tablet / mobile

**Desktop:** container fluid com max-width do padrão shell (não fixar em pixel sem inventariar kit); grid lógico 12 colunas. Gap e padding pelos tokens. Cards/seções verticalmente empilhados, cada um contendo linhas multidimensionais. Seções não se estendem em altura artificial só para ocupar a largura.

**Tablet:** 2 colunas por linha como padrão; campos de endereço e nome podem ocupar a linha. **Mobile ≤768px:** 1 coluna, ordem DOM = visual, nenhuma rolagem horizontal para inputs; barras de ação não encobrem campos nem teclado virtual. Não ocultar campos críticos em accordions por padrão.

Representação esquemática:

```text
┌ Breadcrumb: Fornecedores > 002469/01 > [Editar] ──────────────────────────┐
│ HERO: [ícone] RODRIGUES KANNENBERG        [ações contextuais]            │
│ Ficha · 002469/01   [Bloqueado] [CNPJ mascarado/formato] [Jurídica]       │
├ Identificação ──────────────────────────────────────────────────────────┤
│ Código (2/12) │ Loja (2/12) │ CNPJ/CPF (4/12) │ Tipo pessoa (4/12)       │
│ Razão social (6/12)                 │ Nome fantasia (6/12)              │
├ Endereço ───────────────────────────────────────────────────────────────┤
│ Endereço (6/12)              │ Bairro (3/12) │ CEP (3/12)               │
│ Cidade (4/12) │ Cód. município (2/12) │ UF (2/12) │ País (4/12)         │
├ Contato ────────────────────────────────────────────────────────────────┤
│ Nome de contato (4/12) │ DDD (2/12) │ Telefone (3/12) │ E-mail (3/12)    │
├ Fiscal e administrativo ────────────────────────────────────────────────┤
│ Inscrição estadual (4/12) │ Municipal (4/12) │ ROHS (4/12)             │
│ Código do país* │ País BACEN* │ Condição pgto │ Forma pgto              │
├ Compras e financeiro ───────────────────────────────────────────────────┤
│ Natureza financeira (4/12) │ Conta contábil (4/12) │ extensões se reais│
└ Barra de ações só no modo CREATE/EDIT ──────────────────────────────────┘
```

\* Código do país / país BACEN: **não duplicar o mesmo dado como dois controles mutáveis** sem comprovação de que são conceitos distintos no contrato. O mockup visual mostrava ambos por composição; inventariar o shape real e consolidar em um campo `bacen_country_code` se forem aliases. Similarmente, "complemento", inscrição municipal, ROHS e forma de pagamento só aparecem quando suportados pelo contrato atual; não criar novos campos por causa do mockup.

## 2. Tela CONSULTA — read-only profile

- Breadcrumb: `Fornecedores / 002469/01`; título é a razão social, subtítulo `Ficha do fornecedor · código/loja`.
- Chips informacionais: bloqueio, documento formatado (respeitar minimização), tipo pessoa. Status contextual, não decorativo.
- Ações: `Editar cadastro` somente se usuário puder solicitar o fluxo; `Atualizar dados` = refetch GET (não update/write automático); menu de overflow apenas para ações já existentes e permitidas.
- Dados representados com `DisplayField` **como padrão visual/composição**, sem inputs desabilitados em série. Label curta + valor escaneável; `—` para indisponível, não confundir com valor vazio gravado.
- Cards por agrupamento: Identificação, Endereço, Contato, Fiscal/Administrativo, Compras/Financeiro.
- Histórico/tracking somente se rota e contrato existentes e autorizados; não inventar painel adicional nesta fatia.
- Limitação técnica: REST GET fornecedor pode retornar apenas subconjunto cadastral; renderizar estados `indisponível` corretamente, **nunca preencher com exemplo de wireframe**.
- A captura usada para diagnóstico era de um fornecedor real; o exemplo no wireframe é ilustrativo e nunca seed de dados.

## 3. Tela EDIÇÃO — mesma composição, comportamento seguro

- Rota existente e acesso URL/F5 preservados; inventariar rota real antes de qualquer refactor.
- Header conserva identidade/status; aviso curto: `Você está editando dados cadastrais. Código, loja e CNPJ/CPF são protegidos.`.
- Primeira linha: Código/Loja/CNPJ/CPF protegidos como display estático com cadeado discreto somente se acessível; tipo pessoa protegido/editável **conforme allowlist real**, não pelo mockup.
- Demais campos: inputs/selects/masks kit-first; labels sempre acima, campos relacionados na mesma linha em desktop.
- Campos alterados: destaque sutil e acessível, sem depender apenas de cor; contador `N alterações pendentes`. Comparação com baseline normalizada sem mascarar mudanças semânticas.
- Diff-only: PUT deve enviar **só campos alterados permitidos**, preservar omitidos, recusar clears null/empty quando contrato não suporta; sem read-modify-write.
- Sticky action bar dentro do fluxo (quando viável e sem encobrir conteúdo): `Cancelar` / `Revisar alterações` / `Salvar`. Não duplicar submit concorrente; revisão pode ser etapa obrigatória conforme contrato existente. Sem alterações: ações de save/revisão desabilitadas com explicação; ao sair com alterações, confirmação de descarte.
- Sucesso e tracking: feedback `Enviado` ≠ `Confirmado`; mostrar `Em reconciliação` / `Falha` quando aplicável, sem afirmar persistência antes da evidência.

## 4. Tela CRIAÇÃO — mesmo grid / componentes

- Header `Novo fornecedor`, texto de apoio curto. Não mostrar chips de status fictícios.
- Código do fornecedor: output do ERP, não input livre quando `SYSTEM_GENERATED`; Loja deve seguir contrato executável vigente (na F4.4 `supplier_store=01`, portanto não rotular como sempre gerada).
- CNPJ/CPF com máscara e validação declarada na camada correta (DV em backend antes do POST é recomendação de outra fatia, não implementação implicada pela UX).
- Indicadores requeridos (*) apenas para campos cuja regra de required foi comprovada. Mensagens de erro por campo e sumário acessível.
- Campos dependentes (país/estado/município/natureza/condição/conta) usam seletores/search quando providers/rotas realmente existem; não inventar busca, fonte ou auto-preenchimento.
- CTA `Revisar dados` / `Incluir fornecedor` com prevenção de duplo clique e loading; nenhum retry silencioso de POST após timeout, 5xx ou UNKNOWN.
- Registro de operação e resultado server-side quando disponível; confirmação honesta se POST foi ACK mas tracking não comprova persistência.

## 5. Diálogo de REVISÃO — antes de confirmar

```text
┌ Revisar alterações ──────────────────────────────────────────── [Fechar] ┐
│ Confira as alterações antes de salvar. Somente campos modificados.      │
│ Identificação                                                           │
│ Campo                 Valor atual                    Novo valor         │
│ Nome fantasia         Empresa A                      Empresa B          │
│ Contato                                                                 │
│ Telefone              (47) ...                      (47) ...           │
│ E-mail                —                             contato@...        │
│ Endereço                                                                │
│ Bairro                Centro Antigo                  Centro             │
│                                   [Cancelar] [Confirmar e salvar]        │
└──────────────────────────────────────────────────────────────────────────┘
```

- Modal acessível (role dialog, aria-label, focus trap, escape, restoration focus); layout responsivo (tabela desktop, pares empilhados mobile).
- Mostrar seção, campo, valor atual, novo valor apenas para diffs. Tratar PII conforme política e não expor dados fora do escopo do usuário.
- UPDATE: diff-only. CREATE: revisão do conjunto de campos informados sem inventar `valor atual`; texto CTA `Confirmar inclusão`.
- Loading/erro preservam informações e evitam submissão dupla. Avisos sobre resultado indeterminado devem instruir consulta de operação, jamais reenviar automaticamente.

## 6. Inventário de componentes — responsabilidades, não novos pacotes autorizados

| Nome conceitual (identificador técnico em inglês) | Papel visual | Regra de reuso |
|---|---|---|
| `SupplierPageHeader` | Breadcrumb, título, subtítulo, status e ações | Compor PagePath/PageHero + Badge/Button do kit |
| `SupplierIdentitySummary` | Código/loja/documento/tipo/status | Read-only; não duplica dados internos |
| `SupplierFormLayout` | Layout compartilhado Create/Edit e seções | Extração local somente se evita duplicação real |
| `SupplierFormSection` | Card com título, ícone opcional e grid | Compor Card/FormField do kit |
| `SupplierFieldGrid` | Grid lógico 12/6/4/3/2 spans adaptativos | CSS local com tokens/grid do kit, sem nova lib |
| `SupplierDisplayField` | Label+valor no modo consulta e protected edit | Representação, não `disabled input` |
| `SupplierProtectedField` | Exibir campos imutáveis com indicação discreta | Nunca colocar valores protegidos no PUT |
| `SupplierEditableField` | Label, input/select, ajuda, required, erro | Inputs/Select/FormField do kit, RHF atual se existir |
| `SupplierFormActions` | Barra de cancelar/revisar/confirmar + dirty count | Uso de Button/Bar existente; sticky opcional seguro |
| `SupplierChangeReviewDialog` | Diff agrupado, CTA seguro | Dialog/Modal do kit; não reimplementar a11y |
| `SupplierSubmissionStatus` | ACK, CONFIRMED, RECONCILIATION_REQUIRED etc. | Status reais do BFF/tracking, nunca inferidos |
| `SupplierFormFeedback` | Loading, skeleton, empty, partial, error, 403, 404 | Primitivas existentes do kit e padrões do MFE |

**Os nomes acima são proposta de decomposição, não evidência de componentes existentes ou autorização de criação de abstrações.** Inventário do código e `@delpi/plugin-ui` determina quais composições são de fato necessárias.

## 7. Mapeamento dos 18 campos Gabriel → seção visual

| Campo REST | TOTVS | Seção | Apresentação |
|---|---|---|---|
| `supplier_store` | A2_LOJA | Identificação | protected na edição, controlled no CREATE conforme contrato |
| `supplier_name` | A2_NOME | Identificação | largo |
| `supplier_short_name` | A2_NREDUZ | Identificação | largo |
| `tax_id` | A2_CGC | Identificação | documento formatado; protegido na edição |
| `address` | A2_END | Endereço | largo |
| `district` | A2_BAIRRO | Endereço | médio |
| `postal_code` | A2_CEP | Endereço | curto |
| `city` | A2_MUN | Endereço | médio |
| `city_code` | A2_COD_MUN | Endereço | curto |
| `state` | A2_EST | Endereço | curto |
| `bacen_country_code` | A2_CODPAIS | Endereço/Fiscal (uma vez) | seleção ou campo de código conforme existente |
| `contact_name` | A2_CONTATO | Contato | médio |
| `area_code` | A2_DDD | Contato | curto |
| `phone` | A2_TEL | Contato | médio |
| `email` | A2_EMAIL | Contato | largo/mobile |
| `financial_nature_code` | A2_NATUREZ | Compras/Financeiro | código |
| `payment_condition_code` | A2_COND | Fiscal/Financeiro | código |
| `accounting_account` | A2_CONTA | Compras/Financeiro | código |

Campos extras visualizados no mockup (inscrição estadual, municipal, ROHS, forma de pagamento, tipo de pessoa) devem ser cruzados com contrato real no HEAD antes da renderização. **Não inserir inputs não contratados.**

## 8. Estados e edge cases obrigatórios

- Loading, empty (incluindo informação não fornecida pelo GET), partial, erro de rede, 403, 404; erros de campo e erros gerais.
- Falta de permissão do usuário: ações invisíveis/desabilitadas conforme UX, sempre backend autoriza. Unidade, owner/recurso e regras server-side.
- Criação com documento inválido, field errors e regras condicionais; ausência de dicionário de seleção; dados parciais/charset/strings longas.
- UPDATE sem alterações, reverter alterações, navegação para trás e F5, alteração concorrente, response ACK/UNKNOWN; não repetir POST/PUT automaticamente.
- Desktop, tablet, mobile; light/dark; navegação por teclado; foco visível; leitores de tela; contraste; altura touch; tooltip por label; rolagem e barra de ação.
- Testes positive + sibling + negative, loading/empty/partial/error/403/404, URL refresh, validação de mascaramento e proteção de campos, Help sincronizada, build e smoke federado. Se smoke não executado: `INCONCLUSIVE` / `TEST_NOT_RUN`, nunca PASS inferido.

## 9. Gates de implementação e aceite (futuros)

**P0 antes do code change:** HEAD/status, authorities, `.cursor`, contratos de fornecedores, código real de Create/Edit/View e `@delpi/plugin-ui`; inventário de campos existentes e definição do owner da página; autorização explícita de implementar esta fatia visual; lista de rotas e estados. Qualquer divergência estrutural → `EXECUTION_DRIFT`, não corrigir silenciosamente.

**Acceptance:**
1. Visualização usa cards compactos e display fields sem inputs falsos.
2. Create e Edit compartilham grid/seções e mantêm diferenças contratuais (imutáveis).
3. Desktop usa a largura útil sem buracos desnecessários; tablet 2 col; mobile 1 col.
4. Dialog de revisão mostra apenas alterações no EDIT, e campos que serão enviados no CREATE.
5. Não altera payloads, AuthZ, flags, endpoints nem ownership; diffs enviados seguem contrato atual.
6. Estados e Help, a11y, light/dark, teclado/foco, responsividade, build/teste/smoke provados.
7. Rastreabilidade por arquivos, RQ/AC, teste, SHA e screenshots antes/depois. `@delpi/plugin-ui` tem precedência sobre customização.

**Status desta entrega GitHub:** `TARGET / DOCUMENTED` somente. Não é implementação e não muda o estado dos gates F4/E10.
