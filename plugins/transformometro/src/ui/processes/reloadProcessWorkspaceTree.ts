/**
 * Reloads process workspace tree with partial failure isolation:
 * - process fetch failure → fatal (null process)
 * - instances/revisions failure → keep prior data + partial error message
 */
export async function reloadProcessWorkspaceTree(input: {
  fetchProcesso: () => Promise<unknown>;
  fetchInstancias: () => Promise<{ items: unknown[] }>;
  fetchRevisoes: () => Promise<{ items: unknown[] }>;
  setProcesso: (value: unknown) => void;
  setInstancias: (value: unknown[]) => void;
  setRevisoes: (value: unknown[]) => void;
  setTreePartialError: (value: string | null) => void;
}): Promise<void> {
  input.setTreePartialError(null);
  try {
    const proc = await input.fetchProcesso();
    input.setProcesso(proc);
  } catch {
    input.setProcesso(null);
    return;
  }

  const partial: string[] = [];
  try {
    const inst = await input.fetchInstancias();
    input.setInstancias(inst.items);
  } catch {
    partial.push("melhorias");
  }
  try {
    const revs = await input.fetchRevisoes();
    input.setRevisoes(revs.items);
  } catch {
    partial.push("revisões");
  }
  if (partial.length > 0) {
    input.setTreePartialError(
      `Não foi possível atualizar ${partial.join(" e ")} na árvore. O processo continua disponível.`
    );
  }
}
