# 09 — UX do Copilot

## 1. Princípio

O Copilot deve parecer parte da plataforma, não uma janela de chat isolada.

Ele acompanha o contexto do usuário, explica o que pode fazer, mostra progresso operacional e oferece ações úteis relacionadas ao estado atual da tela.

## 2. Superfícies

### Painel lateral persistente

Recomendação principal para uso cotidiano.

- abre sem tirar o usuário do app atual;
- conhece Workspace Context;
- pode navegar/alterar visão;
- exibe activity e resultados;
- permite continuar trabalhando na UI.

### Página completa de Copilot

Para:

- análises longas;
- workflows complexos;
- relatórios;
- histórico;
- agentes/projetos.

### Entry points contextuais

Botões como:

```text
Analisar com Copilot
Explicar este indicador
Perguntar sobre este cliente
Criar ação a partir deste resultado
```

Esses entry points devem passar `entityRefs`/`resultRefs`, não prompts gigantes hardcoded.

## 3. PLAN → EXECUTE → OBSERVE → EXPLAIN

A UI deve mostrar plano operacional resumido, não chain-of-thought.

Exemplo:

```text
Analisando atraso do item 90264238

✓ Estoque consultado
✓ Pedidos em aberto consultados
✓ Produção consultada
○ Consultando compras
○ Preparando análise
```

## 4. Estados visuais

```text
thinking
planning
waiting_for_input
waiting_for_confirmation
executing
partially_completed
completed
blocked
failed
cancelled
```

Cada estado deve ter copy clara e ação de recuperação quando possível.

## 5. Confirmação de writes

A confirmação deve ser apresentada como cartão estruturado contendo:

- ação;
- entidade;
- principais campos;
- efeito;
- risco/sensitivity;
- botões confirmar/cancelar.

Nunca esconder write atrás de uma resposta textual ambígua.

## 6. Resultados ricos

Reutilizar o pipeline de renderização existente para:

- texto;
- KPI;
- tabela;
- gráfico;
- árvore;
- dashboard;
- checklist;
- cards de entidades;
- timeline.

## 7. Ações após resposta

Após uma análise, o Copilot pode oferecer sugestões contextuais:

```text
[Abrir pedidos em atraso]
[Comparar com mês passado]
[Criar solicitação para Compras]
[Gerar relatório]
```

Somente capabilities autorizadas devem ser oferecidas.

## 8. Navegação perceptível

Quando o Copilot mudar a página:

- mostrar mensagem curta do que está fazendo;
- preservar a conversa;
- manter o painel aberto quando fizer sentido;
- atualizar Workspace Context após a navegação.

## 9. Context chips

O composer pode mostrar chips como:

```text
Portal Comercial
Cliente 000123
Filial 01
Período: setembro/2026
```

O usuário pode remover um chip para impedir que aquele contexto seja usado no próximo turno.

## 10. Correção pelo usuário

O usuário deve poder dizer:

> “Não, use a filial 02.”

O novo contexto explícito prevalece imediatamente.

## 11. Histórico e continuidade

Após F5/reload:

- conversa permanece;
- ações concluídas continuam marcadas;
- pending confirmation não deve ser reexecutada automaticamente;
- contexto visual é reestabelecido quando seguro/possível.

## 12. Explicabilidade operacional

Exibir quando útil:

- fontes consultadas;
- dados usados;
- período/filtros;
- actions executadas;
- limitações/partial failures;
- motivo de bloqueio por permissão/policy.

Não expor prompt interno ou chain-of-thought.

## 13. Feedback

Permitir feedback contextual:

- resposta útil/não útil;
- action errada;
- dado incorreto;
- navegação errada;
- análise incompleta.

Feedback deve alimentar evals/observabilidade, não modificar regra automaticamente em produção.

## 14. Acessibilidade

- activity compatível com leitores de tela;
- foco previsível após navegação;
- confirmações operáveis por teclado;
- status não depender somente de cor;
- mensagens de erro com ação recomendada.
