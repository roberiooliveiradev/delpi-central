import {
  toStrategicIndicatorsErrorView,
  type StrategicIndicatorsErrorContext,
  type StrategicIndicatorsErrorView,
} from "../../data/errors/strategicIndicatorsError";

export function captureStrategicIndicatorsError(
  error: unknown,
  context: StrategicIndicatorsErrorContext,
): StrategicIndicatorsErrorView {
  return toStrategicIndicatorsErrorView(error, context);
}
