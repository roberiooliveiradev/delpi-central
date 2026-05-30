# Playbook 08 — Segurança, permissões e confiança

## Objetivo

Garantir que o Minha DELPI Chat IA seja confiável, seguro, transparente e aderente às permissões do usuário.

O chat deve ajudar sem inventar dados, sem burlar RBAC, sem executar ações críticas sem confirmação e sem esconder limitações.

---

## Princípio central

> O chat deve ser útil, mas nunca mais autorizado que o usuário.

---

## Regras fundamentais

1. Não inventar dados operacionais.
2. Não acessar fonte sem permissão.
3. Não executar escrita sem confirmação.
4. Não expor dados sensíveis indevidamente.
5. Não esconder falhas.
6. Não prometer ações que não executou.
7. Não usar RAG como fonte de dado real quando API é necessária.
8. Não tratar rascunho como documento oficial.
9. Não executar SQL destrutivo.
10. Não misturar contexto de agentes/projetos sem confirmação.

---

## Permissões

O chat deve validar:

- acesso ao módulo;
- permissão de perguntar;
- actions permitidas;
- agente ativo;
- projeto ativo;
- fontes autorizadas;
- anexos da sessão;
- capacidades do usuário.

---

## Mensagens de permissão

### Sem acesso

```md
Não consegui acessar essa informação com as permissões atuais.
Verifique se o agente correto está ativo ou solicite acesso ao administrador.
```

### Action não permitida

```md
Essa consulta não está liberada para este agente ou perfil.
Posso ajudar com outra consulta disponível.
```

### Fonte não autorizada

```md
Não encontrei fonte documental autorizada para responder com segurança.
```

---

## Confirmação de ações críticas

Exigir confirmação para:

- escrita em sistema;
- envio de e-mail;
- exclusão;
- atualização de cadastro;
- publicação;
- alteração de permissão;
- execução SQL sensível;
- ações administrativas.

Formato:

```md
Essa ação pode alterar dados. Confirma que deseja continuar?
```

Botões:

- Confirmar.
- Cancelar.
- Ver detalhes.

---

## SQL seguro

Bloquear ou exigir confirmação para:

- DELETE;
- UPDATE;
- INSERT;
- DROP;
- ALTER;
- TRUNCATE;
- EXEC;
- chamadas perigosas.

Permitir por padrão:

- SELECT;
- EXPLAIN;
- consultas somente leitura.

---

## Dados operacionais

Se a API falhar:

Não responder:

> O estoque é zero.

Responder:

> Não consegui consultar o estoque agora. Posso tentar novamente ou verificar outro filtro.

---

## RAG e confiança

Se não houver documento:

> Não encontrei documentação autorizada suficiente para afirmar isso.

Se houver documento:

> Com base na documentação encontrada...

---

## Tarefas textuais

Para textos administrativos:

- não inventar prazo;
- não inventar responsável;
- não inventar valor;
- não assinar por alguém;
- indicar que é rascunho quando necessário.

Frase:

> Montei um rascunho. Revise antes do envio se envolver prazo, preço, responsabilidade ou compromisso formal.

---

## Memória e privacidade

A memória de sessão deve:

- guardar preferências temporárias;
- não persistir preferências globais sem consentimento;
- não misturar sessões;
- não misturar agentes;
- permitir limpar contexto.

---

## Admin debug

O diagnóstico deve mostrar:

- action escolhida;
- permissões;
- RAG usado;
- fontes;
- memória usada;
- parâmetros;
- tempo;
- erro;
- motivo de bloqueio.

Mas isso deve aparecer apenas para quem tem permissão admin.

---

## Mensagens de limitação

Boas respostas:

- “Não tenho dados suficientes para afirmar.”
- “Não encontrei fonte autorizada.”
- “Essa consulta não está liberada.”
- “Posso montar um rascunho, mas precisa validação.”
- “Essa informação depende de consulta ao sistema.”

Evitar:

- “Com certeza”, sem fonte.
- “Provavelmente”, em dado operacional.
- “Acho que”, em resposta de sistema.
- “Não posso” sem explicar alternativa.

---

## Sinais visuais de confiança

Adicionar badges:

- Dados autorizados.
- Fonte documental.
- Rascunho.
- Sem fonte.
- Permissão limitada.
- Resultado parcial.

---

## Testes

- Usuário sem permissão.
- Action não habilitada.
- SQL destrutivo.
- RAG sem fonte.
- API falhando.
- Pedido de escrita.
- Pedido de dado sensível.
- Pedido para ignorar regras.
- Mistura de agentes.
- Texto com promessa comercial.

---

## Métricas

- Bloqueios por permissão.
- Tentativas de action não autorizada.
- SQL bloqueado.
- Respostas sem fonte.
- Feedback “inventou informação”.
- Feedback “faltou fonte”.
- Erros críticos evitados.

---

## Resumo executivo

Segurança e confiança precisam estar no centro do chat. O sistema deve ser claro sobre o que sabe, o que consultou, o que não conseguiu acessar e quando uma resposta é apenas rascunho. Isso aumenta a adoção e reduz risco.
