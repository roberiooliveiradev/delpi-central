import {
  useLayoutEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";

export type DocumentPageWatermarkProps = {
  children: ReactNode;
};

/**
 * Marca d'água do DocumentPage: um tile por faixa A4 (297 mm) ao longo do
 * papel contínuo na prévia. Na impressão, o HTML é extraído para a camada
 * fixa em `printDocumentReaderHtml` (todas as páginas do PDF).
 */
export function DocumentPageWatermark({ children }: DocumentPageWatermarkProps) {
  const rootRef = useRef<HTMLDivElement>(null);
  const [tileCount, setTileCount] = useState(1);

  useLayoutEffect(() => {
    const root = rootRef.current;
    const page = root?.closest(".delpi-ui-document-page");
    if (!root || !(page instanceof HTMLElement)) return;

    const measure = () => {
      const tile = root.querySelector<HTMLElement>(
        ".delpi-ui-document-page__watermark-tile",
      );
      const tileHeight = tile?.offsetHeight || 1;
      const next = Math.max(1, Math.ceil(page.offsetHeight / tileHeight));
      setTileCount((prev) => (prev === next ? prev : next));
    };

    measure();
    if (typeof ResizeObserver === "undefined") return;
    const observer = new ResizeObserver(measure);
    observer.observe(page);
    return () => observer.disconnect();
  }, [children]);

  return (
    <div
      ref={rootRef}
      className="delpi-ui-document-page__watermark"
      aria-hidden="true"
      data-delpi-document-watermark=""
    >
      {Array.from({ length: tileCount }, (_, index) => (
        <div
          key={index}
          className="delpi-ui-document-page__watermark-tile"
          data-delpi-document-watermark-tile=""
        >
          {children}
        </div>
      ))}
    </div>
  );
}
