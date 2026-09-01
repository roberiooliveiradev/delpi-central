import { ActionButton, SectionHintLabel } from "@delpi/plugin-ui/index";
import { useMemo } from "react";
import type { useCatalogStructureValidation } from "../../state/hooks/useCatalogStructureValidation";
import { SI_HELP } from "../../content/helpTooltips";
import type {
  CatalogAdminAction,
  CatalogAdminView,
  GoalsAdminAction,
  SettingsAdminTab,
} from "../settings/settingsAdminTabs";
import { InfoState } from "./InfoState";
import { LoadingActivityInline } from "./LoadingActivityInline";
import "./SettingsOverviewWorkspace.css";

type ValidationState = ReturnType<typeof useCatalogStructureValidation>;

type SettingsOverviewWorkspaceProps = {
  validation: ValidationState;
  onNavigate: (
    tab: SettingsAdminTab,
    catalogView?: CatalogAdminView,
    options?: {
      catalogAction?: CatalogAdminAction | null;
      goalsAction?: GoalsAdminAction | null;
    },
  ) => void;
};

function formatIssuePreview(text: string, maxLength = 96): string {
  const trimmed = text.trim();
  if (trimmed.length <= maxLength) return trimmed;
  return `${trimmed.slice(0, maxLength - 1)}…`;
}

export function SettingsOverviewWorkspace({
  validation,
  onNavigate,
}: SettingsOverviewWorkspaceProps) {
  const departmentCount = useMemo(() => {
    const ids = new Set<string>();
    for (const row of validation.rows) {
      ids.add(row.departmentId);
    }
    return ids.size;
  }, [validation.rows]);

  const activeIndicators = validation.summary.totalRows;
  const goalsInYear = useMemo(
    () =>
      validation.rows.reduce(
        (total, row) => total + row.goalCoverage.activeCount,
        0,
      ),
    [validation.rows],
  );

  const openIssues =
    validation.summary.errors +
    validation.summary.warnings +
    validation.summary.infos;

  const pendingRows = useMemo(
    () =>
      validation.rows
        .filter((row) => row.worstSeverity !== "ok")
        .slice(0, 5),
    [validation.rows],
  );

  if (validation.loading && validation.rows.length === 0) {
    return (
      <LoadingActivityInline
        title="Carregando início"
        description="Contagens do catálogo e pendências de validação."
        variant="panel"
        tone="info"
      />
    );
  }

  if (validation.error) {
    return (
      <InfoState
        title="Início indisponível"
        description={validation.error}
        actionLabel="Tentar novamente"
        onAction={() => void validation.reload()}
      />
    );
  }

  return (
    <div className="si-settings-overview">
      <div className="si-settings-overview__kpi-strip" role="list">
        <article className="si-settings-overview__kpi" role="listitem">
          <SectionHintLabel
            label="Departamentos"
            hint={SI_HELP.overview.kpiDepartments}
          />
          <strong>{departmentCount}</strong>
        </article>
        <article className="si-settings-overview__kpi" role="listitem">
          <SectionHintLabel
            label="Indicadores"
            hint={SI_HELP.overview.kpiIndicators}
          />
          <strong>{activeIndicators}</strong>
        </article>
        <article className="si-settings-overview__kpi" role="listitem">
          <SectionHintLabel
            label={String(validation.goalYear)}
            hint={SI_HELP.overview.kpiGoalsYear}
          />
          <strong>{goalsInYear}</strong>
          <small>com meta no ano</small>
        </article>
        <article
          className={`si-settings-overview__kpi ${
            openIssues > 0 ? "si-settings-overview__kpi--warning" : ""
          }`}
          role="listitem"
        >
          <SectionHintLabel
            label="Pendências"
            hint={SI_HELP.overview.kpiValidationIssues}
          />
          <strong>{openIssues}</strong>
          <small>validação {validation.goalYear}</small>
        </article>
      </div>

      <div className="si-settings-overview__actions">
        <ActionButton
          variant="primary"
          title={SI_HELP.overview.actionGoValidation}
          onClick={() => onNavigate("catalog", "validation")}
        >
          Ir para validação
        </ActionButton>
        <ActionButton
          variant="ghost"
          title={SI_HELP.overview.actionNewIndicator}
          onClick={() =>
            onNavigate("catalog", "structure", {
              catalogAction: "new-indicator",
            })
          }
        >
          Novo indicador
        </ActionButton>
        <ActionButton
          variant="ghost"
          title={SI_HELP.overview.actionNewGoalYear}
          onClick={() => onNavigate("goals", undefined, { goalsAction: "new-year" })}
        >
          Novo ano de metas
        </ActionButton>
      </div>

      {pendingRows.length > 0 ? (
        <section className="si-settings-overview__pending">
          <header className="si-settings-overview__pending-header">
            <SectionHintLabel
              label="Pendências de validação"
              hint={SI_HELP.overview.pendingIssues}
            />
            <ActionButton
              variant="link"
              onClick={() => onNavigate("catalog", "validation")}
            >
              Ver todas →
            </ActionButton>
          </header>
          <ul className="si-settings-overview__pending-list">
            {pendingRows.map((row) => (
              <li key={`${row.departmentId}:${row.indicatorId}`}>
                <span className={`si-settings-overview__severity is-${row.worstSeverity}`}>
                  {row.worstSeverity === "error"
                    ? "Erro"
                    : row.worstSeverity === "warning"
                      ? "Atenção"
                      : "Info"}
                </span>
                <strong>
                  {row.departmentShortName || row.departmentName} · {row.indicatorName}
                </strong>
                <p>
                  {formatIssuePreview(
                    row.issues.map((issue) => issue.message).join(" · "),
                  )}
                </p>
              </li>
            ))}
          </ul>
        </section>
      ) : (
        <InfoState
          title="Catálogo coerente"
          description="Nenhum apontamento de validação para o ano selecionado."
        />
      )}
    </div>
  );
}
