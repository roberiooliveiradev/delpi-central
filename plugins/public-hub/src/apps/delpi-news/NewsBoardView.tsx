import { useEffect, useMemo, useState } from "react";

import type { PublicNewsBoard, PublicNewsBoardItem } from "./types";
import "./news-board.css";

function formatPublishedAt(value: string | null): string {
  if (!value) return "Data não informada";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Data não informada";
  return new Intl.DateTimeFormat("pt-BR", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

function FeaturedBadge({ featured }: { featured: boolean }) {
  if (!featured) return null;
  return <span className="dn-pub__badge">Destaque</span>;
}

function HeroCard({ item }: { item: PublicNewsBoardItem }) {
  return (
    <article className="dn-pub__hero" aria-live="polite">
      <div className="dn-pub__hero-meta">
        {item.category_name ? <span className="dn-pub__category">{item.category_name}</span> : null}
        <FeaturedBadge featured={item.is_featured} />
      </div>
      <h2 className="dn-pub__headline">{item.title}</h2>
      {item.summary ? <p className="dn-pub__summary">{item.summary}</p> : null}
      <footer className="dn-pub__hero-foot">
        <span>{item.source_name}</span>
        <span aria-hidden="true">·</span>
        <time dateTime={item.published_at ?? undefined}>{formatPublishedAt(item.published_at)}</time>
      </footer>
    </article>
  );
}

export function NewsBoardView({ board }: { board: PublicNewsBoard }) {
  const items = board.items;
  const intervalMs = Math.max(4, board.rotation_interval_sec) * 1000;
  const [index, setIndex] = useState(0);
  const [progress, setProgress] = useState(0);

  const active = items[index] ?? null;
  const upcoming = useMemo(() => {
    if (items.length <= 1) return [];
    const rest: PublicNewsBoardItem[] = [];
    for (let offset = 1; offset < Math.min(items.length, 4); offset += 1) {
      rest.push(items[(index + offset) % items.length]!);
    }
    return rest;
  }, [items, index]);

  useEffect(() => {
    if (items.length <= 1) return;
    setProgress(0);
    const started = performance.now();
    let frame = 0;
    const tick = (now: number) => {
      const elapsed = now - started;
      setProgress(Math.min(1, elapsed / intervalMs));
      if (elapsed >= intervalMs) {
        setIndex((current) => (current + 1) % items.length);
        return;
      }
      frame = window.requestAnimationFrame(tick);
    };
    frame = window.requestAnimationFrame(tick);
    return () => window.cancelAnimationFrame(frame);
  }, [index, intervalMs, items.length]);

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (items.length <= 1) return;
      if (event.key === "ArrowRight" || event.key === "PageDown") {
        event.preventDefault();
        setIndex((current) => (current + 1) % items.length);
      }
      if (event.key === "ArrowLeft" || event.key === "PageUp") {
        event.preventDefault();
        setIndex((current) => (current - 1 + items.length) % items.length);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [items.length]);

  if (!active) {
    return (
      <div className="dn-pub dn-pub--empty">
        <p>Nenhuma notícia publicada no momento.</p>
      </div>
    );
  }

  return (
    <div className="dn-pub" data-testid="delpi-news-board">
      <header className="dn-pub__brand">
        <div>
          <p className="dn-pub__eyebrow">Minha DELPI · TVs corporativas</p>
          <h1>{board.title}</h1>
          {board.subtitle ? <p className="dn-pub__subtitle">{board.subtitle}</p> : null}
        </div>
        <div className="dn-pub__clock" aria-hidden="true">
          <span>
            {index + 1}/{items.length}
          </span>
        </div>
      </header>

      <div className="dn-pub__stage">
        <HeroCard item={active} />
        <aside className="dn-pub__rail" aria-label="Próximas notícias">
          <p className="dn-pub__rail-title">A seguir</p>
          <ul className="dn-pub__rail-list">
            {upcoming.map((item, railIndex) => (
              <li key={item.id}>
                <button
                  type="button"
                  className="dn-pub__rail-item"
                  onClick={() => setIndex((index + railIndex + 1) % items.length)}
                >
                  <span className="dn-pub__rail-cat">{item.category_name ?? item.source_name}</span>
                  <span className="dn-pub__rail-title-text">{item.title}</span>
                </button>
              </li>
            ))}
          </ul>
        </aside>
      </div>

      <div className="dn-pub__progress" aria-hidden="true">
        <div className="dn-pub__progress-bar" style={{ transform: `scaleX(${progress})` }} />
      </div>

      <nav className="dn-pub__controls" aria-label="Navegação do board">
        <button
          type="button"
          className="dn-pub__nav-btn"
          onClick={() => setIndex((current) => (current - 1 + items.length) % items.length)}
          disabled={items.length <= 1}
        >
          Anterior
        </button>
        <button
          type="button"
          className="dn-pub__nav-btn"
          onClick={() => setIndex((current) => (current + 1) % items.length)}
          disabled={items.length <= 1}
        >
          Próxima
        </button>
      </nav>
    </div>
  );
}
