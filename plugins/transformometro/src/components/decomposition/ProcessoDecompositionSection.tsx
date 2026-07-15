import { useCallback, useEffect, useMemo, useState } from "react";
import { Download, Sparkles } from "lucide-react";

import type { AppProps } from "../../App";
import { FieldLabel } from "@delpi/plugin-ui/index";
import { TM_HELP_TOOLTIPS } from "../../content/helpTooltips";
import {
  downloadProcessoDecomposicaoCsv,
  fetchProcessoDecomposicao,
  saveProcessoDecomposicao,
  suggestDecomposicaoRascunho,
} from "../../data/api/transformometroDecompositionApi";
import { emptyDecompositionTree, type DecompositionTreeV1 } from "../../types/decomposition";
import { DecompositionFlatPreview } from "./DecompositionFlatPreview";
import { TabPanelTransition } from "../TabPanelTransition";
import { DecompositionTreeEditor } from "./DecompositionTreeEditor";
import { DecompositionValidationPanel } from "./DecompositionValidationPanel";
import { useConfirm } from "../ui/ConfirmDialogProvider";
import {
  humanizeDecompositionApiError,
  scrollToDecompositionNode,
  validateDecompositionTreeForSave,
  type DecompositionValidationReport,
} from "../../utils/decompositionValidation";

type Props = Pick<AppProps, "getAccessToken"> & {
  processoId: string;
  processoNome?: string;
  readOnly?: boolean;
  embeddedInCard?: boolean;
  resyncVersion?: number;
  onError: (message: string | null) => void;
  onEntityChanged?: () => void;
};

export function ProcessoDecompositionSection({
  processoId,
  processoNome,
  getAccessToken,
  readOnly = false,
  embeddedInCard = false,
  resyncVersion = 0,
  onError,
  onEntityChanged,
}: Props) {
  const confirm = useConfirm();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [tree, setTree] = useState<DecompositionTreeV1>(emptyDecompositionTree());
  const [tab, setTab] = useState<"arvore" | "planilha">("arvore");
  const [validationReport, setValidationReport] = useState<DecompositionValidationReport | null>(null);

  const invalidNodeIds = useMemo(() => {
    if (!validationReport?.issues.length) return undefined;
    const ids = validationReport.issues.map((issue) => issue.nodeId).filter(Boolean) as string[];
    return ids.length ? new Set(ids) : undefined;
  }, [validationReport]);

  const load = useCallback(async () => {
    setLoading(true);
    onError(null);
    try {
      const data = await fetchProcessoDecomposicao(processoId, getAccessToken);
      setTree(data.conteudo ?? emptyDecompositionTree());
      setValidationReport(null);
    } catch (err) {
      onError(err instanceof Error ? err.message : "Erro ao carregar mapeamento.");
    } finally {
      setLoading(false);
    }
  }, [getAccessToken, onError, processoId]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    if (!resyncVersion) return;
    void load();
  }, [resyncVersion, load]);

  useEffect(() => {
    if (!validationReport?.issues.length) return;
    const nextReport = validateDecompositionTreeForSave(tree);
    setValidationReport(nextReport.valid ? null : nextReport);
  }, [tree, validationReport?.issues.length]);

  function applyValidationReport(report: DecompositionValidationReport) {
    setValidationReport(report);
    if (report.valid) return;
    setTab("arvore");
    const firstNodeId = report.issues.find((issue) => issue.nodeId)?.nodeId;
    if (firstNodeId) {
      window.requestAnimationFrame(() => scrollToDecompositionNode(firstNodeId));
    }
  }

  async function handleSave() {
    const clientReport = validateDecompositionTreeForSave(tree);
    if (!clientReport.valid) {
      onError(null);
      applyValidationReport(clientReport);
      return;
    }

    setSaving(true);
    onError(null);
    setValidationReport(null);
    try {
      await saveProcessoDecomposicao(processoId, tree, getAccessToken);
      await load();
      onEntityChanged?.();
    } catch (err) {
      const raw = err instanceof Error ? err.message : "Erro ao salvar mapeamento.";
      const apiReport = humanizeDecompositionApiError(raw, tree);
      if (apiReport.issues.some((issue) => issue.nodeId)) {
        onError(null);
        applyValidationReport(apiReport);
      } else {
        onError(apiReport.issues[0]?.message ?? raw);
      }
    } finally {
      setSaving(false);
    }
  }

  async function handleExportCsv() {
    onError(null);
    try {
      const blob = await downloadProcessoDecomposicaoCsv(processoId, getAccessToken);
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `mapeamento-${processoId}.csv`;
      link.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      onError(err instanceof Error ? err.message : "Erro ao exportar CSV.");
    }
  }

  async function handleSuggestDraft() {
    if (tree.nodes.length > 0) {
      const confirmed = await confirm({
        title: "Substituir mapeamento",
        message: "Substituir a árvore atual pelo rascunho sugerido a partir do fluxo?",
        confirmLabel: "Substituir",
        variant: "danger",
      });
      if (!confirmed) {
        return;
      }
    }
    onError(null);
    try {
      const draft = await suggestDecomposicaoRascunho(processoId, getAccessToken);
      setTree(draft.conteudo);
    } catch (err) {
      onError(err instanceof Error ? err.message : "Erro ao sugerir rascunho.");
    }
  }

  if (loading) {
    return <p className="ds-hint">Carregando mapeamento do processo…</p>;
  }

  return (
    <div className="tm-decomposition-section">
      {!embeddedInCard ? (
        <FieldLabel className="tm-field__label" label="Mapeamento do processo" hint={TM_HELP_TOOLTIPS.decomposition.mapeamento} />
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
            tree={tree}
            readOnly={readOnly}
            title={processoNome ? `Macroprocesso — ${processoNome}` : "Mapeamento do processo"}
            invalidNodeIds={invalidNodeIds}
            onChange={setTree}
          />
        ) : (
          <DecompositionFlatPreview tree={tree} macroprocesso={processoNome} />
        )}
      </TabPanelTransition>

      <DecompositionValidationPanel report={validationReport} />

      {!readOnly ? (
        <div className="tm-decomposition-section__actions">
          <button type="button" className="ds-ghost-btn" onClick={() => void handleSuggestDraft()}>
            <Sparkles size={14} />
            Sugerir do fluxo
          </button>
          <button type="button" className="ds-ghost-btn" onClick={() => void handleExportCsv()}>
            <Download size={14} />
            Exportar CSV
          </button>
          <button type="button" className="ds-primary-btn" disabled={saving} onClick={() => void handleSave()}>
            {saving ? "Salvando…" : "Salvar mapeamento"}
          </button>
        </div>
      ) : (
        <div className="tm-decomposition-section__actions">
          <button type="button" className="ds-ghost-btn" onClick={() => void handleExportCsv()}>
            <Download size={14} />
            Exportar CSV
          </button>
        </div>
      )}
    </div>
  );
}
