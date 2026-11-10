# Pesquisa de satisfação de clientes — Índice mestre de requisitos

> **Status:** requisitos funcionais consolidados para especificação; implementação **não comprovada**.  
> **Escopo:** evolução do Portal Comercial com persistência das pesquisas sob responsabilidade da API Comercial.  
> **Referência da leitura:** branch `main`, HEAD `4a79fde42be0fdfa3eb4f1c2ecb0bdd5135e708c` antes da criação deste índice (10/11/2026).

## Como usar este arquivo

**Este é o ponto de entrada.** Primeiro consulte a linha do requisito; só abra o documento em **Detalhe** quando precisar aprofundar aquela frente. Este índice descreve *o que* foi pedido/decidido, **não** comprova que o recurso já esteja implementado e não aprova automaticamente backlog, CRUD ou novas abstrações.

**Fontes e prioridade:** (1) [Plano de Monitoramento da Satisfação dos Clientes — Delpi] — documento integral de 5 páginas anexado às **fontes do projeto** (não há cópia integral publicada nesta pasta); (2) [registro das decisões da entrevista](./OPEN-DECISIONS.md), que complementa o plano quando o usuário decidiu um comportamento; (3) fontes técnicas canônicas, a identificar por frente. A página 1 do plano contém exemplos gerais de métodos de pesquisa; **as seções 1–10 e as decisões específicas** governam o produto proposto.

**Estados na tabela:** `DEFINIDO` = decisão funcional informada pelo solicitante; `FONTE DEFINIDA` = especificação explícita no plano; `DEFINIDO COM VALIDAÇÃO` = intenção definida, condicionada a verificação normativa; `TO_INVENTORY` = evidência/contrato técnico ainda a levantar. *Nenhum desses estados significa implementado, testado ou aprovado para release.*

**Regra antirretrabalho:** alterar a linha **somente** quando houver decisão nova, evidência canônica ou impedimento real para implementar/testar. Nunca reabrir assunto já respondido por mera hipótese. Quando uma linha exigir detalhes que não caibam aqui, criar **um documento por assunto necessário nesta mesma pasta** e adicionar o link na coluna Detalhe. Não criar arquivos vazios nem reproduzir todo o conteúdo das fontes. Um requisito fica **pronto para execução** quando regra, owner, contrato a respeitar, critérios verificáveis e dependências da frente estiverem suficientes; revisão técnica é limitada à frente, não a um inventário global recorrente.

## Tabela de requisitos

### 01. Público, campanhas e questionário

| ID | Tema | Requisito / decisão | Base | Estado | Detalhe / verificação |
|---|---|---|---|---|---|
| CSS-001 | Público | Selecionar por campanha empresas já cadastradas no TOTVS e consultáveis pelo Portal; sem novo cadastro de clientes. | Decisão Q02–Q03 | DEFINIDO | [Q02–Q03](./OPEN-DECISIONS.md); inventariar rota API DELPI |
| CSS-002 | Público | Uma única resposta definitiva por empresa em cada campanha; identificação vinculada à empresa, não à pessoa física. | Decisão Q01/Q04 | DEFINIDO | [Q01/Q04](./OPEN-DECISIONS.md) |
| CSS-003 | Campanha | Usar duas campanhas anuais como referência (maio/junho e novembro/dezembro), com datas livremente configuráveis. | Plano §2 p.2; decisão Q05 | DEFINIDO | [Q05](./OPEN-DECISIONS.md) |
| CSS-004 | Campanha | Abertura e encerramento automáticos pelas datas; aceitar respostas apenas durante a janela válida. | Decisão Q05 | DEFINIDO | [Q05](./OPEN-DECISIONS.md); definir fuso e instante de corte na implementação |
| CSS-005 | Questionário | Preservar as 15 perguntas, texto e ordem: dez dimensões (1–5), satisfação geral (1–5), NPS (0–10), três abertas. | Plano §§3–6 p.2–3; decisão Q09 | DEFINIDO | [Q09](./OPEN-DECISIONS.md); texto integral na fonte do projeto |
| CSS-006 | Questionário | Exigir satisfação geral e NPS; nas dez dimensões permitir 'Não se aplica'; perguntas abertas opcionais. | Decisão Q08 | DEFINIDO | [Q08](./OPEN-DECISIONS.md); ausência em dimensão/rascunho não definida |
| CSS-007 | Questionário | Revisão antes de enviar; após submissão confirmada, resposta imutável inclusive com campanha aberta. | Decisão entrevista 10 / Q08 | DEFINIDO | [Q08](./OPEN-DECISIONS.md) |

### 02. Convites e respostas

| ID | Tema | Requisito / decisão | Base | Estado | Detalhe / verificação |
|---|---|---|---|---|---|
| CSS-008 | Convite | Gerar link exclusivo e obrigatório por empresa/campanha; compartilhar sem criar segunda resposta. | Decisão Q02 | DEFINIDO | [Q02](./OPEN-DECISIONS.md); inventariar segurança do link |
| CSS-009 | Convite | Pré-preencher contato/e-mail da consulta ao ERP; permitir edição no convite sem atualizar cadastro mestre. | Decisão Q03 | DEFINIDO | [Q03](./OPEN-DECISIONS.md) |
| CSS-010 | Convite | Enviar convite diretamente no Portal somente por e-mail, sob ação de Marketing ou Manager. | Decisão Q06 | DEFINIDO | [Q06](./OPEN-DECISIONS.md); inventariar serviço de envio |
| CSS-011 | Convite | Copiar link para envio manual via WhatsApp, Teams, e-mail externo ou outros canais; sem integração de disparo desses aplicativos. | Decisão Q06 | DEFINIDO | [Q06](./OPEN-DECISIONS.md) |
| CSS-012 | Convite | Exibir empresas pendentes; permitir reenvio manual usando mesmo link; sem lembretes automáticos. | Decisão Q07 | DEFINIDO | [Q07](./OPEN-DECISIONS.md); limites operacionais não especificados |

### 03. Indicadores, filtros e visualizações

| ID | Tema | Requisito / decisão | Base | Estado | Detalhe / verificação |
|---|---|---|---|---|---|
| CSS-013 | Indicadores | IGS = média aritmética das notas da pergunta geral (1–5), igual peso por empresa; sem ponderar faturamento. | Plano §4 p.3; decisão entrevista 11/Q10 | DEFINIDO | [Q10](./OPEN-DECISIONS.md) |
| CSS-014 | Indicadores | NPS = % promotores (9–10) menos % detratores (0–6); neutros (7–8) no denominador; igual peso por empresa. | Plano §5 p.3; decisão entrevista 12/Q11 | DEFINIDO | [Q11](./OPEN-DECISIONS.md) |
| CSS-015 | Indicadores | Calcular médias das dez dimensões só com notas válidas; 'Não se aplica' não é nota nem entra na média. | Plano §§3/9 p.2/4; decisão Q08 | DEFINIDO | [Q08](./OPEN-DECISIONS.md) |
| CSS-016 | Indicadores | Classificar satisfação geral: 1–2 críticos, 3 neutros/intermediários, 4–5 satisfeitos; sem classificação individual por dimensão. | Plano §§3/9 p.2/4; decisão entrevista 13/Q12 | DEFINIDO | [Q12](./OPEN-DECISIONS.md) |
| CSS-017 | Indicadores | Taxa de resposta = empresas respondentes ÷ empresas convidadas, por campanha. | Plano §9 p.4 | FONTE DEFINIDA | [Plano no projeto](./README.md); validar semântica de convite no contrato |
| CSS-018 | Indicadores | Acompanhar evolução dos indicadores e comparar com pesquisa anterior, em visão semestral/anual. | Plano §§8–9 p.4 | FONTE DEFINIDA | [Q14](./OPEN-DECISIONS.md); mesma base de público não presumida |
| CSS-019 | Visualização | Exibir filtros: cliente, segmento, vendedor, região, tempo de relacionamento, volume/faturamento e estratégico versus demais. | Plano §7 p.3 | FONTE DEFINIDA | [Q13](./OPEN-DECISIONS.md); inventariar fontes e períodos |
| CSS-020 | Visualização | Oferecer comparação simples Geral / Estratégicos / Demais para satisfação geral e dimensões, como no exemplo do plano. | Plano §7 p.3 | FONTE DEFINIDA | [Q13](./OPEN-DECISIONS.md); valores ilustrativos não são dados reais |
| CSS-021 | Visualização | Disponibilizar IGS, NPS, taxa de resposta, médias dimensionais, % satisfeitos/críticos, evolução e ações concluídas. | Plano §9 p.4 | FONTE DEFINIDA | [Q20](./OPEN-DECISIONS.md); evitar criar painéis além do necessário |

### 04. Consolidação e tratamento

| ID | Tema | Requisito / decisão | Base | Estado | Detalhe / verificação |
|---|---|---|---|---|---|
| CSS-022 | Consolidação | Até cinco dias após encerramento, consolidar indicadores, evolução, comentários relevantes e clientes críticos. | Plano §8 etapa 1 p.4 | FONTE DEFINIDA | [Q20](./OPEN-DECISIONS.md); prazo do processo, não automação presumida |
| CSS-023 | Tratamento | Classificar problemas nas oito categorias: Produto, Qualidade, Entrega, Atendimento, Comercial, Técnico, Comunicação e Preço. | Plano §8 etapa 2 p.4 | FONTE DEFINIDA | [Q15](./OPEN-DECISIONS.md); regra automática de triagem não prevista |
| CSS-024 | Tratamento | Registrar por oportunidade relevante: problema, cliente, causa, ação, responsável, prazo e status. | Plano §8 etapa 3 p.4 | FONTE DEFINIDA | [Q16](./OPEN-DECISIONS.md); status concretos a especificar no menor contrato |
| CSS-025 | Tratamento | Marketing e Manager operam triagem, atribuição/acompanhamento de ações e registro de retornos/reavaliações. | Decisão Q04 e complemento 10/11 | DEFINIDO | [Q15–Q17](./OPEN-DECISIONS.md) |
| CSS-026 | Tratamento | Acompanhar retorno aos clientes com críticas relevantes e sua reavaliação; não presumir disparo automático. | Plano §8 etapa 4 p.4 / §10 p.5 | FONTE DEFINIDA | [Q17](./OPEN-DECISIONS.md); canal específico não definido |
| CSS-027 | Indicadores | Planos de ação concluídos = número de ações concluídas ÷ número de ações identificadas. | Plano §9 p.4 | FONTE DEFINIDA | [Q16/Q20](./OPEN-DECISIONS.md) |

### 05. Acesso, dados e arquitetura

| ID | Tema | Requisito / decisão | Base | Estado | Detalhe / verificação |
|---|---|---|---|---|---|
| CSS-028 | Acesso | `commercial.marketing` (novo requisito) e `commercial.manager` (existência relatada) gerem campanhas, convites, respostas individualizadas e tratamento. | Decisão Q04 | DEFINIDO | [Q04](./OPEN-DECISIONS.md); validar permissões reais no backend |
| CSS-029 | Acesso | Demais usuários autorizados do Portal Comercial acessam somente resultados agregados, sem configuração ou respostas por empresa. | Decisão Q04 | DEFINIDO | [Q04](./OPEN-DECISIONS.md); evitar reidentificação por filtros |
| CSS-030 | Dados | Guardar histórico de campanhas, convites, respostas e acompanhamento em tabelas/esquemas no domínio da API Comercial. | Decisão 10/11 / Q18–Q19 | DEFINIDO | [Q18–Q19](./OPEN-DECISIONS.md); contratos físicos TO_INVENTORY |
| CSS-031 | Dados | Preservar histórico por tempo indeterminado para análise plurianual; revisar proteção e necessidade de dados pessoais conforme LGPD. | Decisão 10/11 / Q18 | DEFINIDO COM VALIDAÇÃO | [Q18](./OPEN-DECISIONS.md); validação jurídica/privacidade necessária |
| CSS-032 | Arquitetura | Reutilizar cadastro do TOTVS via API DELPI; a API Comercial é autoridade das regras e dados da pesquisa; frontend apenas interface. | Decisão Q03/Q19 | DEFINIDO / TO_INVENTORY | [Q03/Q19](./OPEN-DECISIONS.md); verificar owners e consumidores reais |
| CSS-033 | Implementação | Inventariar por frente antes de codificar: HEAD, branch, contratos, rotas, permissões backend, consumidores e testes; menor diff correto. | Decisão 10/11 / Q19 | TO_INVENTORY | [Q19](./OPEN-DECISIONS.md); não transformar em inventário global interminável |
| CSS-034 | Segurança | Autorizar gravações/consultas restritas no backend; validar dados, auditar operações, proteger tokens de convite e dados pessoais. | Diretrizes do projeto; decisões Q04/Q18 | TO_INVENTORY | [Q04/Q18](./OPEN-DECISIONS.md); conformidade e controles de segurança exigidos |

## Limites confirmados e critérios de avanço

- **Fora do escopo já decidido:** disparos diretos por WhatsApp/Teams; lembretes automáticos; segunda resposta por empresa/campanha; edição após envio definitivo; personalização das quinze perguntas por campanha; cadastro mestre paralelo ao TOTVS.
- **Não inferir sem evidência:** rotas, tabelas físicas, enums de status, autorização já implementada, envio em lote/agendado, alertas automáticos, novas telas ou módulos complexos.
- **Aprofundar só ao implementar:** contrato da consulta de clientes, envio de e-mail, token de convite, modelo de campanhas/respostas, cálculos, filtros, permissões, auditoria e critérios de aceite. Cada frente deve identificar arquivos e testes reais.
- **Pendências que não reabrem negócio por si só:** detalhes de corte/fuso; rascunho/resposta interrompida; limites de reenvio; status das ações; canal de retorno; disponibilidade dos segmentos. Decidir o mínimo necessário apenas se bloquear uma frente.
- **Cuidados obrigatórios:** retenção histórica não dispensa LGPD; garantir finalidade, minimização, transparência, segurança, controle de acesso e revisão periódica da necessidade de dados pessoais.

## Documentos desta pasta

| Documento | Função | Quando ler |
|---|---|---|
| [README.md](./README.md) | Contexto e fontes resumidas | Para entender por que esta frente existe |
| **REQUIREMENTS-INDEX.md** (este arquivo) | Índice navegável e estado dos requisitos | Sempre, antes de investigar ou especificar uma frente |
| [OPEN-DECISIONS.md](./OPEN-DECISIONS.md) | Registro histórico das decisões, evidências e ressalvas | Somente quando a linha exigir detalhe de negócio |
| Documento detalhado novo | Criar **quando necessário**, com ID(s) relacionado(s), owner, evidência, contrato, critérios de aceite e link no índice | Só na frente correspondente |

**Critério de conclusão desta etapa:** organização documental, não implementação. Próxima atividade: escolher uma frente delimitada, inventariar seu contrato atual e produzir sua especificação/testes sem reabrir as decisões já fechadas.
