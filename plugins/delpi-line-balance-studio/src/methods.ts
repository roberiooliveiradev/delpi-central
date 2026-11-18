export type MethodId = "M1" | "M2" | "M3" | "M4" | "M5" | "M6";

export type MethodDescriptor = Readonly<{
  id: MethodId;
  name: string;
  status: "PLANNED";
  next: boolean;
}>;

const methods: readonly MethodDescriptor[] = [
  { id: "M1", name: "Capacidade e takt", status: "PLANNED", next: false },
  { id: "M2", name: "First Fit Decreasing e Largest Candidate Rule", status: "PLANNED", next: false },
  { id: "M3", name: "Ranked Positional Weight", status: "PLANNED", next: false },
  { id: "M4", name: "Kilbridge–Wester", status: "PLANNED", next: false },
  { id: "M5", name: "Yamazumi interativo", status: "PLANNED", next: true },
  { id: "M6", name: "Dimensionamento de recursos", status: "PLANNED", next: false },
];

export function listMethods(): readonly MethodDescriptor[] {
  return methods.map(method => ({ ...method }));
}
