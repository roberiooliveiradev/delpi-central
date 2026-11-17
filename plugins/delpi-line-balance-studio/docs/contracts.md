# Contratos candidatos — estudos e ports

**TARGET / NÃO É API IMPLEMENTADA.** Contratos a evoluir no código novo, sem derivar tipos do Portal Engenharia.

```ts
type MethodId = "M1"|"M2"|"M3"|"M4"|"M5"|"M6";
type Origin = "OBSERVED"|"PROVIDED"|"CALCULATED"|"SIMULATION"|"UNKNOWN";
type StudySource = "OFFICIAL_ROUTING"|"MANUAL"|"IMPORTED";
type TimeValue = { minutes: number|null; origin: Origin };
type WorkElement = { id: string; label: string; time: TimeValue; category?: string };
type Operation = { id: string; label: string; time: TimeValue; elements?: WorkElement[]; origin: Origin; sourceRef?: string };
type Station = { id: string; label: string; order: number; operationIds: string[]; operatorsHypothesis?: number };
type Break = { id: string; from?: string; to?: string; minutes?: number };
type Shift = { mode: "CLOCK"|"MINUTES"; start?: string; end?: string; grossMinutes?: number; breaks: Break[] };
type Study = { id: string; version: number; source: StudySource; methodId: MethodId; operations: Operation[]; stations: Station[]; shift: Shift; demand?: number; batchSize?: number; sourceFingerprint?: string };
```

Ports independentes propostos: `OfficialRoutingPort` (consulta autorizada de produto/filial/estágio), `AnalysisPort` (domínio calculador competente), `DraftPort` (persistência isolada), `ExportPort` e `HostContextPort` (contexto autorizado sem token).

**Invariantes:** a operação sem tempo é UNKNOWN (não zero); tempos por lote não são tempos por peça; CT não equivale a posto; uma operação não pode ser contada duas vezes sem política explícita; produto/filial/estágio e versão precisam acompanhar a origem; nunca presumir precedência a partir do código. Sem SKU oficial, não enviar código inventado a endpoint por produto; contrato de análise de estudo manual depende de domínio apropriado. Requests/responses, erro, AuthN/AuthZ, limites, compatibility e observability devem ser fixados antes da API final.
