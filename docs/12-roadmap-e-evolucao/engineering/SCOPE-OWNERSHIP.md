# Portal de Engenharia — escopo e ownership

> **Status:** planejamento de produto e arquitetura.  
> **Implementação:** não autorizada por este documento.

## 1. Objetivo do bounded context

O Portal de Engenharia deve centralizar a experiência operacional e gerencial da Engenharia sem transformar o MFE em owner de todos os sistemas relacionados. O módulo agrega jornadas, compõe dados e oferece deep links para capacidades especializadas, preservando o ownership dos domínios já existentes.

## 2. Estado atual confirmado

### 2.1 Engenharia

- `plugins/dashboard-engineering`: visão atual de indicadores de Engenharia, com LMPs no prazo e TRANSFORMA+.
- `plugins/dashboard-lmps`: dashboard operacional de LMPs, detalhe de OV/LMP, produtos, BOM, histórico, Gantt e não conformidades.
- `api-delpi /engineering/*`: contratos atuais de Engenharia/TOTVS.

### 2.2 Produtos

A `api-delpi` já possui contratos corporativos de produto, incluindo pesquisa, detalhe, análise, estrutura/BOM, onde é usado, desenho PDF, estoque, fornecedores, preço e impacto de custo.

No Portal de Engenharia, **Produtos é uma ferramenta interna do portal**, não uma aplicação independente na navegação global da Minha DELPI.

### 2.3 Controle de matéria-prima

O roadmap vigente de `controle-mp` define:

- legado atual: iframe `controle-mp`;
- alvo: `plugins/my-requests` + `requests-api`;
- tipos: `raw-material-creation` e `raw-material-update`;
- solicitante em `/apps/my-requests/new` e `/mine`;
- analista em `/work-queue` + detalhe especializado;
- sem segundo MFE dedicado a Controle de MP.

O Portal de Engenharia deve fornecer entrada contextual para essas rotas.

### 2.4 TRANSFORMA+

O Transformômetro continua dono de processos, revisões, instâncias, medições, recursos, matriz impacto×esforço, atas e integrações. O Portal Engenharia pode mostrar resumo, ganhos e atalhos, mas não duplica essas regras.

### 2.5 FILESERVER e desenhos

A biblioteca atual de desenhos é exposta pela `api-delpi`, que monta o compartilhamento do FILESERVER read-only e fornece:

- `GET /products/drawings`;
- `GET /products/{code}/drawing`;
- `GET /products/{code}/drawing/pdf`.

O browser não acessa `X:\...` diretamente.

Também existem leituras pontuais de arquivos da área de Engenharia em `X:\ENGENHARIA\...`, porém não há hoje uma API canônica genérica de biblioteca documental de Engenharia equivalente à biblioteca de desenhos.

## 3. Escopo funcional alvo

| Capacidade | Papel no Portal | Owner principal |
|---|---|---|
| Início | central pessoal do usuário | `engineering-api` + integrações |
| Visão geral | saúde da Engenharia, indicadores e tendências | `engineering-api`; SI como fonte estratégica |
| Sala de interação | colaboração geral e contextual | `engineering-api` |
| Minhas tarefas | worklist pessoal consolidada | `engineering-api` agregando owners |
| LMPs | jornada operacional principal | domínio Engenharia/LMP |
| Produtos | ferramenta de consulta técnica | Portal Engenharia; dados por `engineering-api` |
| Controle de MP | entrada contextual | `my-requests` + `requests-api` |
| Não conformidades | experiência de Engenharia vinculada a LMP | domínio Engenharia/LMP |
| TRANSFORMA+ | resumo e acesso | `transformometro-api` |
| Documentos técnicos | biblioteca autorizada de arquivos | `engineering-api` + adapter de storage |
| Biblioteca de desenhos | consulta global + visualização | contratos de desenhos; composição no `engineering-api` |
| Ajuda | ajuda contextual e manual | Portal Engenharia |

## 4. Fronteiras arquiteturais

### 4.1 Alvo

```text
Portal shell
   │
   ▼
plugins/engineering
   │ HTTP + JWT
   ▼
engineering-api
   ├── regras/escopo do Portal Engenharia
   ├── worklist agregada
   ├── sala de interação
   ├── composição de indicadores
   ├── composição de produtos/desenhos
   ├── biblioteca documental autorizada
   └── adapters HTTP
         ├── api-delpi
         ├── requests-api
         ├── transformometro-api
         ├── Strategic Indicators
         └── Core API quando contrato exigir
```

### 4.2 Regras obrigatórias

- MFE `plugins/engineering` chama **somente** `engineering-api` para dados do domínio/composições.
- `engineering-api` pode consumir `api-delpi` por contrato HTTP; não importa domain/use case de outro serviço.
- `api-delpi` permanece owner de contratos genéricos TOTVS e biblioteca de desenhos já existentes.
- `requests-api` permanece owner do workflow de Controle de MP.
- `transformometro-api` permanece owner do TRANSFORMA+.
- Core API permanece owner de app/manifest/rotas/RBAC/auditoria da plataforma.
- FILESERVER não é acessado pelo frontend.

## 5. Navegação e hierarquia

### TopBar travada

```text
Início | Visão geral | Sala de interação | Minhas tarefas | LMPs | Ajuda
```

### Ferramentas

As ferramentas aparecem em uma vitrine/listagem própria na home e podem ser acessadas também por deep link contextual:

- Produtos;
- Controle de MP;
- Documentos técnicos;
- Biblioteca de desenhos;
- Não conformidades;
- TRANSFORMA+;
- futuras ferramentas técnicas.

## 6. Ownership por capacidade

### Início

A home é uma composição de leitura. Pode exibir:

- tarefas do usuário;
- indicadores principais;
- LMPs recentes ou críticas;
- salas com atividade recente;
- atalhos/ferramentas;
- avisos e alertas.

Não cria ownership novo sobre cada origem.

### Visão geral

Apresenta a Engenharia como área. Indicadores estratégicos devem usar a fonte oficial do Strategic Indicators; indicadores operacionais podem ser compostos pelo `engineering-api` a partir de contratos existentes.

### Sala de interação

Novo bounded subcontext de colaboração do Portal Engenharia. Deve suportar salas gerais e contextuais. Mensagem não substitui evento oficial de workflow.

Contextos previstos:

- geral da Engenharia;
- produto;
- LMP;
- projeto;
- não conformidade;
- solicitação de MP.

### Minhas tarefas

É uma **worklist agregada**, não um novo workflow engine. Cada item precisa carregar origem, tipo, prioridade/estado, deep link e ações permitidas quando houver contrato seguro para isso.

Owners permanecem responsáveis pelos estados reais.

### LMPs

É a principal jornada operacional nativa do portal e candidata a absorver a experiência do `dashboard-lmps`. O cutover só acontece após paridade.

### Produtos

Ferramenta interna do portal. Deve concentrar consultas rápidas e ficha 360° do produto:

- pesquisa;
- cadastro/resumo;
- estrutura/BOM;
- onde é usado;
- desenho;
- estoque;
- fornecedores;
- preço/custo quando permitido;
- análise ampliada.

### Controle de MP

O Portal exibe cards, atalhos e status; criação/tratativa navegam para `my-requests`. Não duplicar formulário, fila ou workflow.

### Documentos técnicos e FILESERVER

Criar uma biblioteca **allowlisted**, não um Explorer web genérico do servidor.

O alvo deve suportar fontes explicitamente configuradas, por exemplo:

```text
Bibliotecas de Engenharia
├── desenhos
├── LMPs
├── projetos
└── documentos técnicos
```

Cada biblioteca define:

- raiz autorizada;
- extensões permitidas;
- profundidade/navegação permitida;
- indexação e metadados;
- política de download/preview;
- RBAC;
- auditoria;
- tamanho máximo;
- comportamento quando share indisponível.

Proibido expor path físico, credencial SMB/CIFS ou path arbitrário enviado pelo cliente.

## 7. Permissões — direção inicial

Os códigos finais devem ser confirmados no plano de implementação, mas o modelo funcional precisa distinguir pelo menos:

```text
engineering.access
engineering.overview.view
engineering.tasks.view
engineering.rooms.view
engineering.rooms.write
engineering.lmps.view
engineering.products.view
engineering.documents.view
engineering.drawings.view
engineering.admin
```

Permissões dos sistemas integrados continuam próprias (`my-requests.*`, Transformômetro etc.). O Portal não deve conceder acesso indireto que o usuário não possua no owner.

## 8. Integrações e anti-corruption

Cada integração externa ao contexto deve ter adapter próprio no `engineering-api`, com DTO interno do Portal para evitar acoplamento direto da UI aos payloads de terceiros.

```text
api-delpi payload ──adapter──> EngineeringProductSummary
requests-api      ──adapter──> EngineeringTaskItem
transformometro   ──adapter──> EngineeringTransformaSummary
SI                ──adapter──> EngineeringIndicatorScore
```

## 9. Cutover dos legados

### `dashboard-engineering`

Candidato a ser absorvido pela Visão geral. Remover somente após paridade e redirect definidos.

### `dashboard-lmps`

Candidato a ser absorvido gradualmente por LMPs. Preservar rotas/deep links ou oferecer redirect compatível durante transição.

### `controle-mp`

Seguir roadmap próprio. O Portal Engenharia não altera a decisão de migração para `my-requests`.

## 10. Fora do escopo inicial

- edição direta de arquivos no FILESERVER;
- CAD/PDM/PLM sem integração real confirmada;
- duplicar cadastro mestre de produto;
- duplicar workflow de Controle MP;
- duplicar domínio do Transformômetro;
- converter Sala de interação em fonte oficial de status de processos;
- acesso irrestrito ao FILESERVER.
