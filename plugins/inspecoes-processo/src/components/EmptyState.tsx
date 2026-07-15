import {
  EmptyState as KitEmptyState,
  delpiUiClass,
} from "@delpi/plugin-ui/index";

type EmptyStateProps = {
  title: string;
  description: string;
};

const classNames = {
  root: delpiUiClass("ip-empty-state", "delpi-ui-state-box delpi-ui-state-box--empty"),
  withTitle: true,
};

/** Thin wrapper — chrome do empty no kit (`state-box--empty`). */
export function EmptyState({ title, description }: EmptyStateProps) {
  return (
    <KitEmptyState
      title={title}
      message={description}
      classNames={classNames}
      defaultMessage=""
    />
  );
}
