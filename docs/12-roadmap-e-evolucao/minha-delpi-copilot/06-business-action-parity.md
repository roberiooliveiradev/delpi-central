# 06 — Business Action Parity

## 1. Objetivo

Garantir que toda operação relevante disponível na UI possua um contrato de negócio reutilizável pelo Copilot.

A regra é:

> Se a UI consegue executar uma ação de negócio, o Copilot deve conseguir executar a mesma ação por meio do mesmo use case/API, desde que o usuário tenha permissão.

## 2. Anti-padrão que deve ser evitado

```text
Copilot
→ abre tela
→ procura botão
→ preenche DOM
→ clica salvar
```

Isso só é aceitável quando não existe outra integração possível e mediante decisão arquitetural explícita. O padrão normal é API/use case.

## 3. Padrão correto

```text
UI ──────────────┐
                 ▼
           Use Case/API
                 ▲
Copilot ─────────┘
```

## 4. Requisitos para uma operação ser Copilot-ready

Uma operação deve possuir:

- owner de negócio claro;
- use case único;
- contrato HTTP ou capability interna tipada;
- OpenAPI quando exposta via HTTP;
- input/output schema;
- erros previsíveis;
- permissões;
- sensitivity;
- confirmation policy;
- idempotência quando aplicável;
- auditoria/correlation id para writes;
- testes de contrato;
- apresentação genérica do resultado.

## 5. Leituras

Reads devem ser preferencialmente seguros para execução direta quando autorizados.

Exemplos:

```text
consultar produto
consultar estoque
consultar pedido
consultar solicitação
consultar indicador
consultar fornecedor
```

## 6. Escritas

Writes devem passar por policy determinística.

Exemplos:

```text
criar solicitação
alterar responsável
registrar comentário
editar cadastro
aprovar item
```

O planner propõe; policy decide confirmação e autorização.

## 7. Operações destrutivas

Devem possuir sensitivity explícita e confirmação forte.

Exemplos:

```text
cancelar
arquivar definitivamente
excluir
rejeitar irreversivelmente
```

## 8. Formulários

Formulário de UI não é o contrato da capability.

A capability deve derivar do schema do use case/API. O Copilot pode coletar os mesmos campos em linguagem natural.

Exemplo:

```text
Usuário: “Crie uma solicitação de matéria-prima para o item X, prioridade alta.”

Schema exige:
- item
- motivo
- prioridade
- unidade

Copilot possui item/prioridade
→ pergunta somente motivo/unidade ausentes
→ valida
→ confirma se policy exigir
→ executa
```

## 9. Validação

A validação deve ocorrer em duas camadas:

```text
Copilot binder/validator
→ feedback antecipado

API/use case
→ autoridade definitiva
```

Nunca relaxar regra do backend para facilitar a IA.

## 10. Erros e recuperação

O Copilot deve distinguir:

```text
validation_error
permission_denied
not_found
conflict
provider_unavailable
timeout
business_rule_violation
confirmation_required
```

A resposta deve explicar o que aconteceu e oferecer recuperação coerente.

## 11. Critério de cobertura

Cada app deve possuir uma matriz:

| Função visível na UI | Use case/API | OpenAPI | Capability | Permission | Sensitivity | Copilot-ready |
|---|---|---|---|---|---|---|

O objetivo de longo prazo é atingir paridade para todas as funções materiais.

## 12. Prioridade de migração

1. reads de alto uso;
2. criação de solicitações;
3. comentários/interações;
4. updates reversíveis;
5. aprovações;
6. operações destrutivas;
7. fluxos administrativos.

## 13. Benefício

A mesma evolução melhora UI, automação, integrações e IA porque força regras de negócio a saírem de componentes visuais e convergirem para contratos reutilizáveis.
