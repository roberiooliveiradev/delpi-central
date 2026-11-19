# Limitações oficiais e checklist de homologação TST01 — product-master (SB1)

Status do fonte: `SOURCE_CANDIDATE` — não compilado, não homologado.
Este documento registra o que está comprovado, o que está bloqueado e o
que a equipe ERP deve validar antes de qualquer escrita real.

## 1. Mecanismo comprovado

| Item | Estado | Evidência |
|---|---|---|
| CREATE via MATA010 op 3 | PROVEN_SOURCE + PROVEN_RUNTIME | `DLP04I01.PRW` upstream; DELPIPRODUTO POST publicado (contrato 22 campos) |
| UPDATE via MATA010 op 4 | PROVEN_SOURCE + PROVEN_RUNTIME | idem; PUT com representação completa homologado em TST01 (ledger `protheus-rest-product-update-ledger.md`) |
| Catálogo de campos SX3 | PROVEN_SOURCE | `sb1-field-matrix.json` — dump SX3 do TST01 (319 campos), paridade com PROD verificada |
| Campos elegíveis | PROVEN_SOURCE | 285 READ_WRITE_ELIGIBLE + B1_COD (5 memo SX3 sem coluna física → TO_INVENTORY, fora do catálogo) |
| Campos protegidos | PROVEN_SOURCE | 28 SYSTEM_MANAGED/IMMUTABLE — rejeitados por contrato |

## 2. Pendente de comprovação (TO_INVENTORY / VALIDAR NO TST01)

| Item | Bloqueio |
|---|---|
| Compilação do candidato no RPO TST01 | requer TDS na conexão `233:2001` (REST `:8061/restall`) + restart do REST — exclusivo equipe ERP. Registro 2026-11-19: daemon `:8061` não entrega body ao WSRESTFUL; validação funcional de escrita em avaliação via TDS `233:2002` (`:8701`) |
| 5 campos memo (`TO_INVENTORY`) | `B1_VM_I`, `B1_VM_GI`, `B1_VM_P`, `B1_OBS`, `B1_VM_PROC` — SX3 declara, mas sem coluna física na SB1010 do TST01; removidos do catálogo (286) até materialização |
| DELETE (op 5 MATA010) | sem fonte MATA010 disponível; vínculos SA5/SB2/movimentações não inventariados — **método publicado retorna 501 e não executa nada** |
| Semântica de representação completa no op 4 | política fail-closed assumida por contrato (bug conhecido de zeramento); confirmar comportamento por campo no TST01 |
| Formato de valor `D` no ExecAuto | candidato envia string `AAAAMMDD` e string vazia para data em branco (vazio é legítimo — SB1 grava blank); confirmar se a rotina aceita string ou exige tipo data — validar um campo `D` preenchido e um vazio no TST01 |
| Serialização do GET metadados | `fields[]` monta array de `JsonObject` aninhados — confirmar renderização JSON na compilação (fallback: array de pares `{field,kind}`) |
| PEs/gatilhos ativos na MATA010 do ambiente | `A010TOK` existe como PE; efeitos sobre campos SB1 não mapeados — inventário RPO pendente |
| Campo `B1_YDLPDSC` (referenciado por PE) | **ausente do SX3 do TST01** — divergência de dicionário; campo não entra no catálogo até existir no SX3 |

## 3. Regras invioláveis (não flexibilizar na homologação)

- Nunca `RecLock`/`INSERT`/`UPDATE`/`DELETE` direto em `SB1*` — escrita
  exclusiva via `MSExecAuto` + MATA010.
- PUT exige os **286 campos**; a atualização parcial do cliente é
  expandida na api-delpi via read-merge-write — nunca enviar delta ao
  ExecAuto.
- `B1_COD` é identidade: obrigatório no contrato, imutável como valor.
- Identidade Protheus (`codusr`) **não** é campo do `.PRW` — atribuição
  vive no ledger de tracking da api-delpi.
- Feature gates na api-delpi permanecem OFF por default; escrita exige
  pin `PROTHEUS_REST_EXPECTED_BASE_URL` coerente com o ambiente.

## 4. Checklist de homologação TST01 (ordem)

1. [ ] Compilar `src/DLP04I01.PRW` na conexão TDS `233:2001` (RPO custom do REST `:8061`; alternativa funcional `233:2002` enquanto `:8061` não entrega body).
2. [ ] Reiniciar o REST do ambiente compilado e confirmar no catálogo REST:
       `POST/PUT/DELETE/GET /v1/IncProduto/*`.
3. [ ] `GET /v1/IncProduto/metadados` → `fields_count = 286`, `entity=SB1`.
4. [ ] `DELETE /v1/IncProduto/excluir` → `501 not_homologated` (sem efeito ERP).
5. [ ] `PUT` com payload parcial → `400` "representacao completa".
6. [ ] `PUT` com representação completa em produto de teste dedicado →
       `200`; **read-back SQL** confirmando somente os campos alterados.
7. [ ] `PUT` com campo protegido (ex.: `B1_MSBLQL`) → `400`.
8. [ ] `PUT` com campo desconhecido → `400`.
9. [ ] `POST` com só `B1_COD` → comportamento oficial da MATA010
       (sucesso com defaults ou erro oficial legível — ambos aceitáveis;
       registrar o resultado observado).
10. [ ] `POST` sem `B1_COD` → `400`.
11. [ ] Confirmar que os 5 campos memo `TO_INVENTORY` (`B1_VM_I/GI/P`, `B1_OBS`, `B1_VM_PROC`) não constam no `metadados` →
        confirmar gravação ou marcar `NOT_SUPPORTED`.
12. [ ] Verificar que campos protegidos/sistema permanecem intactos após
        UPDATE (B1_MSBLQL, saldos, custos, datas de sistema).
12b.[ ] `PUT` em produto com data em branco (ex.: `B1_DTCORTE`) → `200` —
        data vazia trafega como `""` e não pode ser rejeitada.
13. [ ] Registrar evidência em `handoffs/` e atualizar `module.yaml`
        (`status` → `PROVEN_RUNTIME` parcial/total conforme resultado).

## 5. Divergência conhecida de ambiente

A versão do `DELPIPRODUTO` compilada no RPO de produção (231:8061)
respondeu `"nao e um JSON valido"` a payloads válidos em teste anterior —
o objeto compilado diverge de qualquer fonte versionado (v1/v2/WIP).
O `DELPIPRODFORN` do mesmo ambiente funciona normalmente. Antes de
homologar o v2, a equipe deve recompilar o I01 a partir **deste** fonte
(commit que contém `src/DLP04I01.PRW` v2) e confirmar o comportamento
de parse do body.
