import { ActionButton, SectionHintLabel } from "@delpi/plugin-ui/index";
import { useEffect, useMemo, useState } from "react";
import type { CatalogValidationRow } from "../../domain/catalogStructureValidation";
import type { ValidationSeverity } from "../../domain/catalogStructureValidation";
import { InfoState } from "./InfoState";
import { LoadingActivityInline } from "./LoadingActivityInline";
import { DrawerPanel } from "./DrawerPanel";
import { useCatalogStructureValidation } from "../../state/hooks/useCatalogStructureValidation";
import { getAggregationModeLabel, getScopeTypeLabel } from "../presentation/labels";
import { SI_HELP } from "../../content/helpTooltips";
import "./CatalogStructureValidationWorkspace.css";
import { SiSelectControl } from "./siFiltersUi";
import { SiNativeCheckboxControl } from "./siNativeFormFields";
import { SiAdminFormField } from "./SiAdminFormField";

type CatalogStructureValidationWorkspaceProps = {
  getAccessToken?: () => string | undefined;
  onOpenIndicator?: (departmentId: string, indicatorId: string) => void;
  onOpenGoals?: () => void;
};

const SEVERITY_LABEL: Record<ValidationSeverity, string> = {
  ok: "OK",
  info: "Info",
  warning: "Atenção",
  error: "Erro",
};

function validationRowKey(row: CatalogValidationRow): string {
  return row.indicatorId === "—"
    ? `dept-${row.departmentId}`
    : `${row.departmentId}-${row.indicatorId}`;
}

function GoalScopeBadges({
  consolidated,
  branch01,
  branch02,
}: {
  consolidated: boolean;
  branch01: boolean;
  branch02: boolean;
}) {
  return (
    <span className="si-catalog-validation__scopes">
      <span className={consolidated ? "is-on" : "is-off"} title={SI_HELP.badges.goalScopeConsolidated}>
        C
      </span>
      <span className={branch01 ? "is-on" : "is-off"} title={SI_HELP.badges.goalScope01}>
        01
      </span>
      <span className={branch02 ? "is-on" : "is-off"} title={SI_HELP.badges.goalScope02}>
        02
      </span>
    </span>
  );
}

function ValidationRowDetail({
  row,
  goalYear,
  onOpenIndicator,
  onOpenGoals,
}: {
  row: CatalogValidationRow;
  goalYear: number;
  onOpenIndicator?: (departmentId: string, indicatorId: string) => void;
  onOpenGoals?: () => void;
}) {
  const canOpenIndicator = row.indicatorId !== "—";

  return (
    <div className="si-catalog-validation__detail">
      <header className="si-catalog-validation__detail-header">
        <div>
          <h3>{row.indicatorName}</h3>
          <p>
            {row.departmentShortName || row.departmentName}
            {canOpenIndicator ? ` · ${row.indicatorId}` : ""}
          </p>
        </div>
        <span className={`si-catalog-validation__badge severity-${row.worstSeverity}`}>
          {SEVERITY_LABEL[row.worstSeverity]}
        </span>
      </header>

      <dl className="si-catalog-validation__detail-meta">
        <div>
          <dt>Agregação dept</dt>
          <dd>{getAggregationModeLabel(row.departmentAggregation)}</dd>
        </div>
        {canOpenIndicator ? (
          <>
            <div>
              <dt>Escopo</dt>
              <dd>{getScopeTypeLabel(row.scopeType)}</dd>
            </div>
            <div>
              <dt>Metas {goalYear}</dt>
              <dd>
                <GoalScopeBadges
                  consolidated={row.goalCoverage.consolidated}
                  branch01={row.goalCoverage.branch01}
                  branch02={row.goalCoverage.branch02}
                />
              </dd>
            </div>
          </>
        ) : null}
      </dl>

      <div className="si-catalog-validation__detail-issues">
        <h4>Apontamentos</h4>
        {row.issues.length === 0 ? (
          <p className="is-muted">Alinhado ao modelo esperado.</p>
        ) : (
          <ul>
            {row.issues.map((issue) => (
              <li key={issue.code} className={`severity-${issue.severity}`}>
                {issue.message}
              </li>
            ))}
          </ul>
        )}
      </div>

      {canOpenIndicator ? (
        <div className="si-catalog-validation__detail-actions">
          {onOpenIndicator ? (
            <ActionButton
              variant="primary"
              onClick={() => onOpenIndicator(row.departmentId, row.indicatorId)}
            >
              Ir para indicador
            </ActionButton>
          ) : null}
          {onOpenGoals ? (
            <ActionButton variant="ghost" onClick={onOpenGoals}>
              Ir para metas
            </ActionButton>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}

export function CatalogStructureValidationWorkspace({
  getAccessToken,
  onOpenIndicator,
  onOpenGoals,
}: CatalogStructureValidationWorkspaceProps) {
  const validation = useCatalogStructureValidation({ getAccessToken });
  const [onlyIssues, setOnlyIssues] = useState(true);
  const [departmentFilter, setDepartmentFilter] = useState("");
  const [selectedRowKey, setSelectedRowKey] = useState<string | null>(null);
  const [mobileDetailOpen, setMobileDetailOpen] = useState(false);

  const departmentOptions = useMemo(() => {
    const seen = new Map<string, string>();
    for (const row of validation.rows) {
      if (!seen.has(row.departmentId)) {
        seen.set(row.departmentId, row.departmentShortName || row.departmentName);
      }
    }
    return [...seen.entries()].map(([id, label]) => ({ id, label }));
  }, [validation.rows]);

  const filteredRows = useMemo(() => {
    return validation.rows.filter((row) => {
      if (departmentFilter && row.departmentId !== departmentFilter) return false;
      if (onlyIssues && row.worstSeverity === "ok") return false;
      return true;
    });
  }, [validation.rows, departmentFilter, onlyIssues]);

  const yearOptions = useMemo(() => {
    const current = new Date().getFullYear();
    return [current + 1, current, current - 1];
  }, []);

  useEffect(() => {
    if (filteredRows.length === 0) {
      setSelectedRowKey(null);
      return;
    }
    if (
      !selectedRowKey ||
      !filteredRows.some((row) => validationRowKey(row) === selectedRowKey)
    ) {
      setSelectedRowKey(validationRowKey(filteredRows[0]));
    }
  }, [filteredRows, selectedRowKey]);

  const selectedRow =
    filteredRows.find((row) => validationRowKey(row) === selectedRowKey) ?? null;

  function handleSelectRow(row: CatalogValidationRow) {
    setSelectedRowKey(validationRowKey(row));
    if (typeof window !== "undefined" && window.innerWidth <= 768) {
      setMobileDetailOpen(true);
    }
  }

  if (validation.loading && validation.rows.length === 0) {
    return (
      <LoadingActivityInline
        title="Carregando catálogo"
        description="Departamentos, indicadores e metas do ano selecionado."
        variant="panel"
        tone="info"
      />
    );
  }

  if (validation.error) {
    return (
      <InfoState
        title="Validação indisponível"
        description={validation.error}
        actionLabel="Tentar novamente"
        onAction={() => void validation.reload()}
      />
    );
  }

  return (
    <div className="si-catalog-validation">
      <div className="si-catalog-validation__toolbar">
        <SectionHintLabel
          label="Validação estrutural do catálogo"
          hint={SI_HELP.catalog.validationColIssues}
          className="si-catalog-validation__hint"
        />
        <button
          type="button"
          className="si-btn si-btn--secondary"
          onClick={() => void validation.reload()}
        >
          Atualizar
        </button>
      </div>

      <div className="si-catalog-validation__summary">
        <article className="si-catalog-validation__stat">
          <span>Indicadores</span>
          <strong>{validation.summary.totalRows}</strong>
        </article>
        <article className="si-catalog-validation__stat is-error">
          <span>Erros</span>
          <strong>{validation.summary.errors}</strong>
        </article>
        <article className="si-catalog-validation__stat is-warning">
          <span>Atenções</span>
          <strong>{validation.summary.warnings}</strong>
        </article>
        <article className="si-catalog-validation__stat is-info">
          <span>Informativos</span>
          <strong>{validation.summary.infos}</strong>
        </article>
        <article className="si-catalog-validation__stat is-ok">
          <span>Sem apontamento</span>
          <strong>{validation.summary.ok}</strong>
        </article>
      </div>

      {validation.departmentWeightIssues.length > 0 ? (
        <div className="si-catalog-validation__weight-banner" role="status">
          <strong>Pesos dos indicadores por departamento</strong>
          <ul>
            {validation.departmentWeightIssues.map((item) => (
              <li key={item.departmentId}>
                {item.shortName || item.departmentName}: soma{" "}
                <strong>{item.totalWeight}%</strong> (esperado 100%)
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      <div className="si-catalog-validation__filters">
        <SiAdminFormField label="Ano das metas" hint={SI_HELP.catalog.validationYear}>
          <SiSelectControl
            value={String(validation.goalYear)}
            onChange={(value) => validation.setGoalYear(Number(value))}
            options={yearOptions.map((year) => ({
              value: String(year),
              label: String(year),
            }))}
          />
        </SiAdminFormField>

        <SiAdminFormField label="Departamento" hint={SI_HELP.catalog.validationDepartment}>
          <SiSelectControl
            value={departmentFilter}
            onChange={setDepartmentFilter}
            allowEmpty
            emptyLabel="Todos"
            options={departmentOptions.map((option) => ({
              value: option.id,
              label: option.label,
            }))}
          />
        </SiAdminFormField>

        <SiNativeCheckboxControl
          className="si-catalog-validation__checkbox"
          checked={onlyIssues}
          onChange={setOnlyIssues}
          label="Mostrar só linhas com apontamento"
        />
      </div>

      {filteredRows.length === 0 ? (
        <InfoState
          title="Nenhuma linha neste filtro"
          description={
            onlyIssues
              ? "Não há inconsistências para o ano e filtros atuais."
              : "Não há registros para exibir."
          }
        />
      ) : (
        <div className="si-catalog-validation__split">
          <div className="si-catalog-validation__list" role="listbox" aria-label="Linhas de validação">
            {filteredRows.map((row) => {
              const key = validationRowKey(row);
              const isSelected = key === selectedRowKey;
              const preview =
                row.issues[0]?.message ??
                (row.worstSeverity === "ok" ? "Alinhado ao modelo esperado." : "—");

              return (
                <button
                  key={key}
                  type="button"
                  role="option"
                  aria-selected={isSelected}
                  className={`si-catalog-validation__list-item severity-${row.worstSeverity} ${
                    isSelected ? "is-selected" : ""
                  }`}
                  onClick={() => handleSelectRow(row)}
                >
                  <div className="si-catalog-validation__list-item-top">
                    <strong>
                      {row.departmentShortName || row.departmentName}
                      {row.indicatorId !== "—" ? ` › ${row.indicatorName}` : ""}
                    </strong>
                    <span className={`si-catalog-validation__badge severity-${row.worstSeverity}`}>
                      {SEVERITY_LABEL[row.worstSeverity]}
                    </span>
                  </div>
                  <p>{preview}</p>
                </button>
              );
            })}
          </div>

          {selectedRow ? (
            <div className="si-catalog-validation__detail-panel">
              <ValidationRowDetail
                row={selectedRow}
                goalYear={validation.goalYear}
                onOpenIndicator={onOpenIndicator}
                onOpenGoals={onOpenGoals}
              />
            </div>
          ) : null}
        </div>
      )}

      {selectedRow ? (
        <DrawerPanel
          open={mobileDetailOpen}
          onClose={() => setMobileDetailOpen(false)}
          title={selectedRow.indicatorName}
          description={selectedRow.departmentShortName || selectedRow.departmentName}
          size="lg"
        >
          <ValidationRowDetail
            row={selectedRow}
            goalYear={validation.goalYear}
            onOpenIndicator={(departmentId, indicatorId) => {
              setMobileDetailOpen(false);
              onOpenIndicator?.(departmentId, indicatorId);
            }}
            onOpenGoals={() => {
              setMobileDetailOpen(false);
              onOpenGoals?.();
            }}
          />
        </DrawerPanel>
      ) : null}
    </div>
  );
}
