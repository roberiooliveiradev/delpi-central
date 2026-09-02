# Superfícies operador P2+ — tipos de device, combo, alertas, metas

> **Status:** especificação (set/2026) — **não implementado** no MFE/API além do que já existe (`counter_pad`, `gauge_readout` + thresholds)  
> **Plano API + frontend:** [API-MFE-DEVICE-EVOLUTION.md](./API-MFE-DEVICE-EVOLUTION.md)  
> **Wireframes:** [WIREFRAMES.md](./WIREFRAMES.md) § WF-PP-OP-TEMP … WF-PP-OP-COMBO  
> **Drivers:** [DEVICE-DRIVERS.md](./DEVICE-DRIVERS.md) · **Design:** [DESIGN-FRONTEND.md §9](./DESIGN-FRONTEND.md)

---

## Objetivo

Expandir o modo operador além de **contador** e **gauge genérico**, cobrindo:

| Família | Exemplos no chão | Superfície UI |
|---------|------------------|---------------|
| Temperatura | motor, cabine, forno, óleo | `temperature_focus` |
| Rotação / velocidade | fuso, ventilador, eixo | `rotation_ring` |
| Pressão / vazão / nível | linha, tanque | `process_scalar` (herda gauge + unidade) |
| Telemetria multi | vibração + °C + rpm | `telemetry_stack` |
| Painel do posto | N devices no mesmo placement | `placement_combo` |
| Meta / OEE leve | golpes vs meta turno, rpm vs faixa | overlay `goal_percent` |
| Alertas | limiar warn/danger, offline | banner + chips (todas as superfícies) |

---

## Decisões travadas

| Tema | Decisão |
|------|---------|
| Extensão vs novo driver | **Novo `operatorSurface` + perfil no registry** — não forçar tudo em `gauge_readout` |
| Fonte de limiares | Já em `drivers.*.thresholds` / `capabilities.thresholds` — alertas **consomem** o mesmo contrato |
| Metas | Config por **device** (`goal` no cadastro) e/ou por **placement+turno** (P2b) — JSON + Postgres, sem regra no MFE |
| % na tela | Calculado na **API** (`metrics` + `goals` → `progress.pct`) — MFE só renderiza |
| Painel combinado | Rota `/operator/placements/:placementKey/board` — 1 tela, cards por device; tap → superfície dedicada |
| Contador | Continua `counter_pad` — meta/alerta **como faixa** acima do valor, sem misturar pad |
| Firmware | Drivers novos = protocolo HTTP próprio; não acoplar ao `Teste.ino` do contador |
| Kit UI | Tiles + banners via `@delpi/plugin-ui`; gráfico % com `ComparativeAreaChart` / anel SVG domínio `.pp-operator-ring` |

---

## Matriz de fluxos (P2)

| Fluxo | Superfície | Caminho | P0 P2 | Herança | Fora |
|-------|------------|---------|-------|---------|------|
| Ler °C / rpm no tablet | TEMP / ROTATION | `/operator/devices/:id` | sim | poll/live | — |
| Ver posto inteiro | COMBO | `/operator/.../board` | sim | placements API | edição admin |
| Alerta limiar no card | banner | todas superfícies | sim | thresholds | SMS/e-mail |
| Meta do turno % | GOAL | contador ou gauge | sim | goal API | PCP OEE oficial |
| Histórico no operador | sparkline 1h | TEMP/ROTATION | P2b | readings | detalhe admin |
| Comando em gauge | — | — | — | — | write em sensor |
| Quiosque multi-TV | COMBO fullscreen | `?kiosk=1` | P3 | ADR-001 | wallboard TV Dashboard |

---

## Papéis (`role_key`) e superfícies

| role_key | operatorSurface | Métricas típicas | Comandos |
|----------|-----------------|------------------|----------|
| `pulse_counter` | `counter_pad` | `counter` | increment/decrement/reset/set |
| `process_gauge` | `gauge_readout` | `rpm`, `temperature_c` | `[]` |
| `temperature_probe` | `temperature_focus` | `temperature_c` (+ opcional `temperature_c_max`) | `[]` |
| `rotation_probe` | `rotation_ring` | `rpm` (+ `rpm_target` via goal) | `[]` |
| `process_scalar` | `gauge_readout` | 1 métrica + `unit` | `[]` |
| `telemetry_bundle` | `telemetry_stack` | 3–6 métricas | `[]` |
| *(placement)* | `placement_combo` | agrega devices do posto | navega |

`operatorEligible: true` obrigatório para entrar no hub.

---

## Alertas (todas as superfícies)

### Semântica

| Nível | Origem | UI |
|-------|--------|-----|
| `ok` | valor dentro da faixa | anel/tile neutro |
| `warn` | `thresholds.*.warn` | cor `--pp-warning`; chip «Atenção» |
| `danger` | `thresholds.*.danger` | cor `--pp-danger`; banner sticky |
| `offline` | connectivity | banner existente `operator.offlineBanner` |
| `stale` | sem poll > 3× intervalo | chip «Desatualizado» |

### Regras

1. Avaliação na **API** no poll/live → `presentation.alertLevel` + `presentation.alertMetricKey` (MFE não recalcula).
2. Hub/picker: badge colorido no card se algum device `warn`/`danger`.
3. Combo board: ordenar cards danger → warn → ok → offline.
4. **Sem** dismiss persistente no MVP P2 (só visual); ack/histórico = P3.

### Wireframe referência

Ver **WF-PP-OP-ALERT** em [WIREFRAMES.md](./WIREFRAMES.md).

---

## Metas e percentuais

### Contrato (API → MFE)

```json
{
  "metrics": { "counter": 842, "rpm": 1850 },
  "goals": {
    "counter": { "target": 1200, "window": "shift", "labelPt": "Meta do turno" },
    "rpm": { "targetMin": 1600, "targetMax": 2200, "labelPt": "Faixa nominal" }
  },
  "progress": {
    "counter": { "pct": 70.2, "remaining": 358, "state": "on_track" },
    "rpm": { "pctInBand": 100, "state": "in_band" }
  }
}
```

| Tipo de meta | Cálculo `pct` | UI |
|--------------|---------------|-----|
| Contagem vs alvo | `min(100, value/target*100)` | barra + anel |
| Faixa (min–max) | 100 se dentro; senão distância normalizada | anel dual (warn fora) |
| Temperatura máx | % até teto de segurança | barra invertida (longe do teto = bom) |

### Estados `progress.*.state`

`on_track` · `at_risk` · `missed` · `in_band` · `out_of_band` · `unknown`

### Onde aparece

| Tela | Elemento |
|------|----------|
| Contador | Faixa sob o valor: «842 / 1.200 · 70%» + barra |
| Rotação | Anel % da faixa nominal ao redor do rpm |
| Temperatura | Barra «margem até teto» |
| Combo | Mini-barra no card de cada device com goal |
| Admin detalhe | Mesmo contrato (histórico vs meta = P2b) |

---

## Descrição por superfície

### 1. `temperature_focus` (WF-PP-OP-TEMP)

- **Hero:** valor °C enorme; unidade fixa.
- **Secundário:** min/max da janela curta (15 min) se API enviar `stats`.
- **Alerta:** cor do tile conforme thresholds.
- **Meta:** barra «até limite» se `goals.temperature_c.targetMax`.
- **Sem** comandos; sync automático.

### 2. `rotation_ring` (WF-PP-OP-ROTATION)

- **Hero:** rpm + anel circular (% na faixa ou % do target).
- **Secundário:** temperatura acoplada se o mesmo device reportar (tile menor).
- **Alerta:** anel muda de cor (ok/warn/danger).
- Reutiliza leituras do driver `esp8266_gauge_v1` **ou** driver dedicado `esp8266_rotation_v1`.

### 3. `process_scalar` / `telemetry_stack`

- Scalar = 1 card (pressão bar, nível %, etc.) — layout = gauge 1 métrica.
- Stack = lista vertical de tiles (máx 6); overflow scroll; primary no topo.

### 4. `placement_combo` (WF-PP-OP-COMBO)

- Entrada: no picker, botão **«Ver posto»** (board) além dos cards individuais.
- Grid de tiles: cada device = papel + valor + alert chip + mini %.
- Tap tile → superfície dedicada.
- Header: placement_label + contagem online/total + «pior» alert do posto.

### 5. Overlay meta (WF-PP-OP-GOAL)

- Não é rota: **composição** injetada em counter/temp/rotation quando `progress` existe.
- Contador: não reduz tamanho do número; meta fica **abaixo** do valor, acima do pad.

---

## Drivers futuros (registry — rascunho)

| driver_key | role | surface | Path HTTP piloto |
|------------|------|---------|------------------|
| `esp8266_temp_v1` | temperature_probe | temperature_focus | `GET /api/temperatura` → `{ temperatura }` |
| `esp8266_rotation_v1` | rotation_probe | rotation_ring | `GET /api/rotacao` → `{ rpm }` |
| `esp8266_pressure_v1` | process_scalar | gauge_readout | `GET /api/pressao` → `{ pressure_bar }` |
| `modbus_generic_v1` | telemetry_bundle | telemetry_stack | via gateway (P3) |

Checklist ao criar driver: [DEVICE-DRIVERS.md § novo driver](./DEVICE-DRIVERS.md).

---

## API (esboço P2)

| Endpoint | Uso |
|----------|-----|
| `GET /operator/devices/{id}` (enriquecido) | `metrics` + `goals` + `progress` + `presentation.alertLevel` |
| `GET /operator/placements/{key}/board` | lista devices com preview + alert + progress |
| `PATCH /devices/{id}/goals` † manage | define metas do device |
| Poll existente | passa a calcular `progress` se goal configurado |

† Permissão `devices.manage` — operador **só lê**.

---

## Helps previstos (`PP_HELP.operator.*`)

| Chave | Copy (rascunho) |
|-------|-----------------|
| `tempValue` | Temperatura atual do sensor. |
| `tempMargin` | Quanto falta para o limite configurado. |
| `rotationRing` | Rotação e posição na faixa nominal. |
| `comboBoard` | Visão de todos os sensores deste posto. |
| `goalBar` | Progresso em relação à meta do turno. |
| `alertBanner` | Leitura fora da faixa segura — avise a supervisão. |
| `pctChart` | Percentual calculado pela plataforma (não estime de cabeça). |

Implementação: espelhar em `content/helpTooltips.ts` + plugin na entrega P2.

---

## Critérios de pronto (doc → código)

1. Wireframes ASCII em WIREFRAMES.md revisados (TEMP, ROTATION, COMBO, ALERT, GOAL, PCT).
2. Registry com ≥1 driver stub + surface nova.
3. Contrato `progress` / `presentation.alertLevel` testado na API.
4. MFE: roteador `OperatorDeviceSurface` reconhece surfaces; combo board rota nova.
5. Testes: thresholds → alertLevel; goal → pct; board ordena danger primeiro.

---

## Fora do escopo (P2)

- Alarme sonoro / push mobile
- Integração OEE oficial PCP / Transformômetro
- Escrita em PLC / Modbus write
- Wallboard TV (`tv-dashboard`) — só link futuro
- Persistência de meta por turno automático (P2b)

---

## Referências de mercado (inspiração UX)

- HMI ISA-101: hierarquia de atenção (alarm > warn > normal)
- Contadores industriais retained + meta de turno no painel de linha
- Anéis / bullet charts para «valor na faixa» (Few / SCADA leve)
