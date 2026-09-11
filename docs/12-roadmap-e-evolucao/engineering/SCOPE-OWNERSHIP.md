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

A biblioteca atual de desenhos é exposta pela `api-delpi`, que monta o compartilhamento do FILESERVER read-only e fornece contratos de catálogo/metadados/PDF.

O browser não acessa `X:\\...` diretamente.

Também existem leituras pontuais de arquivos da área de Engenharia em `X:\\ENGENHARIA\\...`, porém não há hoje uma API canônica genérica de biblioteca documental de Engenharia equivalente à biblioteca de desenhos. Qualquer biblioteca adicional precisa de allowlist/configuração server-side.

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
         └── Core API
```

### 4.2 Regras obrigatórias

- MFE `plugins/engineering` chama **somente** `engineering-api` para dados do domínio/composições.
- `engineering-api` consome outros serviços por contratos HTTP/ports; não importa domain/use case de outro serviço.
- `api-delpi` permanece owner de contratos genéricos TOTVS e biblioteca de desenhos já existentes.
- `requests-api` permanece owner do workflow de Controle de MP.
- `transformometro-api` permanece owner do TRANSFORMA+.
- Strategic Indicators permanece owner de metas/realizado/IDD estratégicos.
- Core API permanece owner de app/manifest/rotas/RBAC/auditoria da plataforma.
- FILESERVER não é acessado pelo frontend.

## 5. Navegação e hierarquia

### TopBar travada

```text
Início | Visão geral | Sala de interação | Minhas tarefas | LMPs | Ajuda
```

### Ferramentas

As ferramentas aparecem em uma vitrine/listagem própria na Home e podem ser acessadas também por Ctrl+K, Favoritos e deep link contextual:

- Produtos;
- Controle de MP;
- Documentos técnicos;
- Biblioteca de desenhos;
- Não conformidades;
- TRANSFORMA+;
- futuras ferramentas técnicas autorizadas.

## 6. Ownership por capacidade

### Início

A Home é uma composição de leitura. Pode exibir tarefas, indicadores principais, LMPs críticas/recentes, salas/menções, ferramentas e atividade recente. Não cria ownership novo sobre cada origem.

### Visão geral

Apresenta a Engenharia como área. Indicadores estratégicos usam a fonte oficial do Strategic Indicators; indicadores operacionais podem ser compostos pelo `engineering-api` a partir de contratos existentes e fichas aprovadas.

### Sala de interação

Novo subcontexto de colaboração do Portal Engenharia. Deve suportar salas gerais e contextuais. Mensagem não substitui evento oficial de workflow.

Contextos candidatos:

- geral da Engenharia;
- produto;
- LMP;
- projeto;
- não conformidade;
- solicitação de MP.

A política de membership e unicidade por contexto permanece decisão explícita antes da migration.

### Minhas tarefas

É uma **worklist agregada**, não um novo workflow engine. Cada item precisa carregar origem, tipo, prioridade/estado, deep link e ações permitidas quando houver contrato seguro para isso. Owners permanecem responsáveis pelos estados reais.

### LMPs

É a principal jornada operacional nativa do portal e candidata a absorver a experiência do `dashboard-lmps`. O cutover só acontece após paridade.

### Produtos

Ferramenta interna do portal para pesquisa, cadastro/resumo, estrutura/BOM, onde é usado, desenho, estoque, fornecedores e preço/custo quando permitido. O backend compõe e protege informação sensível.

### Controle de MP

O Portal exibe cards, atalhos e status; criação/tratativa navegam para `my-requests`. Não duplicar formulário, fila ou workflow.

### Documentos técnicos e FILESERVER

Criar uma biblioteca **allowlisted**, não um Explorer web genérico do servidor. Cada biblioteca define raiz autorizada, extensões, profundidade, metadados, preview/download, RBAC, auditoria, tamanho máximo e comportamento de indisponibilidade.

Proibido expor path físico, credencial SMB/CIFS ou path arbitrário enviado pelo cliente.

## 7. Permissões — direção mínima

O catálogo inicial deve seguir minimização de permissions e ser validado em [PERFIS-E-PERMISSOES.md](./PERFIS-E-PERMISSOES.md).

Direção P0:

```text
engineering.access
engineering.analytics.access
engineering.lmps.access
engineering.products.access
engineering.documents.access
engineering.nonconformities.write
engineering.costs.view
```

Sala e Minhas tarefas usam `engineering.access` + resource/self scope enquanto não houver risco que justifique permission adicional. Não criar permissions CRUD de Sala por simetria.

Legados a mapear durante coexistência:

```text
dashboard-engineering.view
dashboard-lmps.view
dashboard-lmps.nc.write
```

O Portal não deve conceder acesso indireto que o usuário não possua no owner integrado.

## 8. Integrações e anti-corruption

Cada integração externa deve ter adapter próprio no `engineering-api`, com DTO interno do Portal para evitar acoplamento da UI a payloads de terceiros.

```text
api-delpi       ──adapter──> EngineeringLmp/Product DTOs
requests-api    ──adapter──> EngineeringTask/RawMaterial summary
transformometro ──adapter──> EngineeringTransformaSummary
SI              ──adapter──> EngineeringIndicatorScore
Core            ──adapter──> EffectiveAuthorization/UserIdentity
```

## 9. Cutover dos legados

### `dashboard-engineering`

Candidato a ser absorvido pela Visão geral. Remover somente após paridade de dados/score/permissions e redirect definidos.

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
- converter Sala em fonte oficial de status de processos;
- acesso irrestrito ao FILESERVER;
- administração P0 sem requisito/owner explícito;
- hard cutover junto com a primeira entrega do target.
