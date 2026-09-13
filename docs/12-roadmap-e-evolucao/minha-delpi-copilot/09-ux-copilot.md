# 09 — UX do Minha DELPI Copilot

**Standalone boundary:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)  
**Multimodal/Meeting/Frontline:** [`53-multimodal-meeting-frontline-and-industrial-copilot.md`](./53-multimodal-meeting-frontline-and-industrial-copilot.md)  
**Biometric/Human Observation:** [`54-biometric-identity-and-human-observation-governance.md`](./54-biometric-identity-and-human-observation-governance.md)  
**Internet/External Connectors:** [`55-internet-research-and-external-connectors.md`](./55-internet-research-and-external-connectors.md)

## 1. Princípio

O Copilot deve parecer parte do trabalho real, não apenas uma janela de chat. Texto, voz, mídia, dados DELPI, internet e fontes conectadas convergem para a mesma experiência, com provenance e governança visíveis quando materiais.

## 2. Surfaces

```text
GLOBAL
WORKSPACE
MEETING
FRONTLINE
```

Mesma Copilot API/MFE/policy/state. Nenhuma surface cria outro agente/runtime.

## 3. Fontes visíveis

Quando útil, a resposta deve deixar claro de onde veio a informação:

```text
Minha DELPI
Internet
Outlook / Microsoft 365
Gmail / Google Workspace
WhatsApp Business
Drive / OneDrive / SharePoint
outra fonte conectada
```

Fonte externa não deve ser apresentada como dado oficial DELPI sem classificação adequada.

## 4. Research UX

Exemplo:

> “Pesquise na internet a norma mais recente e compare com nosso procedimento.”

Activity pode mostrar:

```text
Consultando procedimento interno
Pesquisando fontes externas
Abrindo fontes relevantes
Comparando versões
Preparando resposta
```

Resultado deve permitir progressive disclosure de:

- source/title/provider;
- data/freshness;
- Evidence usada;
- conflito entre fontes;
- classificação como fonte interna oficial, externa oficial, referência pública ou conteúdo não verificado.

## 5. Connections UX

O Copilot deve possuir surface de **Conexões** dentro do próprio produto.

Exemplo:

```text
Conexões

Microsoft 365        Conectado
Gmail                 Não conectado
WhatsApp Business     Administrado pela empresa
Google Drive          Conectado via Google Workspace
```

Para cada conexão mostrar, quando material:

- owner/type (`Pessoal`, `Organizacional`, `Compartilhado`, `Serviço`);
- conta/resource label;
- capabilities/scopes concedidos em linguagem humana;
- data da última validação/sync;
- status;
- reconnect/revoke/disconnect;
- política de compartilhamento/retenção relevante.

Nunca exibir token/secret.

## 6. Connect flow

```text
[Conectar Microsoft 365]
→ explicar o que será acessado
→ provider authorization/consent
→ retorno ao Copilot
→ status da conexão
```

Se um scope adicional for necessário depois, a UI deve pedir nova autorização; nunca elevar silenciosamente.

## 7. Personal versus organizational UX

O usuário deve saber quando está usando uma fonte pessoal/delegada.

Exemplo:

```text
Fonte: Gmail conectado por você
Visibilidade: somente você
```

Compartilhar em Case/Room ou promover para Knowledge deve ser uma ação explícita e mostrar o impacto.

## 8. External search/read UX

Exemplos naturais:

> “Ache no Outlook a última conversa com o fornecedor ACME sobre o item 90264238.”

> “Procure no Gmail o orçamento que recebi ontem e compare com a última OC.”

> “Busque no OneDrive o certificado deste lote.”

Resultado pode trazer cards de recurso com source, data, participantes, attachment refs e ações permitidas.

Se source não estiver conectado ou scope faltar, explicar isso sem fingir que o dado não existe.

## 9. Draft versus Send UX

Separação visual obrigatória:

```text
RASCUNHO GERADO
[Editar]
[Revisar fontes]
[Enviar]
```

Gerar rascunho não envia nada.

Antes de send material, mostrar conforme policy:

```text
De: conta/conexão
Para: destinatários
Assunto/canal
Conteúdo
Anexos
Fonte/contexto usados
Gate requerido
```

Send segue Decision Gate e apresenta outcome real.

## 10. External outcome UX

Estados explícitos:

```text
RASCUNHO
AGUARDANDO CONFIRMAÇÃO
ENVIANDO
ENVIADO / CRIADO / ATUALIZADO
FALHOU
RESULTADO INCERTO — verificando
```

Nunca mostrar sucesso antes de provider outcome verificável.

## 11. Provider event / Watch UX

Usuário pode pedir:

> “Me avise quando o fornecedor responder.”

Item de Watch deve mostrar:

- source/connection;
- condição;
- modo `OBSERVE | ADVISE | ACT`;
- expiry/status;
- o que acontecerá ao disparar;
- como pausar/desabilitar.

Se subscription/connection ficar stale, mostrar degraded state em vez de falsa tranquilidade.

## 12. External Knowledge UX

Depois de pesquisa ou leitura externa, o usuário pode ter opções distintas:

```text
[Usar somente nesta conversa]
[Anexar como Evidence ao Case]
[Salvar como conhecimento pessoal candidato]
[Propor para conhecimento organizacional]
```

A última opção inicia governance/review; não publica automaticamente.

## 13. Meeting Mode

Meeting pode consultar DELPI + internet + sources conectadas autorizadas. A ata distingue:

```text
transcript
resumo
fonte interna/externa
decisão humana
ação candidata
ação executada
```

External send citado em reunião ainda precisa do mesmo review/gate.

## 14. Frontline Mode

Frontline mantém UI large-touch/hands-free e prioriza procedimento/desenho/revisão interna vigente. Internet/external sources podem complementar, mas não substituir silenciosamente authority operacional interna.

## 15. Biometric UX

Quando habilitado:

```text
UNKNOWN → CANDIDATE → CONFIRMED/CORRECTED
```

Biometric association é visível/corrigível e nunca apresentada como permission grant.

## 16. Activity operacional

Mostrar estado verificável, não CoT:

```text
Consultando Minha DELPI
Pesquisando internet
Consultando Outlook
Lendo arquivo conectado
Analisando Evidence
Gerando rascunho
Aguardando confirmação
Enviando
Verificando resultado
Aguardando resposta externa
```

## 17. Evidence/Sources

Progressive disclosure pode mostrar:

- source system/provider;
- account/connection label sem credential;
- entity/resource;
- timestamp/freshness;
- page/region/frame/time range;
- confidence/limitations;
- internal versus external authority classification.

## 18. Decision Gate UX

Exibir ação, target, mudanças/impacto, Evidence, risk, connection/source e gate. Não esconder external write atrás de texto, voz ou gesture ambíguo.

## 19. Context chips

Exemplos:

```text
Portal Comercial · Cliente 000123 · Filial 01
Outlook · thread fornecedor ACME
Internet · pesquisa de norma atual
Case Q-2026-0042
```

Usuário pode remover/corrigir contexto.

## 20. Reload/logout/user switch

- pending send nunca executa automaticamente;
- provider token nunca fica no browser state;
- user switch limpa resources/caches locais do usuário anterior;
- source/connection permissions são revalidadas;
- media capture não reinicia silenciosamente;
- Chat offline não altera Copilot.

## 21. Error UX

Distinguir:

```text
not_connected
consent_required
scope_missing
connection_expired
permission_revoked
provider_unavailable
rate_limited
resource_not_found
external_access_blocked
subscription_stale
waiting_for_decision
```

Não confundir `provider indisponível` com `não existem resultados`.

## 22. Privacy UX

Mostrar quando necessário:

- qual conta/source será consultada;
- se source é pessoal ou organizacional;
- se dado será compartilhado/persistido;
- scopes/capabilities em linguagem humana;
- como desconectar/revogar;
- quando external data está sendo promovida para Knowledge.

## 23. Accessibility

Keyboard/focus/screen-reader/contrast/live regions/captions/large-touch/non-voice fallback continuam obrigatórios. Connection/Decision/send UIs precisam ser acessíveis.

## 24. UX success

O usuário deve conseguir evoluir naturalmente:

```text
pergunta
→ pesquisa interna/externa
→ Evidence
→ draft/action
→ Decision
→ Task/Case/Watch
→ follow-up externo
→ Knowledge candidate
```

sem precisar conhecer APIs, escolher agentes ou entender diferenças técnicas entre Gmail, Outlook, WhatsApp Business e futuros providers.
