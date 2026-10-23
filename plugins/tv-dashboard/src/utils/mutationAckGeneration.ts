/**
 * PresentationMutation ack with generation guard (RIBBON-TEXT-002).
 *
 * Optimistic local preview is allowed; durable state comes from nativeConfig ack.
 * Stale responses (older generation) must not overwrite newer editor revisions.
 */

import type { ComunicadoConfig } from "@delpi/tv-dashboard-presentation";

import type { PresentationMutationOp, WriteGuard } from "../api/tvDashboardApi";
import {
  commitPresentationOps,
  commitUpsertBlocks,
  type MutationCommitMeta,
} from "./presentationMutationClient";
import {
  coveredKeysForBlocks,
  coveredKeysForMutationOps,
  diffedFieldKeys,
  type PendingProjectionRegistry,
} from "./pendingMutationProjection";

export type MutationAckApply = (canonical: ComunicadoConfig) => void;

/**
 * Canal de projeção pendente (027): enquanto a mutation está in-flight, as
 * entidades cobertas ficam marcadas e o canal de autosave serializa o
 * baseline confirmado — nunca a projeção. `getBaseline` retorna o config de
 * antes da projeção local (stash do applyConfig ou config pré-optimistic);
 * `getLive` retorna o config corrente para derivar campos projetados fora dos
 * ops tipados; `refresh` reemite a visão persistível para que um autosave já
 * agendado carregue o baseline e não a projeção capturada.
 */
export type PendingMutationProjection = {
  registry: PendingProjectionRegistry;
  getBaseline?: () => ComunicadoConfig | undefined;
  getLive?: () => ComunicadoConfig;
  refresh?: () => void;
};

function markPendingCoverage(
  pending: PendingMutationProjection | undefined,
  keys: string[],
  baseline: ComunicadoConfig | undefined,
  gen: number,
  live?: ComunicadoConfig,
): string[] {
  if (!pending) return keys;
  const allKeys = new Set(keys);
  if (live && baseline) {
    for (const key of diffedFieldKeys(baseline, live)) allKeys.add(key);
  }
  pending.registry.mark(allKeys, baseline, gen, live);
  pending.refresh?.();
  return [...allKeys];
}

/**
 * Identidade da mutação que falhou (025-R2). Capturada no dispatch — a
 * navegação do usuário para outro slide não pode reatribuir o erro ao
 * recurso errado. Correlação apenas; nunca autorização.
 */
export type MutationErrorContext = {
  playlistId: string;
  slideId: string;
};

export type MutationErrorHandler = (
  error: unknown,
  context: MutationErrorContext,
) => void;

export function createMutationGenerationGate() {
  let generation = 0;

  return {
    next(): number {
      generation += 1;
      return generation;
    },
    isCurrent(token: number): boolean {
      return token === generation;
    },
    current(): number {
      return generation;
    },
  };
}

export type MutationGenerationGate = ReturnType<typeof createMutationGenerationGate>;

/**
 * Upsert blocks and apply canonical ack when still current.
 * Returns applied canonical config, or null if skipped/stale/failed.
 */
export async function ackUpsertBlocksWithGeneration(args: {
  playlistId: string;
  slideId: string;
  blocks: Record<string, unknown>[];
  gate: MutationGenerationGate;
  applyAck: MutationAckApply;
  writeGuard?: WriteGuard;
  onCommitted?: (meta: MutationCommitMeta) => void;
  onError?: MutationErrorHandler;
  pending?: PendingMutationProjection;
}): Promise<ComunicadoConfig | null> {
  const { playlistId, slideId, blocks, gate, applyAck } = args;
  if (!playlistId || !slideId || blocks.length === 0) return null;
  const token = gate.next();
  const pending = args.pending;
  const baseline = pending?.getBaseline?.();
  const covered = markPendingCoverage(
    pending,
    coveredKeysForBlocks(blocks),
    baseline,
    token,
    pending?.getLive?.(),
  );
  try {
    const canonical = await commitUpsertBlocks({
      playlistId,
      slideId,
      blocks,
      writeGuard: args.writeGuard,
      onCommitted: args.onCommitted,
    });
    pending?.registry.settle(covered, token, canonical ?? undefined);
    if (!canonical || !gate.isCurrent(token)) {
      pending?.refresh?.();
      return null;
    }
    applyAck(canonical);
    pending?.refresh?.();
    return canonical;
  } catch (error) {
    /* Falha: marks ficam — o canal de autosave segue no baseline até a
     * reconciliação autoritativa (server-wins) limpar o registro. */
    args.onError?.(error, { playlistId, slideId });
    return null;
  }
}

/**
 * Commit typed ops and apply ack when still current.
 */
export async function commitOpsAndApplyAck(args: {
  playlistId: string;
  slideId: string;
  ops: PresentationMutationOp[];
  gate: MutationGenerationGate;
  applyAck: MutationAckApply;
  /** Local preview applied before the network round-trip. */
  optimistic?: () => void;
  writeGuard?: WriteGuard;
  onCommitted?: (meta: MutationCommitMeta) => void;
  onError?: MutationErrorHandler;
  pending?: PendingMutationProjection;
}): Promise<ComunicadoConfig | null> {
  const { playlistId, slideId, ops, gate, applyAck, optimistic } = args;
  if (!playlistId || !slideId || ops.length === 0) return null;
  const token = gate.next();
  const pending = args.pending;
  const baseline = pending?.getBaseline?.();
  optimistic?.();
  const covered = markPendingCoverage(
    pending,
    coveredKeysForMutationOps(ops),
    baseline,
    token,
    pending?.getLive?.(),
  );
  try {
    const canonical = await commitPresentationOps({
      playlistId,
      slideId,
      ops,
      writeGuard: args.writeGuard,
      onCommitted: args.onCommitted,
    });
    pending?.registry.settle(covered, token, canonical ?? undefined);
    if (!canonical) {
      pending?.refresh?.();
      return null;
    }
    if (!gate.isCurrent(token)) {
      pending?.refresh?.();
      return null;
    }
    applyAck(canonical);
    pending?.refresh?.();
    return canonical;
  } catch (error) {
    args.onError?.(error, { playlistId, slideId });
    return null;
  }
}
