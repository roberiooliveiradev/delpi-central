# 76 — DÉLIA: Unified Avatar, identidade viva e perfil do usuário

**Status:** `APPROVED_PRODUCT_UX_DIRECTION` para **Opção A — símbolo Sparkles institucional animado** (aprovação expressa do Product Master em 2026-10-09). **Não implementado por esta tarefa**; integrações, dados de perfil, animações e permissões continuam sujeitos a inventário, contratos, fase e evidências.
**Escopo:** design de um sistema unificado de avatares para DÉLIA e usuário, com base visual potencialmente reutilizável em `plugins/plugin-ui` e consumer standalone `plugins/delia`. Página completa, dock e estados futuros de voz, sem criar backend.
**Reanchor:** HEAD de elaboração `bfc539484e2f67ce875097bd0d7372430032b7d8`; execução deve sempre verificar HEAD, status, Project Instructions/.cursor → 16 → 50 → 17 → 49 → 51 → 52 → 21 → 20 → 25 → arquitetura técnica → product spec → specs temáticas → ledger.
**Referências:** [73 — identidade chat-first](./73-chat-first-visual-identity-and-message-anatomy-specification.md), [75 — mensagem DÉLIA](./75-assistant-message-visual-specification.md), [69 — experiência conversacional](./69-conversation-experience-ux-wireframes-and-activity-plan.md), [70 — atividade](./70-tool-activity-and-source-transparency-ux-specification.md), [74 — composer](./74-message-composer-visual-specification.md).

## 1. Decisão de identidade — Opção A

**REQUIRED:** preservar o símbolo `Sparkles` (estrela principal e brilhos secundários) atualmente usado pela DÉLIA; fundo circular azul institucional com contraste apropriado, identidade reconhecível quando estática, em claro e escuro. Animações são incrementais e discretas: não substituir permanentemente o símbolo por ondas, órbitas, rosto ou mascote. **FORBIDDEN:** logo da Minha DELPI como avatar da DÉLIA; olhos, emoções atribuídas à IA, mascote não aprovado, movimento incessante, mudança de marca por estado, usar movimento para insinuar autorização, execução de ferramenta específica ou raciocínio privado.

**Forma:** círculo plano ou gradiente muito sutil derivado de tokens legítimos `--primary` e esquema de contraste Portal/plugin-ui; `Sparkles` centrado com espessura consistente em 24–64px. O halo de atividade é camada separada, opcional, não parte permanente do glyph. Sem texto dentro do círculo. `DÉLIA` é rótulo externo quando contexto não identifica o autor.

## 2. Unified Avatar — responsabilidades e fronteiras

Modelo conceitual, **não exigência de criar cinco componentes novos**:

```text
UnifiedAvatar (UI, provider-neutral)
 ├─ AvatarImage (imagem autorizada/fallback)
 ├─ AvatarIdentity (rótulo e nome acessível)
 ├─ AvatarStatus (estado semântico comprovado)
 ├─ AvatarMotion (movimento decorativo por estado)
 └─ AvatarProfilePopover (composição sobre dados do Portal, se contrato permitir)
```

Variantes propostas: `assistant` e `person`. O `plugin-ui` possui apenas apresentação, interações acessíveis e tokens. O Portal é owner da identidade publicada, rota oficial e foto/perfil; Keycloak é identidade/SSO; Core é RBAC; DÉLIA consome perfil legitimamente publicado e observa atividade de seu próprio turno. **Não** importar componentes internos do Portal por acesso transversal não contratado; não buscar foto por ID/claim arbitrário; não criar API duplicada. Antes de implementar, exigir `EXISTING_EQUIVALENT=YES|NO|TO_INVENTORY` e `REUSE_DECISION=REUSE|EXTEND|NEW` para Avatar, Image, Popover, User Menu, Profile Card e Avatar fallback em `plugin-ui`/Portal.

## 3. Matriz de estados da DÉLIA — contrato de animação

| Estado UI | Gatilho comprovado | Movimento preferido | Encerramento |
|---|---|---|---|
| `idle` / repouso | Sem interação pendente | **Estático**; brilho fixo muito discreto permitido | Permanece idle |
| `receiving` / recebimento | Entrada entregue ao frontend, antes do pending | Uma expansão suave `scale 1→1.035→1` em 300–450 ms, uma vez | Transição para pending/idle |
| `processing` / processando | `POST /interaction/turns` realmente pendente | Halo externo de pulso lento e suave; `Sparkles` quase estático | Sai assim que request encerra/aborta; jamais spinner eterno |
| `responding` / apresentando | Resposta real sendo exibida; quando houver fase observável, não timer artificial | Brilho curto/pequena oscilação do símbolo uma vez | `idle` ao concluir apresentação |
| `attention` / atenção | Aviso real (`PRECONDITION_REQUIRED`, `SOURCE_UNAVAILABLE`, etc.) | Realce estático de borda/halo contextual; no máximo uma ênfase inicial | Rótulo/aviso persiste conforme contrato |
| `disabled` | Superfície desabilitada por condição real | Nenhuma animação; não sugerir execução | Retoma após recuperação |
| `voice_listening` (futuro) | Apenas sessão de áudio explicitamente autorizada e ativa | Anel de baixa amplitude, não inferir transcrição ou intenção | Termina ao finalizar/retirar permissão |
| `voice_speaking` (futuro) | Playback efetivamente ativo | Oscilação sutil de luminância, NÃO lip-sync fictício | Termina com áudio |
| `error` | Erro confirmado, não mera demora | Uma transição curta opcional; depois estático | Persistir status textual sem piscar |

**Não inferir `thinking`, emoções, confiança, pesquisa web ou MCP ativo só pela duração da requisição.** O avatar é presença visual, não fonte de business facts, AuthZ ou Policy. Em demonstração, `SIMULAÇÃO` visível e estado separado dos dados reais.

## 4. Motion design — valores de referência

Os números abaixo são **guidelines de design (TARGET)**, não contrato CSS congelado; adaptar aos tokens, densidade e testes reais.

| Efeito | Duração | Curva / amplitude | Repetição | Quando |
|---|---|---|---|---|
| Entrada inicial | 160–260 ms | opacidade 0→1, translado Y no máximo 3px | Uma vez | Montagem, se não gerar layout shift |
| Recebimento | 300–450 ms | scale 1→1.035→1, `ease-out` | Uma vez | Entrada recebida |
| Pulso de atividade | 1600–2200 ms/ciclo | halo borda de opacidade ≤0.35 que expande até 1.12–1.18 e desaparece | Loop **somente pending** | Processamento real |
| Micro-oscilação Sparkles | 2200–3000 ms | rotação ±3° ou brilho/opacidade discreta | Opcional, limitada ao pending | Sem competir com leitura |
| Resposta recebida | 250–420 ms | brilho/scale 1→1.025→1 | Uma vez | Resposta exibida |
| Atenção | 200–350 ms | realce de contorno contextual; zero loop | Uma vez | Aviso material |
| Hover no avatar interativo | 100–180 ms | leve realce da superfície; não acionar estado de IA | Enquanto hover | Apenas elemento clicável |
| Foco de teclado | Imediato | `focus-visible` contrastante | Até blur | Avatar acionável |
| Transição tema | 120–220 ms | cores/tokens, sem flash ou salto | Em troca real de tema | Light/dark |

**FORBIDDEN:** pulso em repouso infinito, bounce, shake de erro repetido, rotação contínua, efeitos epileptogênicos, mudança de tamanho que desloque a timeline, efeitos sonoros/voz automáticos, usar `filter` muito caro em dezenas de avatares. Preferir `transform`/`opacity`; a camada animada não interfere em hit target nem acessibilidade. `prefers-reduced-motion: reduce` desliga *todos* os loops e movimentos decorativos, mantendo cor, ícone e texto de estado legíveis. Quando aba oculta ou componente fora de viewport, reduzir/parar animação sempre que viável sem mecanismo custom complexo.

## 5. Variações por contexto e tamanho

| Uso | Dimensão de referência | Movimento |
|---|---|---|
| Recepção inicial | 52–64px | repouso estático; receiving apenas após ação real |
| Turno DÉLIA na timeline | 32–40px | no máximo pulso sutil se for o turno pending |
| Linha DÉLIA Activity | 24–32px | status preferencial no ActivityViewer; evitar **dois spinners** |
| Dock | 28–36px | mesma implementação, menor halo e boa margem de clipping |
| Cabeçalho | 32–40px | normalmente estático |
| Voz/Live futuro | definido por contrato próprio | estados de áudio somente após gate |
| Avatar do usuário na timeline | 32–40px | estático, salvo hover/focus no elemento de perfil |
| Perfil do Portal / popover | 40–56px | foto real/fallback; sem movimento de IA |

Áreas clicáveis com tamanho confortável, independentes do diâmetro gráfico. Não cortar halo em containers com `overflow:hidden`; não deixar efeito cobrir texto vizinho. O mesmo componente base deve suportar página e dock.

## 6. Avatar da pessoa — foto e fonte autorizada

**Direção de produto:** foto real do usuário proveniente de contrato oficial do Portal/perfil, reusando primitive legítima dos outros plugins. Se foto não publicada: iniciais com nome autorizado, ou `UserRound` neutro como fallback. Não fabricar URL, nome, email, cargo ou departamento; não buscar dados por claims JWT isolados. Não presumir foto disponível até inventário de rotas e props do host.

**Popover/cartão de perfil, somente quando permitido pelo contrato:** foto, nome público, cargo/área/unidade (quando publicados e permitidos), ação explícita `Abrir meu perfil` com rota oficial publicada. Desktop: hover com atraso moderado e acesso por click/Enter/Space; dispositivos touch: tap. Foco controlado e restaurado; Escape fecha; sem hover-only; `aria-haspopup` e associação apropriada; não mostrar dado não autorizado. Se rota/perfil não publicados, sem link fictício e sem popover vazio — mostrar avatar fallback.

**Privacy:** não armazenar foto/base64 em memória pessoal, prompts, embeddings ou logs comuns; image loading com fallback e tratamento de erro; impedir URL arbitrária não confiável sem validação de origem pelo owner; revogação de acesso deve ser refletida pelo host/backend.

## 7. API pública proposta (somente contrato visual)

```ts
type AvatarKind = "assistant" | "person";
type AssistantMotionState =
  | "idle" | "receiving" | "processing" | "responding"
  | "attention" | "disabled";
type UnifiedAvatarProps = {
  kind: AvatarKind;
  label: string;
  size?: "xs" | "sm" | "md" | "lg" | "xl";
  imageUrl?: string;          // apenas origem autorizada
  fallbackText?: string;      // apenas perfil publicado
  motionState?: AssistantMotionState;
  interactive?: boolean;
  onActivate?: () => void;    // callback host legítimo
};
```

API ilustrativa; confirmar convenções de compound components e exports do `plugin-ui`. Evitar misturar `imageUrl` de pessoa com controle de `motionState` da DÉLIA quando discriminated union reduzir combinações inválidas. `motionState` é status visual observado, **não** permissão, comando de domínio, "intenção" ou inferência de emoção. Eventos de voz futuros exigem extensão contratual, não ativação por heurística.

## 8. Estados da interface e fallback

- **Sem foto** → fallback imediatemente acessível; nenhuma quebra de layout.
- **Imagem carregando** → placeholder sem animação excessiva; não expor `src` em texto.
- **Imagem falhou** → fallback e observabilidade segura; não mostrar link quebrado.
- **Avatar DÉLIA idle** → identidade plena sem depender de CSS animation.
- **Resposta concluída** → sair de `processing`, inclusive em erro/timeout/abort.
- **`SOURCE_UNAVAILABLE` / `AUTHZ_DENIED`** → estado visual adequado e aviso textual no componente de mensagem/activity; avatar não deve substituir aviso.
- **Demo** → badge de simulação pertence à experiência de demo, não ao avatar isolado.
- **Claro/escuro** → invariância da forma, legibilidade e halo; usar tokens Portal/plugin-ui, incluindo `--primary`, `--surface`, `--text`, `--border`; não criar paleta paralela.

## 9. Integração com timeline, recepção, Activity e Portal

- `DeliaReception`: `UnifiedAvatar(kind=assistant, size=lg, motionState=idle)` antes de interação; sem animação repetida.
- `DeliaAssistantMessage`: avatar por turno, estado real derivado da interação; não iniciar outro spinner quando `ActivityViewer` já mostra pending.
- `ConversationTimeline`: usuário recebe `UnifiedAvatar(kind=person,...)` com foto publicada ou fallback, sem fetch direto a provider.
- `ActivityViewer`: estado principal de atividade; avatar o acompanha sem redundância excessiva.
- Portal/dock: rota e perfil apenas mediante contrato host existente, não imports internos ou autoridade paralela.
- Sem dependência de backend DÉLIA novo nesta especificação.

## 10. Testes e critério de aceite futuro

**Unit/component:** todas as sizes; assistant/person; fallback; imagem válida/inválida; label acessível; estático em idle; pulso apenas pending; encerramento de animação após request/erro; `prefers-reduced-motion`; foco/teclado; popover com/sem dados; múltiplos avatares em timeline; markup hostil inerte; URL não autorizada bloqueada pelo owner.

**Browser evidence:** light/dark; desktop; dock; narrow/mobile; zoom 200%; alto contraste; touch; scroll; não-clipping do halo; performance em timeline longa; motion off. JSdom isolado não prova geometria ou animação real. Exigir snapshot/visual e gravação curta dos estados ou inspeção CSS real quando mecanismo de teste permitir.

**Acceptance gates:** perfil/foto/rota reais identificados por `OWNER → SOURCE → CONSUMERS → CONTRACT`; nenhum dado pessoal inventado; AVATAR_DÉLIA visível sem animação; animações sem falsa telemetria; erro e AuthZ preservados; kit não acoplado a DÉLIA; no novo frontend/backends fora de escopo; regressões compartilhadas; commit/testes no SHA; ledger atualizado apenas com outcome factual. Aceite independente `ACCEPT|ACCEPT_WITH_RESIDUAL|REWORK|EXECUTION_DRIFT|INCONCLUSIVE`.

## 11. Status e decisões pendentes

- **APPROVED:** Opção A, `Sparkles` circular azul, identidade institucional, animação leve e contextual, reduced-motion, base visual comum para DÉLIA/pessoa.
- **DESIGN_SPECIFIED:** duração/amplitude/famílias de estado, variações por contexto, fallback e UI de perfil.
- **TO_INVENTORY:** componente de avatar/profile do Portal/plugin-ui, origem da imagem, props de usuário publicadas, rota oficial e possibilidade de popover governado; redução de motion efetiva, tokens aplicáveis.
- **TARGET / CONTRACT_REQUIRED:** animação de voz/Live, perfil interativo se rota não publicada, novos dados de status progressivo.
- **TEST_NOT_RUN:** testes de implementação/deploy; este documento é apenas design.
- **FORBIDDEN:** sentimento/consciência inferidos, loop não factual, tool metadata como autorização, impersonação da pessoa, dados de perfil fictícios, novo backend por conveniência.

**Próxima tarefa separada:** inventário real de avatar/profile e contrato de host → bounded implementation `plugin-ui` + integração DÉLIA, testes browser light/dark/dock, revisão e ledger. Documentação não avança a fase.
