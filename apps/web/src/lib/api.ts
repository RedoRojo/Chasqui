import type {
  Article,
  DashboardOverview,
  ScrapeRun,
  Source,
  StoryEvent,
  StoryThread,
  StoryThreadDetail,
} from "./types";

export const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function fetchOverview(): Promise<DashboardOverview> {
  const res = await fetch(`${API_BASE}/api/overview`, { cache: "no-store" });
  if (!res.ok) throw new Error("No se pudo cargar el resumen de Chasqui");
  return res.json();
}

export async function fetchThreads(params?: {
  department?: string;
  category?: string;
  blindspot_only?: boolean;
  q?: string;
}): Promise<StoryThread[]> {
  const sp = new URLSearchParams();
  if (params?.department && params.department !== "Todos") {
    sp.set("department", params.department);
  }
  if (params?.category && params.category !== "Todas") {
    sp.set("category", params.category);
  }
  if (params?.blindspot_only) {
    sp.set("blindspot_only", "true");
  }
  if (params?.q) {
    sp.set("q", params.q);
  }
  const qs = sp.toString();
  const res = await fetch(`${API_BASE}/api/threads${qs ? `?${qs}` : ""}`, {
    cache: "no-store",
  });
  if (!res.ok) throw new Error("No se pudieron cargar los hilos");
  return res.json();
}

export async function fetchThreadBySlug(
  slug: string
): Promise<StoryThreadDetail> {
  const res = await fetch(`${API_BASE}/api/threads/${encodeURIComponent(slug)}`, {
    cache: "no-store",
  });
  if (!res.ok) throw new Error("Hilo no encontrado");
  return res.json();
}

export async function fetchEvents(params?: {
  department?: string;
  category?: string;
  blindspot_only?: boolean;
  limit?: number;
}): Promise<StoryEvent[]> {
  const sp = new URLSearchParams();
  if (params?.department && params.department !== "Todos") {
    sp.set("department", params.department);
  }
  if (params?.category && params.category !== "Todas") {
    sp.set("category", params.category);
  }
  if (params?.blindspot_only) {
    sp.set("blindspot_only", "true");
  }
  if (params?.limit) {
    sp.set("limit", String(params.limit));
  }
  const qs = sp.toString();
  const res = await fetch(`${API_BASE}/api/events${qs ? `?${qs}` : ""}`, {
    cache: "no-store",
  });
  if (!res.ok) throw new Error("No se pudieron cargar los eventos");
  return res.json();
}

export async function fetchArticles(params?: {
  q?: string;
  department?: string;
  category?: string;
  tier?: string;
  source_slug?: string;
  from_date?: string;
  to_date?: string;
}): Promise<Article[]> {
  const sp = new URLSearchParams();
  if (params?.q) sp.set("q", params.q);
  if (params?.department && params.department !== "Todos") {
    sp.set("department", params.department);
  }
  if (params?.category && params.category !== "Todas") {
    sp.set("category", params.category);
  }
  if (params?.tier && params.tier !== "all") {
    sp.set("tier", params.tier);
  }
  if (params?.source_slug) sp.set("source_slug", params.source_slug);
  if (params?.from_date) sp.set("from_date", params.from_date);
  if (params?.to_date) sp.set("to_date", params.to_date);
  const qs = sp.toString();
  const res = await fetch(`${API_BASE}/api/articles${qs ? `?${qs}` : ""}`, {
    cache: "no-store",
  });
  if (!res.ok) throw new Error("No se pudo buscar en el archivo histórico");
  return res.json();
}

export async function fetchSources(tier?: string): Promise<Source[]> {
  const qs = tier && tier !== "all" ? `?tier=${encodeURIComponent(tier)}` : "";
  const res = await fetch(`${API_BASE}/api/sources${qs}`, { cache: "no-store" });
  if (!res.ok) throw new Error("No se pudieron cargar las fuentes");
  return res.json();
}

export async function triggerDailyScrape(
  liveNetwork = false
): Promise<ScrapeRun> {
  const res = await fetch(
    `${API_BASE}/api/scrape/run?live_network=${liveNetwork ? "true" : "false"}`,
    { method: "POST" }
  );
  if (!res.ok) throw new Error("Error al ejecutar el escaneo diario");
  return res.json();
}

export function formatShortDate(iso: string): string {
  try {
    return new Intl.DateTimeFormat("es-BO", {
      day: "2-digit",
      month: "short",
      year: "numeric",
    }).format(new Date(iso));
  } catch {
    return iso;
  }
}

export function formatRelativeDays(iso: string): string {
  try {
    const diffMs = Date.now() - new Date(iso).getTime();
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    if (diffHours < 1) return "Hace minutos";
    if (diffHours < 24) return `Hace ${diffHours} h`;
    const diffDays = Math.floor(diffHours / 24);
    if (diffDays === 1) return "Ayer";
    if (diffDays < 30) return `Hace ${diffDays} días`;
    return formatShortDate(iso);
  } catch {
    return iso;
  }
}
