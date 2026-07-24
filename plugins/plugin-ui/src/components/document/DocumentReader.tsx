import type { ReactNode } from "react";

import { printScopedWindow } from "../../export/pdf/printOnce";

export type DocumentReaderProps = {
  children: ReactNode;
  toolbar?: ReactNode;
  className?: string;
  ariaLabel?: string;
};

export type DocumentPageProps = {
  children: ReactNode;
  header?: ReactNode;
  watermark?: ReactNode;
  footer?: ReactNode;
  className?: string;
};

export type DocumentHeaderProps = {
  title: ReactNode;
  subtitle?: ReactNode;
  logo?: ReactNode;
  className?: string;
};

export type DocumentFooterProps = {
  left?: ReactNode;
  center?: ReactNode;
  right?: ReactNode;
  className?: string;
};

export type DocumentSignatureBlockProps = {
  name: ReactNode;
  role?: ReactNode;
  image?: ReactNode;
  status?: ReactNode;
  className?: string;
};

/** Superfície de leitura/print de documentos formais; o conteúdo continua no domínio consumidor. */
export function DocumentReader({
  children,
  toolbar,
  className,
  ariaLabel = "Leitura do documento",
}: DocumentReaderProps) {
  return (
    <section
      className={["delpi-ui-document-reader", className].filter(Boolean).join(" ")}
      aria-label={ariaLabel}
    >
      {toolbar ? <div className="delpi-ui-document-reader__toolbar">{toolbar}</div> : null}
      <div className="delpi-ui-document-reader__viewport">{children}</div>
    </section>
  );
}

/** Papel A4 responsivo, com slots para cabeçalho, marca d'água e rodapé. */
export function DocumentPage({
  children,
  header,
  watermark,
  footer,
  className,
}: DocumentPageProps) {
  return (
    <article className={["delpi-ui-document-page", className].filter(Boolean).join(" ")}>
      {watermark ? (
        <div className="delpi-ui-document-page__watermark" aria-hidden="true">
          {watermark}
        </div>
      ) : null}
      {header ? <div className="delpi-ui-document-page__header">{header}</div> : null}
      <div className="delpi-ui-document-page__body">{children}</div>
      {footer ? <div className="delpi-ui-document-page__footer">{footer}</div> : null}
    </article>
  );
}

export function DocumentHeader({
  title,
  subtitle,
  logo,
  className,
}: DocumentHeaderProps) {
  return (
    <header className={["delpi-ui-document-header", className].filter(Boolean).join(" ")}>
      {logo ? <div className="delpi-ui-document-header__logo">{logo}</div> : null}
      <div className="delpi-ui-document-header__copy">
        <div className="delpi-ui-document-header__title">{title}</div>
        {subtitle ? (
          <div className="delpi-ui-document-header__subtitle">{subtitle}</div>
        ) : null}
      </div>
    </header>
  );
}

export function DocumentFooter({
  left,
  center,
  right,
  className,
}: DocumentFooterProps) {
  return (
    <footer className={["delpi-ui-document-footer", className].filter(Boolean).join(" ")}>
      <span>{left}</span>
      <span>{center}</span>
      <span>{right}</span>
    </footer>
  );
}

export function DocumentSignatureBlock({
  name,
  role,
  image,
  status,
  className,
}: DocumentSignatureBlockProps) {
  return (
    <div
      className={["delpi-ui-document-signature", className].filter(Boolean).join(" ")}
    >
      <div className="delpi-ui-document-signature__image">{image}</div>
      <div className="delpi-ui-document-signature__line" aria-hidden="true" />
      <div className="delpi-ui-document-signature__name">{name}</div>
      {role ? <div className="delpi-ui-document-signature__role">{role}</div> : null}
      {status ? <div className="delpi-ui-document-signature__status">{status}</div> : null}
    </div>
  );
}

/**
 * Imprime somente o DocumentReader ativo sem exigir CSS específico do MFE.
 * Usa o helper canônico (um `print()` por sessão — sem reabrir ao cancelar/duplo clique).
 */
export function printDocumentReader(): boolean {
  return printScopedWindow({
    bodyClassName: "delpi-ui-document-printing",
    deferFrames: false,
  });
}
