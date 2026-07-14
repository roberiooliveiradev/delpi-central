# Regras de negócio — Auditoria 5S

> **Arquivo:** `docs/12-roadmap-e-evolucao/auditoria-5s/REGRAS-NEGOCIO.md`  
> **Status:** alinhado com qualidade (2026-05-28)  
> **Relacionados:** [ROADMAP.md](./ROADMAP.md), [CRITERIOS-CATALOGO.md](./CRITERIOS-CATALOGO.md)

---

## 1. Turnos

Turno da auditoria — valor **obrigatório** no cabeçalho. Opções fixas:

| Código interno | Rótulo na UI |
|----------------|--------------|
| `TURNO_1` | 1º |
| `TURNO_2` | 2º |
| `TURNO_3` | 3º |
| `ADMINISTRATIVO` | administrativo |

Não há cadastro livre de turnos: apenas estas quatro opções.

---

## 2. Área auditada

A área auditada **não** é texto livre na hora da auditoria. O fluxo é:

1. **Cadastro de áreas** — usuários com permissão de auditoria podem cadastrar novas áreas conforme a necessidade da filial.
2. **Seleção na auditoria** — ao iniciar ou editar o cabeçalho, a área é escolhida na lista cadastrada da filial.

### 2.1 Regras do cadastro

| Regra | Detalhe |
|-------|---------|
| Escopo | Cada área pertence a uma **filial** (`01` ou `02`) |
| Nome | Obrigatório; único por filial (case-insensitive) |
| Ativação | Área pode ser desativada (`active=false`); não aparece em novas auditorias |
| Histórico | Auditorias antigas mantêm referência à área mesmo se desativada depois |
| Responsável pela área | Informado no **cabeçalho da auditoria**, não no cadastro da área |

### 2.2 Modelo previsto

Tabela `audit_5s_areas`:

- `id`, `branch_code`, `name`, `active`, `created_at`, `created_by_user_id`

Endpoints previstos:

- `GET /quality/audit-5s/areas?branch=01` — listagem (ativas por padrão)
- `POST /quality/audit-5s/areas` — cadastrar nova área na filial
- `PATCH /quality/audit-5s/areas/{id}` — renomear ou desativar (soft)

---

## 3. Escala de notas por critério

| Valor | Rótulo | Elegível NC | Entra no cálculo |
|-------|--------|-------------|------------------|
| `1` | Ruim | Sim | Sim |
| `3` | Médio | Sim | Sim |
| `5` | Bom | Não | Sim |
| `NA` | Não se aplica | Não | Não |

Observação e foto permanecem **opcionais** em qualquer nota.

---

## 4. Validação — conclusão da avaliação

**Regra acordada:** todos os critérios do catálogo da auditoria **devem ter nota** antes de avançar para a fase de NC.

| Situação | Permitido concluir avaliação? |
|----------|-------------------------------|
| 48/48 critérios com nota (1, 3, 5 ou NA) | **Sim** |
| Qualquer critério sem nota | **Não** |
| Observação ou foto faltando | **Sim** (opcionais) |
| Cabeçalho incompleto (sem turno, área, etc.) | **Não** |

### 4.1 Comportamento na UI

- Barra de progresso: `critérios_com_nota / total_critérios` (ex.: 48 critérios).
- Botão **Concluir avaliação** desabilitado até 100% dos critérios avaliados.
- Lista ou indicador dos critérios pendentes (por senso).
- Mensagem clara: *“Todos os critérios precisam receber uma nota (1, 3, 5 ou NA) antes de continuar.”*

### 4.2 Comportamento na API

`PATCH /audits/{id}` com `status=evaluation_complete`:

- Retorna **422** se faltar nota em qualquer critério do `catalog_version` da auditoria.
- Retorna **422** se cabeçalho obrigatório estiver incompleto (data, `area_id`, turno, responsável pela área, ao menos um auditor).

**NA conta como nota preenchida** — atende à regra “todos precisam ter notas”.

---

## 5. Cálculo de percentuais

### 5.1 Por senso

```text
percentual_senso = (Σ notas aplicáveis) / (qtd_criterios_aplicaveis × 5) × 100
```

- **Aplicável:** nota 1, 3 ou 5.
- **NA:** excluído do numerador e do denominador.
- Se **todos** os critérios do senso forem NA → senso **não entra** na média geral.

### 5.2 Geral da auditoria

```text
percentual_geral = média(percentual_senso dos sensos com ≥1 critério aplicável)
```

### 5.3 Exemplo

Senso Utilização (8 critérios), 7 com notas somando 28 e 1 NA:

- Aplicáveis: 7 → max 35 pts  
- Percentual: 28/35 × 100 = **80%**

---

## 6. Transição para fase NC

Após `evaluation_complete`:

1. Sistema lista critérios com nota **1** ou **3** (`nc-candidates`).
2. Nota **5** e **NA** não geram candidatura automática.
3. Para cada candidato, equipe pode registrar NC (descrição, responsável, prazo, evidência).
4. Foto coletada na avaliação pode ser reutilizada como evidência padrão.

Critérios com nota 1 ou 3 **não exigem** NC obrigatória para fechar a auditoria — regra de fechamento será detalhada na Fase 5 com a qualidade.

---

## 7. Cabeçalho da auditoria

| Campo | Obrigatório | Origem |
|-------|-------------|--------|
| Código serial | Sim (automático) | `01-000123` / `02-000045` |
| Data da auditoria | Sim | Informada pelo auditor |
| Filial | Sim | Rota do plugin / `branch_code` |
| Área auditada | Sim | Seleção em `audit_5s_areas` |
| Turno | Sim | Enum fixo (seção 1) |
| Responsável pela área | Sim | Texto no cabeçalho |
| Auditores | Sim (≥1) | Usuários vinculados à auditoria |

### 7.1 Edição do cabeçalho

O cabeçalho permanece **editável** enquanto a auditoria **não** estiver em status terminal (`closed` ou `closed_without_nc_treatment`). Após o encerramento, a edição é bloqueada na UI e na API.

---

## 8. Status da auditoria

| Status | Significado |
|--------|-------------|
| `draft` | Cabeçalho e/ou avaliação em andamento |
| `evaluation_complete` | Todos os critérios com nota; pronto para NC |
| `nc_in_progress` | Fase de NC aberta |
| `closed` | Auditoria encerrada (NCs tratadas ou score 100%) |
| `closed_without_nc_treatment` | Encerrada por admin **sem** tratar NCs em aberto |

```text
draft → evaluation_complete → nc_in_progress → closed
                                     ↘ (admin) closed_without_nc_treatment
```

### 8.1 Encerramento administrativo sem tratar NCs

Usuários com permissão `auditoria-5s.admin.filial-01` ou `auditoria-5s.admin.filial-02` (rotas `/apps/auditoria-5s/filial-XX/admin`) podem, na filial correspondente, em auditorias `evaluation_complete` ou `nc_in_progress` com NC pendente:

1. Cancelar todas as NCs `open` / `in_progress` (`status=cancelled`).
2. Definir a auditoria como `closed_without_nc_treatment`.

Endpoint: `POST /quality/audit-5s/audits/{id}/close-without-nc-treatment` (exige admin da filial da auditoria).

---

## 9. Histórico

| Data | Nota |
|------|------|
| 2026-05-28 | Turnos: 1º, 2º, 3º, administrativo |
| 2026-05-28 | Área auditada: cadastro sob demanda por filial |
| 2026-05-28 | Validação: 100% dos critérios com nota (incl. NA) para concluir avaliação |
| 2026-07-14 | Status `closed_without_nc_treatment` + admin por filial (`auditoria-5s.admin.filial-XX`) |
