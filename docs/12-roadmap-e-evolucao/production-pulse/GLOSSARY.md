# Glossário — Production Pulse

| Termo (EN) | PT | Definição |
|------------|-----|-----------|
| **Device** | Dispositivo IoT | Hardware na rede (IP + driver). Entidade central do plugin. |
| **Binding** | Amarração | Vínculo vigente: onde o device está instalado (`device_bindings`). |
| **anchor_type** | Tipo de âncora | `work_center`, `machine`, `equipment`, `area`, `standalone`. |
| **placement_label** | Rótulo operacional | Texto canônico para UI (hub, agrupamento). Composto pela API. |
| **placement_key** | Chave de agrupamento | ID estável para URL hub/picker — ver [SCHEMA.md](./SCHEMA.md). |
| **driver_key** | Driver | Protocolo/firmware (`esp8266_counter_v1`). |
| **role_key** | Papel | Semântica operacional derivada do driver (`pulse_counter`, `process_gauge`). |
| **metrics** | Métricas | Valores lidos (`counter`, `rpm`, `temperature_c`) em JSONB. |
| **CT** | Centro de trabalho | Cadastro TOTVS (`SHB010`). **Atalho opcional** — não é o único vínculo. |
| **status (device)** | Conectividade derivada | `online` \| `offline` \| `disabled` \| `no_binding` — grace **2× poll_interval** (min 60 s, max 600 s). Ver R9–R12. |
| **operatorSurface** | Superfície operador | UI tablet: `counter_pad`, `gauge_readout`, … |
| **capabilities** | Capabilities | Comandos e métricas permitidos — vêm do registry. |
| **Rascunho** | — | Device sem binding vigente — excluído de hub operador. |

**Não confundir:** *dispositivo IoT* (ESP no IP) ≠ *equipamento monitorado* (ventilador, motor) — um ESP mede um equipamento via amarração.
