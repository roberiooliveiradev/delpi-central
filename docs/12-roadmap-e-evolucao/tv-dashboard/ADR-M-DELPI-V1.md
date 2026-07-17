# ADR — M DELPI v1

> **Status:** aceito para implementação futura  
> **Data:** 2026-07-16  
> **Fase:** 0 — decisão e proteção de baseline  
> **Não autoriza:** parser, compilador, runtime M, endpoints `/data/m/*` ou escrita v2

## Contexto e causa raiz

O editor já persiste uma IR JSON `dataTransform.steps`, mostra uma pseudo-sintaxe M no TypeScript, possui outro parser de pseudo-fórmula no Python e executa uma DSL de coluna calculada por AST Python. A execução tabular canônica é Python.

**Causa raiz:** a experiência visual evoluiu mais rápido que o contrato da linguagem, criando quatro representações com semânticas parcialmente diferentes. Ampliar regex ou manter interpretação em TypeScript aumentaria drift e superfície de ataque.

## Decisão

Adotar futuramente o perfil explicitamente limitado **M DELPI v1**, compilado somente no `tv-dashboard-api`:

```text
script M
  → lexer/parser Lark LALR
  → AST com SourceRange
  → análise semântica deny-by-default
  → TransformPlan tipado
  → tv_data_transform_service.py
```

Nesta Fase 0:

- `lark==1.3.1` fica fixado em `requirements.txt`;
- flags e limites existem em `tv_dashboard_settings.json`, todos inertes;
- nenhum módulo importa Lark e nenhum script M é interpretado;
- o executor legado e os parsers atuais não são ampliados;
- fixtures golden preservam o comportamento v1 em Python e TypeScript.

## Parser generator versus parser próprio

### Alternativas avaliadas

1. **Lark 1.3.1 + gramática LALR declarativa (escolhida).**
   - gramática revisável e versionável;
   - conflitos detectáveis na construção;
   - metadados de posição por token/regra;
   - custo de manutenção menor que lexer e precedência próprios;
   - dependência pequena, pura e fixada.
2. **Lexer + recursive descent próprios.**
   - controle total, porém exige implementar Unicode, comentários, precedência, recuperação de erro e ranges;
   - maior probabilidade de divergência e vulnerabilidades em entradas adversariais.
3. **Regex como parser.**
   - rejeitado: não representa gramática aninhada, precedência, comentários ou ranges de forma segura.
4. **Runtime M externo/completo.**
   - rejeitado: amplia I/O, conectores e semântica além do produto.

### POC documental

A POC da Fase 0 é deliberadamente não integrada. A gramática futura deve ser criada com:

```python
Lark(grammar, parser="lalr", propagate_positions=True, maybe_placeholders=False)
```

Critérios já congelados no corpus:

- `let/in`, identificadores cotados e Unicode;
- comentários de linha e bloco;
- listas, chamadas qualificadas, `each`, `if`, operadores e tipos;
- erro de sintaxe e semântico com range;
- rejeição de I/O, banco, avaliação dinâmica, reflexão, função de usuário e recursão;
- limites de bytes, profundidade, nós e etapas.

Não foi criada gramática executável nesta fase para não introduzir acidentalmente uma segunda autoridade antes dos contratos v2.

## Source ranges e diagnósticos

Todo nó futuro da AST carregará um `SourceRange` imutável, em coordenadas 1-based e fim exclusivo:

```text
startLine, startColumn, endLine, endColumn, startOffset, endOffset
```

O range deriva dos tokens do parser, nunca de busca textual posterior. Diagnósticos terão `code` estável, severidade, mensagem, range e hint. A API pode traduzir mensagens, mas testes e clientes dependem do código. AST, plano e ranges não serão persistidos como fonte de verdade.

## Threat model

### Ativos

- JWT e escopo RBAC;
- dados retornados pela `api-delpi`;
- disponibilidade e memória do serviço;
- isolamento entre usuários, playlists e filiais;
- integridade da configuração persistida.

### Fronteiras e ameaças

- script M é entrada não confiável;
- abuso de CPU/memória por profundidade, cardinalidade, pivot/join ou token enorme;
- tentativa de filesystem, rede, banco, credencial, reflexão ou avaliação dinâmica;
- referência a consulta irmã sem autorização;
- vazamento por cache entre usuários;
- logs contendo token, script sensível ou linhas de dados;
- Unicode confusável para contornar allowlist;
- erro convertido silenciosamente em `null`.

### Controles obrigatórios futuros

- whitelist deny-by-default por símbolo normalizado, sem resolução dinâmica;
- sem `eval`, `exec`, `Expression.Evaluate`, transpile para Python ou conectores;
- limites antes do fetch e deadline durante loops;
- DAG com detecção de ciclo e RBAC antes de disponibilizar consulta irmã;
- cache de compilação sem token e cache de preview com escopo de autorização;
- logs por hash/código, sem JWT ou linhas;
- erro estruturado, sem conversão implícita para `null`.

**Risco baseline preservado:** o cache atual distingue apenas `user` versus `service`, portanto dois JWTs de usuários diferentes compartilham a mesma chave. A Fase 0 testa e documenta esse fato sem alterar produção.

## Arquitetura canônica

| Responsabilidade | Fonte de verdade futura |
|---|---|
| sintaxe/semântica | compilador Python em `tv-dashboard-api` |
| AST/ranges/tipos | domain `data_query` |
| compile/mutate/dependências | application `m_query` |
| execução | fachada existente `tv_data_transform_service.py` |
| script persistido | `dataTransform.version=2`, `language=m-delpi-v1` |
| compatibilidade | adapter `steps` v1; dual-read/single-write |
| preview | fluxo server-side existente, evoluído por `targetStepName` |
| frontend | draft e render dos contratos HTTP; zero interpretação M |

O compilador produzirá `TransformPlan`; não haverá “M engine” paralela nem executor de produção TypeScript.

## Decisões de `plugin-ui`

- Não alterar `plugin-ui` na Fase 0.
- Evoluir o `DataTable` existente é a opção preferida para seleção, eventos de cabeçalho/célula, índice e `aria-selected`.
- Criar `DataGrid` somente se o contrato do `DataTable` ficar incoerente e no mesmo ciclo houver segundo consumidor real.
- Segundo consumidor candidato já existente: tabelas administrativas/métricas do `minha-delpi-chat` e tabelas de manutenção/qualidade que precisam seleção e menu; a migração deve ser comprovada no PR que alterar o kit.
- Ribbon, fórmula M, etapas e diagnósticos continuam locais por serem domínio M.
- CSS de componente compartilhado permanece exclusivamente em `plugins/plugin-ui/src/styles/**`; o MFE só define layout e tokens.

## Consequências

### Positivas

- uma autoridade semântica;
- parser auditável com ranges;
- compatibilidade mensurável por fixtures;
- frontend sem execução de linguagem;
- rollout protegido por flags.

### Custos e riscos

- dependência Python adicional fixada;
- gramática e semântica M continuam trabalho futuro;
- migração exige adapter legado e testes de paridade;
- Cancelar atualmente persiste durante edição;
- merge atual perde matches 1:N e erros de expressão viram `null`;
- política estática de filial vazia é permissiva;
- catálogo atual contém 232 operações GET.

## Critérios para revisar o ADR

- Lark deixar de atender ranges/LALR ou apresentar risco de supply chain;
- necessidade comprovada de recuperação incremental incompatível;
- mudança da autoridade de execução server-side;
- alteração incompatível do perfil, que exige `m-delpi-v2`, não expansão silenciosa.
