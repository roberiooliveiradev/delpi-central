# QA manual — Playbook 12 Fase 5

Checklist de smoke após refatoração do admin MFE. Executar com Portal + plugin `minha-delpi-chat` no ar.

## Pré-requisitos

- Tema escuro (padrão)
- Viewport 1440×900 (e opcional 768×1024)
- Usuário com permissões admin completas

## Por seção

### 1. Painel (`/admin/.../painel`)

- [ ] KPIs alinhados em grid, sem faixa vazia excessiva à direita
- [ ] Links de navegação rápida funcionam

### 2. Conhecimento

| Sub-aba | Verificar |
|---------|-----------|
| Documentos | `AdminTabHeader`, KPIs clicáveis (Total/Indexados/…), split ingestão + lista |
| Diretrizes | Strip de status, criar/editar diretriz |
| Comportamentos | Lista de skills, CRUD |
| Aprendizagem | KPIs em grid, abas Candidatos/Vocabulário/Memória/Regressão/Ajuste fino |

### 3. Agentes

| Sub-aba | Verificar |
|---------|-----------|
| Especialização | Nome legível + badge; UUID em `<code>`; mini dashboard com KPIs e gráfico legível |
| Simulação | Formulário e resultado |

### 4. Qualidade

| Sub-aba | Verificar |
|---------|-----------|
| Métricas | Blocos com eyebrow «Qualidade»; rankings e tabelas legíveis; largura útil ≥70% |
| Avaliações | Lista e painel de contexto |

### 5. Plataforma

| Sub-aba | Verificar |
|---------|-----------|
| Ferramentas | Strip LLM/Saúde/Ações; health table; catálogo por agente |
| Inteligência | Painel de políticas do pipeline |

### 6. Governança

| Sub-aba | Verificar |
|---------|-----------|
| Segurança | KPIs 24h; scan de mensagem; lista de eventos |
| Auditoria | KPIs; filtros; timeline; tabela unificada + paginação; detalhe ao clicar linha |

## Regressões a evitar

- UUID como título principal na lista de agentes
- Tabela de métricas sem borda/alinhamento
- Toolbar de gráfico ilegível (< 36px) no admin
- Eyebrows «Playbook NN» na UI operacional

## Automação local

```bash
cd plugins/minha-delpi-chat
npm run build
npm test -- --run src/ui/components/admin/
```
