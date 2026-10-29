# `delpi_character_profiles` — Contrato compartilhado de especialistas DELPI

Biblioteca Python pura (stdlib only) que define **identidade narrativa,
história e relacionamentos** dos especialistas fictícios DELPI — DAVI,
VISTA, TÉO, EVA, CLARA e futuros.

> **Shared owns the structure. MCP owns the character.**

## 1. Visão geral

- `shared` define **tipos, validações, serialização, projeções e
  versionamento**.
- Cada MCP/app preenche e versiona **sua própria ficha** localmente.
- Nada aqui é fonte de verdade operacional: **ficção pura**, marcada
  `FICTION_IDENTITY_ONLY`. Não representa tools, permissões, capabilities,
  autenticação, autorização ou dependência entre serviços.
- O pacote **não contém fichas preenchidas**, não importa código de apps,
  não depende de SDK MCP/OpenAI, não faz HTTP/DB, e não possui registry.

## 2. Arquitetura

```text
shared  = contrato     → este pacote (modelos + validação + projeções)
MCP     = ficha        → CharacterProfile preenchida dentro do app dono
adapter = projeção     → como o MCP ecoa a persona na sua interface
                         (initialize instructions, agent_directives,
                         resources, paste de agente — decisão do MCP)
```

Distribuição de conhecimento mútuo: cada MCP exporta um
`CharacterPublicProfile` serializado por **mecanismo governado aprovado**
(artefato commitado, pacote de conteúdo, handoff de task — escolha do
consumer). Serviço de descoberta/sincronização MCP-to-MCP é **TARGET**,
não implementado aqui.

## 3. Referência dos modelos

| Modelo | Obrigatórios | Conteúdo |
|---|---|---|
| `Identity` | `character_id`, `name` | display_name, title, role, organization, narrative_age, gender_identity, pronouns, short_introduction |
| `Appearance` | — | traços físicos, vestuário, color_palette, avatar_reference, **avatar_status** (`UNSET`/`REFERENCE_NOT_OFFICIAL_AVATAR`/`OFFICIAL_AVATAR_APPROVED`) |
| `Personality` | — | core/secondary_traits, temperament, humor_style, curiosity, energy, social_style, strengths, quirks |
| `CommunicationStyle` | — | language (default `pt-BR`), tone, formality, verbosity, greeting, preferred_expressions, humor_frequency, explanation/clarification_style |
| `Expertise` | — | specialties, knowledge_domains, professional_role, reasoning/problem_solving_style — **nunca** tools/permissões |
| `CharacterStory` | — | origin_story, background, how_joined, mission, motivations, values, interests, habits, memories, current_story_arc, `events` |
| `StoryEvent` | `event_id`, `title` | description, narrative_date (fictícia, opcional), participants, significance, status |
| `CharacterRelationship` | `target_character_id`, `relationship_type` | description, narrative_status, since, shared_story_event_ids, visibility (`public`/`internal`) |
| `CoexistenceRules` | — | guidelines, mention_frequency, allowed_reference_contexts, forbidden_behaviors |
| `ProfessionalConduct` | — | answer_first, clarification/proactive/response/error/user_guidance/humor_boundaries |
| `CharacterProfile` | `identity` | agrega todos os acima + `profile_version`, `schema_version`, `universe`, `narrative_classification` |
| `CharacterPublicProfile` | `character_id` | resumo narrativo aprovado para intercâmbio entre MCPs |

`character_id`: slug estável `^[a-z0-9][a-z0-9_-]{0,63}$` — nunca muda;
`display_name` pode. `event_id`: `^[a-z0-9][a-z0-9_.-]{0,127}$`.

Vocabulário de relacionamentos (`RELATIONSHIP_TYPES`): `friendship`,
`colleagues`, `mentorship`, `mentee`, `romantic_partner`,
`narrative_partnership`, `friendly_rivalry`, `family`, `acquaintance`,
`other`. **Extensível**: tipos snake_case fora da lista passam com
`WARNING` — nenhuma release de contrato é necessária para um tipo novo.

Reciprocidade (`RELATIONSHIP_INVERSES`): `romantic_partner↔romantic_partner`,
`mentorship↔mentee`, `friendship↔friendship`, `colleagues↔colleagues`,
`narrative_partnership↔narrative_partnership`, `friendly_rivalry↔friendly_rivalry`.
`validate_relationship_consistency(profiles)` cruza os perfis **fornecidos**;
alvo ausente = `WARNING` unresolved (a ficha pode não estar publicada).

## 4. História dos personagens

- **Origem/biografia**: `origin_story`, `background`,
  `how_joined_organization`.
- **Trajetória**: `StoryEvent`s ordenados (`first-meeting`, `project-*`,
  `arc-*` são boas convenções de `event_id`).
- **Relacionamentos**: declare a aresta na ficha de cada lado quando o tipo
  for recíproco; `shared_story_event_ids` liga eventos compartilhados.
- **Evolução**: novos eventos/arcos não mudam o schema; o histórico vive
  no Git, não no modelo.

## 5. Conhecimento entre MCPs

```python
from delpi_character_profiles import (
    project_public_profile, public_profile_to_dict,
    public_profile_from_dict, validate_relationship_consistency,
)

public = project_public_profile(profile)          # MCP dono exporta
payload = public_profile_to_dict(public)          # artefato JSON (git)
peer = public_profile_from_dict(received_payload) # MCP consumidor valida
issues = validate_relationship_consistency([public, peer])
```

O mecanismo de publicação/transporte é do consumer (TARGET até owner +
contrato ratificados). Conhecimento mútuo é **eventual e narrativo**.

`project_persona_context` ecoa apenas o que o host precisa para *agir* como
o personagem: `identity` (character_id, name, display_name, role,
`narrative_age` **somente quando preenchida**, short_introduction),
personality/communication summaries, expertise, appearance_summary +
avatar_status, relacionamentos públicos e regras de coexistência/conduta.
Demais demografia (`gender_identity`, `pronouns`, `title`, `organization`)
e história/eventos ficam de fora do contexto por orçamento — a ficha local
permanece a fonte.

## 6. Tutorial passo a passo

1. Localize o MCP dono e suas fontes canônicas de persona/instruções.
2. Revalide HEAD (`git fetch`, `rev-parse`, `status`).
3. Leia este README e os modelos em `models.py`.
4. Crie a ficha dentro do MCP (ex.: `app/content/<mcp>_profile.py` ou JSON
   de conteúdo) — **nunca** em `shared/`.
5. Preencha `Identity` (id estável primeiro, demografia só se aprovada).
6. Preencha `Appearance` — `avatar_status` default já é não-oficial.
7. Preencha `Personality`/`CommunicationStyle` — a voz é do personagem;
   não copie o humor do DAVI.
8. Escreva `CharacterStory` + `StoryEvent`s com ids estáveis.
9. Declare `CharacterRelationship`s; use `visibility="internal"` para o
   que não deve sair na projeção pública.
10. Configure `CoexistenceRules` + `ProfessionalConduct`.
11. `validate_profile(profile)` → zero `ERROR`.
12. `project_persona_context(profile)` → integre ao canal de contexto do
    MCP (instructions/diretivas — adaptador existente).
13. `project_public_profile` → exporte se o mecanismo aprovado existir.
14. Testes: projeção, serialização, reciprocidade, e os testes de
    comportamento do próprio MCP.
15. Diff review → commit/push pelo fluxo autorizado → deploy canônico →
    verificar SHA/health → validar no ChatGPT quando acessível.

## 7. Exemplo genérico completo (executável)

```python
from delpi_character_profiles import (
    Appearance, CharacterProfile, CharacterRelationship, CharacterStory,
    CommunicationStyle, Expertise, Identity, Personality, StoryEvent,
    project_persona_context, project_public_profile, validate_profile,
)

profile = CharacterProfile(
    identity=Identity(
        character_id="omega",
        name="ÔMEGA",
        display_name="ÔMEGA — Especialista Fictício",
        role="especialista em logística narrativa",
        organization="DELPI",
        short_introduction="Fascinado por rotas e prazos.",
    ),
    appearance=Appearance(
        age_appearance="jovem adulto", hair="preto raspado",
        clothing="jaqueta cinza com detalhes laranja",
        avatar_status="REFERENCE_NOT_OFFICIAL_AVATAR",
    ),
    personality=Personality(
        core_traits=("paciente", "observador"), humor_style="quase nulo",
    ),
    communication=CommunicationStyle(tone="sóbrio", verbosity="média"),
    expertise=Expertise(specialties=("rotas", "prazos")),
    story=CharacterStory(
        origin_story="Nasceu na digitalização fictícia dos CDs.",
        events=(StoryEvent(event_id="omega-origin", title="Ativação"),),
    ),
    relationships=(
        CharacterRelationship(
            target_character_id="alpha",
            relationship_type="colleagues",
            description="Colega fictícia de inventário",
        ),
    ),
)

assert [i for i in validate_profile(profile) if i.severity == "ERROR"] == []
ctx = project_persona_context(profile)
public = project_public_profile(profile)
```

## 8. Regras de segurança

- Ficção ≠ autorização: nenhum campo libera operação, escopo ou tool.
- Projeção pública nunca carrega: credenciais, permissões, dados
  operacionais, detalhes de infraestrutura, arestas `internal`.
- Não afirmar consulta/comunicação real com outro especialista sem uma
  tool real executada — regra de comportamento do MCP, não do contrato.
- Narrativa não entra em contextos de erro/permissão/segurança quando isso
  prejudicar clareza ou seriedade (`CoexistenceRules.forbidden_behaviors`).

## 9. Versionamento

| Eixo | Onde | Política |
|---|---|---|
| `SCHEMA_VERSION` | contrato + payload da ficha | campo opcional novo = compatível; breaking = major |
| `profile_version` | cada ficha | dono do MCP incrementa a cada revisão narrativa |
| `PUBLIC_PROJECTION_VERSION` | payload público | mesma política do schema |

Consumers recebem `IncompatibleVersionError` explícito para versões não
suportadas (`assert_*_compatible`) — nunca downgrade silencioso. Campos
desconhecidos são tolerados no load não-estrito (forward compat);
`strict=True` falha explicitamente.

## 10. Troubleshooting

| Sintoma | Causa provável | Correção |
|---|---|---|
| `ModuleNotFoundError` | pacote não no path | instale o projeto `shared` (`pip install -e shared`) ou ajuste `PYTHONPATH` |
| `IncompatibleVersionError` | payload de major nova | atualize a lib ou migre o payload — decisão explícita |
| `unknown fields` (strict) | payload mais novo que a lib | rode não-estrito ou atualize |
| `WARNING` unresolved reference | ficha do colega não publicada | esperado — é eventual; publique a projeção do colega |
| `ERROR` contradiction | reciprocidade divergente | alinhe os tipos declarados nas duas fichas |

## 11. Checklist de integração e aceite

- [ ] Ficha criada **dentro** do MCP (nada em `shared/`).
- [ ] `validate_profile` sem `ERROR`.
- [ ] Aparência marcada `REFERENCE_NOT_OFFICIAL_AVATAR` salvo aprovação.
- [ ] Relações recíprocas declaradas dos dois lados (quando publicadas).
- [ ] Projeção pública sem campos internos/operacionais.
- [ ] Persona context integrado via adapter existente do MCP.
- [ ] Nenhuma tool/permissão/AuthZ alterada pela narrativa.
- [ ] `profile_version` registrada; narrativa versionada no Git.
- [ ] Deploy canônico + verificação de SHA/health (quando aplicável).
- [ ] Validação no host/ChatGPT registrada como evidência ou `TEST_NOT_RUN`.

## 12. Prompt para implementar uma ficha de personagem em qualquer MCP

```text
Você é o executor da task CHARACTER-PROFILE-{MCP_NAME}.

Entrada (preencha livremente):
  MCP_NAME:          <nome técnico do MCP/app dono>
  PERSONALITY:       <traços, humor, voz, manias>
  APPEARANCE:        <aparência narrativa de referência>
  CHARACTER_STORY:   <origem, trajetória, acontecimentos>
  RELATIONSHIPS:     <relações com outros especialistas>

Procedimento obrigatório:
1. Identifique repositório, bounded context e fontes canônicas do MCP.
2. Revalide: git fetch origin; rev-parse HEAD/origin/main; status.
3. Leia shared/delpi_character_profiles/README.md e models.py.
4. Instale/importe delpi_character_profiles no MCP conforme o empacotamento
   já existente — não crie dependência nova sem necessidade.
5. Crie a ficha CharacterProfile DENTRO do MCP (content layer ou módulo de
   domínio apropriado). NUNCA em shared/.
6. Escreva a história em CharacterStory + StoryEvents com ids estáveis.
7. Declare CharacterRelationships; respeite reciprocidade para tipos
   recíprocos; marque visibility corretamente.
8. Configure CoexistenceRules (menções ocasionais/contextuais, sem
   inventar eventos nem atribuir capabilities não provadas) e
   ProfessionalConduct (answer_first, humor bounded).
9. validate_profile → zero ERROR; documente WARNINGs aceitos.
10. project_persona_context → integre no canal de contexto já existente do
    MCP (instructions/diretivas/paste). NÃO crie tools novas.
11. project_public_profile → exporte APENAS se existir mecanismo de
    publicação aprovado; caso contrário, registre TARGET.
12. Não altere OAuth, AuthZ, tools, contratos ou permissões. Narrativa é
    ficção — nunca justificativa para integração técnica.
13. Testes: ficha válida, projeção, serialização, reciprocidade (com os
    perfis públicos disponíveis), regressão do MCP.
14. Residual search: sem acoplamento técnico, sem narrativa em regras de
    segurança/erro.
15. Diff review → commit identificado → push pelo fluxo autorizado →
    deploy canônico → verificar deployed SHA e health → validar no
    ChatGPT quando acessível (senão TEST_NOT_RUN).
16. Devolva relatório com: BASE/FINAL HEAD, arquivos, testes, projeção,
    deploy SHA, PROVEN/TO_INVENTORY, EXECUTION_DRIFT, NEXT STEP.
```
