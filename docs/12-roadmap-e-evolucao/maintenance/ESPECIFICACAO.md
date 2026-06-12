# Especificação — Manutenção (mini-aplicadores)

> **Nota (jun/2026):** especificação inicial derivada do legado WinForms **MiniAplicadores** — **primeiro submódulo** do produto `maintenance`. Implementação alvo: **Postgres + maintenance-api + plugin MFE**. Leitura TOTVS exclusivamente via **api-delpi**.

## 1. Visão geral

O submódulo **mini-aplicadores** registra trocas de peças em ferramentas de produção (grupos Protheus 23 e 24), quantifica **golpes** entre reposições e apoia **manutenção preventiva** com alertas por percentual de uso vs. média histórica.

### Objetivos

1. Substituir o cadastro local Access por Postgres centralizado na plataforma.
2. Manter integração TOTVS **única** na api-delpi (sem segundo ponto de consulta SQL).
3. Oferecer UX web integrada ao portal (filial, permissões, design system).
4. Preparar extensão do produto **Manutenção** para outros domínios além de ferramentaria.

## 2. Atores e permissões

| Ator | Capacidades |
|------|-------------|
| Operador filial | Registrar reposição, consultar histórico da ferramenta |
| Supervisor | Relatório preventivo, filtros, export (futuro) |
| Admin config | CRUD motivos, ajuste percentuais de status |
| Admin filial | CRUD na filial conforme RBAC |

## 3. Entidades funcionais

### 3.1 Persistidas (Postgres — API dedicada)

| Entidade | Descrição | Campos principais |
|----------|-----------|-------------------|
| **Reposição** | Troca de peça registrada | filial, codigo_ferramenta, codigo_peca, datas, golpes, motivo_id, observacao |
| **Motivo** | Causa da troca | descricao (QUEBRA, DESGASTE, …) |
| **Status peça** | Regra preventiva | descricao, operador (`>=`, `<`), percentual |

Seeds iniciais (legado): CRÍTICO ≥95%, ATENÇÃO ≥80%, OK <80%.

### 3.2 Consultadas (TOTVS — api-delpi)

| Entidade | Origem Protheus | Uso |
|----------|-----------------|-----|
| **Ferramenta** | SB1010 grupos 23/24 | Listagem e detalhe |
| **Peça** | SB1010 grupo 3019 | Peças substituíveis |
| **Ferramenta × Peça** | SG1010 + SB1010 | Combo peças da ferramenta |
| **Golpes** | SD4, SHY, SH4, SH6 | Contagem no período |
| **Componente** | Estrutura + estoque | Painel detalhe / FormInfo |

## 4. Regras de negócio

### 4.1 Reposição

- Filial obrigatória (`01` ou `02`).
- Ferramenta e peça obrigatórias; peça deve pertencer à amarração da ferramenta.
- Golpes > 0.
- Motivo obrigatório.
- `data_reposicao` > `data_ultima_reposicao` (mesma regra do legado).
- Exclusão lógica (`excluido`); auditoria `data_criacao` / `data_alteracao`.

### 4.2 Golpes automáticos (cadastro)

Ao criar reposição, o sistema deve:

1. Obter data da última reposição (Postgres) para ferramenta + peça + filial.
2. Consultar golpes TOTVS entre essa data e agora (api-delpi).
3. Pré-preencher campo golpes na UI (editável com validação).

### 4.3 Preventiva

Para cada par ferramenta/peça com última reposição:

```text
media_golpes     = média(histórico de golpes nas reposições)
golpes_atuais    = golpes TOTVS desde última reposição
percentual_uso   = golpes_atuais / media_golpes × 100   (se media > 0)
status           = primeira regra StatusPeca que satisfaz operador/percentual
```

Ordenação alertas: status mais severo primeiro; depois ferramenta/peça.

Cores UI: CRÍTICO (vermelho claro), ATENÇÃO (amarelo), OK (verde), SEM STATUS (cinza).

### 4.4 Filial

Sessão de filial obrigatória para operações (equivalente ao combo empresa do legado). Filiais conhecidas: 01 Matriz, 02 ES.

## 5. Telas (MFE)

| Tela | Legado | Função |
|------|--------|--------|
| Home | Home tab | Seleção filial |
| Ferramentas | Lista + filtros | Busca por código/descrição |
| Ferramenta | Detalhe tab | Histórico reposições, filtros, CRUD |
| Form reposição | FormReposicao | Nova/edição — formulário colapsável; botão «Nova reposição» no histórico |
| Componentes | FormInfo | Árvore componentes + estoque |
| Relatório | Relatório tab | Últimas reposições + alertas + detalhe com gráficos |
| Configuração | Config tab | Motivos + status |

### 5.1 Apresentação de listas (MFE)

Todas as telas de tabela usam o módulo canônico `DataTableSection` (`plugins/maintenance/src/components/data/`):

| Comportamento | Detalhe |
|---------------|---------|
| Paginação | **Anterior · Página N de M · Próxima** — default 20 linhas/página; estado via `useServerTable` |
| Origen dos dados | **Server-side** em todas as listas (ferramentas, reposições, componentes, alertas, últimas, motivos, status, filiais) |
| Query params | `page`, `page_size` (1–200), `sort_by`, `sort_dir` (`asc`/`desc`) + filtros por rota |
| Ordenação | Colunas com `sortable` + `sortValue`; clique alterna asc/desc |
| Ordenação padrão | Alertas: `% uso` desc; reposições: data desc; ferramentas: código asc |

**Select de peça (reposição):** somente códigos **`3019*`** — filtro na api-delpi (`B1_GRUPO = 3019`) e reforço em `GET /ferramentas/{codigo}/pecas` na API dedicada.

**Histórico de reposições:** gráfico de linha «Golpes por reposição» (`ReposicoesGolpesChart`) acima da tabela quando `total > 0`.

### 5.2 Gráficos (detalhe preventivo)

| Gráfico | Tipo | Detalhe |
|---------|------|---------|
| Uso vs. média | Barras verticais | Golpes atuais vs. média histórica + linha de referência |
| Histórico entre reposições | Linha + tendência | Série de golpes por ciclo + regressão linear tracejada (Recharts) |

Wireframe futuro preventiva parametrizável: legado `telas.md` (critério, limites por filial) — **Fase 4**.

## 6. Integrações

| Sistema | Direção | Contrato |
|---------|---------|----------|
| api-delpi | API plugin → api-delpi | Ver Playbook 01 |
| Core API | Portal → manifesto | `maintenance.manifest.json` |
| Postgres plugins | API dedicada | schema `maintenance` |

## 7. Não escopo (Fase 1–2)

- Autenticação própria (usa Keycloak do portal).
- Escrita no Protheus.
- Sincronização bidirecional Access após go-live.
- App WinForms em paralelo indefinido (desligar na Fase 3).

## 8. Critérios de aceite (MVP Fase 2)

- [ ] CRUD reposição por filial com validações legadas.
- [ ] Listagem ferramentas/peças idêntica ao filtro TOTVS legado.
- [ ] Golpes calculados via api-delpi com amostra validada.
- [ ] Relatório preventivo com status e ordenação equivalentes.
- [ ] Listas web com paginação e ordenação de colunas (paridade UX legado em telas longas).
- [ ] Permissões RBAC filial funcionando.
- [ ] Zero query Protheus fora da api-delpi.
