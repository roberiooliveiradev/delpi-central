/**
 * Pending mutation-projection ledger (VISTA-TV-EDITOR-DUAL-WRITE-BOUNDARY-027).
 *
 * Contrato: uma projeção local otimista NÃO é autorização para persistência por
 * outro write path. Enquanto uma PresentationMutation cobre entidades do
 * nativeConfig (blocks / campos top-level / dataModels), a serialização emitida
 * ao canal de autosave resolve essas entidades para o baseline confirmado —
 * nunca para a projeção pendente. A confirmação acontece exclusivamente pelo
 * fluxo governado (ACK canônico ou reconciliação autoritativa).
 *
 * O registro é por slide (vive no provider do editor) e não decide nada sobre
 * domínio: apenas marca quais entidades estão cobertas por uma mutation
 * in-flight e qual era o último estado confirmado delas.
 */

import type {
  ComunicadoBlock,
  ComunicadoConfig,
} from "@delpi/tv-dashboard-presentation";

import type { PresentationMutationOp } from "../api/tvDashboardApi";

export const PENDING_BLOCK_KEY_PREFIX = "block:";
export const PENDING_FIELD_KEY_PREFIX = "field:";
export const PENDING_DATAMODEL_KEY_PREFIX = "dataModel:";

export function pendingBlockKey(blockId: string): string {
  return `${PENDING_BLOCK_KEY_PREFIX}${blockId}`;
}

export function pendingFieldKey(field: string): string {
  return `${PENDING_FIELD_KEY_PREFIX}${field}`;
}

export function pendingDataModelKey(modelId: string): string {
  return `${PENDING_DATAMODEL_KEY_PREFIX}${modelId}`;
}

type PendingEntry = {
  /** Último estado confirmado da entidade; `present=false` = inserção pendente. */
  baseline: unknown;
  present: boolean;
  /** Valor projetado localmente no dispatch — detecta divergência de undo/redo. */
  projected: unknown;
  /** Gerações de mutation que cobrem a entidade (write lane é FIFO). */
  gens: Set<number>;
};

function lookupBaseline(
  baseline: ComunicadoConfig,
  key: string,
): { value: unknown; present: boolean } {
  if (key.startsWith(PENDING_BLOCK_KEY_PREFIX)) {
    const id = key.slice(PENDING_BLOCK_KEY_PREFIX.length);
    const block = (baseline.blocks ?? []).find(
      (item) => item.id === id,
    );
    return { value: block, present: block !== undefined };
  }
  if (key.startsWith(PENDING_DATAMODEL_KEY_PREFIX)) {
    const id = key.slice(PENDING_DATAMODEL_KEY_PREFIX.length);
    const model = (baseline.dataModels ?? []).find((item) => item.id === id);
    return { value: model, present: model !== undefined };
  }
  if (key.startsWith(PENDING_FIELD_KEY_PREFIX)) {
    const field = key.slice(PENDING_FIELD_KEY_PREFIX.length);
    const record = baseline as unknown as Record<string, unknown>;
    return {
      value: record[field],
      present: Object.prototype.hasOwnProperty.call(record, field),
    };
  }
  return { value: undefined, present: false };
}

export type PendingProjectionRegistry = ReturnType<
  typeof createPendingProjectionRegistry
>;

export function createPendingProjectionRegistry() {
  const entries = new Map<string, PendingEntry>();

  /**
   * Marca entidades cobertas por uma mutation in-flight. `baseline` deve ser o
   * config confirmado ANTES da projeção local (sem baseline disponível o mark
   * é ignorado — fail-open preserva o comportamento anterior, nunca inventa
   * uma baseline). O primeiro baseline vence: mutations subsequentes sobre a
   * mesma entidade apenas adicionam sua geração.
   */
  function mark(
    keys: Iterable<string>,
    baseline: ComunicadoConfig | undefined,
    gen: number,
    live?: ComunicadoConfig,
  ): void {
    if (!baseline) return;
    for (const key of keys) {
      const existing = entries.get(key);
      if (existing) {
        existing.gens.add(gen);
        // Atualiza a projeção esperada para a mutation mais nova — undo/redo
        // reconciliam contra o último resultado projetado.
        if (live) existing.projected = lookupBaseline(live, key).value;
        continue;
      }
      const { value, present } = lookupBaseline(baseline, key);
      entries.set(key, {
        baseline: value,
        present,
        projected: live ? lookupBaseline(live, key).value : value,
        gens: new Set([gen]),
      });
    }
  }

  /**
   * Settle de uma geração. Com `confirmed` (config canônico do ACK), entidades
   * ainda cobertas por gerações mais novas têm o baseline promovido para o
   * valor recém-confirmado — baseline é sempre "último estado confirmado".
   */
  function settle(
    keys: Iterable<string>,
    gen: number,
    confirmed?: ComunicadoConfig,
  ): void {
    for (const key of keys) {
      const entry = entries.get(key);
      if (!entry || !entry.gens.has(gen)) continue;
      entry.gens.delete(gen);
      if (entry.gens.size === 0) {
        entries.delete(key);
        continue;
      }
      if (confirmed) {
        const { value, present } = lookupBaseline(confirmed, key);
        entry.baseline = value;
        entry.present = present;
      }
    }
  }

  function clear(): void {
    entries.clear();
  }

  function hasPending(): boolean {
    return entries.size > 0;
  }

  function get(key: string): PendingEntry | undefined {
    return entries.get(key);
  }

  function keys(): string[] {
    return [...entries.keys()];
  }

  return { mark, settle, clear, hasPending, get, keys };
}

/**
 * Entidades cobertas por ops de uma PresentationMutation.
 * `blockId`/`blockIds`/`block.id` → blocks; `patch_native_config` → campos
 * top-level; `modelId`/`model.id` → dataModels.
 */
export function coveredKeysForMutationOps(
  ops: readonly PresentationMutationOp[],
): string[] {
  const keys = new Set<string>();
  for (const op of ops) {
    const record = op as Record<string, unknown>;
    if (typeof record.blockId === "string" && record.blockId) {
      keys.add(pendingBlockKey(record.blockId));
    }
    if (Array.isArray(record.blockIds)) {
      for (const id of record.blockIds) {
        if (typeof id === "string" && id) keys.add(pendingBlockKey(id));
      }
    }
    const block = record.block as Record<string, unknown> | undefined;
    if (block && typeof block.id === "string" && block.id) {
      keys.add(pendingBlockKey(block.id));
    }
    if (op.op === "patch_native_config") {
      const patch = record.patch as Record<string, unknown> | undefined;
      if (patch && typeof patch === "object") {
        for (const field of Object.keys(patch)) keys.add(pendingFieldKey(field));
      }
    }
    if (typeof record.modelId === "string" && record.modelId) {
      keys.add(pendingDataModelKey(record.modelId));
    }
    const model = record.model as Record<string, unknown> | undefined;
    if (model && typeof model.id === "string" && model.id) {
      keys.add(pendingDataModelKey(model.id));
    }
  }
  return [...keys];
}

export function coveredKeysForBlocks(
  blocks: readonly { id?: string }[],
): string[] {
  const keys: string[] = [];
  for (const block of blocks) {
    if (block?.id) keys.push(pendingBlockKey(block.id));
  }
  return keys;
}

/**
 * Campos top-level que divergem entre baseline e live (projeções que tocam
 * `groupTransforms`, `background` etc. fora dos ops tipados). `version` é
 * metadado de formato, não dado de entidade — nunca é pendurado.
 */
export function diffedFieldKeys(
  baseline: ComunicadoConfig | undefined,
  live: ComunicadoConfig,
): string[] {
  if (!baseline) return [];
  const base = baseline as unknown as Record<string, unknown>;
  const next = live as unknown as Record<string, unknown>;
  const keys = new Set<string>();
  for (const field of new Set([...Object.keys(base), ...Object.keys(next)])) {
    if (field === "blocks" || field === "dataModels" || field === "version") {
      continue;
    }
    if (base[field] !== next[field]) keys.add(pendingFieldKey(field));
  }
  return [...keys];
}

export type PersistableResolution = {
  resolved: ComunicadoConfig;
  /** true quando alguma entidade pendente foi substituída/omitida. */
  dropped: boolean;
};

function entityEquals(a: unknown, b: unknown): boolean {
  if (a === b) return true;
  if (a == null || b == null) return a === b;
  return JSON.stringify(a) === JSON.stringify(b);
}

/**
 * Entidades cujo valor live diverge da projeção registrada — sinal de que um
 * undo/redo (ou reconciliação) substituiu o resultado da mutation pendente e
 * a intenção do usuário precisa de uma mutation compensatória.
 */
export function driftedPendingKeys(
  registry: PendingProjectionRegistry,
  live: ComunicadoConfig,
): string[] {
  const drifted: string[] = [];
  for (const key of registry.keys()) {
    const entry = registry.get(key);
    if (!entry) continue;
    const { value } = lookupBaseline(live, key);
    if (!entityEquals(value, entry.projected)) drifted.push(key);
  }
  return drifted;
}

/**
 * Resolve a visão persistível do config: entidades cobertas por mutation
 * in-flight retornam ao baseline confirmado (ou são omitidas quando a baseline
 * não as continha — inserção pendente). Tudo que não está pendurado segue
 * exatamente como está — edições autosave-only nunca são tocadas.
 */
export function resolvePersistableConfig(
  config: ComunicadoConfig,
  registry: PendingProjectionRegistry,
): PersistableResolution {
  if (!registry.hasPending()) return { resolved: config, dropped: false };
  let dropped = false;
  const next = { ...config } as Record<string, unknown>;

  const blocks = config.blocks;
  if (blocks) {
    const resolvedBlocks: ComunicadoBlock[] = [];
    for (const block of blocks) {
      const entry = registry.get(pendingBlockKey(block.id));
      if (!entry) {
        resolvedBlocks.push(block);
        continue;
      }
      dropped = true;
      if (entry.present) {
        resolvedBlocks.push(entry.baseline as ComunicadoBlock);
      }
      // present=false → inserção pendente: omitir da serialização persistível.
    }
    next.blocks = resolvedBlocks;
  }

  const dataModels = config.dataModels;
  if (dataModels) {
    next.dataModels = dataModels
      .map((model) => {
        const entry = registry.get(pendingDataModelKey(model.id));
        if (!entry) return model;
        dropped = true;
        return entry.present ? (entry.baseline as typeof model) : null;
      })
      .filter((model): model is NonNullable<typeof model> => model !== null);
  }

  for (const key of registry.keys()) {
    if (!key.startsWith(PENDING_FIELD_KEY_PREFIX)) continue;
    const entry = registry.get(key);
    if (!entry) continue;
    dropped = true;
    const field = key.slice(PENDING_FIELD_KEY_PREFIX.length);
    if (entry.present) next[field] = entry.baseline;
    else delete next[field];
  }

  return { resolved: next as ComunicadoConfig, dropped };
}
