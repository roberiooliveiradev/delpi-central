# Contratos e modelo de estudo — proposta tipada

**Estado:** TARGET / SCHEMA_CANDIDATE / TEST_NOT_RUN. Não é um DTO/API vigente.

## Entidades mínimas
```ts
type Origin = "OBSERVED" | "PROVIDED" | "SIMULATION" | "DRAFT_LOCAL" | "UNKNOWN";
type StudySource = "OFFICIAL_ROUTING" | "MANUAL" | "IMPORTED";
type MethodId = "M1" | "M2" | "M3" | "M4" | "M5" | "M6";
type Duration = { value: number | null; unit: "MIN" | "SEC"; origin: Origin };
type TaskElement = {
  id: string; description: string; duration: Duration;
  category?: "MANUAL" | "AUTOMATIC" | "WALK" | "WAIT" | "AGGREGATE_UNKNOWN";
  predecessorIds?: string[]; origin: Origin;
};
type StudyOperation = {
  id: string; externalRef?: string; productRef?: string; stageRef?: string;
  description: string; workCenterRef?: string; resourceRef?: string;
  standardTime: Duration; setupHours?: number | null;
  elements?: TaskElement[]; origin: Origin;
};
type StudyStation = {
  id: string; name: string; order: number;
  operationIds: string[]; operatorCountHypothesis?: number;
  parallelPositionsHypothesis?: number; notes?: string;
};
type Pause = { id: string; start?: string; end?: string; minutes?: number };
type Schedule = {
  mode: "CLOCK" | "MINUTES"; start?: string; end?: string;
  grossMinutes?: number; pauses: Pause[]; timezone?: string;
  overnight?: boolean; periodUnit?: "SHIFT" | "DAY" | "WEEK";
};
type StudyScenario = {
  id: string; methodId: MethodId; studySource: StudySource;
  sourceFingerprint?: string; productContext?: { code: string; branch?: string; stage?: string };
  operations: StudyOperation[]; stations: StudyStation[];
  schedule: Schedule; demand?: number; batchSize?: number;
  version: number; caveats: string[];
};
```

**Cuidado:** o retorno do motor atual não aceita esses DTOs; apenas o adaptador do consumidor pode traduzi-los para o contrato comprovado. Não chamar `runBalanceAnalysis` com estruturas não suportadas.

## Ports propostos
```ts
interface StudioContextPort { getAuthorizedContext(): Promise<{ principalScope: string; permissions: string[] }>; }
interface RoutingSourcePort {
  loadProductRouting(input: { code: string; branch?: string }): Promise<OfficialRoutingReadResult>;
}
interface BalanceAnalysisPort {
  analyzeOfficialRoute(input: OfficialBalanceRequest): Promise<OfficialBalanceResult>;
  // analyzeManualStudy: FUTURO, não adicionar ao runtime sem contrato de domínio
}
interface DraftStoragePort {
  load(key: ScopedDraftKey): Promise<StoredDraft | null>;
  save(key: ScopedDraftKey, draft: StoredDraft): Promise<void>;
  remove(key: ScopedDraftKey): Promise<void>;
}
interface StudioExportPort { export(format: "csv" | "xlsx" | "pdf", payload: ExportStudy): Promise<void>; }
```

## Regras de integridade
- IDs estáveis; operações oficiais deduplicadas por (produto, nível, operação, CT, recurso) no owner apropriado.
- Tempo ausente `null/UNKNOWN`, nunca `0` para completar gráfico.
- `setup_hours` é por lote: não somar ao tempo por peça sem lote > 0 explícito.
- Atribuição exclusiva por operação como default V3; replicar ou fracionar requer contrato explícito.
- Operações de estágios diferentes não formam uma linha por inferência.
- Validação antes da prévia: duração/pausas/demanda; não perder precisão por arredondamento no editor.
- `sourceFingerprint` e compatibilidade de cenários obrigatórios para comparativo quantitativo; mudanças geram `STALE`.
- Dados de outros usuários/filiais não migram em draft.
- Schemas versionados; migrations de rascunho explícitas, sem autoconversão silenciosa.

## Contrato de API futura para estudo manual
Antes de criar endpoint: owner, consumers, request/response, erros, limites (operações/arestas/postas), auth, compatibilidade, idempotência, observabilidade, provenance e postcondition. O sistema atual **não** possui capacidade comprovada para análise manual independente de SKU.

## Tabela de status
| Contrato | Evidência | Status |
|---|---|---|
| GET /v1/products/{code}/routing | MFE V3 e API existente | PROVEN como interface atual; revalidar HEAD |
| POST /v1/products/{code}/line-balance | domínio atual | PROVEN com vocabulário fechado |
| StudyScenario acima | Documento candidato | TARGET |
| Portas agnósticas acima | Documento candidato | TARGET |
| Solver de manual/precedência/recurso | Sem API confirmada | TARGET |
