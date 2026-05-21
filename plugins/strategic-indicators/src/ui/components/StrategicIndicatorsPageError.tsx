import {
  withStrategicIndicatorsErrorMode,
  type StrategicIndicatorsErrorMode,
  type StrategicIndicatorsErrorView,
} from "../../data/errors/strategicIndicatorsError";
import { StrategicIndicatorsErrorState } from "./StrategicIndicatorsErrorState";

type StrategicIndicatorsPageErrorProps = {
  error: StrategicIndicatorsErrorView;
  mode?: StrategicIndicatorsErrorMode;
  actionLabel?: string;
  onAction?: () => void;
};

/**
 * Erro padronizado das páginas analíticas do módulo (card com causas, sugestões e detalhe técnico).
 */
export function StrategicIndicatorsPageError({
  error,
  mode = "load",
  actionLabel = "Tentar novamente",
  onAction,
}: StrategicIndicatorsPageErrorProps) {
  return (
    <StrategicIndicatorsErrorState
      error={withStrategicIndicatorsErrorMode(error, mode)}
      actionLabel={onAction ? actionLabel : undefined}
      onAction={onAction}
    />
  );
}
