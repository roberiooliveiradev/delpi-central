# Assets do Delpi MES

Imagens consumidas pelo MFE via `import.meta.glob` (`src/utils/assets.ts`).
Arquivos ausentes degradam para placeholders sem quebrar o build.

| Arquivo | Uso | Tamanho recomendado | Formato |
|---|---|---|---|
| `hero-factory.webp` | Banner do header | ~1600×520 px (≈3:1) | WebP (também aceita `.jpg`/`.png`) |
| `logo-delpi-white.png` / `logo-delpi.png` | Logo na sidebar escura | ~480×160 px, fundo transparente | PNG, WebP ou `.svg` (`logo-delpi-white.svg`) |
| `sidebar-icon.png` | Ilustração decorativa no rodapé da sidebar | ~600×600 px, fundo transparente | PNG, WebP ou `.svg` (`sidebar-icon.webp`/`.svg`) |
| `machines/<CT>.png` | Foto da máquina no card do CT | ~800×600 px (4:3) | WebP ou PNG/JPG |
| `machines/machine-default.webp` | Fallback quando o CT não tem foto | ~800×600 px | WebP ou PNG |

Nomenclatura das fotos de máquina: mesmo código exibido no card, em
maiúsculas e com `-` no lugar de caracteres inválidos — ex.: `CT-35.png`.
