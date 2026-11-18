# DELPI Line Balance Studio — UX V4: entrada do estudo e sidebar secundária de métodos

**Decisão de produto aprovada:** 2026-11-18  
**Owner:** DELPI Line Balance Studio (experiência reutilizável)  
**Primeiro consumer:** Portal Engenharia > Processos > Balanceamento de Linha  
**Estado:** `APPROVED_PRODUCT_DESIGN / TARGET_IMPLEMENTATION / TEST_NOT_RUN`  
**Escopo desta revisão:** documentação e critérios de aceite; **não** afirmar alteração de runtime.  
**Referência visual:** visual clean já aprovado do Studio em GitHub Pages, preservando estilos e controles públicos do `@delpi/plugin-ui`, light/dark e responsividade.

## 1. Decisão consolidada

1. **A origem é a ação primária.** A entrada do Studio apresenta **dois cards grandes, com ícones expressivos**: `Produto DELPI` (consultar roteiro oficial autorizado) e `Estudo manual` (criar processo sem SKU). Os dois cards devem ter paridade de tamanho, ser clicáveis por inteiro, com estados hover/focus/selecionado e descrições curtas.
2. **Métodos em segunda sidebar interna, retrátil.** A navegação pelos métodos M1–M6 é parte do **Studio**, não um menu do Portal Engenharia nem seis páginas independentes. Expandida: ícone específico, nome e status; recolhida: trilho compacto somente de ícones, seleção ativa e tooltip acessível. O controle de expandir/recolher fica no topo do painel.
3. **A área de trabalho é prioritária.** O painel de métodos fica estreito quando expandido e ainda menor quando recolhido. O espaço liberado é usado por operações, postos, tabela, Yamazumi, outros métodos e comparação. Não criar um catálogo textual extenso sob o campo de produto.
4. **Um estudo, vários métodos.** Fonte/roteiro, filial/estágio, operações, revisão/fingerprint, condições de turno, demanda e lote pertencem ao contexto comum; a seleção de método troca apenas a experiência específica e seus resultados. Não alterar nem zerar esses dados sem pedido explícito.
5. **A entrada grande é transitória.** Após escolher/carregar a origem, substituir os dois cards por um cabeçalho compacto do estudo com origem, identificação, status e ação `Trocar origem` (protegida contra perda de alterações). A sidebar continua acessível.
6. **Sem capacidades falsas.** Métodos planejados ficam sob grupo discreto `Próximos métodos` (recolhível) e sem CTA de execução. O M2 deve distinguir FFD limitado de LCR planejado; M1 para processo manual só se houver contrato/capability válida no domínio.
7. **Não confundir sidebar do Studio com sidebar do Portal.** A principal permanece do Portal Minha DELPI; a secundária é interna ao workspace, sem duplicar cabeçalho de app ou navegação Core.
8. **A mesma experiência segue para outros portais.** O host oferece contextos e adapters; o Studio contém o estado de expansão/seleção e o layout. Persistência UI local é distinta da persistência dos dados do estudo e não muda RBAC.

## 2. Mapa funcional e navegação

```text
Minha DELPI (sidebar corporativa / Core)
  └── Portal Engenharia (home)
       └── Processos (categoria)
            └── Balanceamento de Linha (ferramenta)
                 ├── Origem do estudo (2 cards grandes, somente no início)
                 │    ├── Produto DELPI → Buscar roteiro → filial → estágio
                 │    └── Estudo manual → nome → operações criadas pelo usuário
                 ├── Sidebar interna de métodos (retrátil)
                 │    ├── M1 — Capacidade e takt
                 │    ├── M5 — Yamazumi interativo
                 │    ├── M2 — FFD limitado / LCR futuro
                 │    └── Próximos métodos: M3, M4, M6
                 └── Workspace compartilhado
                      ├── Origem e identificação compacta
                      ├── Operações / postos / condições
                      ├── Vista do método selecionado
                      └── Cenários / resultados / exportações / limitações
```

A página de Processos é um catálogo de **ferramentas** (Balanceamento, futura cronoanálise etc.). A sidebar do Studio é um catálogo de **métodos internos à ferramenta**. Não repetir um no outro.

## 3. Cards grandes de escolha de origem

### Card A — Produto DELPI
- **Nome:** `Produto DELPI`.
- **Descrição:** `Consultar roteiro oficial`.
- **Ícone de conceito:** `package-search` (Lucide ou equivalente público do kit), tamanho visual grande.
- **Ação:** selecionar origem `OBSERVED_ROUTING`, mostrar campo código de produto e ação `Buscar roteiro`.
- **Após consulta:** seleção explícita de filial/estágio quando necessária, apresentação da fonte com provenance e truncamento. Nunca consultar silenciosamente sem código ou sem autorização.

### Card B — Estudo manual
- **Nome:** `Estudo manual`.
- **Descrição:** `Criar processo do zero`.
- **Ícone de conceito:** `panels-top-left` ou `square-pen`, visualmente distinto do produto.
- **Ação:** selecionar origem `MANUAL`, nomear estudo e iniciar a tabela/fluxo de criação de operações.
- **Sem SKU:** não exigir código de produto nem inventar identificador oficial para chamar API por produto.

### Comportamento comum
- Cards igualmente destacados e clicáveis por toda a superfície; texto e ícones alinhados.
- Um dos dois pode ficar selecionado; até lá mostrar `Como deseja começar?`.
- Teclado Enter/Space, foco visível, aria-label/semântica de botão e indicador de seleção que não dependa somente de cor.
- Ao selecionar, mostrar formulário contextual **abaixo dos cards**, não ambos os formulários simultaneamente.
- Se a origem for trocada após dados preenchidos, proteger o rascunho com confirmação/ação de troca segura; jamais sobrescrever sem aviso.
- `Importar` não é terceiro card ativo enquanto não existir contrato, parser, validação e capability real; pode ser registrado como `TARGET` sem CTA operacional.

## 4. Sidebar interna — dimensões, estados e interação

### Expandida
- Painel lateral **estreito** (alvo inicial: ~180–220 px em desktop; validar em mock/testes reais), com título `Métodos`, botão recolher, itens com ícone, nome e status.
- Item ativo em destaque discreto, com foco e seleção acessíveis.
- Mostrar métodos implementados antes dos planejados; documentação de requisito não ocupa o corpo do workspace.
- `Próximos métodos` recolhível; o grupo pode existir mesmo que não haja capacidade implementada.
- `M1`, `M5` e `M2` só aparecem como executáveis quando a capability daquele método **e da origem do estudo** for comprovada.

### Recolhida
- Trilho de ícones com largura-alvo ~48–64 px em desktop.
- Preservar ícone, indicador de método selecionado e botão `Expandir métodos`.
- Tooltip/popover ao hover e ao foco com **nome completo e estado**, sem depender exclusivamente do hover.
- Não desmontar estudo, descartar rascunhos, mudar método nem rolar toda a página ao recolher.

### Trocar de método
- Selecionar método disponível troca o painel específico, **não** recria a origem nem a lista de operações.
- O resultado específico antigo pode ficar `STALE` quando entradas mudarem; não reutilizar como se estivesse atualizado.
- Persistir seleção de método e estado da sidebar apenas como preferência de UI local com namespace do Studio/host apropriado. Não guardar JWT ou segredo. Se a preferência falhar, o Studio continua usável.
- Método desabilitado: mostrar texto `Planejado` no grupo apropriado; sem CTA de execução, sem disparar solver.

### Tablet e mobile
- A sidebar secundária não pode sufocar o workspace. Em telas menores, preferir trilho recolhido, drawer/overlay temporário ou seletor compacto; o padrão final deve ser validado com Plugin UI e acesso por teclado.
- Após escolher o método, recolher automaticamente o drawer **somente no layout mobile**, sem descartar seleção nem dados; em desktop manter escolha de expansão do usuário.
- Sem overflow horizontal da página em 1024/390/320 px; componentes internos com scroll próprio quando necessário.
- Ao abrir menu no mobile, foco/escape/restauração de foco e leitura por screen reader devem funcionar.

## 5. Ícones e catálogo de métodos

Ícones sugeridos para a **sidebar** (Lucide ou equivalentes do Plugin UI; a implementação deve verificar exports e disponibilidade):

| ID | Nome curto | Ícone | Situação/semântica |
| --- | --- | --- | --- |
| M1 | Capacidade e takt | `gauge` | Diagnóstico; ativo somente sob contrato de cálculo válido |
| M2 | FFD / LCR | `list-ordered` | FFD limitado; LCR futuro. Badge `Limitado` quando aplicável |
| M3 | Peso posicional (RPW) | `git-branch` | Planejado; exige precedências |
| M4 | Kilbridge-Wester | `columns-3` | Planejado; exige precedências |
| M5 | Yamazumi | `chart-no-axes-column-increasing` | Primeiro método visual interativo |
| M6 | Dimensionamento de recursos | `users-round` | Planejado; exige recurso/simultaneidade |

**Nota:** o desenho anterior utilizou seleção interativa `m1`, sidebar recolhida e origem `Produto DELPI`; isso demonstra o comportamento possível, **não** configura default obrigatoriamente salvo. Inicialmente sem estudo, o Studio deve explicar claramente que a origem é necessária para executar análises.

## 6. Wireframe textual — desktop, antes de iniciar

```text
Portal Engenharia (chrome / sidebar principal existentes)
┌──────────────────────────────────────────────────────────────────────────┐
│ DELPI LINE BALANCE STUDIO                  [Estudos] [Ajuda] [Ações]      │
├───────────────┬──────────────────────────────────────────────────────────┤
│ MÉTODOS   [◀]│ NOVO ESTUDO                                              │
│               │ Como deseja começar?                                     │
│ [📟] Capacidade│ ┌────────────────────┐ ┌────────────────────────────┐  │
│ [📊] Yamazumi │ │    ÍCONE GRANDE     │ │       ÍCONE GRANDE         │  │
│ [☷] FFD lim.  │ │    Produto DELPI    │ │       Estudo manual        │  │
│ ───────────   │ │ Consultar roteiro  │ │ Criar processo do zero    │  │
│ Próximos  [v] │ └────────────────────┘ └────────────────────────────┘  │
│ [↗] RPW       │                                                          │
│ [▥] K-W       │ [Formulário contextual somente após escolher origem]     │
│ [♧] Recursos  │                                                          │
└───────────────┴──────────────────────────────────────────────────────────┘
```

## 7. Wireframe textual — após selecionar/carregar origem

```text
┌──────┬───────────────────────────────────────────────────────────────────┐
│ [▶]  │ Estudo: Produto 9026.... · Filial 02 · Estágio ...   [Trocar]     │
│  M1  │ OBSERVED / DRAFT_LOCAL · Fonte/revisão/status                      │
│  M5* │ [Operações] [Turnos e pausas] [Postos] [Cenário A ▾]               │
│  M2  ├────────────────────┬──────────────────────────────────────────────┤
│  ... │ Tabela / Operações │ Painel do método selecionado                  │
│      │ + Adicionar       │ YAMAZUMI — Carga × takt                        │
│      │ Arrastar/mover    │ gráfico sincronizado com atribuições          │
│      ├────────────────────┴──────────────────────────────────────────────┤
│      │ Alertas / Não atribuídas / Comparação / Limitações / Exportar     │
└──────┴───────────────────────────────────────────────────────────────────┘
```

O desenho não obriga duas colunas em todos os métodos: a estrutura de estudo é comum, mas cada método pode fornecer seu painel específico e suas métricas.

## 8. Propriedade do estado e contratos

- `StudyContext` é compartilhado e não pertence ao menu: source, produto/filial/estágio quando oficial, operações, elementos, tempos, unidade, turno/pausas, demanda, lote, fonte/revisão e cenários.
- `SelectedMethod` é a seleção de viewport; métodos podem ter inputs próprios, versionados por método/cenário, sem tocar nos dados-base do estudo.
- `MethodSidebarState` (`expanded/collapsed`) é uma preferência visual; não deve viver em DTO oficial/BFF.
- A troca de método não deve recalcular automaticamente métodos indisponíveis nem mascarar limitações. Não confundir `PREVIEW` de UI com `CALCULATED` oficial do domínio.
- A UI só usa componentes públicos do `@delpi/plugin-ui`; Studio mantém a composição. Portal Engenharia é adapter/host. Nenhuma dependência em componentes específicos do balanceamento legado.
- A apresentação da fonte `OBSERVED` e alterações `DRAFT_LOCAL` continua explícita; `Yamazumi != solver`, `CT != posto`, tempos ausentes `UNKNOWN`.

## 9. RQ/AC de implementação futura

| RQ | Critério de aceite | Evidência exigida |
| --- | --- | --- |
| UX4-01 | Dois cards grandes de origem, com ícones próprios, sem formulário inicial obrigatório de SKU | screenshot desktop/mobile + teclado |
| UX4-02 | Produto DELPI abre busca autorizada, filial/estágio; manual abre estudo sem SKU | e2e oficial/manual |
| UX4-03 | Sidebar secundária retrátil faz parte do Studio, não do host | teste de consumer independente |
| UX4-04 | Sidebar recolhida reduz largura, preserva seleção, oferece tooltip/foco | DOM+visual+teclado |
| UX4-05 | Cada método possui ícone específico e status compatível com capability | teste catálogo/versão |
| UX4-06 | Somente métodos executáveis ficam clicáveis; planejados em grupo discreto | testes negativos |
| UX4-07 | Escolha de origem substitui cards por cabeçalho compacto após criação/carregamento | e2e e screenshots |
| UX4-08 | Troca de método conserva fonte, operações, condições, cenários e draft | e2e alternância+F5 |
| UX4-09 | Mudança de origem com alterações protege contra perda de dados | teste de confirmação |
| UX4-10 | Mobile tem navegação apropriada, foco/escape e sem overflow | 1024/390/320 |
| UX4-11 | UI idêntica em demo independente e host no que compete ao Studio; tema light/dark | comparativo visual |
| UX4-12 | Nenhuma alteração de cálculo oficial ou roteiro publicada pelo Studio | contratos, AuthZ e residual search |

## 10. Escopo e sequenciamento

**Fase A — limpeza do host:** tarefa separada de navegação remove o grid de seis cards `Em planejamento` na página `Engenharia de Processos` e substitui por acesso compacto às ferramentas realmente disponíveis. Preservar a categoria Processos e rotas. Remover lista textual extensa de métodos somente onde redundante no host, sem excluir catálogo/metadados. **Não implementar V4 nesta fase.**

**Fase B — implementar V4 no Studio:** desenvolver cards, sidebar, estado de método, painel contextual e cabeçalho de estudo. Integração no Portal Engenharia vem por API pública do Studio. Sem duplicação visual pelo host.

**Fase C — bancada interativa:** operações/tabular, turnos, postos, Yamazumi e comparação com mesma modelagem e sem perda na alternância de métodos.

**Fase D — verificação:** unit/component/contract, browser com SSO em HML, desktop/mobile light/dark, Verify independente, regression e rollout governado. `INCONCLUSIVE` não é `PASS`.

Nenhuma destas fases é comprovada como implementada por esta documentação. **Não fazer deploy de código por alteração de docs.**

## 11. Proteção de decisões

A Sidebar do Portal Minha DELPI permanece inalterada. A nova sidebar é **secundária e específica do Studio**. O Studio permanece **greenfield**, distribuído como ferramenta reutilizável; o host não se torna owner de seus editores/métodos. Os seis métodos integram um só produto, mas os não implementados não ganham cálculo fictício. As experiências de estudos e cenários não são source of truth nem podem publicar processo/roteiro oficial.

**Aprovação:** direção visual explicitamente aprovada pelo Product Owner em conversa de projeto em 2026-11-18.  
**Próximo passo:** após limpeza da página Processos, detalhar e implementar a entrada V4 como uma fatia do Studio independente.