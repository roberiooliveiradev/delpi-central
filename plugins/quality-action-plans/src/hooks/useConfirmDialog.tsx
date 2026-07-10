import { useConfirmDialogController, type ConfirmDialogOptions } from "@delpi/plugin-ui/index";

import { ConfirmModal } from "../components/ui/ConfirmModal";

export type { ConfirmDialogOptions };

export function useConfirmDialog() {
  const { confirm, pending, confirmPending, cancelPending } = useConfirmDialogController();

  const confirmDialog = (
    <ConfirmModal
      open={pending !== null}
      title={pending?.title}
      message={pending?.message ?? ""}
      confirmLabel={pending?.confirmLabel}
      cancelLabel={pending?.cancelLabel}
      variant={pending?.variant}
      onConfirm={confirmPending}
      onCancel={cancelPending}
    />
  );

  return { confirm, confirmDialog };
}
