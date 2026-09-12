# 13 — Catálogo funcional do Minha DELPI Copilot

## 1. Objetivo

Este documento descreve as funcionalidades esperadas do Copilot como produto, independentemente da fase em que forem implementadas.

---

## 2. Conversa e entendimento

### 2.1 Linguagem natural

O usuário pode escrever pedidos curtos ou longos, com uma ou várias intenções.

Exemplos:

- “Abra o Portal Comercial.”
- “Mostre os pedidos atrasados deste cliente.”
- “Compare estoque, compras e vendas deste produto.”
- “Analise o problema, crie uma solicitação e avise o responsável.”

### 2.2 Pedidos compostos

O Copilot decompõe pedidos em goals/subtasks, preservando dependências.

### 2.3 Follow-up contextual

Entende continuidades como:

- “e no mês passado?”;
- “só filial 01”;
- “abra esse”;
- “faça o mesmo para o outro cliente”.

### 2.4 Clarification inteligente

Pergunta apenas dados obrigatórios ausentes e não repete informações já disponíveis.

---

## 3. Navegação

### 3.1 Abrir app

Abre qualquer app autorizado disponível no Portal.

### 3.2 Abrir rota

Navega para uma página/rota específica autorizada.

### 3.3 Abrir entidade

Abre detalhe de cliente, produto, solicitação, pedido, fornecedor ou outra entidade com deep link registrado.

### 3.4 Trocar visão

Pode selecionar abas, visualizações ou agrupamentos declarados pelo MFE.

### 3.5 Aplicar filtros

Aplica filtros visuais suportados sem alterar dados de negócio.

---

## 4. Contexto do workspace

### 4.1 Entidade atual

O Copilot sabe qual entidade o usuário está visualizando quando o MFE publica contexto.

### 4.2 Filtros e período

Usa filial, período e filtros ativos como contexto opcional.

### 4.3 Seleção atual

Pode compreender uma linha/item selecionado.

### 4.4 Context chips

Mostra no composer os contextos que serão usados e permite removê-los.

---

## 5. Consultas de negócio

### 5.1 Produtos

- cadastro;
- estoque;
- estrutura;
- preço;
- fornecedor;
- compras;
- vendas;
- inspeção;
- produção.

### 5.2 Comercial

- clientes;
- propostas;
- pedidos;
- carteira;
- faturamento;
- indicadores.

### 5.3 Suprimentos

- requisições;
- pedidos de compra;
- fornecedores;
- estoque;
- OTD;
- CPV;
- giro;
- rankings.

### 5.4 Produção

- ordens;
- programação;
- consumo;
- perdas;
- centros de trabalho;
- planejado x realizado;
- indicadores.

### 5.5 Financeiro

- indicadores autorizados;
- inadimplência;
- centro de custo;
- séries e comparações.

### 5.6 Qualidade

- inspeções;
- planos de ação;
- indicadores;
- ocorrências.

### 5.7 Solicitações

- listar;
- localizar;
- acompanhar;
- abrir detalhe;
- criar;
- comentar;
- atualizar quando autorizado.

> O catálogo concreto depende das APIs e permissões existentes. Esta seção descreve a capacidade-alvo, não autoriza inventar endpoints inexistentes.

---

## 6. Escritas e operações

### 6.1 Criar registros

Exemplos:

- solicitação;
- comentário;
- registro operacional permitido.

### 6.2 Atualizar registros

Exemplos:

- responsável;
- prioridade;
- campos de cadastro;
- status quando permitido.

### 6.3 Aprovar/rejeitar

Disponível somente com permission/sensitivity/policy adequadas.

### 6.4 Cancelar/arquivar

Exige confirmação forte quando impacto material.

---

## 7. Análise

### 7.1 Comparar

- períodos;
- filiais;
- produtos;
- clientes;
- fornecedores;
- indicadores.

### 7.2 Explicar variação

Busca evidências relevantes e resume fatores associados.

### 7.3 Análise multi-fonte

Cruza múltiplas APIs e resultados.

### 7.4 Anomalias e tendências

Destaca desvios quando dados suportarem essa conclusão.

### 7.5 Limitações

Se fontes faltarem ou falharem, declarar explicitamente a limitação.

---

## 8. Conhecimento e ajuda

### 8.1 Procedimentos

Explica processos usando RAG autorizado.

### 8.2 Ajuda contextual

Explica a página/app/campo atual.

### 8.3 Políticas e normas

Responde com grounding documental e acesso adequado.

### 8.4 Como fazer

Pode orientar o usuário e, quando possível, oferecer execução da capability correspondente.

---

## 9. Artefatos

### 9.1 Relatório

Gera relatório a partir de dados consultados.

### 9.2 Resumo executivo

Consolida resultados para gestão.

### 9.3 Mensagem/e-mail

Redige comunicação com base no contexto e facts obtidos.

### 9.4 Exportação

Integra com capacidades existentes de exportação quando disponíveis.

---

## 10. Recomendações

Após uma análise, pode sugerir próximos passos baseados em:

- goal;
- resultados;
- limitações;
- capabilities autorizadas;
- ações já executadas.

Não usar catálogo estático como authority permanente.

---

## 11. Workflows compostos

### 11.1 Investigar + agir

```text
consultar
→ analisar
→ navegar
→ criar ação
→ comunicar
```

### 11.2 Preparar + confirmar + executar

Write é preparado e resumido antes da confirmação quando policy exigir.

### 11.3 Partial completion

O Copilot entrega o que conseguiu e mostra passos bloqueados.

---

## 12. Histórico e continuidade

- manter conversa;
- preservar result references;
- reutilizar entidades/argumentos;
- retomar após F5;
- não reexecutar writes automaticamente no reload;
- distinguir ação concluída de ação somente preparada.

---

## 13. Administração futura

### 13.1 Capability governance

Admin pode inspecionar capabilities disponíveis, origem, sensitivity e status.

### 13.2 Provider/action governance

Habilitar/desabilitar integrações conforme modelo já existente de agents/actions.

### 13.3 Autonomy policy

Configurar limites L0–L5 por capability/grupo quando maturidade permitir.

### 13.4 Observability

Dashboards de uso, sucesso, falhas, custo, latency, confirmations e feedback.

### 13.5 Evals

Executar suites e simulações antes de rollout.

---

## 14. Notificações e continuidade futura

Em evolução posterior, workflows podem gerar acompanhamentos/alertas quando existir infraestrutura apropriada de tarefas/eventos.

Exemplos:

- avisar quando solicitação mudar de status;
- lembrar follow-up;
- monitorar indicador;
- continuar workflow após evento externo.

Isso deve ser implementado como mecanismo explícito de automação/eventos, não como promessa de execução em background do chat síncrono.

---

## 15. Funcionalidades fora do padrão

Não é objetivo padrão:

- controlar qualquer página pelo DOM;
- contornar APIs ruins com browser automation silenciosa;
- executar ação sem permission;
- escolher endpoint por hardcode;
- armazenar chain-of-thought;
- tornar cada departamento um agente isolado com engine própria.

---

## 16. Experiência final desejada

O usuário deve sentir que a Minha DELPI possui um copiloto que:

```text
sabe onde estou
+ entende o que quero
+ conhece o que posso fazer
+ encontra os dados certos
+ explica
+ executa
+ navega
+ mantém contexto
+ respeita minhas permissões
+ mostra claramente o que fez
```
