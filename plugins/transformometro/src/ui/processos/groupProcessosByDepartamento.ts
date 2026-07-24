import type { Processo, ProcessoInstanciaSetor } from "../../data/api/transformometroApi";

export const SEM_DEPARTAMENTO_KEY = "__sem_departamento__";

export type ProcessoDepartamentoRef = {
  key: string;
  label: string;
  codigoSetor: string;
};

export type DepartamentoFolder = {
  key: string;
  label: string;
  codigoSetor: string;
  processes: Processo[];
  processCount: number;
};

/** Resolve departamentos do escopo do processo-mestre (N:N). */
export function resolveProcessoDepartamentos(processo: Processo): ProcessoDepartamentoRef[] {
  const fromSetores = (processo.setores || [])
    .map((setor) => normalizeSetorRef(setor))
    .filter((item): item is ProcessoDepartamentoRef => Boolean(item));

  if (fromSetores.length > 0) {
    return uniqueByKey(fromSetores);
  }

  const fromIds = (processo.setor_ids || [])
    .map((raw) => String(raw || "").trim())
    .filter(Boolean)
    .map((id) => ({ key: id, label: id, codigoSetor: id }));

  if (fromIds.length > 0) {
    return uniqueByKey(fromIds);
  }

  const legacy = String(processo.setor_id || "").trim();
  if (legacy) {
    return [{ key: legacy, label: legacy, codigoSetor: legacy }];
  }

  return [];
}

function normalizeSetorRef(setor: ProcessoInstanciaSetor): ProcessoDepartamentoRef | null {
  const codigo = String(setor.codigo_setor || setor.setor_id || "").trim();
  const id = String(setor.setor_id || "").trim();
  const key = codigo || id;
  if (!key) return null;
  const label = String(setor.nome_setor || codigo || id).trim() || key;
  return { key, label, codigoSetor: codigo || id };
}

function uniqueByKey(items: ProcessoDepartamentoRef[]): ProcessoDepartamentoRef[] {
  const seen = new Set<string>();
  const out: ProcessoDepartamentoRef[] = [];
  for (const item of items) {
    if (seen.has(item.key)) continue;
    seen.add(item.key);
    out.push(item);
  }
  return out;
}

/**
 * Agrupa processos em pastas de departamento.
 * Um processo com vários departamentos aparece em cada pasta correspondente.
 */
export function groupProcessosByDepartamento(items: Processo[]): DepartamentoFolder[] {
  const folders = new Map<string, DepartamentoFolder>();

  const ensure = (ref: ProcessoDepartamentoRef): DepartamentoFolder => {
    const existing = folders.get(ref.key);
    if (existing) {
      if (ref.label && ref.label !== ref.key && existing.label === existing.codigoSetor) {
        existing.label = ref.label;
      }
      return existing;
    }
    const created: DepartamentoFolder = {
      key: ref.key,
      label: ref.label,
      codigoSetor: ref.codigoSetor,
      processes: [],
      processCount: 0,
    };
    folders.set(ref.key, created);
    return created;
  };

  for (const processo of items) {
    const depts = resolveProcessoDepartamentos(processo);
    if (depts.length === 0) {
      const bucket = ensure({
        key: SEM_DEPARTAMENTO_KEY,
        label: "Sem departamento",
        codigoSetor: "",
      });
      bucket.processes.push(processo);
      continue;
    }
    for (const dept of depts) {
      ensure(dept).processes.push(processo);
    }
  }

  for (const folder of folders.values()) {
    folder.processCount = folder.processes.length;
  }

  return Array.from(folders.values()).sort((a, b) => {
    if (a.key === SEM_DEPARTAMENTO_KEY) return 1;
    if (b.key === SEM_DEPARTAMENTO_KEY) return -1;
    return a.label.localeCompare(b.label, "pt-BR", { sensitivity: "base" });
  });
}

export function sortDepartamentoFolders(
  folders: DepartamentoFolder[],
  direction: "asc" | "desc",
): DepartamentoFolder[] {
  const factor = direction === "asc" ? 1 : -1;
  return [...folders].sort((a, b) => {
    if (a.key === SEM_DEPARTAMENTO_KEY) return 1;
    if (b.key === SEM_DEPARTAMENTO_KEY) return -1;
    return factor * a.label.localeCompare(b.label, "pt-BR", { sensitivity: "base" });
  });
}
