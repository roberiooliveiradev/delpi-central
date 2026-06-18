# Fase 0 — Validação views Inspeções de Entrada

> Procedimento para confirmar views TOTVS antes de homologar api-delpi + plugin em um ambiente.

---

## Pré-requisitos

- Container `delpi-api-delpi` em execução com variáveis `TOTVS_DB_*` (ou `DB_*`) válidas
- Views publicadas no SQL Server:

```text
dbo.vw_minha_delpi_inspecoes_entrada_resumo_filial
dbo.vw_minha_delpi_inspecoes_entrada_pendentes
dbo.vw_minha_delpi_inspecoes_entrada_pendentes_fornecedor
dbo.vw_minha_delpi_inspecoes_entrada_rejeitadas_ensaiador
dbo.vw_minha_delpi_inspecoes_entrada_historico_tela
```

---

## Execução

### No container (recomendado)

```bash
docker exec delpi-api-delpi python scripts/validate_inspecoes_entrada_views.py
```

### Com relatório JSON

```bash
docker exec delpi-api-delpi python scripts/validate_inspecoes_entrada_views.py \
  --json /tmp/inspecoes-entrada-fase0.json

docker cp delpi-api-delpi:/tmp/inspecoes-entrada-fase0.json ./inspecoes-entrada-fase0.json
```

### No host (venv local)

```bash
cd api-delpi
python scripts/validate_inspecoes_entrada_views.py
```

---

## O que o script verifica

Para **cada view** × **filial `01` e `02`**:

1. `COUNT(*)` com filtro `Filial = ?`
2. `SELECT TOP 10 *` (amostra)
3. Lista de colunas retornadas
4. Captura de erro SQL (view ausente, permissão, etc.)

---

## Critério de sucesso

| Métrica | Esperado |
|---------|----------|
| Exit code | `0` |
| `checks_passed` | `checks_total` (10 checks: 5 views × 2 filiais) |
| `all_ok` | `true` |

Falha em qualquer combinação view/filial → exit code `1`. Investigar mensagem em `error` no resumo.

---

## Interpretação

| Situação | Ação |
|----------|------|
| View não existe | Solicitar deploy DBA da view |
| Total = 0 | Aceitável se filial sem movimento; confirmar com negócio |
| Colunas divergentes | Atualizar [ESPECIFICACAO-VIEW.md](./ESPECIFICACAO-VIEW.md) e repository |
| Erro de login SQL | Revisar secrets / rede no compose |

---

## Após Fase 0

1. Registrar resultado (data, ambiente, totais) neste doc ou anexo JSON versionado
2. Prosseguir smoke HTTP: [TESTING.md](../../../plugins/inspecoes-entrada/docs/TESTING.md)
3. Marcar Fase 0 como concluída no [ROADMAP.md](./ROADMAP.md) para o ambiente

---

## Template de registro

```markdown
### Validação — {ambiente} — {data}

| View | Filial 01 total | Filial 02 total | OK |
|------|-----------------|-----------------|-----|
| resumo_filial | | | |
| pendentes | | | |
| pendentes_fornecedor | | | |
| rejeitadas_ensaiador | | | |
| historico_tela | | | |

Responsável: ___  
Observações: ___
```

---

## Referência

Script: `api-delpi/scripts/validate_inspecoes_entrada_views.py`
