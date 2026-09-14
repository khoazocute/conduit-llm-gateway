// Deterministic, purely presentational per-agent accent color + initial glyph.
// Derived from real fields (id/title) — never invents backend data (no
// ratings/runs/category, none of which exist on the real Agent model).

const PALETTE = [
  "#54f0a8",
  "#7ab9ff",
  "#ffb454",
  "#ff7ac6",
  "#a78bfa",
  "#f0c454",
  "#7ad4b0",
  "#ff8a5b",
];

function hashString(input: string): number {
  let hash = 0;
  for (let i = 0; i < input.length; i++) {
    hash = (hash * 31 + input.charCodeAt(i)) | 0;
  }
  return Math.abs(hash);
}

export function agentAccentColor(id: string): string {
  return PALETTE[hashString(id) % PALETTE.length];
}

export function agentInitial(title: string): string {
  return title.trim().charAt(0).toUpperCase() || "?";
}
