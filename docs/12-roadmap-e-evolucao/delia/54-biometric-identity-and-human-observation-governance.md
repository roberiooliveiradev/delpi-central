# DÉLIA — Identidade Biométrica e Observação Humana Governada

**Status:** `TARGET` — thematic architecture/security/product spec  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Standalone boundary:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)  
**Multimodal/Frontline:** [`53-multimodal-meeting-frontline-and-industrial-copilot.md`](./53-multimodal-meeting-frontline-and-industrial-copilot.md)  
**Security:** [`08-security-autonomy-audit.md`](./08-security-autonomy-audit.md)

## 1. Decisão de produto

A DÉLIA poderá, quando explicitamente habilitada por política, finalidade e capability aprovadas, **reconhecer usuários conhecidos por foto/vídeo e voz**, associar participantes a identidades corporativas e observar fatos operacionais visíveis durante reuniões, treinamento e trabalho Frontline.

Isso não transforma biometria em autenticação, autorização, RBAC ou decisão trabalhista.

```text
foto/vídeo/voz
→ biometric/perceptual adapter
→ candidate identity / observable fact
→ confidence + Evidence
→ policy + user/session/context validation
→ bounded DÉLIA use
```

Nenhum adapter, store, enrollment service ou primitive é considerado implementado por esta especificação. C0 deve provar owner, fonte canônica, consumers, contrato, privacy basis, storage e lifecycle.

## 2. Objetivos legítimos de produto

Casos de uso alvo incluem:

- reconhecer um usuário previamente enrolled em terminal/posto compartilhado;
- sugerir identidade de participante em reunião para diarização/ata;
- reconhecer speaker conhecido quando policy permitir;
- personalizar contexto somente após identidade/sessão autorizada;
- associar Evidence de mídia a participante conhecido;
- observar sequência objetiva de trabalho para treinamento/melhoria de processo;
- detectar fatos operacionais observáveis formalmente definidos;
- permitir correção manual de identidade ou associação incorreta.

## 3. Biometria não é authority

Invariante:

```text
biometric match
!= authenticated session
!= Keycloak identity proof by itself
!= Core permission
!= Domain authorization
!= authorization for Business Action
```

Biometria pode ajudar a resolver candidate userRef ou atuar como sinal adicional apenas em fluxo explicitamente aprovado. Para ações sensíveis, biometria sozinha nunca é suficiente.

## 4. Enrollment explícito

Reconhecimento de usuário conhecido exige enrollment controlado pelo owner correto.

Semântica candidata, a congelar em C0:

```text
userRef
modality: face | voice
purpose
policy/legal-governance basis
createdAt
version
status
quality metadata
template/model version
retention class
revocation/deletion state
```

Preferir biometric templates protegidos em vez de mídia bruta persistente quando o caso permitir. Raw enrollment media só pode ser retido com finalidade e governance explícitas.

## 5. Face recognition

Permitida somente como **closed-set recognition/verification de usuários enrolled** dentro do escopo aprovado.

```text
camera frame
→ face detection
→ enrolled-user candidate search
→ {userRef, confidence, evidenceRef}
→ threshold/policy
→ correctable association
```

Não usar reconhecimento aberto de pessoas externas por bases desconhecidas/internet. Confidence insuficiente permanece `UNKNOWN_PERSON` ou requer confirmação.

## 6. Voice recognition / speaker identity

Distinguir rigorosamente:

```text
speech-to-text
speaker diarization
speaker recognition
voice authentication
```

São capabilities diferentes. Reconhecer voz não autentica nem autoriza write.

## 7. Vídeo e reconhecimento temporal

Tracking pode ser usado somente de forma bounded, purpose-specific e session-scoped.

Saída material deve preservar source/frame/time range, candidate userRef, confidence quando válida, model/template version, corrections e session/device context.

Não persistir vídeo bruto por default apenas porque tracking foi usado.

## 8. Human Observation

A DÉLIA pode analisar **fatos observáveis do processo**, por exemplo:

- sequência de etapas executadas;
- interação visível com máquina/ferramenta/material;
- deslocamentos relevantes ao fluxo;
- uso observável de EPI quando houver método, owner e finalidade aprovados;
- tempo entre etapas quando medido de forma válida;
- repetição/retrabalho observável;
- pedidos de ajuda;
- desvio observável de procedimento;
- prática operacional candidata a conhecimento.

Não inferir personalidade, honestidade, intenção, emoção como verdade, saúde, atributos sensíveis ou valor profissional.

Ergonomia/postura só pode ser tratada quando houver metodologia, owner e uso aprovados; caso contrário permanece fora do escopo.

## 9. Limites de people inference

Por default, proibido inferir de rosto, voz, vídeo ou comportamento:

- personalidade;
- honestidade/confiabilidade;
- intenção moral;
- lealdade;
- estado emocional como truth;
- saúde física/mental;
- diagnóstico;
- raça/etnia/religião/orientação sexual ou outros atributos sensíveis;
- aptidão profissional global;
- propensão disciplinar;
- productivity/trust/performance score oculto.

Descrição objetiva de fato observável não pode ser convertida em diagnóstico psicológico ou julgamento de caráter.

## 10. Sem decisão trabalhista automática

Biometric/Human Observation não pode ser authority automática para contratar, promover, punir, advertir, remunerar, avaliar desempenho formal, suspender ou demitir.

A DÉLIA pode organizar Evidence operacional verificável, mas não automatiza decisão trabalhista baseada em biometria ou inferências pessoais.

## 11. Identity Resolution Contracts

C0 deve avaliar se primitives como abaixo são realmente necessárias:

```text
PersonObservationRef
BiometricIdentityCandidate
BiometricEnrollmentRef
```

Qualquer shape anterior ao freeze é candidate. Não duplicar o modelo de usuário corporativo; `userRef` aponta para a authority corporativa apropriada.

## 12. Correção humana

Associação biométrica material deve ser corrigível.

Correções:

- alteram somente association/session apropriada;
- não mudam template automaticamente sem enrollment flow;
- geram audit/telemetry apropriado;
- podem alimentar candidate improvement governado.

## 13. Segurança dos templates

Biometric templates são dados de alta sensibilidade e exigem encryption, strict service access, tenant/company scope quando aplicável, ausência de exposure desnecessário ao MFE, no logging, key management, retention/revocation/deletion e audit de enrollment/match/delete.

Templates/tokens nunca vão para prompt, embeddings de conhecimento, Personal Memory ou logs comuns.

## 14. Anti-spoof / liveness

Se biometria algum dia participar de step-up verification, C0/C3 devem provar necessidade e mecanismo adequado de liveness/anti-spoof. Sem proteção suficiente, tratar biometria somente como candidate identity.

## 15. Meeting Mode

Target:

```text
provider/authenticated participant refs
+ face/voice candidate opcional
→ participant association
→ confidence/correction
→ diarized transcript / artifact refs
```

Participante não enrolled permanece label de sessão ou associação manual.

## 16. Frontline / shared devices

Target:

```text
worker approaches approved station
→ biometric candidate opcional
→ explicit approved session/login continuation
→ Keycloak/Core remain identity/RBAC authorities
→ bounded operational context
```

Nunca manter usuário anterior ativo apenas porque a câmera continua vendo alguém semelhante.

## 17. Process learning

Human Observation pode alimentar conhecimento operacional somente como candidate:

```text
observable fact
+ operational context
+ supporting Evidence
→ candidate practice/insight
→ owner/review
→ eval
→ version
→ publish
```

Nada vira procedure/policy/knowledge corporativo automaticamente.

## 18. Data minimization

Separar:

```text
raw photo/video/audio
biometric template
identity candidate
confirmed association
observable-process Evidence
knowledge candidate
```

Cada classe tem purpose/access/retention próprios.

## 19. UX obrigatória

Quando reconhecimento estiver ativo, a UI deve tornar visível câmera/microfone ativos, finalidade, estado do identity recognition, identidade reconhecida quando relevante, ambiguidade/confidence quando material, opção de corrigir/recusar associação e estado de gravação/retenção quando aplicável.

Não implementar identificação silenciosa como default.

## 20. Arquitetura

Providers concretos ficam em adapters. Ports só existem se o Abstraction Gate de `49` justificar.

Possíveis candidates:

```text
FaceIdentityPort
SpeakerIdentityPort
BiometricEnrollmentPort
HumanObservationPort
LivenessPort
```

Pipeline target:

```text
media/session ref
→ perception/biometric adapter
→ candidate identity + observable Evidence
→ policy
→ canonical userRef/context association
→ DÉLIA intelligence/work
```

Nenhum provider biométrico vira source de RBAC.

## 21. Evals obrigatórios

Quando a capability entrar em runtime, provar no SHA/config avaliado:

- enrolled positive;
- non-enrolled negative;
- look-alike negative;
- low-confidence unknown;
- wrong-speaker negative;
- spoof/replay quando aplicável;
- multi-person meeting;
- correction;
- revoked/deleted enrollment;
- model/template version change;
- quality variation por iluminação/ruído/device;
- false accept/false reject;
- unauthorized enrollment access;
- template leakage;
- cross-user/shared-device leakage;
- candidate identity cannot grant permission;
- observable fact vs hypothesis;
- no emotion/personality inference;
- no hidden worker score;
- no automatic disciplinary outcome.

Sem evidência obrigatória, `PENDING`/`INCONCLUSIVE`, nunca PASS.

## 22. Fases

### C0
Inventariar e congelar user/photo/media sources, enrollment authority, storage/keys, governance/retention, devices, participant sources, provider/data handling, thresholds/correction, liveness needs e prohibited inference classes.

### C1/C2
Preparar somente contracts/surfaces/session identity permitidos pelo freeze, sem reconhecimento automático antecipado.

### C3
Implementar biometric/perception adapters somente se priorizados e com C0 gates PASS.

### C6
Integrar reconhecimento governado a Meeting/Frontline e process-learning candidates.

### C7
Otimizar realtime/Edge/model routing somente com evidence e privacy/security gates aprovados. L5 não é concedido por biometria.

## 23. Acceptance outcomes

```text
closed-set recognition only under explicit governance
biometric result never grants permission
unknown/ambiguous remains unknown or corrected
Evidence traceable/correctable
biometric templates protected/revocable
no emotion/personality/character inference
no biometric-based automatic employment decision
Human Observation uses observable process facts only
learning creates governed candidates
shared devices do not leak identity/session data
```

## 24. Regra final

> A DÉLIA pode usar biometria para associação de identidade governada e fatos observáveis do processo, mas nunca como atalho de autenticação/autorização, julgamento psicológico ou decisão trabalhista automática.
