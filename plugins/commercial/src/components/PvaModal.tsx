import { PvaHostModal } from "../ui/pvaKit";

type PvaModalProps = {
  open: boolean;
  title: string;
  subtitle?: string;
  onClose: () => void;
  children: React.ReactNode;
};

export function PvaModal({ open, title, subtitle, onClose, children }: PvaModalProps) {
  return (
    <PvaHostModal
      open={open}
      title={title}
      description={subtitle}
      onClose={onClose}
      closeAriaLabel="Fechar modal"
    >
      {children}
    </PvaHostModal>
  );
}
