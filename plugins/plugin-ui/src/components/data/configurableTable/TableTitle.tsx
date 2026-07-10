import { useConfigurableTableClasses } from "../configurableTableClasses";

export type TableTitleProps = {
  title?: string;
  visible?: boolean;
};

export function TableTitle({ title, visible = true }: TableTitleProps) {
  const cn = useConfigurableTableClasses();
  if (!visible || !title?.trim()) return null;
  return <div className={cn.title}>{title.trim()}</div>;
}
