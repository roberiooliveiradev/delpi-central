import "@google/model-viewer";

type Props = {
  src: string;
  alt: string;
  className?: string;
};

export function ProductModelViewer({ src, alt, className }: Props) {
  return (
    <div className={className ?? "pcp-pub-model"}>
      <model-viewer
        src={src}
        alt={alt}
        camera-controls
        touch-action="pan-y"
        shadow-intensity="0.6"
        exposure="1"
        environment-image="neutral"
      />
    </div>
  );
}
