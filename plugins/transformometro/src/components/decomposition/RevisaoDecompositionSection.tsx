import { useCallback, useEffect, useState } from "react";

import type { AppProps } from "../../App";
import { FieldLabel } from "@delpi/plugin-ui/index";
import { TM_HELP_TOOLTIPS } from "../../content/helpTooltips";
import {
  fetchRevisaoDecomposicaoMerged,
  saveRevisaoDecomposicaoOverlay,
} from "../../data/api/transformometroDecompositionApi";
import {
  emptyDecompositionTree,
  type DecompositionTreeV1,
  type MergedRevisaoDecomposition,
} from "../../types/decomposition";
import { decompositionTreeToOverlay } from "../../utils/decompositionOverlayDiff";
import { DecompositionFlatPreview } from "./DecompositionFlatPreview";
import { DecompositionTreeEditor } from "./DecompositionTreeEditor";
import { TabPanelTransition } from "../TabPanelTransition";

type Props = Pick<AppProps, "getAccessToken"> & {
  revisaoId: string;
  processoNome?: string;
  readOnly?: boolean;
  embeddedInCard?: boolean;
  resyncVersion?: number;
  onError: (message: string | null) => void;
};

export function RevisaoDecompositionSection({
  revisaoId,
  processoNome,
  getAccessToken,
  readOnly = false,
  embeddedInCard = false,
  resyncVersion = 0,
  onError,
}: Props) {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [merged, setMerged] = useState<MergedRevisaoDecomposition | null>(null);
  const [treeBase, setTreeBase] = useState<DecompositionTreeV1>(emptyDecompositionTree());
  const [editable, setEditable] = useState<DecompositionTreeV1>(emptyDecompositionTree());
  const [tab, setTab] = useState<"arvore" | "planilha">("arvore");

  const load = useCallback(async () => {
    setLoading(true);
    onError(null);
    try {
      const mergedData = await fetchRevisaoDecomposicaoMerged(revisaoId, getAccessToken);
      setMerged(mergedData);
      const base = mergedData.tree_base ?? {
        format: "decomposition_tree_v1" as const,
        format_version: 1 as const,
        nodes: [],
      };
      setTreeBase(base);
      setEditable(mergedData.tree ?? emptyDecompositionTree());
    } catch (err) {
      onError(err instanceof Error ? err.message : "Erro ao carregar mapeamento da revisão.");
    } finally {
      setLoading(false);
    }
  }, [getAccessToken, onError, revisaoId]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    if (!resyncVersion) return;
    void load();
  }, [resyncVersion, load]);

  async function handleSave() {
    setSaving(true);
    onError(null);
    try {
      const overlay = decompositionTreeToOverlay(treeBase, editable);
      await saveRevisaoDecomposicaoOverlay(revisaoId, overlay, getAccessToken);
      await load();
    } catch (err) {
      onError(err instanceof Error ? err.message : "Erro ao salvar overlay de mapeamento.");
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return <p className="ds-hint">Carregando mapeamento da revisão…</p>;
  }

  if (!merged || (!editable.nodes.length && !treeBase.nodes.length)) {
    return (
      <p className="ds-hint">
        Nenhum mapeamento no escopo desta instância. Cadastre a árvore no processo-mestre e o escopo na instância.
      </p>
    );
  }

  return (
    <div className="tm-decomposition-revisao">
      {!embeddedInCard ? (
        <FieldLabel
          className="tm-field__label"
          label="Mapeamento da revisão"
          hint={TM_HELP_TOOLTIPS.decomposition.mapeamentoRevisao}
        />
      ) : null}

      {!readOnly ? (
        <p className="ds-hint tm-decomposition-revisao__edit-hint">
          Edite livremente o WBS <strong>dentro do escopo</strong> desta melhoria: rótulos, ordem,
          exclusão e novos nós. O macro do processo permanece; o delta entra no{" "}
          <strong>macro composto</strong> pela vigência.
        </p>
      ) : null}

      {merged.warnings?.length ? (
        <div className="ds-state ds-state--warn" role="status">
          {merged.warnings.map((warning) => (
            <p key={warning}>{warning}</p>
          ))}
        </div>
      ) : null}

      {merged.baseline_diff ? (
        <p className="ds-hint" role="status">
          Diff vs baseline: {merged.baseline_diff.changed.length} alterados,{" "}
          {merged.baseline_diff.added.length} novos, {merged.baseline_diff.removed.length} removidos.
        </p>
      ) : null}

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
        {tab === "arvore" ? (
          <DecompositionTreeEditor
            tree={editable}
            readOnly={readOnly}
            title={processoNome ? `Mapeamento — ${processoNome}` : "Mapeamento da revisão"}
            allowRootProcessoChave={merged.escopo?.inherit_all !== false}
            onChange={setEditable}
          />
        ) : null}

        {tab === "planilha" ? (
          <DecompositionFlatPreview tree={editable} macroprocesso={processoNome} />
        ) : null}
      </TabPanelTransition>

      {!readOnly ? (
        <button type="button" className="ds-primary-btn" disabled={saving} onClick={() => void handleSave()}>
          {saving ? "Salvando…" : "Salvar mapeamento da revisão"}
        </button>
      ) : null}
    </div>
  );
}
