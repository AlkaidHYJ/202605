---
name: Nexus Operations
colors:
  surface: '#f9f9ff'
  surface-dim: '#cadaff'
  surface-bright: '#f9f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f1f3ff'
  surface-container: '#e8edff'
  surface-container-high: '#e0e8ff'
  surface-container-highest: '#d7e2ff'
  on-surface: '#041b3c'
  on-surface-variant: '#434654'
  inverse-surface: '#1d3052'
  inverse-on-surface: '#edf0ff'
  outline: '#737685'
  outline-variant: '#c3c6d6'
  surface-tint: '#0c56d0'
  primary: '#003d9b'
  on-primary: '#ffffff'
  primary-container: '#0052cc'
  on-primary-container: '#c4d2ff'
  inverse-primary: '#b2c5ff'
  secondary: '#5e4db9'
  on-secondary: '#ffffff'
  secondary-container: '#9f8eff'
  on-secondary-container: '#341d8d'
  tertiary: '#004b59'
  on-tertiary: '#ffffff'
  tertiary-container: '#006477'
  on-tertiary-container: '#76e2ff'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#dae2ff'
  primary-fixed-dim: '#b2c5ff'
  on-primary-fixed: '#001848'
  on-primary-fixed-variant: '#0040a2'
  secondary-fixed: '#e5deff'
  secondary-fixed-dim: '#c9bfff'
  on-secondary-fixed: '#1a0063'
  on-secondary-fixed-variant: '#4633a0'
  tertiary-fixed: '#afecff'
  tertiary-fixed-dim: '#48d7f9'
  on-tertiary-fixed: '#001f27'
  on-tertiary-fixed-variant: '#004e5d'
  background: '#f9f9ff'
  on-background: '#041b3c'
  surface-variant: '#d7e2ff'
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.01em
  headline-sm:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  body-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
  label-md:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.05em
  code-sm:
    fontFamily: jetbrainsMono
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  base: 8px
  xs: 4px
  sm: 12px
  md: 16px
  lg: 24px
  xl: 32px
  sidebar-width: 260px
  container-max: 1440px
---

## Brand & Style
The brand personality is authoritative yet innovative, designed to provide high-level clarity within complex AI operations. It targets enterprise decision-makers and technical operators who require reliability and precision.

The design style follows a **Corporate / Modern** aesthetic with a specific focus on **Systematic Information Density**. The interface uses a hybrid theme: a high-contrast dark sidebar for navigational focus and a clean, light-mode content area for maximum legibility of data-heavy views. This contrast reinforces a "Command and Control" mental model, where the dark persistent navigation acts as the anchor for the dynamic, bright workspace.

## Colors
The palette is rooted in professional "Tech Blue" to establish trust, while "Intelligence Purple" is used sparingly for AI-enhanced features or high-level insights.

- **Primary & Secondary**: Used for actionable elements and brand-critical touchpoints.
- **Surface Strategy**: The workspace utilizes `#F4F5F7` as a foundational background to reduce eye strain, while active cards and containers use pure `#FFFFFF` to "pop" via elevation.
- **Dark Sidebar**: The `#172B4D` slate color provides a sophisticated frame that houses the primary navigation, using high-contrast white or light-blue icons.
- **Semantic Logic**: Status indicators use highly saturated tones to ensure immediate recognition in dense data tables.

## Typography
The system utilizes **Inter** for its exceptional legibility in UI contexts, particularly within data grids and dashboards.

- **Hierarchy**: Headlines use tighter letter spacing and heavier weights to stand out against functional content. 
- **Body Text**: `body-md` (14px) is the primary size for all interface labels and input text to maximize information density without sacrificing accessibility.
- **Labels**: Small, uppercase labels with increased letter spacing are used for table headers and section overviews to differentiate metadata from primary data.
- **Technical Content**: **JetBrains Mono** is utilized for AI-generated logs, IDs, or technical parameters to provide a distinct visual cue for machine-readable data.

## Layout & Spacing
This design system employs an **8px linear scale** for all spacing and layout decisions, ensuring a consistent rhythm across complex views.

- **Grid Model**: A 12-column fluid grid is used for the main content area, with 24px gutters.
- **Sidebar**: A fixed 260px dark sidebar persists on the left for desktop, collapsing to a 64px icon-only rail for tablet views.
- **Margins**: Main page containers use 32px margins on desktop to provide breathing room around dense data tables, scaling down to 16px on mobile.
- **Density**: Use `sm` (12px) padding for table cells and `md` (16px) for standard card padding.

## Elevation & Depth
Depth is created through **Tonal Layering** supplemented by **Soft Ambient Shadows**. This approach ensures that the UI remains clean and "flat" in spirit while providing necessary cues for interactivity.

- **Level 0 (Base)**: `#F4F5F7` background. No shadow.
- **Level 1 (Cards)**: Pure white surface with a subtle 1px border (`#DFE1E6`) and a soft shadow: `0 1px 3px rgba(0,0,0,0.1)`.
- **Level 2 (Dropdowns/Modals)**: Pure white surface with a more pronounced shadow: `0 8px 16px rgba(17, 31, 54, 0.15)`.
- **Interactions**: On hover, cards should slightly lift by increasing shadow spread and shifting the border color to the primary brand color.

## Shapes
A consistent 8px (`0.5rem`) radius is applied to all primary containers, buttons, and input fields. This "Rounded" setting balances the professional nature of the enterprise tool with a modern, approachable feel.

- **Buttons & Inputs**: 8px corner radius.
- **Tags & Badges**: Fully rounded (pill-shaped) to distinguish them from interactive buttons.
- **Selection States**: High-contrast, 2px stroke indicators for focused states, utilizing the primary blue color.

## Components
- **Buttons**: Primary buttons use Deep Tech Blue with white text. Ghost buttons use a subtle gray outline for secondary actions.
- **Data Tables**: Use a white background with a sticky header. Rows should have a subtle hover state (`#F4F5F7`). Cell text uses `body-md`.
- **Status Indicators**: Represented as a combination of a colored dot and a text label (e.g., Green dot for "Active").
- **Inputs**: Fields must have a clear 1px border. Focus states use a 2px Primary Blue border with a soft blue outer glow.
- **AI Insights**: Components featuring AI-generated content should use a subtle "Intelligence Purple" gradient border or background tint to signify the data source.
- **Cards**: All dashboard widgets reside in white cards with an 8px radius and Level 1 elevation.