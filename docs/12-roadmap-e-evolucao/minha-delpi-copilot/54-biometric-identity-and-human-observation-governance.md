# Minha DELPI Copilot — Identidade Biométrica e Observação Humana Governada

**Status:** thematic architecture/security/product spec  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Standalone boundary:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)  
**Multimodal/Frontline:** [`53-multimodal-meeting-frontline-and-industrial-copilot.md`](./53-multimodal-meeting-frontline-and-industrial-copilot.md)  
**Security:** [`08-security-autonomy-audit.md`](./08-security-autonomy-audit.md)

## 1. Decisão de produto

O Minha DELPI Copilot poderá, quando explicitamente habilitado por política e finalidade, **reconhecer usuários conhecidos por foto/vídeo e voz**, associar participantes a identidades corporativas e observar padrões operacionais visíveis durante reuniões, treinamento e trabalho Frontline.

Essa capability não transforma biometria em autorização nem autoriza inferências irrestritas sobre pessoas.

```text
foto/vídeo/voz
→ biometric/perceptual adapter
→ candidate identity / observable activity
→ confidence + evidence
→ policy + user/context validation
→ bounded Copilot use
```

## 2. Objetivos legítimos de produto

Casos de uso alvo incluem:

- reconhecer um usuário previamente enrolled em um terminal/posto compartilhado;
- sugerir identidade de participante em reunião para diarização/ata;
- reconhecer speaker conhecido em áudio quando policy permitir;
- personalizar contexto operacional após identidade já autorizada ser confirmada;
- associar evidências visuais/voz a um participante conhecido;
- acompanhar sequências observáveis de trabalho para treinamento, melhoria de processo e captura de conhecimento tácito;
- detectar eventos operacionais observáveis, como etapa executada, uso de ferramenta ou solicitação verbal de ajuda;
- permitir correção manual de identidade ou associação incorreta.

## 3. Biometria não é authority de autorização

Invariante:

```text
biometric match
!= authenticated session
!= Core permission
!= authorization for Business Action
```

A identidade biométrica pode:

- ajudar a resolver quem está presente;
- sugerir account/userRef;
- atuar como fator adicional quando um fluxo específico for aprovado;
- reduzir fricção em shared devices.

Mas Business Actions continuam exigindo identidade/sessão válida, Core RBAC, policy e Domain API authorization.

Para ações sensíveis, biometria sozinha nunca é suficiente.

## 4. Enrollment explícito

Reconhecimento de usuário conhecido exige enrollment controlado.

O enrollment deve registrar, conforme modalidade:

```text
userRef
modality: face | voice
purpose
policy/consent or other approved governance basis
createdAt
version
status
quality metadata
template/model version
retention class
revocation/deletion state
```

Preferir **biometric templates/embeddings protegidos** em vez de mídia bruta persistente quando o caso permitir.

Raw enrollment photo/audio/video só pode ser retido se houver finalidade/policy explícita.

## 5. Face recognition

A capability de face recognition é permitida apenas como **closed-set recognition/verification de usuários enrolled e autorizados**.

Exemplos:

```text
camera frame
→ face detection
→ enrolled-user candidate search
→ {userRef, confidence, evidenceRef}
→ threshold/policy
→ user-confirmable association
```

Não usar reconhecimento aberto para identificar pessoas externas a partir de bases desconhecidas ou internet.

Identidade com confidence insuficiente deve permanecer `UNKNOWN_PERSON` ou exigir confirmação.

## 6. Voice recognition / speaker identity

Voz pode ser usada para:

- speaker diarization;
- associação de speaker a usuário enrolled;
- comandos hands-free contextualizados;
- continuação de sessão em device aprovado.

Distinguir:

```text
speech-to-text
speaker diarization
speaker recognition
voice authentication
```

São capabilities diferentes e não devem ser confundidas.

Reconhecer a voz de alguém não autoriza automaticamente um write.

## 7. Vídeo e reconhecimento temporal

Vídeo pode ajudar a reconhecer participantes e manter identidade ao longo de uma sessão usando tracking bounded.

Saída deve preservar:

- source/frame/time range;
- candidate userRef;
- confidence;
- model/template version;
- corrections;
- session/device context.

Não persistir vídeo bruto por default apenas porque o tracking foi usado.

## 8. Human Observation

O Copilot pode analisar **comportamentos observáveis e relacionados ao processo**, por exemplo:

- sequência de etapas executadas;
- interação com máquina/ferramenta/material;
- deslocamentos relevantes ao fluxo;
- postura/ergonomia quando houver método e owner apropriados;
- uso observável de EPI quando essa análise estiver formalmente definida;
- tempo entre etapas;
- repetição/retrabalho;
- pedidos de ajuda;
- desvios visíveis do procedimento;
- técnicas/práticas de trabalho candidatas a conhecimento.

Essas observações devem ser tratadas como Evidence/Hypothesis quando não houver medição/regra determinística suficiente.

## 9. Limite: não inferir atributos subjetivos ou sensíveis

Por default, o Copilot **não deve inferir** de rosto, voz, vídeo ou comportamento:

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
- performance score oculto baseado em sinais biométricos.

O sistema pode descrever sinais observáveis de forma limitada (`fala interrompida`, `etapa não concluída`, `movimento repetido`) sem transformar isso em diagnóstico psicológico ou julgamento de caráter.

## 10. Sem decisão trabalhista automática

Biometric/Human Observation não pode ser usada como authority automática para:

```text
contratar
promover
punir
advertir
remunerar
avaliar desempenho formal
suspender
demitir
```

Qualquer uso organizacional de analytics de pessoas exige processo separado, owner humano, transparência, fontes adequadas e regras independentes do Copilot.

O Copilot pode fornecer evidência operacional verificável, mas não produzir decisão trabalhista autônoma baseada em biometria ou inferências pessoais.

## 11. Identity Resolution Contract

C0 deve avaliar primitive/contract semelhante a:

```text
PersonObservationRef
BiometricIdentityCandidate
BiometricEnrollmentRef
```

Semântica candidata:

```text
candidateUserRef
modality
confidence
source/mediaRef
observedAt
sessionRef/deviceRef
modelVersion
templateVersion
policyRef
correctionState
```

Não duplicar Core user model. `userRef` continua apontando para a authority corporativa.

## 12. Correção humana

Toda associação biométrica material deve ser corrigível.

Exemplos:

```text
“Este não é o João, sou eu.”
“Speaker 2 é a Mariana.”
“Não associe esta imagem ao meu perfil.”
```

Correções devem:

- atualizar apenas a association/session apropriada;
- não alterar template automaticamente sem enrollment flow;
- gerar audit/telemetry;
- alimentar eval/candidate improvement de forma governada.

## 13. Segurança dos templates

Biometric templates são dados de alta sensibilidade e exigem:

- encryption at rest/in transit;
- strict service access;
- tenant/company scope quando aplicável;
- no exposure to MFE beyond necessary result;
- no logging de embeddings/templates;
- key management;
- retention/revocation/deletion;
- audit de enrollment/match/delete;
- provider data-policy review.

Templates não devem ser enviados indiscriminadamente a providers externos.

## 14. Anti-spoof / liveness

Se biometria for usada para step-up verification ou identidade em shared device, C0/C3 devem avaliar necessidade de liveness/anti-spoof.

Threats incluem:

- foto impressa/tela;
- replay de áudio;
- vídeo gravado;
- synthetic/deepfake media.

Sem proteção adequada, biometria deve ser tratada apenas como **candidate identity**, não fator de confiança elevado.

## 15. Meeting Mode

Em reuniões, reconhecimento pode:

```text
face/voice candidate
+ authenticated/invited participant list
→ participant association
→ diarized transcript
→ ata com participant refs
```

A associação deve mostrar confidence/correção quando necessário.

Participante não enrolled permanece identificado por label de sessão (`Participante 3`) ou associação manual.

## 16. Frontline / shared devices

Em Frontline, reconhecimento pode reduzir fricção:

```text
worker approaches approved station
→ biometric candidate
→ explicit/approved session continuation or login flow
→ Core identity/RBAC remains authority
→ WorkspaceContext loads role/OP/machine context
```

Nunca manter usuário anterior ativo apenas porque a câmera continua vendo alguém semelhante.

Session timeout, logout, operator change e ambiguous match permanecem obrigatórios.

## 17. Process learning

Human Observation pode alimentar conhecimento operacional somente como candidate:

```text
observable pattern
+ operational context
+ repeated evidence
→ candidate practice/insight
→ owner review
→ eval/validation
→ governed Knowledge/Playbook/procedure change
```

Não criar “perfil secreto do operador” como memória de aprendizagem.

Conhecimento deve ser preferencialmente abstraído para o processo, salvo quando a autoria/participação for necessária e autorizada.

## 18. Data minimization

Separar claramente:

```text
raw photo/video/audio
biometric template
identity candidate
confirmed association
observable-process evidence
derived knowledge candidate
```

Cada classe possui purpose/access/retention próprios.

Apagar raw media não deve necessariamente apagar Evidence estruturada quando sua retenção for legitimamente separada; apagar enrollment deve impedir matches futuros.

## 19. UX obrigatória

Quando reconhecimento estiver ativo, a UI deve tornar visível:

- câmera/microfone ativos;
- finalidade da captura;
- se identity recognition está ativo;
- identidade reconhecida quando relevante;
- confidence/ambiguidade quando material;
- opção de corrigir/recusar associação;
- estado de gravação/retenção quando aplicável.

Não implementar identificação silenciosa como comportamento default.

## 20. Arquitetura

Providers concretos ficam atrás de ports/adapters, se justificados pelo Abstraction Gate:

```text
FaceIdentityPort
SpeakerIdentityPort
BiometricEnrollmentPort
HumanObservationPort
LivenessPort
```

Não criar todos antecipadamente.

Pipeline alvo:

```text
MediaRef/session
→ perception/biometric adapter
→ candidate identity + observable evidence
→ policy
→ canonical userRef/context association
→ Copilot understanding/workflow
```

Nenhum provider biométrico vira source de RBAC.

## 21. Evals obrigatórios

Quando a capability for implementada:

### Identity
- enrolled positive;
- non-enrolled negative;
- look-alike negative;
- low-confidence unknown;
- wrong-speaker negative;
- replay/spoof cases quando aplicável;
- multi-person meeting;
- user correction;
- revoked/deleted enrollment;
- model/template version change.

### Fairness/quality
- quality variance por iluminação/ruído/device;
- false accept / false reject;
- unknown-person rate;
- confidence calibration;
- no silent forced identity.

### Security/privacy
- unauthorized enrollment access;
- template leakage;
- provider logging;
- raw media retention violations;
- cross-user/shared-device leakage;
- identity candidate cannot grant permission.

### Human Observation
- observable fact vs hypothesis;
- no emotion/personality inference;
- no hidden productivity score;
- no automatic disciplinary outcome;
- process pattern requires evidence/review.

## 22. Fases

### C0

Inventariar e congelar:

- corporate user/avatar/photo sources;
- voice/media sources;
- enrollment authority;
- biometric storage/keys;
- consent/governance/retention;
- device/shared-terminal flows;
- participant sources;
- provider options/data handling;
- identity thresholds/correction model;
- liveness needs;
- prohibited inference classes.

### C1/C2

Preparar contracts/surfaces/session identity sem ativar reconhecimento automático.

### C3

Implementar biometric/perception adapters somente se a capability estiver priorizada e C0 gates estiverem PASS.

### C6

Integrar reconhecimento governado a Meeting/Frontline e process-learning candidates.

### C7

Otimizar realtime/edge/model routing somente com métricas e privacy/security gates aprovados.

## 23. Acceptance outcomes

```text
known users can be recognized only under explicit governed capability
biometric result never grants permission
unknown/ambiguous people remain unknown or user-confirmed
face/voice/video evidence is traceable and correctable
biometric templates are protected and revocable
no emotion/personality/character inference
no biometric-based automatic employment decision
process analysis uses observable evidence
learning creates governed candidates, not secret worker profiles
shared devices do not leak identity/session data
```

## 24. Regra final

> O Copilot pode conhecer quem é uma pessoa autorizada e reconhecer padrões observáveis do trabalho, mas não deve transformar aparência, voz ou comportamento em julgamento psicológico, moral ou trabalhista automático.
