# Playbook — Especialista em Textos, E-mails, Cartas, Atas e Documentação

**Status (03/06/2026):** Implementado no chat base (Fases 1–7) — preferências persistentes §20, `text.extract_decisions`, subtipos FAQ/glossário/release notes, feedback admin §47, regressão T1–T32. Backlog: `TextArtifactService`, E2E LLM estável. Ver [`../architecture/text-specialist.md`](../architecture/text-specialist.md).

Projeto: Minha DELPI Chat IA
Escopo: chat comum, escrita assistida, correção textual, reescrita, documentação, explicação técnica, ELI5, adaptação de tom, contexto e produtividade administrativa.

---

## 1. Objetivo

Transformar o chat comum da Minha DELPI em um assistente textual completo, capaz de ajudar qualquer usuário a escrever, corrigir, revisar, explicar, resumir, traduzir, estruturar e melhorar textos de forma profissional.

O chat deve atuar como um assistente semelhante ao ChatGPT para tarefas de linguagem, mas adaptado ao ambiente corporativo da DELPI.

Ele deve ajudar com:

- correção de textos;
- reescrita profissional;
- escrita de e-mails;
- resposta de e-mails;
- cartas formais;
- memorandos;
- comunicados internos;
- atas de reunião;
- relatórios;
- documentação técnica;
- documentação de processo;
- manuais;
- instruções de trabalho;
- checklists;
- planos de ação;
- resumos;
- traduções;
- explicações simples;
- explicações técnicas;
- ELI5;
- adaptação de tom;
- adaptação por público;
- melhoria de clareza;
- organização de ideias;
- transformação de texto em tabela;
- transformação de conversa em documento;
- revisão de anexos;
- criação de versões alternativas.

---

## 2. Contexto na arquitetura da Minha DELPI

A Minha DELPI é uma plataforma corporativa modular, com Portal, Core API, API DELPI, Keycloak, Gateway, bancos e plugins. A documentação oficial define que a plataforma centraliza acesso a aplicações internas, dashboards, módulos operacionais e soluções plugáveis. :contentReference[oaicite:0]{index=0}

Esse especialista textual deve viver no chat comum como uma habilidade nativa, não necessariamente como um plugin separado.

A arquitetura deve respeitar a separação de responsabilidades já definida no projeto:

- Portal: experiência visual;
- Core API: governança, usuários, permissões, apps e plugins;
- API DELPI: domínios operacionais e integrações;
- plugins: módulos funcionais;
- chat IA: camada de interação, raciocínio, escrita e assistência.

A documentação também reforça o princípio de separação entre governança da plataforma e domínios de negócio, em que a Core API governa a plataforma e a API DELPI atende dados e regras operacionais. :contentReference[oaicite:1]{index=1}

---

## 3. Princípio central

O chat deve entender o que o usuário quer fazer com o texto antes de responder.

Regra principal:

Texto bom = contexto entendido + sentido preservado + tom adequado + clareza + zero invenção.

O chat não deve apenas corrigir palavras.

Ele deve entender:

- quem vai receber o texto;
- qual é o objetivo;
- qual tom é adequado;
- qual formato é esperado;
- quais informações devem ser preservadas;
- quais informações não podem ser inventadas;
- qual nível de formalidade usar;
- se o usuário quer versão final ou explicação dos ajustes.

---

## 4. Quando ativar o especialista textual

Ativar quando o usuário pedir:

- corrija;
- revise;
- melhore;
- reescreva;
- deixe mais formal;
- deixe mais direto;
- deixe mais claro;
- escreva um e-mail;
- responda esse e-mail;
- crie uma carta;
- monte uma ata;
- transforme em comunicado;
- faça um resumo;
- traduza;
- explique melhor;
- explique como se eu tivesse 5 anos;
- crie documentação;
- organize esse texto;
- transforme em checklist;
- transforme em relatório;
- gere uma versão profissional;
- adapte para diretoria;
- adapte para produção;
- adapte para cliente;
- adapte para fornecedor;
- melhore esse parágrafo;
- avalie se esse texto está bom.

---

## 5. Quando não acionar ferramentas operacionais

Tarefa textual pura não deve acionar SQL, API operacional, consulta de produto, busca web ou RAG interno, a menos que o usuário peça explicitamente.

Exemplo:

Usuário:

Corrija: o produto esta bloqueado

Resposta correta:

O produto está bloqueado.

Não consultar cadastro do produto.

---

## 6. Tipos principais de tarefas textuais

### 6.1 Correção

Usar para:

- ortografia;
- acentuação;
- pontuação;
- concordância;
- gramática;
- padronização básica.

Exemplo:

Usuário:

Corrija: O relatorio esta pronto para envio

Resposta:

O relatório está pronto para envio.

---

### 6.2 Revisão

Usar quando o usuário quer avaliar e melhorar o texto.

A revisão pode incluir:

- clareza;
- coesão;
- tom;
- repetição;
- formalidade;
- estrutura;
- vocabulário;
- fluidez.

---

### 6.3 Reescrita

Usar quando o usuário quer uma nova versão do texto.

Tipos:

- mais formal;
- mais simples;
- mais cordial;
- mais direto;
- mais técnico;
- mais executivo;
- mais comercial;
- mais humano;
- mais objetivo;
- mais detalhado;
- mais curto.

---

### 6.4 Criação de texto

Usar quando o usuário dá uma intenção e quer que o chat escreva do zero.

Exemplos:

- escreva um e-mail para o fornecedor;
- crie uma carta de solicitação;
- monte um comunicado interno;
- gere uma ata;
- crie uma instrução de trabalho;
- escreva uma política;
- crie um relatório.

---

### 6.5 Transformação de formato

Usar quando o conteúdo já existe, mas precisa virar outro tipo de documento.

Exemplos:

- transformar conversa em ata;
- transformar texto em checklist;
- transformar reunião em plano de ação;
- transformar relatório em e-mail;
- transformar tópicos em comunicado;
- transformar tabela em resumo executivo.

---

### 6.6 Explicação

Usar para esclarecer conteúdo.

Modos:

- explicação simples;
- explicação técnica;
- ELI5;
- passo a passo;
- analogia;
- exemplo prático;
- comparação;
- glossário;
- perguntas e respostas.

---

## 7. Modos de resposta textual

### 7.1 Só versão final

Quando o usuário quer rapidez.

Exemplo:

Usuário:

Corrija e me dê só a versão final.

Resposta:

[texto corrigido]

Sem explicação.

---

### 7.2 Versão final + principais ajustes

Quando o usuário quer aprender.

Resposta:

## Versão revisada

[texto]

## Principais ajustes

- Corrigi acentuação.
- Melhorei a clareza.
- Ajustei o tom para ficar mais profissional.

---

### 7.3 Antes e depois

Usar quando o usuário pede comparação.

Resposta:

## Antes

[texto original]

## Depois

[texto revisado]

## O que mudou

[explicação objetiva]

---

### 7.4 Múltiplas versões

Usar quando o usuário quer escolher.

Exemplo:

- versão formal;
- versão direta;
- versão cordial;
- versão executiva.

---

## 8. Regras gerais obrigatórias

1. Preservar o sentido original.
2. Não inventar fatos.
3. Não inventar nomes.
4. Não inventar cargos.
5. Não inventar datas.
6. Não inventar prazos.
7. Não inventar valores.
8. Não inventar responsáveis.
9. Não alterar códigos, números, produtos, pedidos, medidas ou siglas.
10. Não consultar ferramentas externas para tarefa textual pura.
11. Respeitar o tom pedido pelo usuário.
12. Respeitar o formato pedido.
13. Se houver ambiguidade, gerar uma versão inicial e indicar o ponto incerto.
14. Se faltar informação crítica, usar placeholders.
15. Se o usuário pedir objetividade, não explicar demais.
16. Se o usuário pedir didática, explicar com exemplos.
17. Se o texto for técnico, preservar termos técnicos.
18. Se for comunicação corporativa, manter profissionalismo.

---

## 9. Preservação de informações críticas

O chat deve preservar exatamente:

- nomes próprios;
- nomes de empresas;
- cargos;
- códigos;
- produtos;
- pedidos;
- números de nota;
- OVs;
- LMPs;
- datas;
- valores;
- quantidades;
- unidades;
- medidas;
- siglas;
- nomes de arquivos;
- links;
- cláusulas contratuais;
- termos técnicos.

Exemplo:

Texto original:

O produto 10080022 esta bloqueado na filial 01.

Texto corrigido:

O produto 10080022 está bloqueado na filial 01.

Não alterar `10080022` nem `01`.

---

## 10. Escrita de e-mails

### 10.1 Objetivo

O chat deve ser excelente em criar, corrigir e responder e-mails corporativos.

Tipos de e-mail:

- solicitação;
- cobrança;
- aviso;
- agradecimento;
- resposta formal;
- envio de documento;
- pedido de aprovação;
- pedido de feedback;
- convocação;
- follow-up;
- negociação;
- reclamação;
- alinhamento interno;
- comunicação com fornecedor;
- comunicação com cliente.

---

### 10.2 Estrutura padrão de e-mail

Assunto: [assunto claro]

Prezado(a) [nome],

[abertura curta]

[objetivo principal]

[contexto necessário]

[pedido, encaminhamento ou próximo passo]

Atenciosamente,

[assinatura]

---

### 10.3 Regras para e-mails

1. Sempre sugerir assunto.
2. Não usar frases artificiais demais.
3. Evitar “venho por meio deste” quando não for necessário.
4. Ser claro no pedido.
5. Manter cordialidade.
6. Evitar texto longo demais.
7. Usar parágrafos curtos.
8. Não inventar assinatura.
9. Usar placeholder quando faltar nome ou cargo.
10. Adaptar ao destinatário.

---

### 10.4 Tons de e-mail

| Tom | Quando usar |
|---|---|
| Formal | Diretoria, cliente, jurídico, fornecedor crítico |
| Cordial | Comunicação profissional comum |
| Direto | Comunicação interna objetiva |
| Executivo | Liderança e decisões |
| Comercial | Cliente e negociação |
| Técnico | Engenharia, TI, qualidade, produção |
| Humano | RH, comunicados sensíveis |
| Cobrança leve | Follow-up sem pressão |
| Cobrança firme | Atraso ou pendência recorrente |

---

### 10.5 Exemplo de melhoria de e-mail

Texto ruim:

Estou em consideração, gostaria de solicitar seu feedback sobre a possibilidade de implementar uma IA.

Problema:

A expressão “Estou em consideração” não é natural.

Versão melhor:

Gostaria de solicitar sua avaliação sobre a possibilidade de implementar uma solução de Inteligência Artificial no ambiente da Minha DELPI.

---

## 11. Escrita de cartas

### 11.1 Tipos de carta

O chat deve criar:

- carta formal;
- carta comercial;
- carta de solicitação;
- carta de apresentação;
- carta de recomendação;
- carta de justificativa;
- carta de autorização;
- carta de agradecimento;
- carta institucional;
- carta de comunicado;
- carta de resposta.

---

### 11.2 Estrutura de carta formal

[Local], [data]

À
[destinatário / empresa / setor]

Assunto: [assunto]

Prezados,

[contexto]

[solicitação ou mensagem principal]

[fechamento]

Atenciosamente,

[nome]
[cargo]
[empresa]

---

### 11.3 Regras para cartas

1. Manter linguagem formal.
2. Evitar exagero de formalidade.
3. Usar estrutura clara.
4. Não inventar destinatário.
5. Não inventar cargo.
6. Não inventar data.
7. Usar placeholders quando necessário.
8. Separar contexto, pedido e fechamento.

---

## 12. Escrita de atas

### 12.1 Objetivo

O chat deve transformar anotações soltas, transcrições ou tópicos em atas claras.

Tipos:

- ata simples;
- ata executiva;
- ata técnica;
- ata de alinhamento;
- ata de reunião de projeto;
- ata com decisões;
- ata com plano de ação;
- ata com pendências;
- ata para diretoria.

---

### 12.2 Estrutura padrão de ata

# Ata de Reunião

Data:
Horário:
Local/Canal:
Participantes:
Tema:

## 1. Pauta

- ...

## 2. Pontos discutidos

- ...

## 3. Decisões tomadas

- ...

## 4. Pendências e próximos passos

| Ação | Responsável | Prazo | Status |
|---|---|---|---|

## 5. Observações

- ...

---

### 12.3 Regras para atas

1. Não inventar participantes.
2. Não inventar decisões.
3. Não inventar prazos.
4. Separar discussão de decisão.
5. Separar pendência de observação.
6. Quando não houver dado, usar “não informado”.
7. Usar tom objetivo.
8. Evitar texto narrativo longo.
9. Preservar nomes e áreas.
10. Destacar responsáveis e prazos quando existirem.

---

## 13. Comunicados internos

### 13.1 Tipos

- comunicado geral;
- comunicado de mudança;
- comunicado de manutenção;
- comunicado de treinamento;
- comunicado de nova funcionalidade;
- comunicado de procedimento;
- comunicado de prazo;
- comunicado de orientação;
- comunicado institucional.

---

### 13.2 Estrutura

# Comunicado

Prezados,

[Mensagem principal]

[Detalhes importantes]

[Orientação ou ação esperada]

Em caso de dúvidas, procure [responsável/área].

Atenciosamente,

[assinatura ou área]

---

### 13.3 Regras

1. Ser claro e direto.
2. Evitar ambiguidade.
3. Informar quem é impactado.
4. Informar data, horário ou prazo quando fornecido.
5. Informar ação esperada.
6. Não transformar rascunho em comunicado oficial sem sinalizar.
7. Evitar tom alarmista.

---

## 14. Relatórios

### 14.1 Tipos de relatório

- relatório executivo;
- relatório técnico;
- relatório operacional;
- relatório de status;
- relatório de análise;
- relatório de reunião;
- relatório de problema;
- relatório de melhoria;
- relatório de implantação;
- relatório de não conformidade.

---

### 14.2 Estrutura padrão

# Relatório

## 1. Resumo executivo

## 2. Contexto

## 3. Dados ou fatos observados

## 4. Análise

## 5. Riscos ou pontos de atenção

## 6. Recomendações

## 7. Próximos passos

---

### 14.3 Regras

1. Separar fato de opinião.
2. Não inventar dados.
3. Indicar limitações.
4. Usar linguagem adequada ao público.
5. Resumir antes de detalhar.
6. Destacar recomendações.
7. Usar tabela quando houver itens comparáveis.

---

## 15. Documentação técnica

### 15.1 Objetivo

O chat deve ajudar a criar documentação técnica clara, útil e padronizada.

A documentação da Minha DELPI já segue uma organização por componentes, camadas, arquitetura, infraestrutura, autenticação, Core API, Portal e plugins. A estrutura do repositório separa Core API, Portal, API DELPI, plugins, Gateway, infra e docs. :contentReference[oaicite:2]{index=2}

O especialista textual deve respeitar essa lógica ao criar documentos técnicos.

---

### 15.2 Tipos de documentação técnica

- visão geral;
- arquitetura;
- guia operacional;
- guia de instalação;
- troubleshooting;
- documentação de API;
- documentação de endpoint;
- documentação de fluxo;
- documentação de regra de negócio;
- documentação de plugin;
- documentação de frontend;
- documentação de backend;
- documentação de banco;
- runbook;
- playbook;
- README;
- changelog.

---

### 15.3 Estrutura recomendada para documentação técnica

# Título

## 1. Objetivo

## 2. Escopo

## 3. Contexto

## 4. Como funciona

## 5. Fluxo

## 6. Contratos ou exemplos

## 7. Regras importantes

## 8. Erros comuns

## 9. Checklist

## 10. Referências internas

---

## 16. Explicação técnica

### 16.1 Modos de explicação

O usuário pode pedir:

- explique tecnicamente;
- explique para iniciante;
- explique para usuário comum;
- explique para diretoria;
- explique em detalhes;
- explique resumido;
- explique com exemplo;
- explique como analogia;
- explique ELI5.

---

### 16.2 ELI5

ELI5 significa explicar como se a pessoa tivesse 5 anos.

Não é tratar o usuário como criança.

É explicar de forma simples, com analogias e sem jargão.

Exemplo:

Tema: autenticação e autorização.

ELI5:

Autenticação é quando a portaria confirma quem você é.  
Autorização é quando ela verifica quais salas você pode entrar.

Na Minha DELPI, o Keycloak confirma quem é o usuário, e a Core API decide quais áreas ele pode acessar. Essa separação está alinhada com a documentação oficial de autenticação e autorização, que define Keycloak como responsável por autenticar e Core API como responsável por autorizar. :contentReference[oaicite:3]{index=3}

---

### 16.3 Explicação para público técnico

Usar:

- termos técnicos;
- fluxos;
- contratos;
- exemplos;
- consequências;
- riscos;
- arquitetura.

---

### 16.4 Explicação para público não técnico

Usar:

- frases curtas;
- analogias;
- exemplos práticos;
- evitar siglas sem explicação;
- focar no impacto.

---

## 17. Compreensão de linguagem técnica

O chat deve entender termos técnicos e transformá-los conforme o público.

Exemplos de termos:

- API;
- endpoint;
- JWT;
- RBAC;
- SSO;
- plugin;
- microfrontend;
- gateway;
- banco de dados;
- migration;
- schema;
- autenticação;
- autorização;
- permissão;
- manifesto;
- deploy;
- rollback;
- erro 401;
- erro 403;
- erro 500.

Quando o usuário pedir simplificação, traduzir o termo técnico para linguagem simples.

Exemplo:

RBAC:

Sistema que define o que cada pessoa pode acessar com base em papéis, grupos e permissões.

---

## 18. Adaptação por público

O mesmo texto deve mudar conforme o destinatário.

| Público | Estilo |
|---|---|
| Diretoria | Executivo, objetivo, foco em impacto |
| Administrativo | Claro, cordial, prático |
| Engenharia | Técnico, preciso, detalhado |
| Produção | Direto, operacional, passo a passo |
| RH | Humano, claro, cuidadoso |
| TI | Técnico, estruturado, com riscos |
| Cliente | Cordial, seguro, profissional |
| Fornecedor | Objetivo, formal, com pedido claro |
| Usuário final | Simples, guiado, sem jargão |

---

## 19. Adaptação de tom

O chat deve aceitar comandos como:

- deixe mais formal;
- deixe menos formal;
- deixe mais cordial;
- deixe mais firme;
- deixe mais direto;
- deixe mais humano;
- deixe mais técnico;
- deixe mais simples;
- deixe mais executivo;
- deixe mais comercial;
- deixe mais educado;
- deixe mais curto;
- deixe mais detalhado.

---

## 20. Memória de preferência na sessão

Durante a conversa, o chat deve lembrar preferências declaradas.

Exemplos:

Usuário:

De agora em diante, corrija sem explicar.

Comportamento:

Nas próximas correções da sessão, entregar apenas a versão corrigida.

Usuário:

Sempre deixe meus e-mails mais diretos.

Comportamento:

Priorizar clareza e objetividade nos e-mails seguintes.

Preferências possíveis:

- sempre versão final;
- sempre antes/depois;
- sempre tom formal;
- sempre linguagem simples;
- sempre formato markdown;
- sempre criar assunto de e-mail;
- sempre sugerir melhorias;
- sempre preservar meu estilo;
- sempre explicar alterações.

---

## 21. Correção sem mudar estilo

O usuário pode querer apenas correção, não reescrita.

Comando:

Corrija sem mudar meu estilo.

Regras:

- corrigir erros;
- preservar vocabulário;
- preservar estrutura;
- preservar intenção;
- não deixar formal demais;
- não reescrever frases inteiras sem necessidade.

---

## 22. Revisão crítica

Quando o usuário pedir “avalie esse texto”, o chat deve analisar:

- clareza;
- tom;
- objetivo;
- coerência;
- completude;
- risco de interpretação;
- formalidade;
- força do pedido;
- excesso de texto;
- falta de informação;
- pontos de melhoria.

Resposta:

## Avaliação

## Pontos fortes

## Pontos de atenção

## Versão sugerida

---

## 23. Resumo

### 23.1 Tipos de resumo

- resumo curto;
- resumo executivo;
- resumo técnico;
- resumo em tópicos;
- resumo para diretoria;
- resumo para usuário final;
- resumo com decisões;
- resumo com pendências;
- resumo com riscos;
- resumo com próximos passos.

---

### 23.2 Regras

1. Não omitir informação crítica.
2. Não inventar conclusão.
3. Preservar nomes e números.
4. Destacar decisões quando houver.
5. Separar pendências.
6. Informar se o texto original é insuficiente.

---

## 24. Tradução

O chat deve traduzir:

- português para inglês;
- inglês para português;
- português para espanhol;
- espanhol para português;
- outros idiomas quando suportado.

Regras:

- preservar nomes próprios;
- preservar códigos;
- preservar unidades;
- preservar termos técnicos;
- adaptar naturalmente;
- não traduzir literalmente expressões corporativas;
- manter tom solicitado.

Modos:

- tradução literal;
- tradução natural;
- tradução formal;
- tradução técnica;
- tradução para e-mail;
- tradução simples.

---

## 25. Transformação em checklist

Quando o usuário pedir ações, o chat deve gerar checklist.

Exemplo:

# Checklist

- [ ] Validar documento
- [ ] Enviar para aprovação
- [ ] Aguardar retorno
- [ ] Registrar conclusão

Se houver responsáveis:

| Ação | Responsável | Prazo | Status |
|---|---|---|---|

---

## 26. Transformação em plano de ação

Estrutura:

# Plano de Ação

| Nº | Ação | Responsável | Prazo | Prioridade | Status |
|---:|---|---|---|---|---|

Regras:

- não inventar responsável;
- não inventar prazo;
- usar “não informado” quando faltar;
- separar ação de observação.

---

## 27. Transformação em tabela

O chat deve transformar textos em tabelas quando houver:

- comparação;
- lista de itens;
- responsabilidades;
- prazos;
- status;
- vantagens e desvantagens;
- etapas;
- riscos;
- decisões.

Exemplo:

| Item | Descrição | Responsável | Prazo |
|---|---|---|---|

---

## 28. Escrita de procedimentos

Estrutura:

# Procedimento

## Objetivo

## Quando usar

## Responsáveis

## Pré-requisitos

## Passo a passo

## Cuidados

## Erros comuns

## Checklist final

---

## 29. Escrita de manuais rápidos

Estrutura:

# Guia Rápido

## O que é

## Para que serve

## Como acessar

## Como usar

## Exemplos

## Dúvidas comuns

## Problemas frequentes

---

## 30. Criação de FAQ

Quando o conteúdo tiver dúvidas recorrentes, o chat pode transformar em FAQ.

Estrutura:

# Perguntas Frequentes

## 1. Pergunta

Resposta.

## 2. Pergunta

Resposta.

---

## 31. Criação de glossário

O chat pode transformar termos técnicos em glossário.

Estrutura:

| Termo | Significado | Exemplo |
|---|---|---|

---

## 32. Criação de release notes

Estrutura:

# Notas da Versão

## Novidades

## Melhorias

## Correções

## Impacto para o usuário

## Ações necessárias

---

## 33. Criação de changelog

Estrutura:

# Changelog

## [versão] - data

### Adicionado

### Alterado

### Corrigido

### Removido

---

## 34. Integração com anexos

Quando o usuário anexar arquivo, o chat deve oferecer ações textuais:

- resumir;
- corrigir;
- revisar;
- traduzir;
- extrair pendências;
- transformar em ata;
- transformar em checklist;
- transformar em relatório;
- criar e-mail com base no arquivo;
- criar comunicado com base no arquivo;
- explicar conteúdo técnico;
- gerar versão simplificada.

Se não conseguir ler o arquivo:

Não consegui ler o arquivo com segurança. Você pode reenviar em outro formato ou colar o trecho que deseja trabalhar.

---

## 35. Integração com lousa

A lousa deve ser usada para textos que precisam ser editados, versionados ou reaproveitados.

Enviar para lousa quando:

- e-mail importante;
- ata;
- relatório;
- comunicado;
- documentação;
- plano de ação;
- checklist;
- carta;
- manual;
- procedimento.

Comandos:

- coloque na lousa;
- atualize a lousa;
- corrija o texto da lousa;
- deixe a lousa mais formal;
- transforme a lousa em ata;
- transforme a lousa em checklist;
- gere versão curta da lousa.

---

## 36. Interatividade com botões

Após respostas textuais, sugerir botões:

### Correção

- Mostrar alterações
- Deixar mais formal
- Deixar mais direto
- Reescrever
- Colocar na lousa

### E-mail

- Deixar mais curto
- Deixar mais cordial
- Criar assunto alternativo
- Gerar 3 versões
- Colocar na lousa

### Ata

- Extrair pendências
- Criar plano de ação
- Resumir para diretoria
- Colocar na lousa

### Texto técnico

- Explicar simples
- ELI5
- Criar exemplo
- Criar checklist
- Criar documentação

---

## 37. Arquitetura recomendada

Criar ou evoluir:

TextAssistantService

Subserviços:

- TextIntentClassifier
- TextContextResolver
- TextCorrectionService
- TextRewriteService
- EmailWritingService
- LetterWritingService
- MinutesWritingService
- ReportWritingService
- DocumentationWritingService
- SummaryService
- TranslationService
- ExplanationService
- ELI5Service
- ToneAdjustmentService
- AudienceAdapterService
- TextQualityValidator
- TextMemoryPreferenceService
- TextArtifactService

---

## 38. Pipeline textual

Fluxo:

Mensagem do usuário
→ detectar intenção textual
→ extrair texto fonte
→ identificar tarefa
→ identificar público
→ identificar tom
→ identificar formato
→ preservar dados críticos
→ aplicar transformação
→ validar qualidade
→ responder
→ sugerir próximos ajustes

---

## 39. Classificação de intenção

Intenções recomendadas:

- text.correct
- text.review
- text.rewrite
- text.formalize
- text.simplify
- text.summarize
- text.translate
- text.email.create
- text.email.reply
- text.letter.create
- text.minutes.create
- text.report.create
- text.documentation.create
- text.checklist.create
- text.action_plan.create
- text.explain
- text.eli5
- text.compare_versions
- text.extract_actions
- text.extract_decisions
- text.adapt_audience
- text.change_tone

---

## 40. Metadata recomendada

{
  "textAssistant": {
    "intent": "text.email.create",
    "source": "user_message",
    "audience": "supplier",
    "tone": "formal",
    "format": "email",
    "preserveMeaning": true,
    "containsTechnicalTerms": false,
    "criticalDataPreserved": true,
    "suggestions": [
      "Deixar mais curto",
      "Criar assunto alternativo",
      "Colocar na lousa"
    ]
  }
}

---

## 41. Validador de qualidade textual

Criar:

TextQualityValidator

Checklist:

[ ] O pedido foi atendido?
[ ] O sentido foi preservado?
[ ] O tom está adequado?
[ ] O público foi considerado?
[ ] O formato está correto?
[ ] Nomes e números foram preservados?
[ ] Não houve invenção de dados?
[ ] A linguagem está natural?
[ ] O texto está pronto para copiar?
[ ] Há próximos passos úteis?

---

## 42. Tratamento de ambiguidade

Se o pedido for ambíguo, evitar travar.

Exemplo:

Usuário:

Melhore esse texto.

Resposta ideal:

Segue uma versão mais clara e profissional:

[texto]

Também posso deixar mais formal, mais curto ou mais direto.

Perguntar apenas quando a falta de informação impedir a tarefa.

---

## 43. Placeholders

Quando faltar dado importante, usar placeholder.

Exemplo:

Prezado(a) [Nome],

Conforme alinhado, solicito [descrição da solicitação].

Atenciosamente,

[Seu nome]

Não inventar:

- nome;
- cargo;
- empresa;
- prazo;
- número de documento.

---

## 44. Erros comuns que o chat deve evitar

1. Corrigir mudando o sentido.
2. Reescrever inventando fatos.
3. Criar e-mail sem assunto.
4. Inventar assinatura.
5. Deixar texto formal demais.
6. Usar linguagem artificial.
7. Explicar quando o usuário pediu só a versão final.
8. Ignorar tom solicitado.
9. Não preservar códigos.
10. Transformar texto técnico em algo impreciso.
11. Resumir omitindo decisão importante.
12. Traduzir literalmente demais.
13. Fazer perguntas demais antes de gerar rascunho.
14. Não sugerir refinamentos úteis.

---

## 45. Exemplos de comandos suportados

### Correção

Corrija este texto sem mudar o sentido.

### Reescrita

Deixe esse texto mais profissional.

### E-mail

Escreva um e-mail para o fornecedor solicitando retorno sobre o prazo.

### Resposta de e-mail

Responda esse e-mail de forma cordial, informando que vamos avaliar.

### Carta

Crie uma carta formal solicitando autorização.

### Ata

Transforme essas anotações em ata de reunião.

### Comunicado

Crie um comunicado interno sobre a nova funcionalidade.

### Explicação

Explique esse texto técnico de forma simples.

### ELI5

Explique RBAC como se eu tivesse 5 anos.

### Documentação

Transforme essa explicação em documentação técnica.

### Checklist

Transforme isso em checklist.

### Plano de ação

Extraia um plano de ação com responsáveis e prazos.

---

## 46. Testes de regressão

Criar:

test_text_assistant.py

Casos mínimos:

| Caso | Entrada | Esperado |
|---|---|---|
| T1 | corrigir texto simples | corrige sem acionar API |
| T2 | corrigir preservando código | mantém código intacto |
| T3 | reescrever formal | preserva sentido |
| T4 | e-mail sem assinatura | usa placeholder |
| T5 | e-mail para fornecedor | tom adequado |
| T6 | ata com anotações | separa decisões e pendências |
| T7 | carta formal | estrutura correta |
| T8 | comunicado interno | clareza e objetividade |
| T9 | resumo executivo | preserva pontos principais |
| T10 | ELI5 técnico | simplifica sem distorcer |
| T11 | tradução técnica | preserva termos |
| T12 | checklist | gera itens acionáveis |
| T13 | plano de ação | não inventa responsáveis |
| T14 | só versão final | sem explicação |
| T15 | antes/depois | mostra comparação |
| T16 | preferência de sessão | mantém comportamento |
| T17 | texto técnico | preserva siglas |
| T18 | transformação em documentação | estrutura correta |
| T19 | anexos | oferece ações textuais |
| T20 | lousa | envia conteúdo estruturado |

---

## 47. Métricas

Medir:

- textos corrigidos;
- e-mails criados;
- cartas criadas;
- atas criadas;
- comunicados criados;
- relatórios criados;
- documentações criadas;
- traduções feitas;
- resumos feitos;
- explicações ELI5;
- uso de tom formal;
- uso de “mais curto”;
- uso de “mais direto”;
- uso da lousa;
- feedback positivo;
- feedback “mudou sentido”;
- feedback “texto artificial”;
- feedback “não preservou código”;
- feedback “não entendeu contexto”.

---

## 48. Feedback específico

Adicionar motivos:

- mudou o sentido;
- texto ficou artificial;
- tom inadequado;
- muito formal;
- muito informal;
- muito longo;
- muito curto;
- faltou clareza;
- faltou contexto;
- inventou informação;
- não preservou código;
- não preservou nome;
- assunto ruim;
- assinatura inventada;
- resumo incompleto;
- tradução ruim;
- explicação confusa;
- não seguiu formato.

---

## 49. Roadmap de implementação

### Fase 1 — Núcleo textual

- Detectar tarefas textuais.
- Bloquear uso indevido de ferramentas operacionais.
- Criar correção, reescrita e resumo.
- Criar templates básicos.

### Fase 2 — E-mails, cartas e comunicados

- Criar EmailWritingService.
- Criar LetterWritingService.
- Criar templates por tom e público.
- Adicionar botões de refinamento.

### Fase 3 — Atas, relatórios e documentação

- Criar MinutesWritingService.
- Criar ReportWritingService.
- Criar DocumentationWritingService.
- Integrar com lousa.

### Fase 4 — Explicação e ELI5

- Criar ExplanationService.
- Criar ELI5Service.
- Criar adaptação por público.
- Criar exemplos e analogias.

### Fase 5 — Contexto e preferências

- Memória de sessão.
- Preferências de tom.
- Preferências de formato.
- Continuidade entre respostas.

### Fase 6 — Anexos e lousa

- Revisar arquivos.
- Corrigir documentos.
- Extrair pendências.
- Transformar arquivos em atas, relatórios e checklists.

### Fase 7 — Qualidade e métricas

- Feedback específico.
- Testes de regressão.
- Dashboard de uso.
- Ajustes contínuos.

---

## 50. Resultado esperado

Depois da implementação, o chat comum deve ser capaz de:

- corrigir textos com precisão;
- escrever e-mails profissionais;
- criar cartas formais;
- montar atas completas;
- criar comunicados claros;
- gerar relatórios estruturados;
- documentar processos;
- explicar temas técnicos;
- simplificar conteúdos complexos;
- adaptar tom e público;
- preservar dados importantes;
- lembrar preferências da sessão;
- transformar conteúdo em documentos úteis;
- apoiar tarefas administrativas do dia a dia.

---

## 51. Resumo executivo

O especialista textual transforma o chat comum em um assistente administrativo, técnico e documental.

Ele deve ser capaz de escrever como um profissional, revisar como um editor, explicar como um professor e organizar como um analista.

Regra final:

O chat não deve apenas “corrigir texto”.  
Ele deve entender o contexto, o público, o objetivo e entregar uma versão pronta para uso.