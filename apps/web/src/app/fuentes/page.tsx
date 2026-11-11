"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  CheckCircle2,
  ExternalLink,
  Globe,
  PlusCircle,
  Send,
} from "lucide-react";
import type { Source, SourceTier } from "@/lib/types";
import { BOLIVIA_DEPARTMENTS, TIER_LABELS } from "@/lib/types";
import { API_BASE, fetchSources } from "@/lib/api";

export default function SourcesAndIngestPage() {
  const [sources, setSources] = useState<Source[]>([]);
  const [tierFilter, setTierFilter] = useState<string>("all");
  const [loading, setLoading] = useState<boolean>(true);

  // Estado para probar la ingesta de una noticia y ver cómo se agrupa automáticamente en un Hilo
  const [sourceSlug, setSourceSlug] = useState<string>("erbol");
  const [title, setTitle] = useState<string>("");
  const [url, setUrl] = useState<string>("");
  const [content, setContent] = useState<string>("");
  const [ingestResult, setIngestResult] = useState<{
    event_title: string;
    thread_slug: string;
    thread_title: string;
    created_new_event: boolean;
  } | null>(null);
  const [submitting, setSubmitting] = useState<boolean>(false);

  // Estado para agregar una nueva fuente al catálogo
  const [newSourceName, setNewSourceName] = useState<string>("");
  const [newSourceUrl, setNewSourceUrl] = useState<string>("");
  const [newSourceRss, setNewSourceRss] = useState<string>("");
  const [newSourceTier, setNewSourceTier] = useState<SourceTier>("alternative");
  const [newSourceDept, setNewSourceDept] = useState<string>("Nacional");
  const [newSourceDesc, setNewSourceDesc] = useState<string>("");
  const [sourceAddedMsg, setSourceAddedMsg] = useState<string | null>(null);

  async function loadSources(selectedTier: string) {
    setLoading(true);
    try {
      const data = await fetchSources(selectedTier);
      setSources(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadSources(tierFilter);
  }, [tierFilter]);

  async function handleIngestArticle(e: React.FormEvent) {
    e.preventDefault();
    if (!title.trim() || !content.trim()) return;
    setSubmitting(true);
    setIngestResult(null);
    try {
      const finalUrl =
        url.trim() ||
        `https://chasqui.bo/despacho/${Date.now()}-${encodeURIComponent(
          title.slice(0, 24).toLowerCase().replace(/\s+/g, "-")
        )}`;
      const res = await fetch(`${API_BASE}/api/articles/ingest`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          source_slug: sourceSlug,
          title,
          url: finalUrl,
          content,
        }),
      });
      if (!res.ok) throw new Error("No se pudo procesar la noticia");
      const data = await res.json();
      setIngestResult(data);
      setTitle("");
      setUrl("");
      setContent("");
      loadSources(tierFilter);
    } catch (err) {
      console.error(err);
    } finally {
      setSubmitting(false);
    }
  }

  async function handleCreateSource(e: React.FormEvent) {
    e.preventDefault();
    if (!newSourceName.trim() || !newSourceUrl.trim()) return;
    setSourceAddedMsg(null);
    try {
      const res = await fetch(`${API_BASE}/api/sources`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: newSourceName,
          url: newSourceUrl,
          rss_url: newSourceRss || null,
          tier: newSourceTier,
          department: newSourceDept,
          scrape_strategy: newSourceRss ? "rss" : "html",
          description: newSourceDesc,
        }),
      });
      if (!res.ok) throw new Error("Error al registrar fuente");
      setSourceAddedMsg(
        `Fuente "${newSourceName}" incorporada al catálogo de escaneo diario.`
      );
      setNewSourceName("");
      setNewSourceUrl("");
      setNewSourceRss("");
      setNewSourceDesc("");
      loadSources(tierFilter);
    } catch (err) {
      console.error(err);
    }
  }

  return (
    <div className="space-y-10">
      {/* Formularios de Ingesta Inteligente y Alta de Fuentes */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Ingestar noticia / reporte ciudadano o alternativo */}
        <section className="rounded-2xl border border-stone-200 bg-white p-6 shadow-xs">
          <div className="flex items-center gap-2 text-xs font-bold text-amber-900 uppercase">
            <Send className="h-4 w-4" aria-hidden="true" />
            <span>Motor de Vinculación Longitudinal en Vivo</span>
          </div>
          <h1 className="mt-1 text-xl font-extrabold text-stone-900">
            Ingresar Nueva Noticia o Reporte Regional
          </h1>
          <p className="mt-1 text-xs leading-relaxed text-stone-600">
            Ingresa una nota de cualquier fuente boliviana: el motor extraerá el departamento, actores y embeddings para{" "}
            <strong>
              vincularla automáticamente a un Hilo / Problemática existente
            </strong>{" "}
            o iniciar uno nuevo.
          </p>

          <form onSubmit={handleIngestArticle} className="mt-4 space-y-3.5">
            <div>
              <label
                htmlFor="ingest-source"
                className="mb-1 block text-xs font-semibold text-stone-800"
              >
                Fuente que publica la noticia
              </label>
              <select
                id="ingest-source"
                name="source_slug"
                value={sourceSlug}
                onChange={(e) => setSourceSlug(e.target.value)}
                className="w-full rounded-xl border border-stone-300 bg-stone-50 px-3 py-2 text-sm text-stone-900"
              >
                {sources.map((s) => (
                  <option key={s.slug} value={s.slug}>
                    {s.name} ({TIER_LABELS[s.tier]})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label
                htmlFor="ingest-title"
                className="mb-1 block text-xs font-semibold text-stone-800"
              >
                Titular de la noticia *
              </label>
              <input
                id="ingest-title"
                name="title"
                type="text"
                required
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Ej. Comunidades del río Beni denuncian nuevas dragas auríferas cerca de Rurrenabaque"
                className="w-full rounded-xl border border-stone-300 bg-stone-50 px-3 py-2 text-sm text-stone-900"
              />
            </div>

            <div>
              <label
                htmlFor="ingest-content"
                className="mb-1 block text-xs font-semibold text-stone-800"
              >
                Desarrollo / Cuerpo de la nota *
              </label>
              <textarea
                id="ingest-content"
                name="content"
                rows={3}
                required
                value={content}
                onChange={(e) => setContent(e.target.value)}
                placeholder="Resumen o texto de la noticia reportada..."
                className="w-full rounded-xl border border-stone-300 bg-stone-50 px-3 py-2 text-sm text-stone-900"
              />
            </div>

            <div>
              <label
                htmlFor="ingest-url"
                className="mb-1 block text-xs font-semibold text-stone-800"
              >
                Enlace original (opcional)
              </label>
              <input
                id="ingest-url"
                name="url"
                type="url"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="https://..."
                autoCorrect="off"
                autoCapitalize="none"
                spellCheck={false}
                className="w-full rounded-xl border border-stone-300 bg-stone-50 px-3 py-2 text-sm text-stone-900"
              />
            </div>

            <button
              type="submit"
              disabled={submitting}
              className="inline-flex items-center gap-2 rounded-xl bg-amber-800 px-4 py-2.5 text-xs font-bold text-white transition hover:bg-amber-900 disabled:opacity-60 cursor-pointer"
            >
              <Send className="h-3.5 w-3.5" aria-hidden="true" />
              <span>
                {submitting
                  ? "Analizando y agrupando en hilo..."
                  : "Procesar y Vincular a Línea de Tiempo"}
              </span>
            </button>
          </form>

          {ingestResult ? (
            <div
              role="status"
              aria-live="polite"
              className="mt-4 rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-xs text-emerald-950"
            >
              <div className="flex items-center gap-1.5 font-bold">
                <CheckCircle2 className="h-4 w-4 text-emerald-700" aria-hidden="true" />
                <span>Noticia clasificada y vinculada con éxito</span>
              </div>
              <p className="mt-1">
                Hito asignado: <strong>{ingestResult.event_title}</strong>
              </p>
              <p className="mt-1">
                Hilo longitudinal:{" "}
                <Link
                  href={`/hilos/${ingestResult.thread_slug}`}
                  className="font-bold underline"
                >
                  {ingestResult.thread_title}
                </Link>
              </p>
            </div>
          ) : null}
        </section>

        {/* Registrar una nueva fuente en el catálogo */}
        <section className="rounded-2xl border border-stone-200 bg-white p-6 shadow-xs">
          <div className="flex items-center gap-2 text-xs font-bold text-stone-700 uppercase">
            <PlusCircle className="h-4 w-4 text-amber-800" aria-hidden="true" />
            <span>Ampliar Cobertura</span>
          </div>
          <h2 className="mt-1 text-xl font-extrabold text-stone-900">
            Agregar Nueva Fuente al Escaneo Diario
          </h2>
          <p className="mt-1 text-xs leading-relaxed text-stone-600">
            Añade un portal digital, radio comunitaria, medio alternativo o periódico regional para incluirlo en el barrido automático de cada mañana.
          </p>

          <form onSubmit={handleCreateSource} className="mt-4 space-y-3.5">
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <div>
                <label
                  htmlFor="src-name"
                  className="mb-1 block text-xs font-semibold text-stone-800"
                >
                  Nombre del medio *
                </label>
                <input
                  id="src-name"
                  name="name"
                  type="text"
                  required
                  value={newSourceName}
                  onChange={(e) => setNewSourceName(e.target.value)}
                  placeholder="Ej. Radio Yungas / Chaski Digital"
                  className="w-full rounded-xl border border-stone-300 bg-stone-50 px-3 py-2 text-sm text-stone-900"
                />
              </div>

              <div>
                <label
                  htmlFor="src-tier"
                  className="mb-1 block text-xs font-semibold text-stone-800"
                >
                  Categoría del medio
                </label>
                <select
                  id="src-tier"
                  name="tier"
                  value={newSourceTier}
                  onChange={(e) =>
                    setNewSourceTier(e.target.value as SourceTier)
                  }
                  className="w-full rounded-xl border border-stone-300 bg-stone-50 px-3 py-2 text-sm text-stone-900"
                >
                  <option value="alternative">
                    Alternativo / Investigación
                  </option>
                  <option value="community">
                    Radio Comunitaria / Agencia
                  </option>
                  <option value="regional">Regional / Departamental</option>
                  <option value="mainstream">Tradicional / Masivo</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <div>
                <label
                  htmlFor="src-url"
                  className="mb-1 block text-xs font-semibold text-stone-800"
                >
                  Sitio web principal *
                </label>
                <input
                  id="src-url"
                  name="url"
                  type="url"
                  required
                  value={newSourceUrl}
                  onChange={(e) => setNewSourceUrl(e.target.value)}
                  placeholder="https://..."
                  autoCorrect="off"
                  autoCapitalize="none"
                  spellCheck={false}
                  className="w-full rounded-xl border border-stone-300 bg-stone-50 px-3 py-2 text-sm text-stone-900"
                />
              </div>

              <div>
                <label
                  htmlFor="src-dept"
                  className="mb-1 block text-xs font-semibold text-stone-800"
                >
                  Departamento principal
                </label>
                <select
                  id="src-dept"
                  name="department"
                  value={newSourceDept}
                  onChange={(e) => setNewSourceDept(e.target.value)}
                  className="w-full rounded-xl border border-stone-300 bg-stone-50 px-3 py-2 text-sm text-stone-900"
                >
                  {BOLIVIA_DEPARTMENTS.filter((d) => d !== "Todos").map((d) => (
                    <option key={d} value={d}>
                      {d}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div>
              <label
                htmlFor="src-rss"
                className="mb-1 block text-xs font-semibold text-stone-800"
              >
                URL de Feed RSS / XML (opcional)
              </label>
              <input
                id="src-rss"
                name="rss_url"
                type="url"
                value={newSourceRss}
                onChange={(e) => setNewSourceRss(e.target.value)}
                placeholder="https://.../feed/"
                autoCorrect="off"
                autoCapitalize="none"
                spellCheck={false}
                className="w-full rounded-xl border border-stone-300 bg-stone-50 px-3 py-2 text-sm text-stone-900"
              />
            </div>

            <div>
              <label
                htmlFor="src-desc"
                className="mb-1 block text-xs font-semibold text-stone-800"
              >
                Descripción del enfoque informativo
              </label>
              <input
                id="src-desc"
                name="description"
                type="text"
                value={newSourceDesc}
                onChange={(e) => setNewSourceDesc(e.target.value)}
                placeholder="Cobertura provincial, comunidades indígenas, medio ambiente..."
                className="w-full rounded-xl border border-stone-300 bg-stone-50 px-3 py-2 text-sm text-stone-900"
              />
            </div>

            <button
              type="submit"
              className="inline-flex items-center gap-2 rounded-xl bg-stone-900 px-4 py-2.5 text-xs font-bold text-white transition hover:bg-stone-800 cursor-pointer"
            >
              <PlusCircle className="h-3.5 w-3.5" aria-hidden="true" />
              <span>Guardar Fuente en Catálogo</span>
            </button>
          </form>

          {sourceAddedMsg ? (
            <div
              role="status"
              aria-live="polite"
              className="mt-4 rounded-xl border border-emerald-200 bg-emerald-50 p-3 text-xs font-semibold text-emerald-950"
            >
              {sourceAddedMsg}
            </div>
          ) : null}
        </section>
      </div>

      {/* Catálogo de Fuentes Monitoreadas */}
      <section aria-label="Catálogo de fuentes monitoreadas en Bolivia">
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-stone-200 pb-4">
          <div>
            <h2 className="text-xl font-bold text-stone-900">
              Catálogo de Fuentes Monitoreadas ({sources.length})
            </h2>
            <p className="text-xs text-stone-600">
              Fuentes que alimentan el radar diario y las líneas de tiempo históricas.
            </p>
          </div>

          <div className="flex flex-wrap gap-1.5">
            {[
              { id: "all", label: "Todas" },
              { id: "alternative", label: "Alternativos / Investigación" },
              { id: "community", label: "Radios Comunitarias" },
              { id: "regional", label: "Regionales" },
              { id: "mainstream", label: "Tradicionales" },
            ].map((tab) => (
              <button
                key={tab.id}
                type="button"
                onClick={() => setTierFilter(tab.id)}
                aria-pressed={tierFilter === tab.id}
                className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition cursor-pointer ${
                  tierFilter === tab.id
                    ? "bg-stone-900 text-white"
                    : "bg-stone-200/70 text-stone-800 hover:bg-stone-200"
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {loading ? (
          <div className="mt-4 rounded-2xl border border-stone-200 bg-white p-10 text-center text-sm text-stone-600">
            Cargando catálogo de fuentes...
          </div>
        ) : (
          <div className="mt-5 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {sources.map((src, idx) => (
              <article
                key={src.id}
                className={`flex flex-col justify-between rounded-xl border border-stone-200 bg-white p-5 shadow-2xs ${
                  idx >= 6 ? "deferred-card" : ""
                }`}
              >
                <div>
                  <div className="flex items-center justify-between gap-2">
                    <span className="rounded-md bg-amber-100/90 px-2.5 py-0.5 text-[11px] font-bold text-amber-950">
                      {TIER_LABELS[src.tier]}
                    </span>
                    <span className="rounded bg-stone-100 px-2 py-0.5 text-[11px] font-semibold text-stone-700">
                      {src.department}
                    </span>
                  </div>

                  <h3 className="mt-3 text-base font-bold text-stone-900">
                    {src.name}
                  </h3>
                  <p className="mt-1.5 text-xs leading-relaxed text-stone-600">
                    {src.description}
                  </p>
                </div>

                <div className="mt-4 flex items-center justify-between border-t border-stone-100 pt-3 text-xs">
                  <span className="font-semibold text-stone-700">
                    {src.total_articles_collected} notas archivadas
                  </span>
                  <a
                    href={src.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 font-semibold text-amber-900 hover:underline"
                  >
                    <Globe className="h-3.5 w-3.5" aria-hidden="true" />
                    <span>Portal</span>
                    <ExternalLink className="h-3 w-3" aria-hidden="true" />
                  </a>
                </div>
              </article>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
