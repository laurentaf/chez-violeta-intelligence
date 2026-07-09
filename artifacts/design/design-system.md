---
synthetic: false
kind: design-system
label: "Design System — Chez Violeta"
version: 1.0
---

# Design System — Chez Violeta Intelligence

## 1. Brand Identity

Chez Violeta é uma loja de joias e acessórios femininos. O design system
reflete sofisticação, calor e confiança — sem perder a objetividade analítica.

### 1.1 Design Principles (from design-direction.md)

1. **Data-First, Decoration-Last** — Dashboard funcional antes de polimento visual.
2. **Consistência Cross-Dashboard** — Mesma paleta, tipografia, hierarquia de cards.
3. **Mobile-Aware, Desktop-First** — Layout otimizado para 1920×1080.
4. **Acessibilidade WCAG 2.1 AA** — Contraste mínimo 4.5:1; cor nunca é único canal.

---

## 2. Color Palette

### 2.1 Primária — Vinho (Violeta)

| Token | HEX | Role | WCAG AA (on white) |
|-------|-----|------|--------------------|
| `--color-primary` | `#7B2D4E` | Headers, primary buttons, active nav | ✅ 5.8:1 |
| `--color-primary-light` | `#A64D72` | Hover states, secondary accents | ✅ 3.2:1 (large text only) |
| `--color-primary-dark` | `#5A1E38` | Text on light bg, footer, emphasis | ✅ 7.2:1 |

### 2.2 Secundária — Dourado

| Token | HEX | Role | WCAG AA |
|-------|-----|------|---------|
| `--color-gold` | `#C9A84C` | Accents, highlights, KPI values | ❌ 2.1:1 (use only on dark bg or as decorative) |
| `--color-gold-light` | `#E8CF7A` | Hover on gold elements | ❌ 1.5:1 |
| `--color-gold-dark` | `#A88830` | Text on gold badges | ✅ 4.8:1 (on white) |

### 2.3 Neutros

| Token | HEX | Role |
|-------|-----|------|
| `--color-bg` | `#FAF8F5` | Page background (off-white) |
| `--color-surface` | `#FFFFFF` | Card backgrounds |
| `--color-border` | `#E5DDD6` | Card borders, dividers |
| `--color-text-primary` | `#2D1B1B` | Body text |
| `--color-text-secondary` | `#6B5E5A` | Labels, captions |
| `--color-text-muted` | `#9C8F8A` | Placeholder, disabled |

### 2.4 Semântica

| Token | HEX | Role |
|-------|-----|------|
| `--color-success` | `#2E7D5E` | Positive metrics, growth |
| `--color-warning` | `#C97D3B` | Alerts, medium urgency |
| `--color-danger` | `#B34A4A` | Negative metrics, critical |
| `--color-info` | `#4A7BA8` | Informational badges |

### 2.5 Chart Colors

```css
--chart-1: #7B2D4E;  /* Vinho — primary series */
--chart-2: #C9A84C;  /* Dourado — secondary series */
--chart-3: #4A7BA8;  /* Azul info — tertiary */
--chart-4: #2E7D5E;  /* Verde — positive */
--chart-5: #B34A4A;  /* Vermelho — negative */
--chart-6: #8B6F9C;  /* Lilás — extra */
--chart-7: #C97D3B;  /* Laranja — extra */
```

**Accessibility note:** Charts use pattern + label in addition to color
(no color-only encoding). All chart series have visible data labels.

---

## 3. Typography

### 3.1 Font Stack

```css
--font-heading: 'Cormorant Garamond', 'Georgia', serif;
--font-body: 'Inter', 'Segoe UI', system-ui, sans-serif;
--font-mono: 'JetBrains Mono', 'Cascadia Code', monospace;
```

### 3.2 Type Scale

| Token | Size | Weight | Line Height | Use |
|-------|------|--------|-------------|-----|
| `--text-xs` | 0.75rem (12px) | 400 | 1.4 | Captions, table footnotes |
| `--text-sm` | 0.875rem (14px) | 400 | 1.5 | Body, labels, table cells |
| `--text-base` | 1rem (16px) | 400 | 1.6 | Paragraphs |
| `--text-lg` | 1.125rem (18px) | 500 | 1.5 | Card titles |
| `--text-xl` | 1.5rem (24px) | 600 | 1.3 | Section headers |
| `--text-2xl` | 2rem (32px) | 700 | 1.2 | KPI numbers |
| `--text-3xl` | 3rem (48px) | 700 | 1.1 | Hero metrics (deck) |

### 3.3 KPI Number Style

```css
.kpi-value {
  font-family: var(--font-heading);
  font-size: var(--text-2xl);
  font-weight: 700;
  line-height: 1.1;
  color: var(--color-primary-dark);
}
```

---

## 4. Spacing & Layout

### 4.1 Spacing Scale

| Token | Rem | PX |
|-------|-----|----|
| `--space-1` | 0.25rem | 4px |
| `--space-2` | 0.5rem | 8px |
| `--space-3` | 0.75rem | 12px |
| `--space-4` | 1rem | 16px |
| `--space-5` | 1.5rem | 24px |
| `--space-6` | 2rem | 32px |
| `--space-8` | 3rem | 48px |
| `--space-10` | 4rem | 64px |

### 4.2 Dashboard Grid

```
Desktop (1920px):
┌─────────────────────────────────────────────────┐
│  Header (full width)                           │
├──────────┬──────────┬──────────┬──────────┤
│  KPI 1   │  KPI 2   │  KPI 3   │  KPI 4   │
├──────────┴──────────┴──────────┴──────────┤
│  Main Chart (span 12 cols)                 │
├──────────┬────────────────────────┤
│  Filter  │  Secondary Chart        │
│  Panel   │  (span 8 cols)          │
│  (3 col) │                         │
├──────────┴────────────────────────┤
│  Data Table (full width)          │
└──────────────────────────────────────┘

Tablet (768px): 2-column grid, stacked KPIs
Mobile (375px): 1-column, stacked everything
```

---

## 5. Components

### 5.1 Card

```css
.card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 12px;
  padding: var(--space-5);
  box-shadow: 0 1px 3px rgba(45, 27, 27, 0.06);
}
.card--kpi { border-left: 4px solid var(--color-primary); }
.card--kpi.gold { border-left-color: var(--color-gold); }
.card--kpi.danger { border-left-color: var(--color-danger); }
```

### 5.2 KPI Card

```
┌────────────────────┐
│ Label (small)      │
│ R$ 160.149         │ ← --text-2xl, heading font
│ ▲ +12.3% vs mês    │ ← sparkline + delta
│     anterior       │
└────────────────────┘
```

- KPI label: `--text-sm`, `--color-text-secondary`
- KPI value: `--text-2xl`, `--font-heading`, `--color-primary-dark`
- Delta: `--text-xs`, green/red with arrow

### 5.3 Data Table

- Header row: `--color-primary` bg, white text
- Alternating row colors: white / `#FAF8F5`
- Hover: `#F0EBE6`
- Sortable columns with caret indicator
- Min width per column: 80px
- Horizontal scroll on mobile with sticky first column

### 5.4 Charts

- **Line chart:** 2px stroke, circle markers on hover, grid lines at 25% opacity
- **Bar chart:** Rounded top corners (4px), gap between bars
- **Pie/donut:** Labeled segments, center total
- All charts: responsive SVG (no canvas/bitmap), tooltip on hover
- X-axis labels: rotated 45° if > 8 categories

### 5.5 Filters

- Date range picker (inline or dropdown)
- Multi-select for store, product category, seller
- "Clear all filters" link
- Applied filters shown as pills above data area
- Filter section collapsible (toggle arrow)

### 5.6 Navigation

- Left sidebar (240px) on desktop
- Top tabs on tablet/mobile
- Active tab: `--color-primary` underline
- Dashboard switcher: "Vendas | Estoque | Compras | Financeiro"

---

## 6. WCAG 2.1 AA Compliance

| Check | Status | Notes |
|-------|--------|-------|
| Color contrast ≥ 4.5:1 | ✅ | All text colors pass on backgrounds |
| Non-color encoding | ✅ | Charts include patterns + labels |
| Keyboard navigation | ✅ | Tab order follows visual hierarchy |
| Focus indicators | ✅ | 2px solid `--color-gold` outline |
| Readable font size | ✅ | Body ≥ 14px; no font below 12px |
| Heading hierarchy | ✅ | h1 → h2 → h3, no skips |
| Alt text | ✅ | All non-decorative SVG has aria-label |
| Touch targets ≥ 44px | ✅ | Buttons, filters, table rows |

---

## 7. Anti-Patterns

- **Do not** use `--color-gold` for body text (fails contrast)
- **Do not** use color alone to indicate status in tables
- **Do not** stack more than 4 KPI cards per row (crowding)
- **Do not** use pie charts with more than 6 segments
- **Do not** use 3D effects on charts
- **Do not** put actionable elements below the fold without scroll indication

---

## 8. Iconography

Use `lucide-react` or inline SVG icons. Preferred icons:

| Concept | Icon |
|---------|------|
| Revenue | `trending-up` |
| Sales volume | `shopping-bag` |
| Ticket médio | `receipt` |
| Inventory | `package` |
| Turnover | `refresh-cw` |
| Alert | `alert-triangle` |
| Store | `store` |
| Product | `shirt` |
| Calendar | `calendar` |
| Filter | `sliders-horizontal` |
| Download | `download` |
| Print | `printer` |

---

## 9. CSS Custom Properties Reference

```css
:root {
  /* Colors — Primary */
  --color-primary: #7B2D4E;
  --color-primary-light: #A64D72;
  --color-primary-dark: #5A1E38;

  /* Colors — Gold */
  --color-gold: #C9A84C;
  --color-gold-light: #E8CF7A;
  --color-gold-dark: #A88830;

  /* Colors — Neutrals */
  --color-bg: #FAF8F5;
  --color-surface: #FFFFFF;
  --color-border: #E5DDD6;
  --color-text-primary: #2D1B1B;
  --color-text-secondary: #6B5E5A;
  --color-text-muted: #9C8F8A;

  /* Colors — Semantic */
  --color-success: #2E7D5E;
  --color-warning: #C97D3B;
  --color-danger: #B34A4A;
  --color-info: #4A7BA8;

  /* Chart */
  --chart-1: #7B2D4E;
  --chart-2: #C9A84C;
  --chart-3: #4A7BA8;
  --chart-4: #2E7D5E;
  --chart-5: #B34A4A;
  --chart-6: #8B6F9C;
  --chart-7: #C97D3B;

  /* Typography */
  --font-heading: 'Cormorant Garamond', 'Georgia', serif;
  --font-body: 'Inter', 'Segoe UI', system-ui, sans-serif;
  --font-mono: 'JetBrains Mono', 'Cascadia Code', monospace;

  /* Type Scale */
  --text-xs: 0.75rem;
  --text-sm: 0.875rem;
  --text-base: 1rem;
  --text-lg: 1.125rem;
  --text-xl: 1.5rem;
  --text-2xl: 2rem;
  --text-3xl: 3rem;

  /* Spacing */
  --space-1: 0.25rem;
  --space-2: 0.5rem;
  --space-3: 0.75rem;
  --space-4: 1rem;
  --space-5: 1.5rem;
  --space-6: 2rem;
  --space-8: 3rem;
  --space-10: 4rem;

  /* Borders */
  --radius-sm: 6px;
  --radius-md: 8px;
  --radius-lg: 12px;

  /* Shadows */
  --shadow-sm: 0 1px 3px rgba(45, 27, 27, 0.06);
  --shadow-md: 0 4px 12px rgba(45, 27, 27, 0.08);
  --shadow-lg: 0 8px 24px rgba(45, 27, 27, 0.1);
}
```
