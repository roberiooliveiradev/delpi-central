import { PAC_HELP_TOOLTIPS } from "../content/helpTooltips";
import type { PlanAction } from "../types/actionPlan";
import type { PlanEvidence } from "../types/rnc8d";
import { EvidenceAttachForm } from "./evidence/EvidenceAttachForm";
import { EvidenceListTable } from "./evidence/EvidenceListTable";
import { SectionCard } from "./ui/SectionCard";

type Props = {
  planId: string;
  evidences: PlanEvidence[];
  actions?: PlanAction[];
  onChanged: () => void | Promise<void>;
  title?: string;
  subtitle?: string;
  /** Sem wrapper SectionCard — uso dentro de EditableSectionCard. */
  bare?: boolean;
  /** Somente listagem (sem upload nem exclusão). */
  readOnly?: boolean;
};

export function EvidencePanel({
  planId,
  evidences,
  actions = [],
  onChanged,
  title = "Banco de conhecimento e evidências",
  subtitle = "Anexe prints, PDFs, planilhas e documentos do processo. Visível para o analista e para o agente GPT.",
  bare = false,
  readOnly = false,
}: Props) {
  const body = (
    <div className="pac-evidence-panel">
      {!readOnly ? (
        <EvidenceAttachForm
          planId={planId}
          actions={actions}
          onUploaded={onChanged}
        />
      ) : null}

      {evidences.length || readOnly ? (
        <div className={readOnly ? undefined : "pac-evidence-panel__existing"}>
          {!readOnly ? (
            <h4 className="pac-evidence-panel__existing-title">Já anexados</h4>
          ) : null}
          <EvidenceListTable
            planId={planId}
            evidences={evidences}
            actions={actions}
            readOnly={readOnly}
            onChanged={onChanged}
            compact={readOnly}
          />
        </div>
      ) : null}
    </div>
  );

  if (bare) {
    return body;
  }

  return (
    <SectionCard
      title={title}
      hint={PAC_HELP_TOOLTIPS.sections.evidences}
      subtitle={subtitle}
    >
      {body}
    </SectionCard>
  );
}
