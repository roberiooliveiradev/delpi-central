import { useCallback, useEffect, useMemo, useState } from "react";

import type { AppProps } from "../../App";
import { FieldLabel, NativeTextControl } from "@delpi/plugin-ui/index";
import { TM_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { fetchProcessoDecomposicaoComposed } from "../../data/api/transformometroDecompositionApi";
import type { ComposedProcessoDecomposition } from "../../types/decomposition";
import {
  applyDiffHighlightsToRichTree,
  stripDecompositionHighlights,
} from "../../utils/diffHighlightDisplay";
import { buildDecompositionRichTree } from "../../utils/decompositionRichTree";
import { DecompositionFlatPreview } from "./DecompositionFlatPreview";
import { DecompositionRichTree } from "./DecompositionRichTree";
import { DiffHighlightToggle } from "../DiffHighlightToggle";
import { TabPanelTransition } from "../TabPanelTransition";
import { todayDateInput } from "../../utils/dateInputs";
import { DS_GHOST_BTN } from "../ghostChrome";

type Props = Pick<AppProps, "getAccessToken"> & {
  processoId: string;
  processoNome?: string;
  embeddedInCard?: boolean;
  resyncVersion?: number;
  onError: (message: string | null) => void;
};

export function ProcessoDecompositionComposedSection({
  processoId,
  processoNome,
  getAccessToken,
  embeddedInCard = false,
  resyncVersion = 0,
  onError,
}: Props) {
  const [loading, setLoading] = useState(true);
  const [at, setAt] = useState(todayDateInput());
  const [composed, setComposed] = useState<ComposedProcessoDecomposition | null>(null);
  const [tab, setTab] = useState<"arvore" | "planilha">("arvore");
  const [showDiff, setShowDiff] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    onError(null);
    try {
      const data = await fetchProcessoDecomposicaoComposed(processoId, getAccessToken, { at });
      setComposed(data);
    } catch (err) {
      onError(err instanceof Error ? err.message : "Erro ao carregar macro composto.");
    } finally {
      setLoading(false);
    }
  }, [at, getAccessToken, onError, processoId]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    if (!resyncVersion) return;
    void load();
  }, [resyncVersion, load]);

  const conflictDiff = useMemo(() => {
    if (!composed?.conflicts?.length) return null;
    return {
      changed: [...new Set(composed.conflicts.map((c) => c.node_id))],
      added: [] as string[],
      removed: [] as string[],
    };
  }, [composed]);

  const richRoot = useMemo(() => {
    if (!composed?.tree) return null;
    const source = stripDecompositionHighlights(composed.tree);
    const root = buildDecompositionRichTree(source, {
      title: processoNome ? `Macro composto — ${processoNome}` : "Macro composto",
    });
    return showDiff && conflictDiff ? applyDiffHighlightsToRichTree(root, conflictDiff) : root;
  }, [composed, processoNome, showDiff, conflictDiff]);

  if (loading && !composed) {
    return <p className="ds-hint">Carregando macro composto…</p>;
  }

  return (
    <div className="tm-decomposition-composed">
      {!embeddedInCard ? (
        <FieldLabel
          className="tm-field__label"
          label="Macro composto"
          hint={TM_HELP_TOOLTIPS.decomposition.macroComposto}
        />
      ) : null}

      <div className="tm-decomposition-composed__toolbar">
        <label className="tm-decomposition-composed__date">
          <span className="ds-hint">Compor em</span>
          <NativeTextControl type="date" value={at} onChange={setAt} aria-label="Data de composição" />
        </label>
        <button type="button" className={DS_GHOST_BTN} disabled={loading} onClick={() => void load()}>
          {loading ? "Atualizando…" : "Atualizar"}
        </button>
      </div>

      {composed?.applied_revisoes?.length ? (
        <p className="ds-hint">
          {composed.applied_revisoes.length} revisão(ões) vigente(s) aplicadas
          {composed.conflicts?.length
            ? ` · ${composed.conflicts.length} conflito(s) de interseção`
            : ""}
          .
        </p>
      ) : (
        <p className="ds-hint">Nenhuma revisão vigente nesta data — exibindo o macro base.</p>
      )}

      {composed?.conflicts?.length ? (
        <DiffHighlightToggle
          active={showDiff}
          onChange={setShowDiff}
          summary={`${composed.conflicts.length} conflito(s) de interseção no mesmo nó.`}
        />
      ) : null}

      {showDiff && composed?.conflicts?.length ? (
        <div className="ds-state ds-state--warn" role="status">
          <p>
            Interseções no mesmo nó: o rótulo exibido é o da revisão com início de vigência mais
            recente. Revise as melhorias listadas.
          </p>
          <ul className="tm-decomposition-composed__conflicts">
            {composed.conflicts.map((conflict) => (
              <li key={`${conflict.node_id}-${conflict.field}`}>
                Nó <code>{conflict.node_id}</code> ({conflict.field}):{" "}
                {conflict.revisoes
                  .map((r) => r.versao_revisao || r.revisao_id.slice(0, 8))
                  .join(" × ")}
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {!composed?.tree?.nodes?.length ? (
        <p className="ds-hint">Macro base vazio. Cadastre o mapeamento do processo.</p>
      ) : (
        <>
          <div className="tm-decomposition-section__tabs">
            <button
              type="button"
              className={tab === "arvore" ? "ds-tab-btn is-active" : "ds-tab-btn"}
              onClick={() => setTab("arvore")}
            >
              Árvore
            </button>
            <button
              type="button"
              className={tab === "planilha" ? "ds-tab-btn is-active" : "ds-tab-btn"}
              onClick={() => setTab("planilha")}
            >
              Planilha
            </button>
          </div>

          <TabPanelTransition tabKey={tab}>
            {tab === "arvore" && richRoot ? (
              <DecompositionRichTree root={richRoot} expandDepth={2} />
            ) : null}
            {tab === "planilha" && composed?.tree ? (
              <DecompositionFlatPreview tree={composed.tree} macroprocesso={processoNome} />
            ) : null}
          </TabPanelTransition>
        </>
      )}
    </div>
  );
}
