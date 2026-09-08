# Design de produto — Wizard de Emissão de Nota Fiscal

> **Produto:** Minhas Solicitações  
> **Fluxo:** `invoice-issuance`  
> **Rota:** `/apps/my-requests/new?type=invoice-issuance`  
> **Status:** especificação visual/UX — **implementado (E21)**; responsivo + progresso sequencial **E22**  
> **UI kit:** `@delpi/plugin-ui` via Module Federation  
> **Wireframe mestre:** [WIREFRAMES.md](./WIREFRAMES.md) — WF-04  
> **Prompt transversal de UI:** [PROMPT-ui-excelencia-topbar-ptbr-help.md](./PROMPT-ui-excelencia-topbar-ptbr-help.md)

---

## 1. Objetivo

Evoluir o formulário atual de **Nova emissão de nota fiscal** de uma sequência de botões/abas para um **wizard guiado, progressivo e editável**, mantendo as seis etapas de negócio existentes e sem duplicar regras da `requests-api`.

O novo fluxo deve:

1. mostrar claramente onde o usuário está;
2. mostrar quanto falta para concluir;
3. atualizar o progresso automaticamente conforme os campos obrigatórios são preenchidos;
4. liberar a próxima etapa quando a etapa atual estiver válida;
5. permitir voltar e editar etapas já preenchidas sem perder dados;
6. impedir salto para etapas futuras ainda bloqueadas;
7. encerrar com uma **Conferência** estruturada, com ação **Alterar** em cada seção;
8. manter toda a experiência em PT-BR, responsiva e acessível;
9. usar componentes do `@delpi/plugin-ui` e criar no kit qualquer novo primitivo transversal.

---

## 2. Contexto atual confirmado

Implementação atual principal:

```text
plugins/my-requests/src/features/invoice-issuance/ui/InvoiceIssuanceWizard.tsx
```

Etapas vigentes:

1. Destinatário
2. Tipo de NF
3. Itens
4. Transporte
5. Adicionais
6. Conferência

O fluxo atual já possui:

- filial conforme `branch_scope`;
- Cliente / Fornecedor;
- lookup de destinatário;
- seleção de tipo de NF;
- lookup e inclusão de produtos;
- frete CIF/FOB;
- lookup de transportadora;
- peso, volumes e observação;
- checklist de conferência;
- criação final via `/apps/requests-api`.

Esta especificação é **visual e de interação**. Ela não altera o domínio, os endpoints ou o contrato de criação.

---

## 3. Pesquisa de referências de mercado

A direção abaixo foi baseada em design systems maduros, usando somente princípios aplicáveis ao fluxo atual.

### 3.1 Atlassian Design System — Progress tracker

Referência: `https://atlassian.design/components/progress-tracker/`

O Atlassian define **Progress tracker** como o componente que mostra as etapas e o progresso ao longo de uma jornada.

Aplicação no Minha DELPI:

- as seis etapas devem ser representadas como jornada;
- o tracker não é decoração: ele deve informar posição e estado;
- etapas já concluídas podem funcionar como navegação para revisão/edição.

### 3.2 IBM Carbon — Progress indicator

Referências:

- `https://carbondesignsystem.com/components/progress-indicator/usage/`
- `https://carbondesignsystem.com/components/progress-indicator/style/`

O Carbon recomenda progress indicator para processos lineares com **3 ou mais etapas**, especialmente formulários longos. O padrão diferencia estados como:

- completed;
- current;
- not started;
- error;
- disabled.

Também recomenda:

- validar uma etapa antes de liberar a seguinte;
- permitir voltar a etapas anteriores;
- usar labels curtas;
- manter feedback de foco/hover e navegação por teclado.

Aplicação no Minha DELPI:

```text
✓ concluída
● atual
○ futura liberada
○ futura bloqueada
! contém erro
```

### 3.3 Carbon — Progress bar

Referência: `https://carbondesignsystem.com/components/progress-bar/usage/`

O Carbon diferencia **progress bar** de **progress indicator**: progress bar é orientada principalmente a processamento do sistema; quando o progresso depende de ações manuais do usuário, o progress indicator é o componente principal.

Como o requisito de produto pede uma **barra de progresso**, neste wizard ela será usada apenas como **resumo secundário de completude**, e não como navegação principal.

Assim:

```text
Progress tracker = navegação / estado das etapas
Progress summary bar = percentual geral de completude
```

Não reutilizar `InlineLoadingProgress` como tracker do wizard: esse componente existente no `plugin-ui` tem semântica de **loading/processamento** e deve continuar com essa finalidade.

### 3.4 GOV.UK Design System — Question pages

Referência: `https://design-system.service.gov.uk/patterns/question-pages/`

Pontos aplicáveis:

- perguntar apenas o necessário;
- organizar a experiência para foco na pergunta/atividade atual;
- oferecer navegação de retorno;
- não pedir novamente informação já fornecida;
- usar indicador de progresso quando ele ajuda o usuário.

Aplicação no wizard:

- uma etapa mostra um grupo coerente de informação;
- o usuário não precisa rever campos de outras etapas durante o preenchimento;
- respostas permanecem preenchidas quando ele volta.

### 3.5 GOV.UK — Check answers

Referência: `https://design-system.service.gov.uk/patterns/check-answers/`

A etapa de conferência deve permitir revisar as respostas antes do envio e alterar uma seção específica sem refazer toda a jornada.

Aplicação:

- Conferência vira um resumo por seções;
- cada seção possui ação **Alterar**;
- após alterar, o usuário retorna à Conferência preservando o restante.

---

## 4. Decisões de UX travadas

### 4.1 Tracker é o controle principal da jornada

Os atuais botões:

```text
1. Destinatário
2. Tipo de NF
3. Itens
4. Transporte
5. Adicionais
6. Conferência
```

não devem continuar como uma simples `FormActions` com seis `ActionButton`.

Eles devem virar um **Progress Tracker** próprio para jornadas.

### 4.2 Barra de progresso é complementar

Exibir resumo como:

```text
Progresso da solicitação                         33%
██████████░░░░░░░░░░░░░░░░░░░░
2 de 6 etapas concluídas
```

O percentual deve refletir **completude real das etapas**, não posição visual do usuário.

Exemplo:

- usuário chegou à etapa 4;
- voltou e invalidou a etapa 2;
- progresso não continua artificialmente em 50%; deve recalcular conforme as etapas válidas.

### 4.3 Etapas anteriores são editáveis

Ao concluir uma etapa:

- o tracker mostra check;
- o passo fica clicável;
- clicar reabre os dados já preenchidos;
- alterações revalidam a etapa e podem invalidar dependências posteriores quando houver dependência real.

Não apagar respostas sem uma regra explícita do domínio.

### 4.4 Etapas futuras são controladas

- etapa imediatamente seguinte é liberada quando os requisitos da atual forem satisfeitos;
- etapas futuras ainda não liberadas aparecem visualmente desabilitadas;
- não permitir salto direto para a Conferência com dados incompletos.

### 4.5 Avanço progressivo, sem autoavanço agressivo

O progresso visual deve avançar **automaticamente** conforme o usuário preenche os campos.

A troca automática de tela/etapa deve ser usada somente quando houver uma única ação decisiva e de baixo risco.

Exemplo aceitável:

```text
Selecionou um destinatário válido
→ etapa Destinatário fica concluída
→ próxima etapa fica liberada
→ pode autoavançar se a seleção for claramente final
```

Etapas com vários campos devem seguir:

```text
campos válidos
→ progresso atualiza
→ botão Próximo fica habilitado
→ usuário confirma a mudança de etapa
```

Isso evita que a interface "fuja" enquanto a pessoa ainda está revisando o que acabou de preencher.

---

## 5. Estrutura visual alvo — desktop

```text
┌────────────────────────────────────────────────────────────────────────────┐
│ MyRequestsTopBar                                                          │
│ Minhas solicitações | Fila de trabalho | Nova solicitação | Administração │
├────────────────────────────────────────────────────────────────────────────┤
│ Nova emissão de nota fiscal                                               │
│ Filial 01 · Etapa 1 de 6                                                  │
│ [? Ajuda]                                                                 │
│                                                                            │
│ Progresso da solicitação                                      17%          │
│ █████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░                                     │
│ 0 de 6 etapas concluídas                                                  │
│                                                                            │
│  ● Destinatário ── ○ Tipo de NF ── ○ Itens ── ○ Transporte ── ○ Adicionais│
│                                                        ── ○ Conferência    │
├────────────────────────────────────────────────────────────────────────────┤
│ SectionCard — Destinatário                                                │
│                                                                            │
│ Informe quem receberá a nota fiscal.                         [?]           │
│                                                                            │
│ Tipo de destinatário                                                      │
│ ( ● Cliente | ○ Fornecedor )                                              │
│                                                                            │
│ Buscar destinatário                                                       │
│ [ Código, nome ou CNPJ................................................. ]  │
│ [Buscar]                                                                  │
│                                                                            │
│ Resultados                                                                │
│ ┌──────────────────────────────────────────────────────────────────────┐   │
│ │ ACME Indústria Ltda.                                                 │   │
│ │ Código 001234 · Loja 01 · CNPJ XX.XXX.XXX/XXXX-XX                   │   │
│ │                                                     [Selecionar]     │   │
│ └──────────────────────────────────────────────────────────────────────┘   │
│                                                                            │
│ [Voltar]                                                    [Próximo →]   │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Estrutura visual alvo — etapa concluída editável

```text
Progresso da solicitação                                      33%
███████████░░░░░░░░░░░░░░░░░░░░░
2 de 6 etapas concluídas

✓ Destinatário ── ✓ Tipo de NF ── ● Itens ── ○ Transporte ── ○ Adicionais ── ○ Conferência
   clicável          clicável        atual       bloqueada       bloqueada       bloqueada
```

Ao clicar em **Destinatário**:

```text
→ abre etapa 1
→ mantém destinatário selecionado
→ botão principal vira "Salvar alterações" ou "Continuar"
→ depois de salvar, retorna à etapa de origem quando veio da Conferência
```

---

## 7. Estrutura visual alvo — mobile

No mobile não tentar comprimir seis labels horizontalmente.

```text
┌──────────────────────────────┐
│ TopBar colapsada             │
├──────────────────────────────┤
│ Nova emissão de NF           │
│ Filial 01 · Etapa 3 de 6     │
│                              │
│ Progresso               33%  │
│ █████░░░░░░░░░░░░            │
│ 2 de 6 concluídas            │
│                              │
│ Etapa atual: Itens           │
│ [Ver etapas preenchidas ▾]   │
├──────────────────────────────┤
│ Conteúdo da etapa            │
│                              │
│ campos / resultados          │
│ validações                   │
│                              │
├──────────────────────────────┤
│ [Voltar]        [Próximo]    │
└──────────────────────────────┘
```

Ao abrir **Ver etapas preenchidas**:

```text
✓ Destinatário        [Alterar]
✓ Tipo de NF          [Alterar]
● Itens               Atual
○ Transporte          Bloqueada
○ Adicionais          Bloqueada
○ Conferência         Bloqueada
```

O componente compartilhado deve resolver o modo compacto; não criar um segundo stepper específico no MFE.

---

## 8. Wireframe — Conferência

```text
┌─ Conferência ──────────────────────────────────────────────────────────────┐
│ Revise os dados antes de enviar a solicitação.                       [?]  │
│                                                                          │
│ ✓ Destinatário                                              [Alterar]    │
│   ACME Indústria Ltda.                                                   │
│   Cliente · Código 001234 · Loja 01                                     │
│                                                                          │
│ ✓ Tipo de nota fiscal                                      [Alterar]    │
│   Venda                                                                  │
│                                                                          │
│ ✓ Itens                                                   [Alterar]      │
│   3 itens · quantidade total 12                                          │
│   ------------------------------------------------------------------     │
│   100100 · Produto A · 4 UN · R$ ...                                    │
│   100200 · Produto B · 8 UN · R$ ...                                    │
│                                                                          │
│ ✓ Transporte                                               [Alterar]     │
│   CIF · Transportadora XYZ                                                │
│                                                                          │
│ ✓ Informações adicionais                                  [Alterar]     │
│   Peso 120 kg · 4 volumes · observação ...                                │
│                                                                          │
│ [Voltar]                                           [Enviar solicitação]   │
└──────────────────────────────────────────────────────────────────────────┘
```

A Conferência não deve mostrar chaves técnicas do checklist.

---

## 9. Comportamento por etapa

### 9.1 Destinatário

**Obrigatório:** destinatário selecionado.

Fluxo:

```text
Cliente/Fornecedor
→ busca
→ resultados
→ selecionar registro
→ exibir resumo selecionado
→ marcar etapa concluída
→ liberar Tipo de NF
```

Componentes:

- `SegmentToggle` — existente;
- `TextField` — existente;
- `ActionButton` — existente;
- novo `SelectionSummaryCard` do kit para o registro escolhido;
- loading/error/empty do kit.

### 9.2 Tipo de NF

**Obrigatório:** tipo de NF válido; se `other`, descrição preenchida.

Preferência visual:

- se a quantidade de opções for pequena e estável, avaliar radio cards/segmented choices do kit;
- caso contrário manter `SelectField`.

Não criar cards locais sem necessidade.

### 9.3 Itens

**Obrigatório:** pelo menos um item válido e todas as quantidades/preços requeridos válidos.

Melhoria visual:

- busca separada da lista já adicionada;
- produto selecionado deve entrar em uma lista/tabela operacional;
- usar `DataTable` quando a densidade justificar;
- campos quantitativos com formatação e validação PT-BR;
- ação de remover com `IconButton tone="danger"` se aplicável.

### 9.4 Transporte

- CIF/FOB via `SegmentToggle`;
- help contextual explicando cada modalidade;
- transportadora opcional conforme regra atual;
- registro escolhido em `SelectionSummaryCard`.

### 9.5 Adicionais

- peso;
- volumes;
- observação;
- `FieldLabel` + hints;
- opcionais marcados explicitamente como `(opcional)` quando aplicável.

### 9.6 Conferência

- `ReviewSummaryCard` por grupo;
- CTA `Alterar` em cada grupo;
- voltar de edição retorna à Conferência;
- envio disponível somente quando todas as etapas obrigatórias estiverem válidas.

---

## 10. Modelo de progresso

Não acoplar o percentual ao índice atual.

Criar no MFE apenas um modelo de **estado visual do wizard**, derivado dos valores já preenchidos e das validações de UX existentes.

Exemplo conceitual:

```ts
type WizardStepState = "complete" | "current" | "available" | "locked" | "error";

type WizardStepViewModel = {
  id: string;
  label: string;
  state: WizardStepState;
  completion: number; // 0..100 dentro da etapa, se útil
};
```

O cálculo não deve duplicar regras de autorização/workflow da solicitação. Ele serve apenas para o formulário **antes da criação**.

### Percentual geral

Preferir percentual por requisitos cumpridos em vez de `step / 6` quando houver dados suficientes para isso.

Exemplo simples inicial:

```text
Destinatário concluído = 1
Tipo de NF concluído   = 1
Itens concluído        = 1
Transporte concluído   = 1
Adicionais concluído   = 1
Conferência pronta     = 1

percentual = concluídas / 6 * 100
```

Se uma etapa tiver validação parcial relevante, o kit pode exibir `completion`, mas a primeira implementação pode manter cálculo por etapa concluída para evitar complexidade falsa.

---

## 11. Componentes `plugin-ui` já existentes a reutilizar

Confirmados no catálogo/uso atual:

| Componente | Uso no wizard |
|---|---|
| `TopBar` / `createDashboardTopBar` | navegação do módulo |
| `PageHeader` | título e contexto da página |
| `SectionCard` | container da etapa |
| `ActionButton` | buscar, voltar, próximo, enviar |
| `BackLink` | alternativa para retorno contextual quando fizer sentido |
| `SegmentToggle` | Cliente/Fornecedor; CIF/FOB |
| `TextField` | buscas e números/textos simples |
| `SelectField` | filial e seleções |
| `FieldLabel` | labels + help |
| `NativeTextAreaControl` | observação |
| `DataTable` | itens adicionados, se densidade justificar |
| `StatusBadge` | estados auxiliares, se necessário |
| `StateBanner` | erro de etapa/API |
| `EmptyState` / `EmptyGuidance` | nenhuma busca/nenhum item |
| `LoadingState` | estados de carregamento de lookup |
| `HelpTooltip` | Ajuda contextual |
| `IconButton` | remover/editar item quando aplicável |

### `InlineLoadingProgress`

Existe no `plugin-ui`, mas **não deve ser reutilizado como componente principal do wizard**. A documentação atual do kit o define como barra determinada para **status bar / toolbar / loading**. O novo componente deve ter semântica de jornada/formulário.

---

## 12. Componentes novos a criar no `plugin-ui`

A pesquisa no catálogo atual não encontrou stepper/progress tracker de jornada. Como esse padrão é transversal a cadastro, onboarding, solicitações e outros futuros fluxos, ele deve nascer no `plugin-ui`.

### 12.1 `ProgressTracker` / factory `createDashboardProgressTracker`

**Prioridade:** P0.

Responsabilidade:

- mostrar etapas lineares;
- estados `complete | current | available | locked | error`;
- modo interativo opcional;
- clique somente quando `interactive && enabled`;
- keyboard navigation;
- horizontal desktop;
- variante compacta/mobile;
- labels, helper e aria configuráveis;
- CSS exclusivamente em `plugins/plugin-ui/src/styles/`.

API conceitual:

```ts
<ProgressTracker
  steps={steps}
  currentStepId="items"
  onStepChange={openStep}
  interactive
  ariaLabel="Etapas da emissão de nota fiscal"
/>
```

### 12.2 `JourneyProgressBar` / `ProgressSummaryBar`

**Prioridade:** P0.

Não confundir com `InlineLoadingProgress`.

Responsabilidade:

- representar completude humana de uma jornada;
- `value` 0..100;
- label e summary (`2 de 6 etapas concluídas`);
- usar `role="progressbar"` com `aria-valuenow/min/max`;
- visual compatível com claro/escuro.

### 12.3 `WizardShell` / `WizardStepLayout`

**Prioridade:** P1.

Responsabilidade:

- header da etapa;
- descrição/help;
- body;
- rodapé com ações anterior/próximo;
- composição responsiva;
- não conhecer domínio NF.

Se a composição puder ser feita de forma limpa com `SectionCard` + `FormActions`, não criar esse componente apenas por conveniência. Criar somente se houver ganho real e 2+ consumidores previstos.

### 12.4 `SelectionSummaryCard`

**Prioridade:** P1.

Responsabilidade:

- resumir entidade selecionada após busca;
- título, linhas/meta, leading icon;
- ações `Alterar` / `Remover` opcionais;
- sem dependência de cliente, fornecedor, produto ou transportadora.

Antes de criar, comparar com `NavigationCard`, `WorklistItem` e outros cards existentes. Se um componente atual atender sem distorção semântica, reutilizar.

### 12.5 `ReviewSummaryCard`

**Prioridade:** P0 para Conferência.

Responsabilidade:

- título da seção;
- status concluído/erro opcional;
- pares label/valor;
- ação `Alterar`;
- layout compacto;
- reutilizável em solicitação, cadastro e onboarding.

Antes de criar, pesquisar novamente o catálogo vigente para evitar duplicata.

### 12.6 `InlineValidationSummary`

**Prioridade:** P2/opcional.

Usar somente se houver várias pendências por etapa e o `StateBanner` não for suficiente.

Responsabilidade:

- listar pendências em linguagem humana;
- links/foco para campos inválidos se aplicável.

Não criar se mensagens inline por campo + `StateBanner` já resolverem o caso.

---

## 13. O que fica no `my-requests`

Permanece no domínio/feature:

- definição das 6 etapas de emissão;
- `WIZARD_STEPS` e labels específicas;
- critérios de completude específicos de NF;
- lookups;
- payload da solicitação;
- validações de UX específicas da emissão;
- mapeamento de dados para a Conferência;
- textos PT-BR e helps do fluxo.

---

## 14. O que NÃO fazer

- não transformar os seis passos em Tabs genéricas;
- não usar `FormActions` como stepper;
- não usar `InlineLoadingProgress` como navegação de jornada;
- não criar `.my-requests-stepper*` com chrome próprio no MFE;
- não copiar CSS do Carbon, Atlassian, GOV.UK ou Portal Comercial;
- não importar bibliotecas externas de stepper;
- não mover regra de negócio da API para o frontend;
- não apagar respostas ao navegar para trás;
- não autoavançar enquanto o usuário ainda digita um grupo de campos;
- não liberar etapas futuras inválidas apenas porque o usuário clicou nelas;
- não mostrar chaves técnicas na Conferência;
- não usar a cor como único indicador de estado;
- não quebrar browser back/forward.

---

## 15. Ajuda contextual

Atualizar `plugins/my-requests/src/content/helpTooltips.ts` no mesmo PR.

Cobertura mínima:

```text
invoiceWizard.section
invoiceWizard.progress
invoiceWizard.recipient
invoiceWizard.invoiceType
invoiceWizard.items
invoiceWizard.freight
invoiceWizard.extras
invoiceWizard.review
invoiceWizard.partySearch
invoiceWizard.productSearch
invoiceWizard.carrierSearch
```

Textos devem explicar negócio, não arquitetura.

Exemplo:

```text
Progresso:
"Acompanhe as etapas da solicitação. Etapas concluídas podem ser abertas novamente para revisão antes do envio."
```

---

## 16. Acessibilidade

Obrigatório:

- tracker com `aria-label`;
- estado atual anunciado (`aria-current="step"` ou equivalente);
- etapas bloqueadas não focáveis;
- etapas editáveis acessíveis por teclado;
- progresso geral com semântica `progressbar`;
- check/erro com texto acessível, não só cor/ícone;
- foco movido para heading da etapa ao trocar de passo;
- erros ligados ao campo correspondente;
- botões com alvo mínimo apropriado para toque;
- mobile sem scroll horizontal acidental.

---

## 17. Testes

### Unitários

- cálculo de etapa completa;
- cálculo de percentual;
- desbloqueio sequencial;
- etapa concluída pode ser reaberta;
- etapa bloqueada não abre;
- alterar etapa anterior revalida progresso;
- Conferência só libera quando requisitos mínimos estiverem válidos;
- labels PT-BR;
- callback de domínio recebe códigos originais.

### `plugin-ui`

Para componentes novos:

- render estados;
- teclado;
- aria;
- disabled/locked;
- dark/light por tokens;
- mobile/compact;
- dual-class/factory;
- entrada no catálogo e demo.

### Smoke visual

Validar:

- desktop claro;
- desktop escuro;
- mobile claro;
- mobile escuro;
- ida e volta entre todas as seis etapas;
- edição após preenchimento;
- retorno da Conferência;
- busca vazia/erro/loading;
- itens múltiplos;
- submit final.

---

## 18. Fases sugeridas

### E21.S0 — Inventário e catálogo

- confirmar exports vigentes do `plugin-ui`;
- registrar baseline do wizard atual;
- rodar testes/build atuais.

### E21.S1 — Componentes compartilhados P0

- `ProgressTracker`;
- `JourneyProgressBar`;
- `ReviewSummaryCard` se não houver equivalente no catálogo;
- docs/demo/testes no `plugin-ui`.

### E21.S2 — Modelo de progresso no wizard

- view model das etapas;
- critérios de completude;
- desbloqueio;
- navegação para etapas anteriores;
- testes.

### E21.S3 — Novo layout do wizard

- tracker + progresso;
- SectionCard da etapa;
- rodapé de navegação;
- responsive.

### E21.S4 — Destinatário + Tipo

- resultados;
- seleção;
- resumo do escolhido;
- help.

### E21.S5 — Itens + Transporte + Adicionais

- tabela/lista de itens;
- transportadora selecionada;
- validações.

### E21.S6 — Conferência

- review cards;
- Alterar por seção;
- retorno contextual;
- CTA final.

### E21.S7 — Ajuda + docs + smoke

- helpTooltips;
- WIREFRAMES;
- Manual se comportamento user-facing mudar;
- testes/build;
- smoke claro/escuro/mobile.

---

## 19. Definition of Done

- [x] Não existe mais stepper baseado em seis `ActionButton` soltos.
- [x] Progress Tracker mostra concluída/atual/futura/erro/bloqueada.
- [x] Barra de progresso geral atualiza automaticamente pela completude.
- [x] Próxima etapa só libera após validação necessária.
- [x] Etapas preenchidas podem ser reabertas e alteradas.
- [x] Dados não são perdidos ao navegar entre etapas.
- [x] Mobile tem representação compacta das etapas.
- [x] Conferência possui resumo por seção + `Alterar`.
- [x] Checklist técnico não aparece na UI.
- [x] Componentes transversais novos ficam no `plugin-ui`.
- [x] Zero CSS de componentes do kit no MFE.
- [x] Ajuda contextual sincronizada.
- [x] PT-BR completo.
- [x] Acessibilidade por teclado e screen reader considerada.
- [x] Testes do `plugin-ui` e `my-requests` verdes.
- [x] Build verde.
- [ ] Smoke visual no Portal federado concluído.

---

## 20. Prompt colável para o Cursor

```text
Implemente a evolução visual e de interação do wizard de Emissão de Nota Fiscal
conforme:

docs/12-roadmap-e-evolucao/my-requests/DESIGN-wizard-emissao-nf.md

e WF-04 de:

docs/12-roadmap-e-evolucao/my-requests/WIREFRAMES.md

Objetivo: substituir o stepper atual baseado em FormActions/ActionButton por um
wizard guiado com Progress Tracker interativo, barra de progresso geral,
validação/desbloqueio por etapa e Conferência editável.

Regras obrigatórias:
- 6 etapas existentes permanecem: Destinatário, Tipo de NF, Itens, Transporte,
  Adicionais, Conferência;
- progresso visual atualiza automaticamente conforme a completude real;
- etapas concluídas podem ser reabertas para edição sem perda de dados;
- etapas futuras bloqueadas não podem ser abertas;
- autoavanço de tela somente em seleção decisiva e de baixo risco; etapas com
  vários campos habilitam Próximo após validação;
- Conferência usa resumo por seção com ação Alterar;
- 100% da UI em PT-BR;
- ajuda contextual sincronizada;
- regras de negócio e criação continuam na requests-api;
- MFE continua chamando somente /apps/requests-api;
- use componentes existentes do @delpi/plugin-ui antes de criar qualquer novo;
- não use InlineLoadingProgress como stepper: ele é componente de loading;
- se não existir equivalente, criar no plugin-ui, com teste/docs/demo:
  ProgressTracker/createDashboardProgressTracker,
  JourneyProgressBar/ProgressSummaryBar,
  ReviewSummaryCard;
- avaliar SelectionSummaryCard e WizardStepLayout somente se não houver
  equivalente atual e houver ganho/reuso real;
- zero CSS de componente do kit no my-requests;
- validar claro/escuro, desktop/mobile, teclado e browser back/forward.

Execute pelas fases E21.S0–E21.S7 do documento e atualize o status do design para
implementado somente após testes/build/smoke.
```
