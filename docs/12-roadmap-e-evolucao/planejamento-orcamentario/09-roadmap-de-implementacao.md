# 09 — Roadmap de implementação

## Marcos de calendário

| Marco | Data |
|-------|------|
| Primeira versão | 18/09/2026 |
| Homologação e treinamento | 18/09–30/09/2026 |
| Lançamento | 01/10/2026 |

Janela útil de build após Fase 0 ≈ **6 semanas** (ago→set) — MVP deve ser cirúrgico.

---

## Classificação de requisitos

### Obrigatório para o lançamento (MVP)

| Item | Justificativa |
|------|---------------|
| Plugin MFE federado + manifesto + RBAC básico | Entrada na Minha DELPI |
| Domínio api-delpi + schema Postgres + migrations `up` | Persistência do ciclo |
| Exercício 2027 + config + status open/lock | Guarda-chuva |
| Carta/orientações + confirmação de leitura | Gate de processo (Carta) |
| Escopo usuário↔unidade/CC (admin manual) | Segurança de dados |
| CAPEX CRUD + listas + validações + bundle submit/approve/return | Coração do processo atual |
| Pessoal no shape da **planilha** (área/unidade) | Entregável existente |
| Consolidação CAPEX + headcount (visão diretoria) | Decisão gerencial |
| Export Excel detalhado (CAPEX + pessoal) | Substitui planilhas |
| Auditoria de transições e edições relevantes | Governança |
| Autosave com debounce + revision | Usabilidade / perda zero |

### Importante, mas adiável (pós-01/10 se necessário)

| Item | Motivo da postergação explícita |
|------|--------------------------------|
| PDF executivo polido | Excel cobre homologação; PDF pode ser fase 1.1 |
| Receita completa (clientes/prospects/projetos) | Material ausente; alto risco de escopo |
| Diff campo-a-campo na UI | Snapshot + audit bastam no MVP |
| Notificações e-mail ricas | Pode ser aviso in-app primeiro |
| Sync automático CC/fornecedor TOTVS | Catálogo admin + view sob demanda |
| Chat / TV / OpenAPI agent routes | Fora do caminho crítico do ciclo |

### Evolução futura

- Escrita ERP (PC/imobilizado)
- Série mensal de pessoal / cargo×CC (se Carta vencer planilha)
- API dedicada (só se critérios do ADR)
- Autosave colaborativo multi-cursor
- Importação em massa planilha legado
- Grupos econômicos / segmentos SX nativos

### Risco para o prazo

| Risco | Mitigação |
|-------|-----------|
| Modelo pessoal Carta vs planilha | Congelar MVP = planilha; evoluir depois |
| Receita sem especificação | Tirar do MVP ou spike 3 dias com negócio |
| Escopo CC sem cadastro confiável | Admin CSV + validação manual |
| Aprovação multinível complexa | 1 nível aprovador + Diretoria `.approve.all` |
| Volume CAPEX / export lento | Limiar async; índices Postgres |

### Dependências externas

- Texto Carta **2027** atualizado
- Apresentação Previsão de Receita
- Lista oficial CCs e aprovadores
- Homologação TOTVS (SELECT view CC, ROL)
- Treinamento usuários (janela 18–30/09)
- Perfis RBAC no Core após registro do manifesto

---

## Fases técnicas propostas

| Fase | Entrega | Alvo |
|------|---------|------|
| **0** | Descoberta (este pacote) | 04/08/2026 ✓ |
| **1** | Fundações: MFE vazio, módulo API, migrations, auth, exercício, Carta+confirmação, escopos | ~25/08 |
| **2** | CAPEX + workflow + audit + autosave | ~05/09 |
| **3** | Pessoal + consolidação + Excel | ~12/09 |
| **4** | Hardening, PDF opcional, treino, ajustes | 18–30/09 |
| **5** | Receita + integrações profundas | pós-lançamento |

## Autosave e concorrência (estratégia)

- Debounce 800–1500 ms; flush em blur/navigate/submit
- PATCH com `expected_revision`; 409 → reload server wins + toast
- Salvamento explícito “Salvar agora”
- Offline: fila local curta + banner; sem fake success
- Após `approved`/`locked`: rejeitar PATCH
- Não gravar a cada tecla

## Auditoria (eventos mínimos)

criação, edição (agrupada), importação, submit, approve, return, reject, reopen, lock, confirmação leitura, export, admin scope/config.

## Exportações

- Excel: openpyxl, abas Pessoal/CAPEX/Instruções, metadados exercício+filtros+usuário
- PDF: ReportLab resumo executivo (fase 1.1 se preciso)
- Download autenticado; job respeita escopo; retenção configurável
