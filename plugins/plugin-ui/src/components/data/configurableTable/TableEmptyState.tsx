import { useConfigurableTableClasses } from "../configurableTableClasses";

export type TableEmptyStateProps = {
  message?: string;
};

export function TableEmptyState({ message = "Sem linhas" }: TableEmptyStateProps) {
  const cn = useConfigurableTableClasses();
  return <div className={cn.emptyState}>{message}</div>;
}
