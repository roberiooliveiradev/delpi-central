# DAVI-PRODUCT-VOCABULARY-001 — Inventário e proposta de incorporação governada

**Status:** TO_INVENTORY / PLANNED — especificação e rastreabilidade documental apenas. **Implementação, cópia, ingestão e deploy NÃO autorizados por este documento.**
**Baseline revisada:** origin/main `8e16d2b75ade63ef2af51973c50ef58612f8b00e` (2026-10-16).
**Escopo:** melhorar a interpretação de termos de catálogo de matérias-primas e intermediários em consultas READ do DAVI, preservando `search_products`, output allowlist e AuthZ backend.

## 1. Incidente observado e evidência

Pergunta: "Dê três exemplos de terminal pino." A primeira tentativa do DAVI buscou a expressão literal `TERMINAL PINO` e apresentou apenas `10080683`, com resultado alternativo `10081026` não equivalente ao subtipo pedido. A consulta governada posterior com a expressão cadastral `TERM. PINO` encontrou itens do grupo `1008`, incluindo:

| Código | Descrição retornada pela API DELPI |
|---|---|
| `10081762` | `TERM. PINO 0,75-1,50MM2 LATAO S/ISOLACAO FITADO` |
| `10081555` | `TERM. PINO 1,00-1,50MM2 ESTANHADO S/ISOLACAO FITADO C/ TRAVA MINI HYLOCK- ROHS` |
| `10081798` | `TERM. PINO 1,00-2,00MM2 ESTANHADO GRANEL - DELPHI` |

**Interpretação:** há evidência de um gap de expansão semântica/planejamento de buscas do agente. Não há evidência de ausência de produtos no ERP. O retorno de `search_products` inclui paginação, ranking e possíveis matches amplos: o consumidor deve validar descrição/grupo e não confundir `total` bruto com quantidade de resultados semanticamente corretos. Um filtro com descrição `TERM. PINO` retornou `total=1570`, apesar dos itens relevantes exibidos — **não presumir semântica de busca exata**.

## 2. Fonte de nomenclatura identificada no GitHub

A fonte documental mais diretamente relevante é:

- `minha-delpi-ai-api/docs/knowledge/sources/gpt-instructions/Normas_Tecnicas_DELPI.md` — blob `aa8ec68879ae73ce83155f291e697e2f88416ebd`. Contém seção **1008 · Terminais → Terminais Pino**, com `ITEM` definido como prefixo fixo `TERM.` e tipo `PINO`.
- `minha-delpi-ai-api/docs/knowledge/domains/global/normas-tecnicas-delpi.md` — blob `f1f7e20ac62510bf53a42e1c9f6c3eabd22a9799`. Projeção de conhecimento global proveniente de fonte histórica `api-delpi-py/GPT_instructions/Normas_Tecnicas_DELPI.md`, sincronizada em 2026-06-09. **É uma segunda representação; não presumir que é a versão vigente aprovada.**

O documento de diretriz `diretrizes_criacao_de_descricao.md` exige `Normas_Tecnicas_DELPI.md` para campos, ordem e prefixos. Isso é uma regra de **criação de descrição técnica**, não permissão de gravação nem autorização para que a busca sobrescreva descrições efetivas.

## 3. Documentos candidatos à cópia controlada (Chat AI API → API DELPI / inteligência DAVI)

Cópia proposta **somente após inventário de autoridade, versionamento, revisão de integridade e aprovação da curadoria**. Caminho de destino *sugerido*, não contrato já aceito:

| Prioridade | Origem existente | Destino sugerido em `api-delpi` | Finalidade / ressalva |
|---|---|---|---|
| P0 | `minha-delpi-ai-api/docs/knowledge/sources/gpt-instructions/Normas_Tecnicas_DELPI.md` | `api-delpi/docs/knowledge/product-vocabulary/normas-tecnicas-delpi.md` | Vocabulário de grupos, subtipos, prefixos. **Comparar** com projeção global e obter ratificação da versão normativa. |
| P0 | `minha-delpi-ai-api/docs/knowledge/sources/gpt-instructions/diretrizes_criacao_de_descricao.md` | `api-delpi/docs/knowledge/product-vocabulary/diretrizes-descricao-produto.md` | Regras de interpretação/descrição; separar claramente READ de eventual criação (não autorizada). |
| P1 | `minha-delpi-ai-api/docs/knowledge/domains/agents/minha-delpi-chat/engenharia-codigos-intermediarios-delpi.md` | `api-delpi/docs/knowledge/product-vocabulary/codigos-intermediarios-delpi.md` | Semântica da família 50xx e composição de códigos; validar contra fonte original. |
| P1 | `minha-delpi-ai-api/docs/knowledge/sources/gpt-instructions/drawing_analyser_instructions.md` | `api-delpi/docs/knowledge/product-vocabulary/analise-desenhos-extratos.md` | **Somente trechos relevantes** de identificação de grupos/terminais, após minimização. Documento amplo não deve ser ingerido integralmente sem revisão. |
| P2 | `minha-delpi-ai-api/docs/knowledge/domains/agents/minha-delpi-chat/api-product-instructions.md` | `api-delpi/docs/knowledge/product-vocabulary/api-product-legacy-reference.md` | Referência histórica de consumo de API; comparar com OpenAPI canônica atual, **não usar paths legados como authority**. |

**Documentos auxiliares para comparação, não duplicar automaticamente:**
- `minha-delpi-ai-api/docs/knowledge/domains/global/normas-tecnicas-delpi.md` (cópia global existente).
- `minha-delpi-ai-api/docs/knowledge/domains/agents/minha-delpi-chat/produto-diretrizes-criacao-descricao.md` (versão adaptada).
- `minha-delpi-ai-api/docs/knowledge/sources/gpt-instructions/Understanding DELPI Intermediate Product Codes.md` (fonte da adaptação da família 50xx).
- `minha-delpi-ai-api/docs/knowledge/sources/gpt-instructions/drawing_analyser_instructions_full.md` (conteúdo ampliado; requer minimização).

**IMPORTANTE:** nome de arquivo, origem histórica e repositório não provam owner normativo atual. Identificar o responsável de negócio por Engenharia/cadastro/normas; até ratificação `BUSINESS_OWNER=TO_INVENTORY`. A decisão de cópia não decorre apenas deste documento.

## 4. Inventário de mecanismos antigos e contrato DAVI atual

No `minha-delpi-ai-api` existem `chat_glossary_retrieval_service.py`, `chat_learned_normalization_service.py`, `chat_meaning_discovery_service.py` e o port `vocabulary_term_repository_port.py`. Eles comprovam **implementação de mecanismos** de glossário/normalização, mas **não** comprovam a presença atual de entradas `TERM.` no banco, flags ativas ou uso em produção. Não copiar banco nem dependências internas entre bounded contexts.

No `api-delpi`, `app/content/davi_agent_intelligence.json` e `DaviAgentIntelligenceService` projetam diretivas governadas para discovery. A capability `search_products` continua sendo a fonte de consulta de catálogo, sob identidade do usuário. O corpus existente DAVI possui freeze, manifesto e tópico governados. Antes de adicionar documentos, revisar:
- `api-delpi/docs/integrations/evidence/davi-governed-knowledge-freeze-001.md`;
- `api-delpi/docs/integrations/evidence/davi-governed-knowledge-topics-v1.json`;
- `api-delpi/docs/integrations/evidence/davi-governed-knowledge-manifest-v1.json`;
- `api-delpi/app/content/davi_agent_intelligence.json`.

Não presumir que colocar arquivo no GitHub habilita retrieval no Agent Studio ou que `knowledge_orchestration` realiza busca documental por si só. Provider sync e prova de retrieval são gates distintos.

## 5. Comportamento-alvo proposto (não implementado)

Intenção `terminal pino` → reconhecer forma normativa `TERM. PINO` **com proveniência em norma ratificada** → executar a mesma consulta canônica `search_products` com variantes controladas, respeitando limites e paginação → validar relevância pela descrição retornada, não inventar item → responder com códigos e descrições literais da API, informando cobertura parcial quando cabível.

Proibir: equivalências inventadas, busca SQL genérica, aumento oculto de direitos, filtros de grupo usados como permissão, alterações de cadastro, interpretação de norma documental como valor operacional, fallback silencioso para docs não aprovados.

## 6. Acceptance e plano de execução futuro

1. Revalidar HEAD/`.cursor`, identificar owner de cadastro e curadoria, versão normativa vigente e consumidores (DAVI + outros).
2. Inventariar diferenças entre fontes e projeções; verificar licença interna, sensibilidade, conteúdo obsoleto, duplicações; aprovar allowlist documental e SHA/hashes.
3. Decidir se o owner mantém fonte normativa única com projeção gerada ou cópia versionada minimizada em `api-delpi`; registrar atualização e drift detection. **Não criar um segundo source of truth.**
4. Definir contrato READ da expansão semântica: preferencialmente resolver equivalências na camada de inteligência/presentation do DAVI; sem alterar semântica canônica ou contrato `search_products` sem aprovação do owner de Produto.
5. Testes positivos: `terminal pino` → 3 produtos `TERM. PINO` reais; `terminal faston`, `terminal olhal`, `terminal bandeira`; casos de 50xx somente se suportados pelas normas.
6. Testes negativos: texto sem equivalência aprovada; `pino de ajuste` não vira terminal; ambiguidade, zero resultados, paginação incompleta, termo com pontuação, descrição não padronizada; não inventar item.
7. Regressão de `search_products`, discovery, allowlist, OAuth end-user, backend AuthZ e 2nd-user negative AuthZ (quando disponível).
8. Evidências por etapa: source SHA, doc hashes, fixtures, testes, CI, deploy, provider discovery, retriever/provider sync, E2E positivo/negativo. Classificar PASS/FAIL/PENDING/TEST_NOT_RUN, sem inferir runtime de docs.

**Decision:** documentar lacuna e referências agora; **implementação/cópia/ingestão** somente via brief posterior e aprovação de arquitetura/owner. **Deploy:** NOT_APPLICABLE a esta alteração documental.
