# 01 — Visão de produto

## 1. Definição

O **Minha DELPI Copilot** é a interface inteligente transversal da plataforma Minha DELPI. Ele deve acompanhar o usuário no Portal, compreender contexto, responder perguntas, explicar dados/processos, navegar pela plataforma e executar operações autorizadas.

Não é um chatbot separado. É uma nova forma de operar a mesma plataforma.

## 2. Promessa do produto

> O usuário pode dizer o que deseja alcançar; o Copilot entende o objetivo, encontra os recursos autorizados, explica o que fará, executa o necessário e apresenta o resultado de forma útil.

## 3. Pilares funcionais

### 3.1 Explicar

- explicar páginas, campos, indicadores e processos;
- explicar por que determinado dado está alto/baixo;
- explicar resultado de uma ação executada;
- explicar quais permissões/capabilities estão disponíveis;
- explicar erros sem expor detalhes sensíveis.

### 3.2 Consultar

- consultar dados corporativos;
- localizar entidades por linguagem natural;
- recuperar documentos e conhecimento;
- combinar resultados de múltiplas fontes;
- responder com referências e contexto suficiente.

### 3.3 Analisar

- comparar períodos, unidades, clientes, produtos e fornecedores;
- identificar causas prováveis com base em evidências;
- destacar anomalias, tendências e riscos;
- cruzar resultados de múltiplas APIs;
- produzir resumo executivo e recomendações contextualizadas.

### 3.4 Navegar

- abrir aplicativos autorizados;
- abrir rotas específicas;
- abrir entidade/detalhe;
- alternar aba/visão;
- aplicar filtros e contexto visual;
- retornar ao ponto anterior.

### 3.5 Executar

- criar registros;
- alterar registros;
- enviar solicitações;
- aprovar/rejeitar quando autorizado;
- cancelar/arquivar quando permitido;
- iniciar workflows;
- acionar integrações externas.

### 3.6 Produzir

- relatórios;
- resumos;
- análises executivas;
- e-mails e mensagens;
- artefatos derivados de dados e documentos.

## 4. Experiência-alvo

Exemplo:

> “Por que o produto 90264238 está atrasando entregas?”

O Copilot pode:

1. identificar o produto;
2. consultar estoque;
3. consultar carteira em aberto;
4. consultar ordens de produção;
5. consultar compras;
6. consultar fornecedores;
7. cruzar os dados;
8. explicar as causas;
9. oferecer próximos passos.

Usuário:

> “Abra isso no Portal de Suprimentos.”

O Copilot navega para a rota autorizada e aplica o contexto do produto.

Usuário:

> “Crie uma solicitação para Compras revisar o caso.”

O Copilot prepara a operação, mostra um resumo da alteração e solicita confirmação quando a policy exigir.

## 5. Personas

### Usuário operacional

Quer executar tarefas rapidamente sem decorar onde cada funcionalidade está.

### Analista

Quer cruzar dados, investigar causas e produzir explicações.

### Gestor

Quer síntese executiva, indicadores, riscos e recomendações.

### Especialista de área

Quer trabalhar dentro do portal do departamento com contexto persistente.

### Administrador

Quer administrar capabilities, políticas, integrações, auditoria e qualidade.

## 6. Princípios de UX

- linguagem natural como entrada, não como única interface;
- mostrar o que está acontecendo sem expor chain-of-thought;
- pedir confirmação somente quando necessário;
- não repetir perguntas para dados já conhecidos;
- manter contexto entre chat e página aberta;
- permitir correção/override do usuário a qualquer momento;
- deixar claro o que foi apenas analisado, preparado ou realmente executado;
- resultados acionáveis devem oferecer próximos passos válidos e autorizados.

## 7. Não objetivos

O Copilot não deve:

- obter mais permissão que o usuário;
- operar por cliques quando existe API/use case confiável;
- inventar endpoints, URLs ou IDs;
- manter lógica de negócio paralela à aplicação;
- criar um motor de IA diferente por departamento;
- tomar decisões administrativas/destrutivas fora de policy;
- substituir auditoria corporativa por texto gerado pelo LLM.

## 8. Métrica principal de sucesso

A métrica macro é **Task Completion Rate assistida pelo Copilot**, segmentada por:

- consulta;
- análise;
- navegação;
- escrita;
- workflow composto.

Ela deve ser acompanhada por segurança, precisão, tempo, custo e taxa de necessidade de intervenção humana.
