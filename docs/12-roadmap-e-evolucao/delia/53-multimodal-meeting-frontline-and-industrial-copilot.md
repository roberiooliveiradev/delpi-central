# Minha DELPI Copilot — Multimodal, Meeting, Frontline e Industrial

**Status:** thematic architecture/product spec  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Standalone boundary:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)  
**Security:** [`08-security-autonomy-audit.md`](./08-security-autonomy-audit.md)  
**UX:** [`09-ux-copilot.md`](./09-ux-copilot.md)  
**Biometric/Human Observation:** [`54-biometric-identity-and-human-observation-governance.md`](./54-biometric-identity-and-human-observation-governance.md)

## 1. Decisão de produto

O Minha DELPI Copilot não é um chat administrativo. A visão alvo é uma **interface inteligente entre as pessoas e a operação da DELPI**, disponível no escritório, em reuniões e no chão de fábrica.

Ele deve poder compreender, conforme capability, device e policy:

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

Todas as modalidades usam a mesma Copilot API, a mesma identidade de produto, os mesmos RBAC/policies e o mesmo modelo de Evidence.

Quando habilitado por policy, o Copilot também pode usar **identidade biométrica governada** para reconhecer usuários conhecidos/enrolled por face ou voz e associar observações a pessoas autorizadas, conforme `54`.

## 2. Presença para os usuários

A direção de produto é tornar o **entry point do Copilot amplamente disponível aos usuários autenticados da Minha DELPI**, condicionado à permissão de acesso do próprio Copilot.

Disponibilidade visual não significa autoridade universal.

```text
Copilot visible/available
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
Copilot effective capabilities ⊆ user effective capabilities
```

Um operador, comprador, engenheiro, gestor e diretor usam o mesmo Copilot, porém recebem capability/context/knowledge diferentes conforme suas permissões e situação de trabalho.

## 3. Surfaces canônicas

O produto possui quatro experiências principais sobre o mesmo runtime:

```text
GLOBAL      → painel lateral/contextual no Portal
WORKSPACE   → página completa para análise/trabalho prolongado
MEETING     → reunião presencial/remota com voz, tela e mídia
FRONTLINE   → operador/posto/máquina com voz, câmera e UI simplificada
```

Não são quatro agentes e não são quatro backends.

```text
4 surfaces
→ same Copilot identity
→ same Copilot API
→ same policy/RBAC
→ same Evidence/Work runtime
```

## 4. Copilot Global

Uso cotidiano administrativo e técnico:

- perguntas sobre a tela atual;
- navegação;
- consulta a APIs;
- análise;
- ações governadas;
- acompanhamento de Tasks/Cases/Inbox/Watch;
- anexos e mídia pontual.

## 5. Copilot Workspace

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
- dados consultados nas APIs da Minha DELPI.

### 6.2 Comportamento

Durante a reunião o Copilot pode:

- transcrever;
- responder perguntas com dados reais;
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
→ decisões
→ ações propostas
→ responsáveis/prazos quando confirmados
→ Tasks/Cases/Workflows
→ acompanhamento
→ próxima reunião
```

O Copilot pode gerar uma ata automaticamente, porém **extrair uma ação da conversa não significa executá-la**.

Exemplo:

```text
“João vai revisar o sensor amanhã”
→ candidate action
→ usuário revisa/confirma
→ Decision Gate/Business Action quando aplicável
→ Task/solicitação criada
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

Por padrão, aplicar **data minimization**: não reter mídia bruta quando transcript/evidence derivado atende ao propósito e à policy.

## 8. Participantes e identidade em reunião

Identidade de participantes deve combinar fontes explícitas e, quando habilitado, reconhecimento biométrico governado.

Fontes preferenciais:

- usuários autenticados;
- convite/lista da reunião;
- presença declarada;
- associação manual corrigível;
- face/voice candidate de usuários previamente enrolled conforme `54`.

Pipeline permitido:

```text
authenticated/invited participants
+ face/voice candidate
→ participant association
→ confidence/correction
→ diarized transcript / participant refs
```

Biometria **não substitui autenticação, RBAC ou Decision Gate**. Pessoa não enrolled, ambígua ou abaixo do threshold permanece `UNKNOWN_PERSON`/label de sessão até confirmação.

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

Exemplo:

```text
Operador autenticado ou biometricamente reconhecido como candidate
+ posto/terminal
+ OP
+ operação
+ máquina
+ produto/revisão
→ user/session validation
→ WorkspaceContext operacional
→ Copilot
```

## 10. Contexto operacional

Não criar um segundo modelo paralelo de contexto.

Máquina, OP, operação, produto, lote, ferramenta, posto e material devem ser representados preferencialmente por `EntityRef` dentro do `WorkspaceContext`, com source owner conhecido.

Exemplo conceitual:

```json
{
  "appId": "production",
  "routeId": "operation-execution",
  "entityRefs": [
    {"entityType": "productionOrder", "entityId": "583922", "sourceSystem": "production-api"},
    {"entityType": "machine", "entityId": "PRESS-04", "sourceSystem": "maintenance-api"},
    {"entityType": "product", "entityId": "90264238", "sourceSystem": "api-delpi"}
  ]
}
```

Device/post metadata pode existir como bounded session metadata, mas não substitui EntityRef/authorization.

## 11. Hands-free voice

Frontline deve suportar, quando device/policy permitirem:

```text
“próxima etapa”
“repete”
“abra o desenho”
“qual medida devo conferir?”
“registre uma ocorrência”
“chame manutenção”
“mostre o problema anterior”
```

Voz é um **transport/input modality**, não uma autoridade especial. O mesmo planner/policy/Decision Gate se aplica.

Speaker recognition, quando habilitado, apenas ajuda a resolver `userRef`; não autoriza ações por si só.

## 12. Imagem e câmera

A câmera pode ser usada para:

- mostrar peça/defeito;
- localizar região de desenho/objeto;
- assistência contextual;
- comparação com referência;
- coleta de Evidence;
- apoio ao treinamento;
- reconhecer usuário enrolled/participante quando a capability biométrica estiver habilitada;
- observar atividades/processos visíveis dentro do escopo aprovado.

Resultado visual deve carregar, quando material:

- confidence;
- limitations;
- frame/image/source;
- timestamp;
- entity/context refs;
- person/user candidate refs quando aplicável;
- model/extractor version.

Visão não pode transformar hipótese em fato.

## 13. Vídeo

Suporte a vídeo deve evoluir em níveis:

```text
V1 imagem/frame pontual
V2 vídeo curto sob demanda
V3 amostragem temporal de sessão assistida
V4 real-time/continuous assistance quando custo, rede e policy justificarem
```

Não enviar/armazenar vídeo contínuo indiscriminadamente.

Large/long video deve preferir pipeline assíncrono, segmentação e Evidence refs, evitando requests síncronos ilimitados.

Tracking de pessoa ao longo da sessão deve ser bounded, purpose-specific e não virar perfil global oculto.

## 14. Compartilhamento de tela

Meeting/Workspace podem permitir que o usuário compartilhe uma surface autorizada para contextualização.

Regras:

- consentimento explícito;
- indicator visível;
- bounded capture;
- redaction quando possível;
- nunca interpretar screen sharing como autorização de dados adicionais;
- não usar DOM automation para business actions.

## 15. Assistência ao operador

O Copilot pode combinar:

```text
instrução de trabalho
+ desenho/revisão
+ BOM/estrutura
+ OP/operação
+ histórico de qualidade
+ ocorrências
+ manutenção
+ conhecimento validado
+ câmera/voz
```

para explicar uma tarefa, responder dúvidas ou orientar investigação.

Ele não substitui interlocks, procedimentos obrigatórios, validações de qualidade ou autoridade do processo.

## 16. Treinamento contextual

Frontline pode oferecer aprendizado durante o trabalho:

- passo a passo;
- explicação de desenho;
- vídeos/procedimentos;
- perguntas de checagem;
- exemplos validados;
- ajuda por voz;
- link para especialista/Room.

Treinamento assistido não concede qualificação/certificação automaticamente. Sistemas/owners oficiais continuam authority dessa condição.

## 17. Aprender com o processo fabril

“Aprender” significa **gerar conhecimento candidato de forma governada**, não alterar comportamento automaticamente.

Fluxo:

```text
observação autorizada
+ voz/vídeo/contexto
+ dados de processo
+ person/user ref quando necessário e permitido
→ candidate insight/practice
→ Evidence
→ especialista/owner review
→ eval/validação
→ versioned Playbook/Knowledge/procedure change
→ publish/canary
```

Nunca:

```text
operador faz algo uma vez
→ Copilot muda procedimento de produção automaticamente
```

O objetivo é aprender o processo, não criar um perfil secreto do trabalhador.

## 18. Conhecimento tácito

O Copilot pode ajudar a capturar conhecimento que hoje vive apenas na experiência das pessoas.

Exemplo:

> “Quando esse material vem desse fornecedor eu verifico primeiro esta região porque já tivemos rebarba.”

O sistema pode produzir um **candidate experience/solution pattern**, vinculado a Evidence e contexto, sujeito a revisão do owner.

A autoria pode ser preservada quando necessária, porém o conhecimento publicado deve ser preferencialmente abstraído para o processo e não para julgamentos pessoais.

## 19. Identidade biométrica e análise de pessoas

O Copilot pode reconhecer usuários conhecidos por **face e voz** conforme a capability governada definida em `54`.

Permitido:

- closed-set face recognition/verification de usuários enrolled;
- speaker recognition/diarization;
- participant association em Meeting;
- shared-device identity assistance;
- observação de comportamentos objetivos ligados ao processo;
- análise de sequência de trabalho, interação com ferramentas/máquinas, repetição, etapas e desvios observáveis;
- captura de padrões operacionais para melhoria e treinamento.

Por default, não inferir de biometria/comportamento:

- personalidade;
- honestidade/confiabilidade;
- intenção moral;
- emoção como truth;
- saúde/diagnóstico;
- atributos sensíveis;
- aptidão profissional global;
- propensão disciplinar;
- score oculto de produtividade.

Também não usar biometria como autoridade automática para contratação, promoção, punição, remuneração, avaliação formal ou desligamento.

## 20. Boundary IT/OT e máquinas

Copilot **não é safety controller** e não pode virar caminho livre LLM → PLC/CNC/robô/máquina.

Regra inicial:

```text
Copilot → observar/consultar/explicar/recomendar
Copilot → preparar solicitação/ação empresarial governada
Copilot -X→ comando físico arbitrário de máquina
```

Qualquer futura atuação OT exige programa/gate separado com:

- owner de automação/engenharia;
- protocol allowlist;
- comando determinístico tipado;
- safety PLC/interlocks independentes;
- machine state/version checks;
- human authorization adequada;
- simulation/test environment;
- fail-safe/kill switch;
- audit;
- risk assessment específico.

LLM nunca substitui interlock ou lógica de segurança certificada.

## 21. Qualidade e inspeção

Computer vision/LLM pode auxiliar detecção e priorização, porém não deve declarar automaticamente aprovação/reprovação quando o processo oficial exige medição, equipamento, tolerância ou autoridade distinta.

```text
visual finding
→ Evidence/Hypothesis
→ official inspection rule/data
→ authorized decision
```

Somente uma capability explicitamente validada para inspeção automática pode atuar como decisão de qualidade.

## 22. Shared devices e identidade

Postos, tablets e salas podem ser dispositivos compartilhados.

A arquitetura precisa prever:

- usuário atual explícito;
- biometric candidate quando habilitado;
- lock/session timeout;
- troca rápida de usuário sem state leak;
- logout seguro;
- limpeza de mídia/contexto local;
- device identity separada de user identity;
- scopes limitados;
- kiosk/shared-terminal policy quando necessário.

Um device autenticado ou biometricamente reconhecido nunca substitui autorização do usuário para Business Actions.

## 23. Media architecture

A Copilot API deve esconder providers concretos atrás de ports/adapters.

Possíveis boundaries, se C0 provar necessários:

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

Não criar todos antecipadamente: cada port passa pelo Abstraction Gate de `49`.

## 24. MediaRef e provenance

C0 deve decidir se `MediaRef` é primitive compartilhado necessário.

Semântica candidata:

```text
mediaId/ref
kind: audio|image|video|screen|document
source
capturedAt
owner/session refs
retention class
consent/policy ref
content hash/version
storage ref if persisted
```

Evidence aponta para MediaRef/location quando necessário; não duplica conteúdo bruto.

Biometric template/ref deve ser modelado separadamente da mídia bruta.

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

Meeting transcript, raw audio, raw video e biometric template são classes distintas e não herdam a mesma retenção por conveniência.

## 26. Realtime e custo

Voice/video real-time precisa de budgets e backpressure.

Definir:

- max session duration;
- audio/video bitrate/frame sampling;
- concurrent sessions;
- provider quotas;
- latency targets;
- degraded mode;
- network loss behavior;
- async fallback;
- cost telemetry.

Não criar real-time contínuo como default para todo usuário.

## 27. Meeting artifact model

Meeting pode produzir:

```text
transcript ref
summary
participants refs
participant identity candidates/corrections when applicable
facts/evidence
questions
resolved/unresolved topics
decisions
candidate actions
Task/Case refs
artifact/ata ref
```

A ata deve marcar diferença entre:

- transcrição;
- resumo do Copilot;
- identidade reconhecida/confirmada;
- decisão humana confirmada;
- action executada;
- source data consultado.

## 28. Frontline artifact model

Uma sessão de assistência pode produzir:

```text
session ref
operator/user ref
biometric candidate/confirmation ref when applicable
device/workstation ref
EntityRefs (OP/machine/product/operation)
questions/answers
media/evidence refs
issues/findings
observable process patterns
escalations
candidate knowledge
Task/Case/Request refs
```

Persistir somente o necessário à finalidade e policy.

## 29. Fases C0–C7

### C0 — Foundation

Inventariar/congelar:

- browser/media APIs existentes;
- streaming/SSE/WebSocket/WebRTC candidates;
- devices compartilhados;
- meeting-room hardware/processes;
- mobile/tablet/kiosk patterns;
- media storage;
- privacy/consent/retention;
- corporate photo/avatar/user sources;
- biometric enrollment authority/storage/key management;
- face/voice provider constraints;
- identity thresholds/correction/liveness needs;
- prohibited human-inference classes;
- speech/vision provider constraints;
- network/cost budgets;
- production context sources;
- machine/OT APIs/events e boundary de segurança;
- existing training/procedure sources;
- MediaRef/biometric ref necessidade;
- shared-device identity/session rules.

### C1 — Bootstrap

MFE/API nascem preparados para capability flags, responsive/accessibility e media permission handling, sem ainda implementar Meeting/Frontline/biometric recognition completos.

### C2 — Context

WorkspaceContext suporta contexto operacional via EntityRefs e device/session metadata bounded. Identity association não substitui Core auth/RBAC.

### C3 — Intelligence Core

Implementar conforme escopo:

- speech input/output baseline;
- image/document multimodal;
- short-video/media ingestion quando priorizado;
- media Evidence/provenance;
- biometric/perception adapters quando priorizados e aprovados;
- provider adapters;
- transcription/synthesis foundations.

### C4 — Reads/Graph

Correlacionar mídia/contexto com OP, produto, máquina, lote, manutenção, qualidade e demais entities autorizadas.

### C5 — Writes/Durable

Candidate actions de voz/reunião/frontline passam por Decision Gates, idempotency e Domain APIs. Biometric match nunca substitui esses gates.

### C6 — Product Work/Ecosystem

Entregar progressivamente:

- Meeting Mode;
- ata viva;
- participant/speaker recognition governado;
- Frontline Mode;
- shared-device identity assistance;
- training assistance;
- process-observation candidates;
- Task/Case/Room/Inbox linkage;
- Organizational Knowledge promotion flow.

### C7 — Advanced/Optimization

Somente depois de evidence real:

- continuous multimodal assistance;
- advanced real-time video sampling;
- optimized biometric/realtime processing;
- room appliances/wearables;
- edge processing/model routing;
- selected automation within policy.

**OT physical actuation remains outside default C7 autonomy unless a separate industrial safety gate explicitly authorizes it.**

## 30. Acceptance outcomes

A visão está arquiteturalmente suportada quando:

```text
one Copilot across office + frontline
permission parity across surfaces
voice/image/video are modalities, not bypasses
meeting capture is explicit/consented
data retention is class-specific
operational context uses canonical EntityRefs
frontline shared-device sessions do not leak users/data
known enrolled users can be recognized under explicit policy
unknown/ambiguous people remain unknown or user-confirmed
biometric match never grants permission
media findings produce Evidence/limitations
human observation stays grounded in observable process evidence
meeting actions require governance
process learning produces candidates, not auto-rules
no emotion/personality/character inference
no biometric-based automatic employment decision
no arbitrary LLM→machine control
```

## 31. Non-goals iniciais

- gravação contínua de toda a fábrica;
- reconhecimento aberto/indiscriminado de pessoas externas ou não enrolled;
- emotion detection como truth;
- personalidade/honestidade/intenção inferidas de rosto/voz;
- scoring oculto de pessoas;
- decisão trabalhista automática baseada em biometria;
- substituir sistema de segurança de máquina;
- aprovar/reprovar peça apenas porque um LLM “viu” a imagem;
- mudar procedimento automaticamente a partir de observação;
- delegar Business Actions à automação de tela;
- manter mídia bruta/templates biométricos sem propósito/retenção definidos.

## 32. North Star ampliado

> **Minha DELPI Copilot é a interface inteligente entre as pessoas e a operação da DELPI. Está presente no escritório e na fábrica, entende texto, voz, imagem, vídeo, documentos, contexto operacional e dados empresariais; pode reconhecer usuários conhecidos sob governança explícita e compreender padrões observáveis de trabalho; ajuda pessoas a entender, decidir, executar e aprender, preservando permissões, evidências, segurança, privacidade e governança.**
