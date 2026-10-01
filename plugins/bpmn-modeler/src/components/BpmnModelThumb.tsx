import { useEffect, useRef, useState } from "react";

import { Workflow } from "lucide-react";

import { getWorkingCopy } from "../data/api/bpmnModelerApi";
import {
  renderBpmnThumbnail,
  type BpmnThumbnailResult,
} from "../editor/modelThumbnail";

type GetToken = (() => string | undefined) | undefined;

const CACHE_LIMIT = 60;
const svgCache = new Map<string, Promise<BpmnThumbnailResult | null>>();

function thumbnailFor(
  modelId: string,
  version: number,
  getAccessToken: GetToken,
): Promise<BpmnThumbnailResult | null> {
  const key = `${modelId}@${version}`;
  const cached = svgCache.get(key);
  if (cached) return cached;
  const promise = (async () => {
    const { xml } = await getWorkingCopy(modelId, { getAccessToken });
    return renderBpmnThumbnail(xml);
  })().catch(() => null);
  svgCache.set(key, promise);
  if (svgCache.size > CACHE_LIMIT) {
    const oldest = svgCache.keys().next().value;
    if (oldest !== undefined) svgCache.delete(oldest);
  }
  return promise;
}

type ThumbState = "idle" | "loading" | "ready" | "empty" | "error";

type Props = {
  modelId: string;
  version: number;
  getAccessToken?: GetToken;
};

/**
 * Thumbnail derivada do BPMN XML+DI do modelo — render lazy (IntersectionObserver)
 * + cache em memória por `id@version`. Nunca bloqueia a listagem: falha vira
 * placeholder neutro.
 */
export function BpmnModelThumb({ modelId, version, getAccessToken }: Props) {
  const hostRef = useRef<HTMLSpanElement | null>(null);
  const [state, setState] = useState<ThumbState>("idle");
  const [svg, setSvg] = useState<string | null>(null);

  useEffect(() => {
    const host = hostRef.current;
    if (!host) return;
    let cancelled = false;
    const start = () => {
      setState("loading");
      void thumbnailFor(modelId, version, getAccessToken).then((result) => {
        if (cancelled) return;
        if (result?.kind === "svg") {
          setSvg(result.svg);
          setState("ready");
        } else {
          setState(result?.kind === "empty" ? "empty" : "error");
        }
      });
    };
    if (typeof IntersectionObserver === "undefined") {
      start();
      return;
    }
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries.some((entry) => entry.isIntersecting)) {
          observer.disconnect();
          start();
        }
      },
      { rootMargin: "200px" },
    );
    observer.observe(host);
    return () => {
      cancelled = true;
      observer.disconnect();
    };
  }, [modelId, version, getAccessToken]);

  if (state === "ready" && svg) {
    return (
      <span className="bpmnm-thumb">
        <img
          className="bpmnm-thumb__img"
          src={`data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`}
          alt=""
          draggable={false}
        />
      </span>
    );
  }

  const variant =
    state === "ready" ? null : state === "idle" || state === "loading" ? "loading" : state;

  return (
    <span
      ref={hostRef}
      className={`bpmnm-thumb bpmnm-thumb--${variant}`}
      aria-hidden="true"
    >
      <Workflow size={28} strokeWidth={1.6} />
      {variant === "empty" ? (
        <span className="bpmnm-thumb__hint">Diagrama sem elementos</span>
      ) : null}
      {variant === "error" ? (
        <span className="bpmnm-thumb__hint">Preview indisponível</span>
      ) : null}
    </span>
  );
}
