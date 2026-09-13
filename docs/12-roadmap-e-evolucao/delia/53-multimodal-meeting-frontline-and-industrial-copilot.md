# DÉLIA — Multimodal, Meeting, Frontline e Industrial

**Status:** `TARGET` — thematic architecture/product spec  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Standalone boundary:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)  
**Security:** [`08-security-autonomy-audit.md`](./08-security-autonomy-audit.md)  
**UX:** [`09-ux-copilot.md`](./09-ux-copilot.md)  
**Biometric/Human Observation:** [`54-biometric-identity-and-human-observation-governance.md`](./54-biometric-identity-and-human-observation-governance.md)

## 1. Decisão de produto

A DÉLIA não é um chat administrativo. A visão alvo é uma **interface inteligente entre as pessoas e a operação da DELPI**, disponível no escritório, em reuniões e no chão de fábrica.

Ela deve poder compreender, conforme capability, device e policy aprovados:

```text
texto
voz/áudio
imagem
câmera
vídeo curto
compartilhamento de tela
PDF/documentos/desenhos
contexto operacional
APIs/dados empresariais
```

A semântica alvo é uma única identidade de produto e um único conjunto de contratos governados. Isso **não prova** que API, media runtime, storage, adapters ou primitives já existam; C0/C1 devem congelar owner, contratos e implementação antes de qualquer afirmação `PROVEN`.

Quando habilitado por policy, a DÉLIA também pode usar **identidade biométrica governada** para reconhecer usuários conhecidos/enrolled por face ou voz e associar observações a pessoas autorizadas, conforme `54`.

## 2. Presença para os usuários

A direção de produto é tornar o entry point da DÉLIA amplamente disponível aos usuários autenticados da Minha DELPI, condicionado à permissão de acesso da própria DÉLIA.

Disponibilidade visual não significa autoridade universal.

```text
DÉLIA visible/available
+
user effective permissions
+
current context
+
capability policy
+
risk/sensitivity
=
what this user can actually see/do
```

Invariante:

```text
DÉLIA effective capabilities ⊆ user/service effective authorities
```

Um operador, comprador, engenheiro, gestor e diretor podem usar a mesma DÉLIA, porém recebem capability/context/knowledge diferentes conforme suas permissões e situação de trabalho.

## 3. Surfaces alvo

Experiências candidatas sobre o mesmo produto:

```text
GLOBAL      → painel lateral/contextual no Portal
WORKSPACE   → página completa para análise/trabalho prolongado
MEETING     → reunião presencial/remota com voz, tela e mídia
FRONTLINE   → operador/posto/máquina com voz, câmera e UI simplificada
```

Não são quatro agentes nem quatro autoridades independentes.

Target:

```text
surfaces
→ same DÉLIA product identity
→ same canonical Policy/Decision/Evidence/Work semantics
→ backend/runtime composition frozen only after C0/C1 evidence
```

## 4. Global

Uso cotidiano administrativo e técnico:

- perguntas sobre a tela atual;
- navegação;
- consulta a APIs;
- análise;
- ações governadas;
- acompanhamento de Tasks/Cases/Inbox/Watch;
- anexos e mídia pontual.

## 5. Workspace

Página completa indicada para:

- análises longas;
- cross-domain investigations;
- Business Graph;
- Evidence Board;
- multimodalidade;
- Tasks/Cases/Workflows;
- artifacts;
- administração autorizada;
- histórico e acompanhamento.

## 6. Meeting Mode

Meeting Mode é uma sessão explícita de colaboração assistida.

### 6.1 Entradas possíveis

- microfone/áudio;
- transcrição;
- câmera quando autorizada;
- compartilhamento de tela quando suportado;
- documentos apresentados;
- perguntas por voz/texto;
- dados consultados em fontes autorizadas da DELPI.

### 6.2 Comportamento alvo

Durante a reunião, quando as capabilities correspondentes existirem e estiverem autorizadas, a DÉLIA pode:

- transcrever;
- responder perguntas com dados autorizados;
- abrir indicadores/entidades;
- comparar períodos;
- registrar fatos, decisões e pendências;
- identificar ações propostas;
- produzir resumo/ata;
- associar Evidence/SourceRefs;
- preparar Tasks/Cases/Business Actions;
- associar speakers/participantes a usuários enrolled quando a capability biométrica estiver explicitamente habilitada.

### 6.3 Ata viva

A ata não deve ser apenas um documento morto.

```text
reunião
→ transcript/evidence
→ decisões confirmadas
→ ações propostas
→ responsáveis/prazos quando confirmados
→ Tasks/Cases/Workflows
→ acompanhamento
→ próxima reunião
```

A DÉLIA pode gerar uma ata, porém **extrair uma ação da conversa não significa executá-la**.

```text
“João vai revisar o sensor amanhã”
→ candidate action
→ revisão/confirmação quando necessária
→ Policy/Decision/Business Action quando aplicável
→ Task/solicitação criada por capability autorizada
```

## 7. Consentimento e indicadores de captura

Toda captura contínua de áudio/câmera/tela exige estado explícito e visível.

Exemplos de UI:

```text
Microfone ativo
Transcrição ativa
Câmera ativa
Reconhecimento de identidade ativo/inativo
Compartilhamento de tela ativo
Gravação persistente ativa/inativa
```

A policy deve distinguir:

```text
capture transient
transcription
biometric matching
raw audio retention
raw video retention
screen retention
derived artifacts/evidence retention
```

Por padrão, aplicar data minimization: não reter mídia bruta quando transcript/evidence derivado atende ao propósito e à policy.

## 8. Participantes e identidade em reunião

Identidade de participantes deve combinar fontes explícitas e, quando habilitado, reconhecimento biométrico governado.

Fontes preferenciais:

- usuários autenticados;
- convite/lista da reunião;
- presença declarada;
- associação manual corrigível;
- face/voice candidate de usuários previamente enrolled conforme `54`.

```text
authenticated/invited participants
+ face/voice candidate
→ participant association
→ confidence/correction
→ diarized transcript / participant refs
```

Biometria **não substitui autenticação, Core RBAC ou Decision Gate**. Pessoa não enrolled, ambígua ou abaixo do threshold permanece `UNKNOWN_PERSON`/label de sessão até confirmação.

## 9. Frontline Mode

Frontline Mode atende operador, técnico, inspetor, manutenção e outros usuários próximos ao processo físico.

A experiência prioriza:

- poucos elementos por tela;
- botões grandes;
- alto contraste;
- uso com luvas/touch quando necessário;
- voz/hands-free;
- resposta curta e objetiva;
- leitura em ambiente ruidoso;
- imagem/desenho em tela cheia;
- ações rápidas e seguras.

Exemplo target:

```text
operador com sessão válida
+ biometric candidate opcional
+ posto/terminal
+ OP/operação/máquina/produto
→ user/session validation
→ bounded operational context
→ DÉLIA
```

## 10. Contexto operacional

Não criar um segundo modelo paralelo de contexto.

Máquina, OP, operação, produto, lote, ferramenta, posto e material devem referenciar IDs/owners canônicos. `EntityRef`/`WorkspaceContext` só são usados conforme os contratos efetivamente congelados em C0/C2; contexto nunca concede autoridade.

Exemplo conceitual, não factual:

```json
{
  "appId": "production",
  "routeId": "operation-execution",
  "entityRefs": [
    {"entityType": "productionOrder", "entityId": "583922", "sourceSystem": "production-api"},
    {"entityType": "machine", "entityId": "PRESS-04", "sourceSystem": "maintenance-api"},
    {"entityType": "product", "entityId": "90264238", "sourceSystem": "domain-owner"}
  ]
}
```

Device/post metadata pode existir como bounded session metadata, mas não substitui EntityRef/authorization.

## 11. Hands-free voice

Frontline pode suportar, quando device/policy permitirem:

```text
“próxima etapa”
“repete”
“abra o desenho”
“qual medida devo conferir?”
“registre uma ocorrência”
“chame manutenção”
“mostre o problema anterior”
```

Voz é um **transport/input modality**, não uma autoridade especial. O mesmo Policy/Decision/AuthZ se aplica.

Speaker recognition apenas ajuda a resolver candidate identity; não autoriza ações por si só.

## 12. Imagem e câmera

A câmera pode ser usada, quando aprovada, para:

- mostrar peça/defeito;
- localizar região de desenho/objeto;
- assistência contextual;
- comparação com referência;
- coleta de Evidence;
- apoio ao treinamento;
- reconhecer usuário enrolled/participante;
- observar atividades/processos visíveis dentro do escopo aprovado.

Resultado visual material deve preservar provenance, confidence quando metodologicamente válida, limitations, frame/source/time, entity/context refs e model/extractor version.

Visão não transforma hipótese em fato.

## 13. Vídeo

Evolução target:

```text
V1 imagem/frame pontual
V2 vídeo curto sob demanda
V3 amostragem temporal de sessão assistida
V4 real-time/continuous assistance somente se custo, rede, safety e policy justificarem
```

Não enviar/armazenar vídeo contínuo indiscriminadamente. Tracking de pessoa deve ser bounded e purpose-specific, sem perfil global oculto.

## 14. Compartilhamento de tela

Meeting/Workspace podem permitir contextualização por screen sharing autorizado.

Regras:

- consentimento explícito;
- indicator visível;
- bounded capture;
- redaction quando possível;
- screen share não concede acesso adicional;
- não usar DOM automation como business authority.

## 15. Assistência ao operador

A DÉLIA pode combinar fontes autorizadas como instrução de trabalho, desenho/revisão, BOM/estrutura, OP/operação, histórico de qualidade, ocorrências, manutenção, conhecimento validado e câmera/voz.

Ela não substitui interlocks, procedimentos obrigatórios, validações de qualidade ou autoridade do processo.

## 16. Treinamento contextual

Frontline pode oferecer aprendizado durante o trabalho, conforme owner/source aprovados. Treinamento assistido não concede qualificação/certificação automaticamente; systems/owners oficiais continuam authority dessa condição.

## 17. Aprender com o processo fabril

“Aprender” significa **gerar conhecimento candidato de forma governada**, não alterar comportamento automaticamente.

```text
observação autorizada
+ voz/vídeo/contexto
+ dados de processo
→ Evidence/Hypothesis
→ knowledge candidate
→ owner/review
→ eval/validação
→ version
→ publish pelo owner correto
```

Nunca:

```text
uma observação
→ mudança automática de procedimento/policy
```

O objetivo é aprender o processo, não criar um perfil secreto do trabalhador.

## 18. Conhecimento tácito

A DÉLIA pode ajudar a capturar experiência individual como **candidate insight/practice**, vinculada a Evidence e contexto, nunca como regra corporativa automática.

A autoria pode ser preservada quando necessária; o conhecimento publicado deve seguir owner, review, eval, version e publish.

## 19. Identidade biométrica e observação de pessoas

A DÉLIA pode reconhecer usuários conhecidos por face/voz somente conforme a capability governada definida em `54`.

Permitido:

- closed-set recognition/verification de usuários enrolled;
- speaker recognition/diarization;
- participant association;
- shared-device identity assistance;
- fatos observáveis do processo;
- sequência de trabalho, interação com ferramentas/máquinas, repetição, etapas e desvios observáveis quando metodologicamente definidos.

Por default, não inferir personalidade, honestidade, intenção moral, emoção como truth, saúde, atributos sensíveis, aptidão profissional global, propensão disciplinar ou score oculto de produtividade.

Biometria/Human Observation não é authority automática para decisão trabalhista.

## 20. Boundary IT/OT e máquinas

DÉLIA **não é safety controller** e não pode virar caminho livre LLM/voz/visão → PLC/CNC/robô/máquina.

```text
DÉLIA → observar/consultar/explicar/recomendar
DÉLIA → PREPARE ação empresarial governada
DÉLIA -X→ comando físico arbitrário de máquina
```

Qualquer futura atuação OT exige iniciativa/gate separado com owner industrial, comandos determinísticos tipados, interlocks independentes, state/precondition checks, autorização apropriada, ambiente de teste/simulação, fail-safe/kill switch, audit e risk assessment específico.

## 21. Qualidade e inspeção

Computer vision/LLM pode auxiliar detecção e priorização, porém não deve declarar automaticamente aprovação/reprovação quando o processo oficial exige medição, equipamento, tolerância ou autoridade distinta.

```text
visual finding
→ Evidence/Hypothesis
→ official inspection rule/data
→ authorized decision
```

## 22. Shared devices e identidade

Postos, tablets e salas podem ser dispositivos compartilhados. Prever usuário atual explícito, candidate identity opcional, timeout/logout, troca de usuário sem leak, limpeza local, device identity separada de user identity e policy de kiosk/shared terminal quando necessária.

Biometric match nunca substitui autorização para Business Actions.

## 23. Media architecture

Providers concretos ficam em adapters. Ports só são criados quando o Abstraction Gate de `49` provar boundary, consumer/variation e lifecycle/test-double reais.

Possíveis candidates, não contratos aprovados:

```text
SpeechToTextPort
TextToSpeechPort
MediaIngestPort
VisionAnalysisPort
RealtimeMediaSessionPort
MediaStoragePort
DeviceContextPort
FaceIdentityPort
SpeakerIdentityPort
HumanObservationPort
```

## 24. MediaRef e provenance

C0 deve decidir se `MediaRef` é primitive compartilhado necessário. Qualquer shape antes disso é candidate.

Biometric template/ref deve permanecer separado da mídia bruta.

## 25. Retention e mídia

Para cada modalidade definir antes do runtime:

```text
purpose
capture mode
raw retention yes/no
retention duration
transcript retention
biometric template retention
artifact/evidence retention
who can access
redaction
export/download policy
delete/anonymize
provider data handling
```

Meeting transcript, raw audio, raw video e biometric template são classes distintas.

## 26. Realtime e custo

Voice/video real-time precisa de budgets e backpressure. Não criar real-time contínuo como default para todo usuário.

## 27. Meeting artifact model

Um artifact de Meeting pode referenciar transcript, summary, participants, identity candidates/corrections, facts/evidence, questions, decisions confirmadas, candidate actions, Task/Case refs e ata.

Distinguir explicitamente transcrição, síntese da DÉLIA, identidade candidata/confirmada, decisão humana confirmada e action executada/verificada.

## 28. Frontline artifact model

Uma sessão pode produzir refs de session/operator/device/entities, questions/answers, media/evidence, issues/findings, observable process patterns, escalations, knowledge candidates e Task/Case/Request refs.

Persistir somente o necessário à finalidade e policy.

## 29. Fases C0–C7

### C0 — Foundation

Inventariar e congelar media/device/biometric/privacy/storage/provider/network/OT owners, fontes e contratos. Nenhum runtime multimodal/biométrico é `PROVEN` apenas por esta documentação.

### C1 — Bootstrap

Bootstrap deve suportar futuras capability flags, responsive/accessibility e permission handling conforme contratos congelados, sem antecipar Meeting/Frontline/biometric runtime.

### C2 — Context

Contexto operacional usa refs canônicas e bounded device/session metadata. Identity association não substitui Keycloak/Core/Domain authorization.

### C3 — Intelligence foundations

Implementar somente capabilities priorizadas após C0, com adapters provider-neutral e Evidence/provenance conforme owner/contrato real.

### C4 — Reads/Analysis

Correlacionar mídia/contexto com entities e fontes autorizadas sem duplicar domain truth.

### C5 — Governed ACT

Candidate actions de voz/reunião/frontline podem alcançar L4 governed ACT quando explicitamente autorizadas, com live AuthZ, Policy/Decision, idempotency, audit e Outcome verification. Technical execution permanece no Automation Hub/approved executor boundary; biometric match nunca substitui gates.

### C6 — Product Work/Ecosystem

Meeting/Frontline/participant association/shared-device assistance/process-observation candidates podem evoluir como product experiences. Watch permanece `OBSERVE|ADVISE|PREPARE` por default e não dispara ACT autonomamente.

### C7 — Advanced/Optimization

Continuous multimodal, advanced realtime/Edge e selected autonomous ACT/L5 somente com evidence e gates próprios. L5 OFF por default.

**OT physical actuation permanece fora da autonomia empresarial padrão e exige gate específico de segurança industrial.**

## 30. Acceptance outcomes

Quando a capability estiver em escopo, provar no SHA/config avaliado:

```text
one DÉLIA product identity across approved surfaces
permission parity across surfaces
voice/image/video are modalities, not authority bypasses
meeting capture is explicit/consented
data retention is class-specific
operational context uses canonical refs
shared-device sessions do not leak users/data
known enrolled users recognized only under explicit policy
unknown/ambiguous people remain unknown or corrected
biometric match never grants permission
media findings produce Evidence/limitations
human observation stays grounded in observable process facts
meeting actions require governance
process learning produces candidates, not auto-rules
no emotion/personality/character inference
no biometric-based automatic employment decision
no arbitrary LLM→machine control
```

Sem evidência obrigatória, resultado permanece `PENDING`/`INCONCLUSIVE`, nunca PASS.

## 31. Non-goals iniciais

- gravação contínua de toda a fábrica;
- reconhecimento aberto/indiscriminado de pessoas externas ou não enrolled;
- emotion detection como truth;
- personalidade/honestidade/intenção inferidas de rosto/voz;
- scoring oculto de pessoas;
- decisão trabalhista automática baseada em biometria;
- substituir sistema de segurança de máquina;
- aprovar/reprovar peça apenas porque um modelo “viu” a imagem;
- mudar procedimento automaticamente a partir de observação;
- delegar Business Actions à automação de tela;
- manter mídia bruta/templates biométricos sem propósito/retenção definidos.

## 32. North Star ampliado

> **DÉLIA é a interface inteligente entre as pessoas e a operação da DELPI. A visão alvo cobre escritório e fábrica, texto, voz, imagem, vídeo, documentos, contexto operacional e dados empresariais, preservando permissões, evidências, segurança, privacidade, safety industrial e governança.**
