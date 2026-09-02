# Homologação E6.S2 — ESP8266 piloto (verify live)

> **Objetivo:** fechar o MVP com fluxo ponta a ponta na **rede industrial** — device `192.168.20.2`, driver `esp8266_counter_v1`.  
> **Pré-requisito:** stack dev/prod já passou em [E6.S1](./ROADMAP.md#e6s1--docs--inventário--homologação) (`check-production-pulse.sh` sem `PP_LIVE_ESP`).

---

## 1. Pré-requisitos

| Item | Como verificar |
|------|----------------|
| ESP ligado e na VLAN | `curl -sf --connect-timeout 3 http://192.168.20.2/api/contador` → `{"contador": <int>}` |
| WSL/host alcança LAN | Mesmo comando no host; dev: `production-pulse-api` com **`network_mode: host`** ([ADR-002](./ADR-002-poll-scheduler-and-lan.md)) |
| Stack no ar | `./infra/scripts/up-dev-sequential.sh --fase api --build production-pulse-api` + `--fase mfe --build production-pulse` |
| Migrations | `docker exec delpi-production-pulse-api python -m production_pulse_app.infrastructure.persistence.migrations_runner status` → V001/V002 aplicadas |
| Permissões usuário teste | `production-pulse.access`, `devices.view`, `devices.manage`, `devices.command`, `operator`, `view.filial-01` (SC) — ver [ADR-003](./ADR-003-rbac-mvp.md) |

---

## 2. Smoke automatizado (antes da UI)

```bash
# Da raiz do repo — usa TOKEN ou API_DELPI_INTERNAL_SERVICE_TOKEN (infra/.env)
bash ./scripts/homologacao/check-production-pulse.sh

# Com ESP na LAN
PP_LIVE_ESP=1 PP_LIVE_ESP_IP=192.168.20.2 bash ./scripts/homologacao/check-production-pulse.sh
```

| Passo script | Esperado |
|--------------|----------|
| `remoteEntry.js` | HTTP 200 |
| `/health` | `service: production-pulse-api` |
| `/summary`, `/devices`, `/catalog/drivers` | `success: true` |
| CRUD smoke | create + soft delete OK |
| `[live] test-probe` | `online: true`, `metrics.counter` inteiro ≥ 0 |

Alternativa pytest (host/container na mesma rede do ESP):

```bash
cd production-pulse-api
PP_LIVE_ESP=1 pytest tests/test_esp8266_counter_driver_live.py -q
```

---

## 3. Painel admin — cadastro e amarração

**Rota:** `/apps/production-pulse` → **+ Novo dispositivo**

### 3.1 Dispositivo

| Campo | Valor piloto |
|-------|----------------|
| Nome | ex.: `ESP piloto chão fábrica` |
| Filial | SC (`01`) |
| IP | `192.168.20.2` |
| Driver | `esp8266_counter_v1` (contador) |
| Intervalo poll | `30` s (ou `0,5` se V002 aplicada) |
| Ativo | Sim |

1. **Testar conexão** antes de salvar → modal com contador lido (sem gravar histórico).
2. **Salvar** → redireciona ou volta ao painel com device na lista.

### 3.2 Amarração (escolher um cenário MVP)

| Cenário | `anchor_type` | Campos | Objetivo do teste |
|---------|---------------|--------|-------------------|
| **A — Posto PCP** | Posto PCP | CT autocomplete (SHB010) | Fluxo clássico |
| **B — Avulso** | Avulso | — | Device sem CT (ventilador-like) |
| **C — Equipamento** | Equipamento | rótulo livre | CT opcional colapsado |

Salvar amarração → coluna **Objeto** no painel mostra `placement_label`.

### 3.3 Checklist painel pós-cadastro

- [ ] KPI **Total** incrementou
- [ ] Device aparece na **lista** com status (online após poll ou offline até primeira leitura)
- [ ] Coluna **Métrica** mostra golpes após poll
- [ ] Toggle **Agrupado** + «Agrupar por» coloca device na seção correta
- [ ] Ícone **Poll** na linha atualiza métrica e **Última leitura**

---

## 4. Detalhe — histórico e comandos

**Rota:** clicar no device → `/apps/production-pulse/devices/{id}`

### 4.1 Aba Visão geral

- [ ] Hero exibe contador atual (valor coerente com ESP)
- [ ] Card de amarração mostra tipo + rótulo
- [ ] Botão **Poll agora** atualiza valor

### 4.2 Aba Histórico

- [ ] Gráfico/tabela com pelo menos 1 ponto após poll manual ou scheduler (~30 s)
- [ ] Alternar período / modo tabela se disponível

### 4.3 Aba Comandos

- [ ] Lista auditoria vazia ou com comandos anteriores
- [ ] **Reset** (com permissão `devices.command`) → modal confirma → contador no ESP zera → nova leitura reflete `0` ou valor pós-reset
- [ ] Entrada registrada na aba Comandos

---

## 5. Modo operador (tablet)

**Rota:** `/apps/production-pulse/operator` (menu «Operador · Pulso»)

Permissão mínima: `production-pulse.operator` (não exige `devices.view` na rota operador).

### 5.1 Hub

- [ ] Card do **placement** cadastrado aparece (rótulo legível, não UUID `s:…`)
- [ ] Filtros filial / tipo (Todos, Postos, Máquinas, Equipamentos) funcionam
- [ ] Busca automática filtra por nome do local
- [ ] Meta no card: contagem devices · online/offline

### 5.2 Superfície contador

1. Tocar no card → se 1 device, abre direto; se N, picker.
2. **Rota:** `/apps/production-pulse/operator/devices/{id}`

- [ ] Brand bar com título do posto/equipamento (não chave interna)
- [ ] Valor grande de **golpes** atualizado
- [ ] Botões **+** / **−** / **Limpar** (capability do driver)
- [ ] **Sincronizar agora** força poll
- [ ] **Trocar posto** volta ao hub
- [ ] **Painel admin** (se `devices.view`) abre painel SC

### 5.3 Offline

Desligar ESP ou bloquear IP → banner offline; botões desabilitados ou com aviso (conforme wireframe OP).

---

## 6. Scheduler automático (opcional, ~2 min)

- [ ] Aguardar 1–2× `poll_interval` sem poll manual
- [ ] `last_seen_at` / status **Online** no painel
- [ ] Nova linha em **Histórico** sem ação manual

---

## 7. RBAC rápido

| Usuário | Esperado |
|---------|----------|
| Só `operator` | Hub + contador OK; painel admin 403 ou menu oculto |
| Só `devices.view` | Painel OK; comandos reset 403 |
| Filial ES sem device SC | Lista vazia ou 403 em branch SC |
| `admin` | Ambas filiais |

---

## 8. Critério de pronto E6.S2

Marcar **feito** quando **todos** forem verdadeiros:

1. `PP_LIVE_ESP=1` no script de homologação → **OK live counter**
2. Cadastro UI com IP `192.168.20.2` + test-probe OK
3. Poll manual atualiza painel e detalhe
4. Histórico grava leitura
5. Operador abre hub → contador ao vivo com incremento/reset testado (ambiente controlado)
6. (Opcional) Scheduler marca device **online** dentro do grace

**Commit:** só se correção de regressão encontrada na homologação.

---

## 9. Troubleshooting

| Sintoma | Verificar |
|---------|-----------|
| test-probe timeout | Host na VLAN? `network_mode: host` no dev? Firewall? **WSL:** se `curl 192.168.20.2` falha no host, a VLAN pode não estar roteada para o WSL — teste no Windows ou máquina na LAN |
| Online permanece offline | Grace = 2× poll_interval (min 60 s); ESP responde `/api/contador`? |
| CT autocomplete vazio | api-delpi + gateway; permissão TOTVS; filial correta |
| Operador sem cards | Device `enabled`? Binding ativo? Role operador elegível? |
| MFE erro MF | Rebuild `plugin-ui` fase remote, depois `production-pulse` |

Referências: [infra/README-ambiente.md § Production Pulse](../../infra/README-ambiente.md) · [WIREFRAMES OP](./WIREFRAMES.md)
