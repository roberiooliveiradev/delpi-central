# Roadmap — Administração Inteligente do Minha DELPI Chat

## Objetivo

Transformar o painel administrativo do Minha DELPI Chat em um centro operacional completo de governança da IA.

---

## Estado Atual

### Já implementado

- Estrutura visual administrativa
- Sistema de abas
- Componentização modular
- CSS isolado por componente
- Upload de documentos globais
- Exclusão e reindexação de documentos
- Diretrizes persistentes no banco
- Publicação e arquivamento de diretrizes
- Diretrizes ativas aplicadas no prompt real do chat
- Auditoria inicial
- Métricas operacionais

---

# Próximas Implementações

## 1. Aplicar diretrizes reais no prompt do chat

**Status: Concluído**

### Entregue

- Buscar diretrizes ativas no backend
- Montar bloco de diretrizes administrativas globais
- Injetar diretrizes no system prompt do chat
- Aplicar diretrizes no fluxo normal e no streaming
- Registrar diretrizes aplicadas na auditoria da mensagem

### Evidência funcional

O fluxo `chat.message.streamed` passou a registrar:

```txt
admin_guideline_count: 1
admin_guidelines:
- title: Quem sou eu?
- status: active
- category: behavior
```

---

## 2. Versionamento de diretrizes

**Status: Concluído**

### Objetivo

Permitir histórico e rollback das diretrizes administrativas.

### Entregue

- Criar tabela `ai_admin_guideline_versions`
- Gerar versão ao criar, editar, publicar e arquivar diretriz
- Listar histórico de versões por diretriz
- Exibir histórico de versões no painel administrativo

### Entregue adicional

- Comparar versões
- Restaurar versão anterior como novo rascunho

---

## 3. Edição de diretrizes

**Status: Concluído**

### Objetivo

Permitir manutenção contínua das diretrizes.

### Entregue

- Botão `Editar`
- Carregar dados atuais no formulário
- Salvar alteração como rascunho
- Publicar alteração
- Arquivar diretriz

---

## 4. Diretrizes por ambiente

**Status: Concluído**

### Objetivo

Permitir comportamento diferente por ambiente.

### Ambientes

- DEV
- HOMOLOG
- PROD

### Entregue

- Campo `environment`
- Filtro por ambiente no backend
- Exibição no admin
- Aplicação correta no prompt conforme ambiente atual

---

## 5. Melhorar Teste RAG

**Status: Concluído**

### Objetivo

Explicar por que o agente respondeu algo durante o teste de assertividade.

### Entregue

- `/admin/rag/test` retorna diretrizes ativas aplicadas
- `/admin/rag/test` retorna chunks encontrados
- `/admin/rag/test` retorna documentos usados
- `/admin/rag/test` retorna score semântico
- Frontend exibe `Diretrizes aplicadas`
- Frontend exibe `Documentos acionados`
- Frontend exibe `Chunks usados`
- Frontend exibe score e prévia da resposta
- Layout da aba Diretrizes foi reorganizado para melhorar leitura do teste
- `/admin/rag/test` retorna `debugContext` seguro
- Frontend exibe contexto seguro com contagem de diretrizes, documentos e chunks
- Frontend exibe preview sanitizado do contexto usado no teste
- `/admin/rag/test` retorna comparação estrutural com/sem diretrizes
- `/admin/rag/test` retorna comparação estrutural com/sem RAG
- Frontend exibe comparação de contexto com/sem diretrizes e com/sem RAG
- Frontend diferencia visualmente:
  - conhecimento global;
  - diretrizes administrativas;
  - anexos de conversa;
  - ferramentas/actions.

---

## 6. Ferramentas reais

**Status: Concluído**

### Objetivo

Transformar a aba Ferramentas em painel operacional real.

### Entregue

- Aba Ferramentas conectada aos endpoints administrativos reais
- Exibição de health checks de tools
- Listagem de actions disponíveis
- Exibição de status, provider, chamadas 24h e última execução
- Resumo inicial de governança/permissões
- Exibição de capabilities reais do usuário atual
- Exibição de permissões reais retornadas pelo backend
- Exibição de permissão para uso/gestão de tools e agentes
- Listagem de providers OpenAPI reais
- Listagem de actions reais disponíveis
- Exibição de providers/actions por agente selecionado
- Consulta de logs recentes por action/provider
- Exibição de erros recentes por action/provider

---

## 7. RBAC administrativo

**Status: Concluído no escopo atual**

### Objetivo

Controlar acesso granular às ações administrativas.

### Perfis previstos

- Admin
- Operador
- Auditor
- Viewer

### Entregue

- Endpoint `/admin/rbac/summary`
- Perfis administrativos derivados das permissões atuais
- Matriz de permissões administrativas
- Exibição de RBAC no painel administrativo
- Exibição de permissões brutas do usuário atual
- Bloqueios granulares na aba Conhecimento
- Bloqueios granulares na aba Diretrizes
- Bloqueios granulares na aba Ferramentas
- Bloqueio de visualização da aba Auditoria sem permissão

### Evoluções futuras

- Aplicar bloqueios granulares em exportação de auditoria quando a exportação avançada for implementada
- Separar formalmente perfis Admin, Operador, Auditor e Viewer no backend/core
- Controlar exportação e ações sensíveis por permissão granular conforme novas ações forem adicionadas

---

## 8. Métricas avançadas

**Status: Parcialmente concluído**

### Objetivo

Melhorar observabilidade do chat.

### Entregue

- Total de eventos auditáveis nas últimas 24h
- Taxa de uso de ferramentas nas últimas 24h
- Taxa de erro nas últimas 24h
- Distribuição de eventos por ação
- Distribuição de eventos por contexto
- Distribuição de erros por ação
- Aba de métricas reorganizada para observabilidade operacional
- Instrumentação de latência no envio normal de mensagens
- Instrumentação de latência no streaming de mensagens
- Estimativa de tokens por prompt/resposta
- Agregação de latência média nas últimas 24h
- Agregação de tokens estimados nas últimas 24h
- Custo estimado configurável por 1K tokens de prompt/resposta

### Ainda falta

- Tabela administrativa de custo por provider/modelo
- Falhas RAG
- Assertividade por teste
- Métricas por agente
- Métricas por usuário/perfil

---

## 9. Auditoria avançada

**Status: Pendente**

### Objetivo

Criar auditoria operacional completa.

### Implementar

- Paginação real
- Filtros backend por:
  - ação;
  - contexto;
  - usuário;
  - data inicial;
  - data final.
- Exportação
- Timeline
- Correlação de eventos
- Visualização detalhada do evento

---

## 10. Simulação completa do agente

**Status: Pendente**

### Objetivo

Validar comportamento antes de publicar mudanças.

### Implementar

- Simular pergunta
- Mostrar prompt final
- Mostrar diretrizes aplicadas
- Mostrar chunks usados
- Mostrar tool calls previstas/executadas
- Comparar resposta com e sem diretrizes
- Comparar resposta com e sem RAG

---

## 11. Gestão de conhecimento avançada

**Status: Pendente**

### Objetivo

Melhorar curadoria da base global.

### Implementar

- Tags
- Categorias
- Prioridade
- Score de qualidade
- Namespaces
- Agrupamento por domínio
- Diferenciação visual por tipo de fonte
- Filtros avançados

---

## 12. Pipeline inteligente de ingestão

**Status: Pendente**

### Objetivo

Melhorar qualidade do RAG.

### Implementar

- Chunk adaptativo
- Deduplicação
- Limpeza automática
- Extração por tipo de arquivo
- Normalização de conteúdo
- Sumarização auxiliar
- Metadados enriquecidos

---

## 13. Sistema de avaliação de respostas

**Status: Pendente**

### Objetivo

Permitir aprendizado contínuo.

### Implementar

- Feedback positivo/negativo
- Comentário do usuário
- Score de resposta
- Registro de falha
- Sugestão de nova diretriz
- Sugestão de melhoria de documento
- Painel de respostas problemáticas

---

## 14. Agentes especializados

**Status: Pendente**

### Objetivo

Permitir múltiplos comportamentos especializados.

### Exemplos

- Agente RH
- Agente TI
- Agente Qualidade
- Agente Engenharia
- Agente Compras
- Agente Produção

### Implementar

Cada agente poderá ter:

- diretrizes próprias;
- tools próprias;
- RAG próprio;
- permissões próprias;
- contexto próprio de conversa;
- métricas próprias.

---

## 15. Segurança operacional

**Status: Pendente**

### Objetivo

Blindar comportamento da IA.

### Implementar

- Proteção contra prompt injection
- Validação de tool calls
- Sanitização de entradas
- Sanitização de contexto documental
- Limites operacionais
- Bloqueio de exposição de secrets
- Políticas globais obrigatórias
- Auditoria de tentativas suspeitas

---

# Status consolidado

## Concluído

- Estrutura visual administrativa
- Sistema de abas
- CSS modularizado
- Componentização por área
- Base global de conhecimento
- Upload, exclusão e reindexação de documentos
- Diretrizes persistentes
- Publicação e arquivamento de diretrizes
- Versionamento de diretrizes
- Comparação de versões de diretrizes
- Restauração de versões anteriores como rascunho
- Aplicação de diretrizes ativas no prompt real
- Teste RAG exibindo diretrizes aplicadas
- Teste RAG exibindo documentos acionados
- Teste RAG exibindo chunks usados
- Teste RAG exibindo contexto seguro de depuração
- Teste RAG comparando contexto com e sem diretrizes
- Teste RAG comparando contexto com e sem RAG
- Teste RAG diferenciando visualmente tipos de fonte
- Refatoração visual da aba Diretrizes
- Auditoria inicial
- Métricas iniciais

## Em andamento

- Melhor explicabilidade do comportamento do agente

## Pendente

- Edição completa de diretrizes
- Diretrizes por ambiente
- Ferramentas reais no painel administrativo
- RBAC administrativo aplicado ao painel atual
- RBAC administrativo avançado
- Métricas avançadas
- Auditoria avançada
- Simulação completa do agente
- Gestão avançada de conhecimento
- Pipeline inteligente de ingestão
- Avaliação de respostas
- Agentes especializados
- Segurança operacional avançada

---

# Próxima ação recomendada

Implementar o item:

## 5. Melhorar Teste RAG

### Primeiro passo

Alterar o backend de `/admin/rag/test` para retornar:

```json
{
  "appliedGuidelines": [
    {
      "id": "...",
      "title": "...",
      "category": "behavior",
      "status": "active"
    }
  ]
}
```

### Depois

Alterar a aba Diretrizes no frontend para exibir:

- Diretrizes aplicadas;
- documentos acionados;
- chunks usados;
- score;
- prévia da resposta.

---

# Regra Operacional

Sempre consultar este documento antes de:

- criar funcionalidades;
- alterar estrutura;
- mudar layout;
- criar novos fluxos;
- adicionar endpoints;
- criar migrations;
- alterar comportamento do agente.

Objetivo:

garantir consistência arquitetural e evolução controlada do Minha DELPI Chat.
