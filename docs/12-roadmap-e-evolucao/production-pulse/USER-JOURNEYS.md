# Jornadas de usuário — Production Pulse

---

## J1 — Supervisor cadastra ventilador (sem CT)

```mermaid
sequenceDiagram
  participant S as Supervisor
  participant MFE as MFE
  participant API as production-pulse-api
  participant ESP as ESP LAN

  S->>MFE: Novo dispositivo
  MFE->>API: GET /catalog/drivers
  S->>MFE: IP, driver gauge, anchor equipment
  S->>MFE: Testar conexão
  MFE->>API: POST /devices + POST /test
  API->>ESP: HTTP read
  ESP-->>API: rpm, temperature_c
  S->>MFE: Salvar
  MFE->>API: POST /devices, PUT /binding
  API-->>MFE: placement_label
  Note over S,MFE: Painel lista «Ventilador exaustão A · 1180 rpm»
```

---

## J2 — Operador usa contador no posto PCP

```mermaid
flowchart LR
  A[Menu Operador · Pulso] --> B[Hub placements]
  B --> C{Filtro Postos}
  C --> D[Card CT-53]
  D --> E{1 device?}
  E -->|sim| F[Contador − Limpar +]
  E -->|não| G[Picker devices]
  G --> F
  F --> H[Trocar posto → Hub]
```

---

## J3 — Admin diagnostica offline

1. Painel → filtro Status **Offline**
2. Linha «ESP motor bomba» · badge vermelho · última métrica cacheada
3. Detalhe → aba Histórico — gap nas leituras
4. `POST /poll` manual → timeout → `last_error` visível
5. Opcional: `POST /test` no edit form após corrigir rede

---

## Matriz jornada × superfície

| Jornada | Admin painel | Form | Detalhe | Operador |
|---------|--------------|------|---------|----------|
| J1 ventilador | Lista + badge Equipamento | anchor equipment | Gráfico rpm/°C | Hub → gauge |
| J2 contador CT | Agrupado posto | anchor work_center | Delta + reset | counter_pad |
| J3 offline | Filtro offline | — | last_error | Pad desabilitado |
