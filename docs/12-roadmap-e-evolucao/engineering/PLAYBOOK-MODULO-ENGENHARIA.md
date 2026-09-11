# Playbook — Portal de Engenharia

> **Status:** contrato de produto/arquitetura para implementação incremental.  
> **Regra:** este documento orienta o Cursor; não substitui revalidação do código atual nem autoriza cutover.

## 1. Resultado perceptível

O usuário de Engenharia deve entrar em um único Portal e encontrar, sem conhecer sistemas internos, o que precisa fazer, como a área está, onde colaborar, quais LMPs demandam atenção e quais ferramentas técnicas estão disponíveis para seu perfil.

TopBar travada:

```text
Início → Visão geral → Sala de interação → Minhas tarefas → LMPs → Ajuda
```

Ferramentas ficam no launcher do Início, busca, favoritos e deep links contextuais.

## 2. Princípios de produto

### 2.1 Portal não é um mega-monólito

O Portal centraliza **experiência**, não ownership. Cada bounded context continua dono de suas regras e estados.

### 2.2 Uma fonte, uma regra

- LMP/TOTVS: owner atual do domínio Engenharia/api-delpi até eventual migração explícita.
- Indicadores estratégicos: Strategic Indicators.
- Controle de MP: `requests-api`/`my-requests` no alvo do roadmap próprio.
- TRANSFORMA+: Transformômetro.
- RBAC/apps/rotas: Core.
- Sala/estado de colaboração Engenharia: `engineering-api`.

### 2.3 Backend-first

O MFE apresenta, coleta intenção e navega. Autorização, regra de negócio, agregação e tradução entre providers ficam no backend.

### 2.4 Kit-first

Antes de criar qualquer componente, procurar primitive/factory em `@delpi/plugin-ui`. Se dois ou mais portais precisarem do mesmo comportamento visual, evoluir o kit em vez de duplicar CSS/markup.

## 3. Invariantes arquiteturais

```text
Browser → Portal → plugins/engineering → engineering-api
```

Proibido:

- `plugins/engineering` → `api-delpi` direto;
- `plugins/engineering` → `commercial-api`;
- `engineering-api` importar domain/use case de outro serviço;
- frontend decidir permission por claims JWT;
- frontend acessar FILESERVER;
- copiar regra de LMP/Gantt/NC para React;
- duplicar workflow de Controle MP;
- tratar mensagem da Sala como evento oficial de processo;
- criar CRUD permission por botão sem segregação de risco.

## 4. Arquitetura da informação

### Áreas principais

| Área | Pergunta que responde | Natureza |
|---|---|---|
| Início | O que importa para mim agora? | hub pessoal |
| Visão geral | Como está a Engenharia? | gestão/indicadores |
| Sala de interação | Onde colaboro com a equipe? | comunicação contextual |
| Minhas tarefas | O que depende da minha ação? | worklist agregada |
| LMPs | Como estão propostas/ordens de Engenharia? | jornada operacional principal |
| Ajuda | Como uso o Portal e interpreto os dados? | orientação |

### Ferramentas

Produtos, Controle de MP, Desenhos, Documentos técnicos, Não conformidades, TRANSFORMA+ e futuras ferramentas autorizadas.

Uma ferramenta não vira item da TopBar só porque é importante. TopBar representa jornadas permanentes e de alta frequência.

## 5. Navegação e URL

- basePath alvo: `/apps/engineering`;
- rotas devem funcionar com F5, back/forward e deep link;
- filtros relevantes ficam em query params allowlisted;
- IDs de detalhe ficam no path quando estáveis;
- parâmetros inválidos são normalizados/removidos sem crash;
- retorno de detalhe preserva contexto da lista;
- links para owners externos usam rotas canônicas, não URLs hardcoded de infraestrutura.

## 6. Início

Home não é dashboard duplicado. Deve priorizar:

1. atenção pessoal;
2. tarefas;
3. LMPs críticas/recentes;
4. menções/salas;
5. catálogo de ferramentas;
6. atividade recente.

Uma fonte degradada não deve derrubar o hub inteiro quando os demais blocos continuarem semanticamente válidos. Expor `partial_sources`/estado parcial com linguagem amigável.

## 7. Visão geral

Usar o SI como owner de meta/realizado/score para indicadores estratégicos. Operacionais entram como contexto/drill, não substituem o score estratégico.

Indicadores canônicos já evidenciados:

- `% de Projetos Concluídos no Prazo` (`engineering-projects-on-time`);
- `Ganhos Financeiros do TRANSFORMA+ DELPI` (`engineering-transforma-plus`).

Engenharia é departamento consolidado; não inventar visão por filial se a fonte canônica não a sustentar.

## 8. Sala de interação

Referência de UX: Portal Comercial. Ownership: `engineering-api`.

P0:

- inbox;
- sala geral e salas contextuais;
- thread;
- mensagens;
- edição/exclusão conforme policy;
- menções;
- reações;
- anexos se storage seguro estiver resolvido;
- read/unread;
- realtime;
- deep link;
- identidade/avatar Core.

Contextos tipados: produto, LMP, projeto, NC e solicitação de MP, somente quando a chave real estiver comprovada.

Nunca usar `commercial-api` como serviço compartilhado de chat.

## 9. Minhas tarefas

É uma projeção/worklist. Cada item precisa declarar:

- source/owner;
- external id;
- título e resumo;
- prioridade/estado normalizados;
- prazo quando existe;
- deep link;
- `allowed_actions` somente quando o owner fornece contrato seguro.

O Portal não cria estados paralelos de workflow. Ação rápida deve chamar o owner via BFF e respeitar sua autorização.

## 10. LMPs

A migração de `dashboard-lmps` é por paridade, não reescrita livre.

Preservar e provar:

- listagem e filtros;
- resumo/KPIs;
- detalhe;
- produtos da LMP;
- BOM/estrutura quando aplicável;
- histórico/eventos;
- Gantt;
- não conformidades;
- permissões de escrita de NC;
- deep links existentes;
- exportações, se existirem no runtime real.

Regra de cálculo continua no owner backend. O novo Portal pode melhorar UI sem mudar semântica silenciosamente.

## 11. Produtos

Ferramenta 360° de consulta técnica, composta pelo `engineering-api` a partir de contratos corporativos existentes.

Dimensões P0 candidatas:

- identificação;
- estrutura/BOM;
- onde é usado;
- desenho;
- estoque;
- fornecedores;
- compras/preço/custo quando autorizado;
- contexto LMP.

Informação sensível de preço/custo exige policy explícita.

## 12. FILESERVER e documentos

Não construir Explorer web. O produto oferece bibliotecas lógicas allowlisted.

```text
library_id + document_id opaco
→ backend resolve raiz/config/path
→ valida containment + extensão + permissão
→ stream/preview/download
```

MVP read-only. Upload/edição só em roadmap futuro com owner/storage/auditoria próprios.

## 13. Controle de MP

O Portal pode mostrar resumo e CTAs, mas o fluxo canônico é `my-requests`. Não duplicar wizard, fila ou detalhe de atendimento.

## 14. TRANSFORMA+

Exibir resumo e drill/deep link. Não copiar CRUD, matriz, medições, atas ou workflow do Transformômetro.

## 15. Segurança

- JWT validado em todos os serviços;
- Core como fonte de authorization efetiva;
- fail-closed em capability/resource scope;
- room membership/IDOR protegido;
- download de documento protegido;
- CORS restritivo;
- sem token em log;
- anexos com MIME/tamanho/filename allowlist;
- paths e credenciais de share nunca no DTO público.

## 16. Observabilidade

Cada downstream deve possuir timeout, correlação, logs estruturados e classificação de erro. Retry apenas onde idempotente e transitório. Composições devem distinguir erro total de parcial.

## 17. Definition of Done de página

1. contrato/backend no owner certo;
2. AuthZ e resource scope;
3. UI kit-first;
4. loading/empty/error/forbidden/partial;
5. deep link/F5/back-forward;
6. Help sincronizado;
7. tests positive/sibling/negative;
8. desktop/mobile/light/dark/keyboard;
9. docs atualizados;
10. smoke federado quando material.

## 18. Estratégia de entrega

```text
E0 inventário + decisões
→ fundação API/MFE/manifest/RBAC
→ Início
→ Visão geral
→ Sala
→ Minhas tarefas
→ LMPs
→ ferramentas uma a uma
→ paridade
→ soft cutover
→ observação
→ hard cutover
→ verify-final
```

Não abrir várias páginas user-facing em paralelo sem autorização explícita. Cada onda deve sair testável e reversível.
