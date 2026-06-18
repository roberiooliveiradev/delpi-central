import { AlertCircle } from "lucide-react";

import type { InspecoesEntradaHistoricoDetalheTest } from "../types/inspecoesEntradaHistoricoDetalhe";
import { formatDateTimePt, formatText } from "../utils/format";
import { resolveTestResultBadge } from "../utils/testResultBadge";
import {
  buildTestTitle,
  isFailedTest,
  isNumericTest,
  isTextualTest,
  resolveNumericMeasuredValue,
  resolveTextMeasuredValue,
  resolveTextSpecification,
} from "../utils/testMeasurementDisplay";
import { ResultBadge } from "./ResultBadge";

type InspecaoTestCardProps = {
  test: InspecoesEntradaHistoricoDetalheTest;
};

function SpecLine({
  label,
  value,
  emphasis = false,
}: {
  label: string;
  value: string;
  emphasis?: boolean;
}) {
  return (
    <p className={`ie-test-card__line${emphasis ? " ie-test-card__line--emphasis" : ""}`}>
      <span>{label}</span>
      {value}
    </p>
  );
}

function formatDimensionalSummary(test: InspecoesEntradaHistoricoDetalheTest): string | null {
  const parts: string[] = [];

  if (test.nominal_value?.trim()) {
    parts.push(`Nominal ${test.nominal_value.trim()}`);
  }
  if (test.lower_spec_limit?.trim()) {
    parts.push(`Mín ${test.lower_spec_limit.trim()}`);
  }
  if (test.upper_spec_limit?.trim()) {
    parts.push(`Máx ${test.upper_spec_limit.trim()}`);
  }

  return parts.length > 0 ? parts.join(" · ") : null;
}

export function InspecaoTestCard({ test }: InspecaoTestCardProps) {
  const failed = isFailedTest(test);
  const textual = isTextualTest(test);
  const numeric = isNumericTest(test);
  const textSpecification = resolveTextSpecification(test);
  const textMeasured = resolveTextMeasuredValue(test);
  const numericMeasured = resolveNumericMeasuredValue(test);
  const dimensionalSummary = formatDimensionalSummary(test);

  return (
    <article className={`ie-test-card${failed ? " ie-test-card--danger" : ""}`}>
      <div className="ie-test-card__header">
        <h4 className="ie-test-card__title">{buildTestTitle(test)}</h4>
        <ResultBadge badge={resolveTestResultBadge(test.result, test.result_code)} />
      </div>

      <div className="ie-test-card__content">
        {textual ? (
          <>
            {textSpecification ? (
              <SpecLine label="Especificação:" value={textSpecification} />
            ) : null}
            {textMeasured ? (
              <SpecLine label="Resultado:" value={textMeasured} emphasis={failed} />
            ) : null}
          </>
        ) : null}

        {numeric ? (
          <>
            {dimensionalSummary ? (
              <SpecLine label="Dimensões:" value={dimensionalSummary} />
            ) : null}
            {numericMeasured ? (
              <SpecLine label="Medido:" value={numericMeasured} emphasis={failed} />
            ) : null}
          </>
        ) : null}

        {!textual && !numeric && test.expected_specification ? (
          <SpecLine label="Especificação:" value={formatText(test.expected_specification)} />
        ) : null}
      </div>

      <p className="ie-test-card__meta">
        <span>Responsável:</span> {formatText(test.inspector_name)} ·{" "}
        {formatDateTimePt(test.measurement_date, test.measurement_time)}
      </p>

      {failed ? (
        <div className="ie-test-card__alert" aria-hidden="true">
          <AlertCircle size={14} />
        </div>
      ) : null}
    </article>
  );
}
