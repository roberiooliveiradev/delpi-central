export type MethodId = "M1" | "M2" | "M3" | "M4" | "M5" | "M6";

/** Estado real de execução dentro do Studio:
 *  - `AVAILABLE` — workspace interativo implementado;
 *  - `LIMITED` — painel executável com capacidade parcial e limitações
 *    declaradas (nunca apresentado como cálculo oficial do domínio);
 *  - `PLANNED` — sem implementação; não executável em nenhuma superfície. */
export type MethodStatus = "AVAILABLE" | "LIMITED" | "PLANNED";

export type MethodDescriptor = Readonly<{
  id: MethodId;
  name: string;
  status: MethodStatus;
  next: boolean;
}>;

const methods: readonly MethodDescriptor[] = [
  { id: "M1", name: "Capacidade e takt", status: "LIMITED", next: false },
  { id: "M2", name: "First Fit Decreasing e Largest Candidate Rule", status: "PLANNED", next: true },
  { id: "M3", name: "Ranked Positional Weight", status: "PLANNED", next: false },
  { id: "M4", name: "Kilbridge–Wester", status: "PLANNED", next: false },
  { id: "M5", name: "Yamazumi interativo", status: "AVAILABLE", next: false },
  { id: "M6", name: "Dimensionamento de recursos", status: "PLANNED", next: false },
];

export function listMethods(): readonly MethodDescriptor[] {
  return methods.map(method => ({ ...method }));
}
