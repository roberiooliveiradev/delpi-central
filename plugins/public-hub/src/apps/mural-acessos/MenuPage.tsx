import type { PublicMuralItem, PublicMuralMenu } from "./api";
import "./menu.css";

function initialOf(title: string): string {
  const trimmed = title.trim();
  return trimmed ? trimmed.slice(0, 1).toUpperCase() : "?";
}

function MenuTile({ item }: { item: PublicMuralItem }) {
  return (
    <a className="ma-pub-tile" href={item.url} rel="noopener noreferrer">
      <span className="ma-pub-tile__icon" aria-hidden="true">
        {item.imageUrl ? (
          <img src={item.imageUrl} alt="" />
        ) : (
          <span>{initialOf(item.title)}</span>
        )}
      </span>
      <span className="ma-pub-tile__label">{item.title}</span>
    </a>
  );
}

export function MuralAcessosMenuView({ menu }: { menu: PublicMuralMenu }) {
  return (
    <div className="ma-pub">
      <header className="ma-pub__header">
        <p className="ma-pub__eyebrow">Minha DELPI</p>
        <h1>{menu.title}</h1>
        {menu.subtitle ? <p className="ma-pub__subtitle">{menu.subtitle}</p> : null}
      </header>
      {menu.items.length === 0 ? (
        <p className="ma-pub__empty">Nenhum acesso disponível no momento.</p>
      ) : (
        <nav className="ma-pub__grid" aria-label="Acessos do mural">
          {menu.items.map((item) => (
            <MenuTile key={item.id} item={item} />
          ))}
        </nav>
      )}
    </div>
  );
}
