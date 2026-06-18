import type {
  InspecoesEntradaHistoricoDetalheTest,
  MeasurementSource,
} from "../types/inspecoesEntradaHistoricoDetalhe";
import { formatText } from "./format";

function trimmed(value: string | null | undefined): string | null {
  const normalized = value?.trim();
  return normalized ? normalized : null;
}

export function buildTestTitle(test: InspecoesEntradaHistoricoDetalheTest): string {
  const code = formatText(test.test_code);
  const name = trimmed(test.test_name);
  return name ? `${code} · ${name}` : code;
}

export function isTextualTest(test: InspecoesEntradaHistoricoDetalheTest): boolean {
  return Boolean(
    trimmed(test.text_specification) ||
      trimmed(test.text_measured_value) ||
      (test.measurement_source === "QEQ" && trimmed(test.measured_value)),
  );
}

export function isNumericTest(test: InspecoesEntradaHistoricoDetalheTest): boolean {
  return Boolean(
    trimmed(test.nominal_value) ||
      trimmed(test.lower_spec_limit) ||
      trimmed(test.upper_spec_limit) ||
      trimmed(test.numeric_measured_value) ||
      test.measurement_source === "QES",
  );
}

export function resolveTextSpecification(test: InspecoesEntradaHistoricoDetalheTest): string | null {
  return trimmed(test.text_specification) ?? (isNumericTest(test) ? null : trimmed(test.expected_specification));
}

export function resolveTextMeasuredValue(test: InspecoesEntradaHistoricoDetalheTest): string | null {
  const direct = trimmed(test.text_measured_value);
  if (direct) return direct;

  if (!trimmed(test.numeric_measured_value)) {
    return trimmed(test.measured_value);
  }

  return null;
}

export function resolveNumericMeasuredValue(test: InspecoesEntradaHistoricoDetalheTest): string | null {
  const direct = trimmed(test.numeric_measured_value);
  if (direct) return direct;

  if (test.measurement_source === "QES") {
    return trimmed(test.measured_value);
  }

  return null;
}

export function formatMeasurementSourceHint(source: MeasurementSource | null): string | null {
  if (source === "QEQ") return "QEQ: medição textual";
  if (source === "QES") return "QES: medição numérica";
  return null;
}

export function isFailedTest(test: InspecoesEntradaHistoricoDetalheTest): boolean {
  return test.result_code === "R" || test.result === "REPROVADO";
}
