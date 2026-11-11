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

  // State for testing live article ingestion and automatic longitudinal StoryThread linking
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

  // State for registering a new media source in the catalog
  const [newSourceName, setNewSourceName] = useState<string>("");
  const [newSourceUrl, setNewSourceUrl] = useState<string>("");
  const [newSourceRss, setNewSourceRss] = useState<string>("");
  const [newSourceTier, setNewSourceTier] = useState<SourceTier>("alternative");
  const [newSourceDept, setNewSourceDept] = useState<string>("National");
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
        `https://chasqui.bo/dispatch/${Date.now()}-${encodeURIComponent(
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
      if (!res.ok) throw new Error("Failed to ingest article");
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
      if (!res.ok) throw new Error("Failed to register source");
      setSourceAddedMsg(
        `Source "${newSourceName}" added to the automated daily scan catalog.`
      );
      setNewSourceName("");
      setNewSourceUrl("");
      setNewSourceRss("");
      setNewSourceDesc("");
      loadSources(tierFilter);
    } catch (err) {
      console.error(err);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="space-y-10">
      {/* Intelligent Ingestion & Source Registration Forms */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Ingest news article or regional dispatch */}
        <section className="rounded-2xl border border-stone-200 bg-white p-6 shadow-xs">
          <div className="flex items-center gap-2 text-xs font-bold text-amber-900 uppercase">
            <Send className="h-4 w-4" aria-hidden="true" />
            <span>Live Longitudinal Clustering Engine</span>
          </div>
          <h1 className="mt-1 text-xl font-extrabold text-stone-900">
            Ingest New Article or Regional Dispatch
          </h1>
          <p className="mt-1 text-xs leading-relaxed text-stone-600">
            Submit a report from any Bolivian outlet: the engine extracts the department, entities, and vector embeddings to{" "}
            <strong>
              automatically link it to an existing Story Thread
            </strong>{" "}
            or initialize a new longitudinal thread.
          </p>

          <form onSubmit={handleIngestArticle} className="mt-4 space-y-3.5">
            <div>
              <label
                htmlFor="ingest-source"
                className="mb-1 block text-xs font-semibold text-stone-800"
              >
                Publishing media outlet
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
                Article headline *
              </label>
              <input
                id="ingest-title"
                name="title"
                type="text"
                required
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. Comunidades del río Beni denuncian nuevas dragas auríferas cerca de Rurrenabaque"
                className="w-full rounded-xl border border-stone-300 bg-stone-50 px-3 py-2 text-sm text-stone-900"
              />
            </div>

            <div>
              <label
                htmlFor="ingest-content"
                className="mb-1 block text-xs font-semibold text-stone-800"
              >
                Article body / lead summary *
              </label>
              <textarea
                id="ingest-content"
                name="content"
                rows={3}
                required
                value={content}
                onChange={(e) => setContent(e.target.value)}
                placeholder="Paste the summary or body text of the reported news..."
                className="w-full rounded-xl border border-stone-300 bg-stone-50 px-3 py-2 text-sm text-stone-900"
              />
            </div>

            <div>
              <label
                htmlFor="ingest-url"
                className="mb-1 block text-xs font-semibold text-stone-800"
              >
                Original URL (optional)
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
                  ? "Analyzing and clustering into thread..."
                  : "Process & Link to Timeline"}
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
                <span>Article classified and linked to timeline</span>
              </div>
              <p className="mt-1">
                Assigned milestone: <strong>{ingestResult.event_title}</strong>
              </p>
              <p className="mt-1">
                Longitudinal thread:{" "}
                <Link
                  href={`/threads/${ingestResult.thread_slug}`}
                  className="font-bold underline"
                >
                  {ingestResult.thread_title}
                </Link>
              </p>
            </div>
          ) : null}
        </section>

        {/* Register a new media source in the catalog */}
        <section className="rounded-2xl border border-stone-200 bg-white p-6 shadow-xs">
          <div className="flex items-center gap-2 text-xs font-bold text-stone-700 uppercase">
            <PlusCircle className="h-4 w-4 text-amber-800" aria-hidden="true" />
            <span>Expand Coverage</span>
          </div>
          <h2 className="mt-1 text-xl font-extrabold text-stone-900">
            Add New Outlet to Daily Scan
          </h2>
          <p className="mt-1 text-xs leading-relaxed text-stone-600">
            Register a digital portal, community radio network, alternative investigative outlet, or regional newspaper to include it in the automated morning scan.
          </p>

          <form onSubmit={handleCreateSource} className="mt-4 space-y-3.5">
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <div>
                <label
                  htmlFor="src-name"
                  className="mb-1 block text-xs font-semibold text-stone-800"
                >
                  Outlet name *
                </label>
                <input
                  id="src-name"
                  name="name"
                  type="text"
                  required
                  value={newSourceName}
                  onChange={(e) => setNewSourceName(e.target.value)}
                  placeholder="e.g. Radio Yungas / Chaski Digital"
                  className="w-full rounded-xl border border-stone-300 bg-stone-50 px-3 py-2 text-sm text-stone-900"
                />
              </div>

              <div>
                <label
                  htmlFor="src-tier"
                  className="mb-1 block text-xs font-semibold text-stone-800"
                >
                  Source tier
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
                    Alternative / Investigative
                  </option>
                  <option value="community">
                    Community Radio / Agency
                  </option>
                  <option value="regional">Regional / Departmental</option>
                  <option value="mainstream">Mainstream / Mass Media</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <div>
                <label
                  htmlFor="src-url"
                  className="mb-1 block text-xs font-semibold text-stone-800"
                >
                  Primary website URL *
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
                  Primary department
                </label>
                <select
                  id="src-dept"
                  name="department"
                  value={newSourceDept}
                  onChange={(e) => setNewSourceDept(e.target.value)}
                  className="w-full rounded-xl border border-stone-300 bg-stone-50 px-3 py-2 text-sm text-stone-900"
                >
                  {BOLIVIA_DEPARTMENTS.filter((d) => d !== "All").map((d) => (
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
                RSS / XML Feed URL (optional)
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
                Editorial focus description
              </label>
              <input
                id="src-desc"
                name="description"
                type="text"
                value={newSourceDesc}
                onChange={(e) => setNewSourceDesc(e.target.value)}
                placeholder="Provincial coverage, indigenous territories, environment, municipal affairs..."
                className="w-full rounded-xl border border-stone-300 bg-stone-50 px-3 py-2 text-sm text-stone-900"
              />
            </div>

            <button
              type="submit"
              className="inline-flex items-center gap-2 rounded-xl bg-stone-900 px-4 py-2.5 text-xs font-bold text-white transition hover:bg-stone-800 cursor-pointer"
            >
              <PlusCircle className="h-3.5 w-3.5" aria-hidden="true" />
              <span>Save Source to Catalog</span>
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

      {/* Monitored Media Sources Catalog */}
      <section aria-label="Catalog of monitored Bolivian media sources">
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-stone-200 pb-4">
          <div>
            <h2 className="text-xl font-bold text-stone-900">
              Monitored Media Sources Catalog ({sources.length})
            </h2>
            <p className="text-xs text-stone-600">
              Outlets feeding the automated daily radar and longitudinal timelines across Bolivia.
            </p>
          </div>

          <div className="flex flex-wrap gap-1.5">
            {[
              { id: "all", label: "All Sources" },
              { id: "alternative", label: "Alternative / Investigative" },
              { id: "community", label: "Community Radio" },
              { id: "regional", label: "Regional Press" },
              { id: "mainstream", label: "Mainstream" },
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
            Loading monitored media catalog...
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
                    {src.total_articles_collected} archived articles
                  </span>
                  <a
                    href={src.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 font-semibold text-amber-900 hover:underline"
                  >
                    <Globe className="h-3.5 w-3.5" aria-hidden="true" />
                    <span>Website</span>
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
