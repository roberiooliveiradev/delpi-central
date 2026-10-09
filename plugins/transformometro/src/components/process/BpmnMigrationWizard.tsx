import { useCallback, useEffect, useRef, useState } from "react";
import { renderBpmnThumbnail } from "@delpi/bpmn-editor";

import type { AppProps } from "../../App";
import {
  BpmnMigrationError,
  commitBpmnMigration,
  prepareBpmnMigration,
  type MigrationAmbiguity,
  type MigrationProposal,
  type MigrationResolutions,
} from "../../data/api/bpmnMigrationApi";
import { DS_GHOST_BTN } from "../ghostChrome";
import { HostContainedWideDialog } from "../ui/Modal";

type Props = Pick<AppProps, "getAccessToken"> & {
  processoId: string;
  open: boolean;
  onClose: () => void;
  /** Migração confirmada e verificada — host navega p/ o editor nativo. */
  onMigrated: () => void;
};

type Step = "analyzing" | "report" | "preview" | "committing" | "done";

const CLASS_LABELS: Record<string, string> = {
  EXACT: "Mapeamentos exatos",
  HEURISTIC: "Mapeados por heurística",
  AMBIGUOUS: "Ambíguos",
  UNMAPPABLE: "Não mapeáveis",
  IGNORED_METADATA: "Metadados preservados (não convertidos)",
};

function describeError(err: unknown, fallback: string): string {
  if (err instanceof BpmnMigrationError) {
    if (err.errorCode === "proposal_stale") {
      return "O mapeamento legado mudou após a análise. A proposta expirou — execute a migração novamente.";
    }
    return err.message;
  }
  return err instanceof Error && err.message ? err.message : fallback;
}

/**
 * Wizard da migração governada (G8):
 *   análise TÉO (PREPARE — nunca grava) → relatório de perdas/ambiguidades
 *   → resolução explícita → re-PREPARE → preview BPMN somente leitura
 *   → confirmação humana → commit_proposal (ACT) → editor nativo.
 *
 * O candidato nunca é persistido antes da confirmação; o XML mostrado no
 * preview é o artefato selado na proposta (exact_change.candidate_xml).
 */
export function BpmnMigrationWizard({
  processoId,
  getAccessToken,
  open,
  onClose,
  onMigrated,
}: Props) {
  const [step, setStep] = useState<Step>("analyzing");
  const [proposal, setProposal] = useState<MigrationProposal | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [resolutions, setResolutions] = useState<MigrationResolutions>({});
  const [previewSvg, setPreviewSvg] = useState<string | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const runIdRef = useRef(0);

  const runPrepare = useCallback(
    async (res?: MigrationResolutions) => {
      const runId = ++runIdRef.current;
      setStep("analyzing");
      setError(null);
      setPreviewSvg(null);
      try {
        const next = await prepareBpmnMigration(
          processoId,
          getAccessToken,
          res,
        );
        if (runId !== runIdRef.current) return;
        setProposal(next);
        setStep("report");
      } catch (err) {
        if (runId !== runIdRef.current) return;
        setError(
          describeError(err, "Falha ao analisar o mapeamento legado."),
        );
        setStep("report");
      }
    },
    [processoId, getAccessToken],
  );

  useEffect(() => {
    if (!open) return;
    setProposal(null);
    setResolutions({});
    setPreviewSvg(null);
    void runPrepare();
    return () => {
      runIdRef.current += 1;
    };
  }, [open, runPrepare]);

  function resolutionFor(amb: MigrationAmbiguity) {
    return resolutions[amb.ambiguity_id] ?? { option: "" };
  }

  function setResolutionOption(amb: MigrationAmbiguity, option: string) {
    setResolutions((prev) => ({
      ...prev,
      [amb.ambiguity_id]: { option, values: {} },
    }));
  }

  function setResolutionValue(
    amb: MigrationAmbiguity,
    legacyId: string,
    value: string,
  ) {
    setResolutions((prev) => {
      const current = prev[amb.ambiguity_id] ?? { option: "", values: {} };
      return {
        ...prev,
        [amb.ambiguity_id]: {
          ...current,
          values: { ...(current.values ?? {}), [legacyId]: value },
        },
      };
    });
  }

  const allAmbiguitiesAnswered = (
    proposal?.validation_result.migration_report.ambiguities ?? []
  ).every((amb) => {
    const res = resolutions[amb.ambiguity_id];
    if (!res?.option) return false;
    const option = amb.options.find((o) => o.id === res.option);
    if (!option?.requires_values) return true;
    const targets = amb.legacy_object_ids.slice(1);
    return targets.every((id) => (res.values?.[id] ?? "").trim() !== "");
  });

  async function handlePreview() {
    if (!proposal) return;
    setPreviewLoading(true);
    setError(null);
    try {
      const result = await renderBpmnThumbnail(
        proposal.exact_change.candidate_xml,
      );
      setPreviewSvg(result.kind === "svg" ? result.svg : null);
      setStep("preview");
    } catch {
      setError("Não foi possível renderizar o preview do BPMN candidato.");
    } finally {
      setPreviewLoading(false);
    }
  }

  async function handleConfirm() {
    if (!proposal?.proposal_handle) return;
    setBusy(true);
    setStep("committing");
    setError(null);
    try {
      await commitBpmnMigration(proposal.proposal_handle, getAccessToken);
      setStep("done");
      onMigrated();
    } catch (err) {
      setError(
        describeError(err, "Falha ao confirmar a migração."),
      );
      setStep("preview");
    } finally {
      setBusy(false);
    }
  }

  const report = proposal?.validation_result.migration_report;
  const validation = proposal?.validation_result.bpmn_validation;
  const stats = report?.statistics ?? {};
  const counts = stats.by_classification ?? {};
  const ambiguities = report?.ambiguities ?? [];
  const losses = report?.losses ?? [];
  const warnings = report?.warnings ?? [];
  const ready = Boolean(proposal?.ready && proposal.act_allowed);

  return (
    <HostContainedWideDialog
      open={open}
      title="Migrar mapeamento legado para BPMN"
      onClose={onClose}
      className="tm-bpmn-migration-wizard"
    >
      {step === "analyzing" ? (
        <p className="ds-hint" role="status">
          TÉO está analisando o mapeamento legado…
        </p>
      ) : null}

      {error ? (
        <p className="ds-hint" role="alert">
          {error}
        </p>
      ) : null}

      {step === "report" && report ? (
        <div className="tm-migration-report" data-testid="migration-report">
          <p className="ds-hint">
            TÉO analisou o mapeamento — {(stats.legacy_nodes ?? 0) +
              (stats.legacy_edges ?? 0)}{" "}
            elementos.
          </p>
          <dl className="tm-migration-stats">
            {Object.entries(CLASS_LABELS).map(([cls, label]) =>
              counts[cls] ? (
                <div key={cls}>
                  <dt>{label}</dt>
                  <dd>{counts[cls]}</dd>
                </div>
              ) : null,
            )}
            {losses.length ? (
              <div>
                <dt>Perdas reportadas</dt>
                <dd>{losses.length}</dd>
              </div>
            ) : null}
          </dl>

          {ambiguities.length ? (
            <section aria-label="Ambiguidades">
              <h4 className="ds-subsection-title">
                {ambiguities.length} ambiguidade(s) — resolução humana
                obrigatória
              </h4>
              {ambiguities.map((amb) => {
                const res = resolutionFor(amb);
                const selected = amb.options.find(
                  (o) => o.id === res.option,
                );
                return (
                  <fieldset
                    key={amb.ambiguity_id}
                    className="tm-migration-ambiguity"
                  >
                    <legend>{amb.ambiguity_id}</legend>
                    <p className="ds-hint">{amb.description}</p>
                    {amb.options.map((option) => (
                      <label key={option.id}>
                        <input
                          type="radio"
                          name={amb.ambiguity_id}
                          checked={res.option === option.id}
                          onChange={() =>
                            setResolutionOption(amb, option.id)
                          }
                        />{" "}
                        {option.label}
                      </label>
                    ))}
                    {selected?.requires_values ? (
                      <div className="tm-migration-ambiguity-values">
                        {amb.legacy_object_ids.slice(1).map((legacyId) => (
                          <label key={legacyId}>
                            Condição para <code>{legacyId}</code>
                            <input
                              type="text"
                              value={res.values?.[legacyId] ?? ""}
                              onChange={(event) =>
                                setResolutionValue(
                                  amb,
                                  legacyId,
                                  event.target.value,
                                )
                              }
                              placeholder='Ex.: "Sim", "Não — retrabalho"'
                            />
                          </label>
                        ))}
                      </div>
                    ) : null}
                  </fieldset>
                );
              })}
            </section>
          ) : null}

          {losses.length ? (
            <section aria-label="Perdas">
              <h4 className="ds-subsection-title">Perdas reportadas</h4>
              <ul>
                {losses.map((loss) => (
                  <li key={loss.loss_id}>
                    <strong>{loss.classification}</strong> —{" "}
                    {loss.description}
                  </li>
                ))}
              </ul>
            </section>
          ) : null}

          {warnings.length ? (
            <section aria-label="Avisos">
              <h4 className="ds-subsection-title">Avisos</h4>
              <ul>
                {warnings.map((warning) => (
                  <li key={warning}>{warning}</li>
                ))}
              </ul>
            </section>
          ) : null}

          {validation && validation.passed === false ? (
            <p className="ds-hint" role="alert">
              Validação BPMN: FAIL — {validation.blocking_issues ?? 0}{" "}
              erro(s) bloqueante(s).
            </p>
          ) : null}

          <div
            style={{
              display: "flex",
              gap: 8,
              flexWrap: "wrap",
              marginTop: 16,
            }}
          >
            {ambiguities.length ? (
              <button
                type="button"
                className={DS_GHOST_BTN}
                disabled={!allAmbiguitiesAnswered || busy}
                onClick={() => void runPrepare(resolutions)}
              >
                Re-analisar com resoluções
              </button>
            ) : null}
            {ready ? (
              <button
                type="button"
                className={DS_GHOST_BTN}
                disabled={previewLoading}
                onClick={() => void handlePreview()}
              >
                {previewLoading
                  ? "Renderizando preview…"
                  : "Pré-visualizar BPMN"}
              </button>
            ) : null}
            <button
              type="button"
              className={DS_GHOST_BTN}
              onClick={onClose}
            >
              Cancelar
            </button>
          </div>
        </div>
      ) : null}

      {(step === "preview" || step === "committing") && proposal ? (
        <div data-testid="migration-preview">
          <p className="ds-hint">
            Validação BPMN:{" "}
            {validation?.passed ? "PASS" : "com ressalvas"} — candidato{" "}
            <code>
              {proposal.exact_change.candidate_sha256.slice(0, 12)}…
            </code>
          </p>
          {previewSvg ? (
            <div
              className="tm-migration-preview-diagram"
              // SVG gerado pelo renderer bpmn.js local (fonte confiável —
              // artefato selado na proposta).
              dangerouslySetInnerHTML={{ __html: previewSvg }}
            />
          ) : (
            <p className="ds-hint">
              Preview gráfico indisponível — o XML candidato segue selado
              na proposta.
            </p>
          )}
          <p className="ds-hint">
            O desenho legado será preservado. O novo BPMN passará a ser o
            mapeamento vigente do processo.
          </p>
          <div
            style={{
              display: "flex",
              gap: 8,
              flexWrap: "wrap",
              marginTop: 16,
            }}
          >
            <button
              type="button"
              className={DS_GHOST_BTN}
              disabled={busy}
              onClick={() => void handleConfirm()}
            >
              {busy
                ? "Confirmando migração…"
                : "Confirmar migração para BPMN"}
            </button>
            <button
              type="button"
              className={DS_GHOST_BTN}
              disabled={busy}
              onClick={() => setStep("report")}
            >
              Voltar ao relatório
            </button>
            <button
              type="button"
              className={DS_GHOST_BTN}
              disabled={busy}
              onClick={onClose}
            >
              Cancelar
            </button>
          </div>
        </div>
      ) : null}

      {step === "done" ? (
        <p className="ds-hint" role="status">
          Migração concluída — abrindo o editor BPMN nativo…
        </p>
      ) : null}
    </HostContainedWideDialog>
  );
}
