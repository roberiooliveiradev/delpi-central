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
   * config confirmado ANTES da projeção local — o canal de persistência
   * resolve-o via `resolveProjectionBaseline` (stash → estado autoritativo),
   * então `undefined` é reserva última: sem baseline disponível o mark é
   * ignorado (fail-open preserva o comportamento anterior, nunca inventa
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
 * Baseline da projeção para mark() (028 — baseline ausente nunca pode deixar
 * uma projeção mutation-backed sem cobertura). Preferência: stash do último
 * applyConfig (estado imediatamente anterior à projeção); fallback: último
 * estado confirmado autoritativo (slide-load / remote-apply / ACK canônico) —
 * um baseline confirmado real, nunca inventado. `undefined` só quando nem o
 * estado autoritativo existe — mark() então mantém o fail-open documentado.
 */
export function resolveProjectionBaseline(
  stash: ComunicadoConfig | undefined,
  authoritative: ComunicadoConfig | null | undefined,
): ComunicadoConfig | undefined {
  return stash ?? authoritative ?? undefined;
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
 * Overlay de edições autosave-only não confirmadas (028 — cenário misto).
 * No ACK da mutation, o canônico sobrescreveria o live e apagaria edições
 * autosave-only ainda não persistidas (debounce ~400ms). Para entidades NÃO
 * cobertas pela mutation, o valor live é intenção legítima do usuário — o
 * merge mantém o canônico nas entidades cobertas e reaplica o delta
 * autosave-only por cima, para que ele seja re-emitido e persistido pelo
 * canal de autosave. Blocos presentes só no live não são reintroduzidos
 * (delete remoto confirmado vence).
 */
export function mergeAutosaveOnlyOverlay(
  live: ComunicadoConfig | undefined,
  canonical: ComunicadoConfig,
  coveredKeys: ReadonlySet<string>,
): ComunicadoConfig | null {
  if (!live || live === canonical) return null;
  let changed = false;
  const next = { ...canonical } as Record<string, unknown>;

  const canonicalBlocks = new Map(
    (canonical.blocks ?? []).map((b) => [b.id, b]),
  );
  if (live.blocks) {
    const merged = canonical.blocks ?? [];
    const overlay = new Map(
      live.blocks
        .filter(
          (b) =>
            b?.id &&
            canonicalBlocks.has(b.id) &&
            !coveredKeys.has(pendingBlockKey(b.id)) &&
            !entityEquals(b, canonicalBlocks.get(b.id)),
        )
        .map((b) => [b.id, b]),
    );
    if (overlay.size > 0) {
      changed = true;
      next.blocks = merged.map((b) => overlay.get(b.id) ?? b);
    }
  }

  const canonicalModels = new Map(
    (canonical.dataModels ?? []).map((m) => [m.id, m]),
  );
  if (live.dataModels) {
    const overlay = new Map(
      live.dataModels
        .filter(
          (m) =>
            m?.id &&
            canonicalModels.has(m.id) &&
            !coveredKeys.has(pendingDataModelKey(m.id)) &&
            !entityEquals(m, canonicalModels.get(m.id)),
        )
        .map((m) => [m.id, m]),
    );
    if (overlay.size > 0) {
      changed = true;
      next.dataModels = (canonical.dataModels ?? []).map(
        (m) => overlay.get(m.id) ?? m,
      );
    }
  }

  const liveRecord = live as unknown as Record<string, unknown>;
  const canonicalRecord = canonical as unknown as Record<string, unknown>;
  for (const field of new Set([
    ...Object.keys(liveRecord),
    ...Object.keys(canonicalRecord),
  ])) {
    if (field === "blocks" || field === "dataModels" || field === "version") {
      continue;
    }
    if (coveredKeys.has(pendingFieldKey(field))) continue;
    if (!entityEquals(liveRecord[field], canonicalRecord[field])) {
      changed = true;
      next[field] = liveRecord[field];
    }
  }

  return changed ? (next as ComunicadoConfig) : null;
}

export type PersistableDispatchDecision = {
  /** true = enviar o payload capturado; false = descartar (stale/coberto). */
  send: boolean;
  /**
   * Payload seguro a reemitir quando `send` é false — canônico nas entidades
   * cobertas + delta autosave-only da captura (post-commit pós-navegação).
   */
  reEmit?: Record<string, unknown>;
};

/**
 * Guarda de DISPATCH do autosave (028 — write lane é FIFO: um PATCH capturado
 * com baseline coberto só pode ser ENVIADO depois que a mutation assentou; se
 * a mutation commitou nesse intervalo, o baseline capturado virou stale e o
 * PATCH reverteria a projeção já confirmada — lost update silencioso).
 *
 * Slide corrente: a captura só é segura se ainda é a visão persistível atual
 * (resolve de live+registry). Slide não-corrente (navegação antes do ACK):
 * - mutation não commitou → baseline coberto ainda é a última visão
 *   confirmada → envio seguro (B2: autosave-only viaja com o baseline).
 * - mutation commitou → baseline capturado é stale; quando resta delta
 *   autosave-only não-coberto, reemite canônico+delta (sem reverter).
 */
export function resolvePersistableDispatchDecision(args: {
  /** nativeConfig serializado capturado no save agendado. */
  captured: Record<string, unknown>;
  isCurrentSlide: boolean;
  live: ComunicadoConfig | undefined;
  registry: PendingProjectionRegistry;
  /** Último commit mutation-backed do slide (se houve desde a captura). */
  committed?: { canonical: ComunicadoConfig; coveredKeys: ReadonlySet<string> } | null;
  /** Key serializada do estado já persistido conhecido (suprime no-op write). */
  authoritativeKey?: string | null;
  serialize: (config: ComunicadoConfig) => Record<string, unknown>;
}): PersistableDispatchDecision {
  const capturedKey = JSON.stringify(args.captured);
  if (args.isCurrentSlide) {
    if (!args.live) return { send: true };
    const { resolved } = resolvePersistableConfig(args.live, args.registry);
    const resolvedKey = JSON.stringify(args.serialize(resolved));
    if (resolvedKey !== capturedKey) return { send: false };
    /* A captura segue correta, mas já coincide com o estado persistido —
     * reescrevê-la é no-op write que só bumpa revisão (alarga a janela CAS
     * dos peers e gera eco WS redundante). O commit mutation-backed é
     * registrado no hop mais cedo pós-resolution da lane — cobre a janela
     * em que o PATCH despacha após o settle mas antes do applyAck atualizar
     * a referência autoritativa. */
    if (resolvedKey === args.authoritativeKey) return { send: false };
    if (
      args.committed &&
      resolvedKey === JSON.stringify(args.serialize(args.committed.canonical))
    ) {
      return { send: false };
    }
    return { send: true };
  }
  if (!args.committed) return { send: true };
  const merged = mergeAutosaveOnlyOverlay(
    args.captured as unknown as ComunicadoConfig,
    args.committed.canonical,
    args.committed.coveredKeys,
  );
  if (!merged) return { send: false };
  const mergedSerialized = args.serialize(merged);
  if (JSON.stringify(mergedSerialized) === capturedKey) return { send: true };
  return { send: false, reEmit: mergedSerialized };
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
