"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  CheckCircle2,
  ExternalLink,
  Globe,
  Link2,
  PlusCircle,
  Radio,
  Send,
  Sparkles,
  Video,
} from "lucide-react";
import type { Source, SourceTier } from "@/lib/types";
import {
  BOLIVIA_DEPARTMENTS,
  SCRAPE_STRATEGY_LABELS,
  TIER_LABELS,
} from "@/lib/types";
import { API_BASE, fetchSources } from "@/lib/api";

export default function SourcesAndIngestPage() {
  const [sources, setSources] = useState<Source[]>([]);
  const [tierFilter, setTierFilter] = useState<string>("all");
  const [strategyFilter, setStrategyFilter] = useState<string>("all");
  const [loading, setLoading] = useState<boolean>(true);

  // Social Media / Web URL Quick Extractor & One-Click Ingest state
  const [socialUrl, setSocialUrl] = useState<string>("");
  const [extractingUrl, setExtractingUrl] = useState<boolean>(false);
  const [extractedMeta, setExtractedMeta] = useState<{
    platform: string;
    author_or_outlet: string;
  } | null>(null);
  const [extractError, setExtractError] = useState<string | null>(null);

  // State for testing live article ingestion and automatic longitudinal StoryThread linking
  const [sourceSlug, setSourceSlug] = useState<string>("auto");
  const [title, setTitle] = useState<string>("");
  const [url, setUrl] = useState<string>("");
  const [content, setContent] = useState<string>("");
  const [ingestResult, setIngestResult] = useState<{
    platform?: string;
    author_or_outlet?: string;
    event_title: string;
    thread_slug: string;
    thread_title: string;
    created_new_event: boolean;
  } | null>(null);
  const [submitting, setSubmitting] = useState<boolean>(false);

  // State for registering a new media or social source in the catalog
  const [newSourceName, setNewSourceName] = useState<string>("");
  const [newSourceUrl, setNewSourceUrl] = useState<string>("");
  const [newSourceRss, setNewSourceRss] = useState<string>("");
  const [newSourceTier, setNewSourceTier] = useState<SourceTier>("alternative");
  const [newSourceDept, setNewSourceDept] = useState<string>("National");
  const [newSourceStrategy, setNewSourceStrategy] = useState<string>("auto");
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

  async function handleExtractFromUrl() {
    if (!socialUrl.trim()) return;
    setExtractingUrl(true);
    setExtractError(null);
    setExtractedMeta(null);
    try {
      const res = await fetch(`${API_BASE}/api/articles/extract-url`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: socialUrl.trim() }),
      });
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || "Could not extract post metadata from URL.");
      }
      const data = await res.json();
      setTitle(data.title || "");
      setContent(data.content || "");
      setUrl(data.url || socialUrl.trim());
      setExtractedMeta({
        platform: data.platform,
        author_or_outlet: data.author_or_outlet,
      });
    } catch (err) {
      setExtractError(
        err instanceof Error ? err.message : "Could not extract URL metadata."
      );
    } finally {
      setExtractingUrl(false);
    }
  }

  async function handleOneClickSocialIngest() {
    if (!socialUrl.trim()) return;
    setExtractingUrl(true);
    setExtractError(null);
    setIngestResult(null);
    try {
      const res = await fetch(`${API_BASE}/api/articles/ingest-url`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          url: socialUrl.trim(),
          source_slug: sourceSlug !== "auto" ? sourceSlug : null,
          tier: "alternative",
        }),
      });
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || "Could not ingest social media URL.");
      }
      const data = await res.json();
      setIngestResult(data);
      setSocialUrl("");
      loadSources(tierFilter);
    } catch (err) {
      setExtractError(
        err instanceof Error ? err.message : "Could not ingest URL."
      );
    } finally {
      setExtractingUrl(false);
    }
  }

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
      const chosenSlug =
        sourceSlug === "auto"
          ? sources[0]?.slug || "erbol"
          : sourceSlug;
      const res = await fetch(`${API_BASE}/api/articles/ingest`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          source_slug: chosenSlug,
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
      setExtractedMeta(null);
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
          scrape_strategy: newSourceStrategy,
          description: newSourceDesc,
        }),
      });
      if (!res.ok) throw new Error("Failed to register source");
      const created: Source = await res.json();
      setSourceAddedMsg(
        `Source "${created.name}" (${
          SCRAPE_STRATEGY_LABELS[created.scrape_strategy] || created.scrape_strategy
        }) added to the automated daily scan catalog.`
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

  const filteredSources = sources.filter((src) => {
    if (strategyFilter === "all") return true;
    if (strategyFilter === "social") {
      return src.scrape_strategy === "youtube" || src.scrape_strategy === "telegram";
    }
    return src.scrape_strategy === strategyFilter;
  });

  return (
    <div className="space-y-10">
      {/* Intelligent Ingestion & Social / Web Source Registration Forms */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Ingest news article or social media post */}
        <section className="rounded-2xl border border-stone-200 bg-white p-6 shadow-xs">
          <div className="flex items-center gap-2 text-xs font-bold text-amber-900 uppercase">
            <Send className="h-4 w-4" aria-hidden="true" />
            <span>Social Media & Longitudinal Clustering Engine</span>
          </div>
          <h1 className="mt-1 text-xl font-extrabold text-stone-900">
            Ingest Social Media Post, Video, or Regional Dispatch
          </h1>
          <p className="mt-1 text-xs leading-relaxed text-stone-600">
            Paste a link from{" "}
            <strong>
              YouTube, TikTok, Telegram, X/Twitter, Facebook, or any regional news portal
            </strong>{" "}
            to automatically extract its headline, description, and entities, and link it to an evolving{" "}
            <strong>Story Thread</strong>.
          </p>

          {/* Quick Social URL Extractor Box */}
          <div className="mt-4 rounded-xl border border-amber-200/90 bg-amber-50/50 p-3.5">
            <label
              htmlFor="social-quick-url"
              className="mb-1.5 flex items-center gap-1.5 text-xs font-bold text-amber-950"
            >
              <Link2 className="h-3.5 w-3.5 text-amber-800" aria-hidden="true" />
              <span>Quick Extract from Social Media / Video / Web URL</span>
            </label>
            <div className="flex flex-col gap-2 sm:flex-row">
              <input
                id="social-quick-url"
                name="social_url"
                type="url"
                value={socialUrl}
                onChange={(e) => setSocialUrl(e.target.value)}
                placeholder="https://www.youtube.com/watch?v=... or https://www.tiktok.com/... or https://t.me/..."
                autoCorrect="off"
                autoCapitalize="none"
                spellCheck={false}
                className="flex-1 rounded-xl border border-stone-300 bg-white px-3 py-2 text-xs text-stone-900"
              />
              <div className="flex gap-1.5">
                <button
                  type="button"
                  onClick={handleExtractFromUrl}
                  disabled={extractingUrl || !socialUrl.trim()}
                  className="inline-flex items-center gap-1.5 rounded-xl border border-stone-300 bg-white px-3 py-2 text-xs font-bold text-stone-800 transition hover:bg-stone-100 disabled:opacity-50 cursor-pointer"
                >
                  <Sparkles className="h-3.5 w-3.5 text-amber-800" aria-hidden="true" />
                  <span>{extractingUrl ? "Extracting..." : "Auto-Fill"}</span>
                </button>
                <button
                  type="button"
                  onClick={handleOneClickSocialIngest}
                  disabled={extractingUrl || !socialUrl.trim()}
                  className="inline-flex items-center gap-1.5 rounded-xl bg-amber-800 px-3 py-2 text-xs font-bold text-white transition hover:bg-amber-900 disabled:opacity-50 cursor-pointer"
                >
                  <Send className="h-3.5 w-3.5" aria-hidden="true" />
                  <span>One-Click Link</span>
                </button>
              </div>
            </div>

            {extractedMeta ? (
              <p className="mt-2 text-[11px] font-semibold text-emerald-900">
                Detected platform:{" "}
                <span className="rounded bg-emerald-100 px-1.5 py-0.5 uppercase">
                  {extractedMeta.platform}
                </span>{" "}
                · Author / Channel: <strong>{extractedMeta.author_or_outlet}</strong>
              </p>
            ) : null}

            {extractError ? (
              <p className="mt-2 text-[11px] font-semibold text-red-700">
                {extractError}
              </p>
            ) : null}
          </div>

          <form onSubmit={handleIngestArticle} className="mt-4 space-y-3.5">
            <div>
              <label
                htmlFor="ingest-source"
                className="mb-1 block text-xs font-semibold text-stone-800"
              >
                Publishing outlet or social channel
              </label>
              <select
                id="ingest-source"
                name="source_slug"
                value={sourceSlug}
                onChange={(e) => setSourceSlug(e.target.value)}
                className="w-full rounded-xl border border-stone-300 bg-stone-50 px-3 py-2 text-sm text-stone-900"
              >
                <option value="auto">
                  Auto-detect from URL / Author (or use default outlet)
                </option>
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
                Article or social post headline *
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
                Post caption / video description / article body *
              </label>
              <textarea
                id="ingest-content"
                name="content"
                rows={3}
                required
                value={content}
                onChange={(e) => setContent(e.target.value)}
                placeholder="Paste or auto-extract the summary, caption, or transcript of the reported news..."
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
              className="inline-flex items-center gap-2 rounded-xl bg-stone-900 px-4 py-2.5 text-xs font-bold text-white transition hover:bg-stone-800 disabled:opacity-60 cursor-pointer"
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
                <span>
                  {ingestResult.platform
                    ? `${ingestResult.platform.toUpperCase()} dispatch (${ingestResult.author_or_outlet}) classified & linked`
                    : "Article classified and linked to timeline"}
                </span>
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

        {/* Register a new media or social channel source in the catalog */}
        <section className="rounded-2xl border border-stone-200 bg-white p-6 shadow-xs">
          <div className="flex items-center gap-2 text-xs font-bold text-stone-700 uppercase">
            <PlusCircle className="h-4 w-4 text-amber-800" aria-hidden="true" />
            <span>Expand Web & Social Coverage</span>
          </div>
          <h2 className="mt-1 text-xl font-extrabold text-stone-900">
            Add New Outlet or Social Channel to Daily Scan
          </h2>
          <p className="mt-1 text-xs leading-relaxed text-stone-600">
            Register a{" "}
            <strong>
              YouTube channel, Telegram public channel, community radio network, alternative investigative portal, or regional newspaper
            </strong>{" "}
            to include it in the automated morning scan.
          </p>

          <form onSubmit={handleCreateSource} className="mt-4 space-y-3.5">
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <div>
                <label
                  htmlFor="src-name"
                  className="mb-1 block text-xs font-semibold text-stone-800"
                >
                  Outlet or channel name *
                </label>
                <input
                  id="src-name"
                  name="name"
                  type="text"
                  required
                  value={newSourceName}
                  onChange={(e) => setNewSourceName(e.target.value)}
                  placeholder="e.g. RTP Bolivia (YouTube) / Radio Yungas"
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
                  Website, YouTube, or Telegram URL *
                </label>
                <input
                  id="src-url"
                  name="url"
                  type="url"
                  required
                  value={newSourceUrl}
                  onChange={(e) => setNewSourceUrl(e.target.value)}
                  placeholder="https://www.youtube.com/@... or https://t.me/..."
                  autoCorrect="off"
                  autoCapitalize="none"
                  spellCheck={false}
                  className="w-full rounded-xl border border-stone-300 bg-stone-50 px-3 py-2 text-sm text-stone-900"
                />
              </div>

              <div>
                <label
                  htmlFor="src-strategy"
                  className="mb-1 block text-xs font-semibold text-stone-800"
                >
                  Connector / Scrape strategy
                </label>
                <select
                  id="src-strategy"
                  name="scrape_strategy"
                  value={newSourceStrategy}
                  onChange={(e) => setNewSourceStrategy(e.target.value)}
                  className="w-full rounded-xl border border-stone-300 bg-stone-50 px-3 py-2 text-sm text-stone-900"
                >
                  <option value="auto">Auto-detect from URL</option>
                  <option value="youtube">YouTube Broadcast Channel</option>
                  <option value="telegram">Telegram Public Channel</option>
                  <option value="rss">RSS / XML / RSS-Bridge Feed</option>
                  <option value="html">Web Portal (HTML Scraper)</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
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

              <div>
                <label
                  htmlFor="src-rss"
                  className="mb-1 block text-xs font-semibold text-stone-800"
                >
                  RSS / RSS-Bridge URL (optional)
                </label>
                <input
                  id="src-rss"
                  name="rss_url"
                  type="url"
                  value={newSourceRss}
                  onChange={(e) => setNewSourceRss(e.target.value)}
                  placeholder="Auto-resolved for YouTube/Telegram"
                  autoCorrect="off"
                  autoCapitalize="none"
                  spellCheck={false}
                  className="w-full rounded-xl border border-stone-300 bg-stone-50 px-3 py-2 text-sm text-stone-900"
                />
              </div>
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
                placeholder="Provincial coverage, indigenous territories, social broadcast, municipal affairs..."
                className="w-full rounded-xl border border-stone-300 bg-stone-50 px-3 py-2 text-sm text-stone-900"
              />
            </div>

            <button
              type="submit"
              className="inline-flex items-center gap-2 rounded-xl bg-stone-900 px-4 py-2.5 text-xs font-bold text-white transition hover:bg-stone-800 cursor-pointer"
            >
              <PlusCircle className="h-3.5 w-3.5" aria-hidden="true" />
              <span>Save Outlet / Social Channel to Catalog</span>
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

      {/* Monitored Media & Social Sources Catalog */}
      <section aria-label="Catalog of monitored Bolivian media and social sources">
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-stone-200 pb-4">
          <div>
            <h2 className="text-xl font-bold text-stone-900">
              Monitored Media & Social Channels Catalog ({filteredSources.length})
            </h2>
            <p className="text-xs text-stone-600">
              Web portals, community radio networks, and social broadcast channels feeding the daily radar.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <div className="flex flex-wrap gap-1.5">
              {[
                { id: "all", label: "All Tiers" },
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

            <div className="flex flex-wrap gap-1.5 border-l border-stone-300 pl-2">
              {[
                { id: "all", label: "All Connectors" },
                { id: "social", label: "Social Video / Telegram" },
                { id: "rss", label: "RSS Feeds" },
                { id: "html", label: "HTML Portals" },
              ].map((st) => (
                <button
                  key={st.id}
                  type="button"
                  onClick={() => setStrategyFilter(st.id)}
                  aria-pressed={strategyFilter === st.id}
                  className={`rounded-lg px-2.5 py-1.5 text-xs font-semibold transition cursor-pointer ${
                    strategyFilter === st.id
                      ? "bg-amber-800 text-white"
                      : "bg-amber-100/70 text-amber-950 hover:bg-amber-200/70"
                  }`}
                >
                  {st.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        {loading ? (
          <div className="mt-4 rounded-2xl border border-stone-200 bg-white p-10 text-center text-sm text-stone-600">
            Loading monitored media and social channels catalog...
          </div>
        ) : (
          <div className="mt-5 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {filteredSources.map((src, idx) => {
              const isSocial =
                src.scrape_strategy === "youtube" ||
                src.scrape_strategy === "telegram";
              return (
                <article
                  key={src.id}
                  className={`flex flex-col justify-between rounded-xl border border-stone-200 bg-white p-5 shadow-2xs ${
                    idx >= 6 ? "deferred-card" : ""
                  }`}
                >
                  <div>
                    <div className="flex flex-wrap items-center justify-between gap-1.5">
                      <span className="rounded-md bg-amber-100/90 px-2.5 py-0.5 text-[11px] font-bold text-amber-950">
                        {TIER_LABELS[src.tier]}
                      </span>
                      <div className="flex items-center gap-1.5">
                        <span
                          className={`inline-flex items-center gap-1 rounded px-2 py-0.5 text-[11px] font-semibold ${
                            isSocial
                              ? "bg-red-100 text-red-900"
                              : "bg-stone-100 text-stone-700"
                          }`}
                        >
                          {isSocial ? (
                            <Video className="h-3 w-3" aria-hidden="true" />
                          ) : (
                            <Radio className="h-3 w-3" aria-hidden="true" />
                          )}
                          {SCRAPE_STRATEGY_LABELS[src.scrape_strategy] ||
                            src.scrape_strategy.toUpperCase()}
                        </span>
                        <span className="rounded bg-stone-100 px-2 py-0.5 text-[11px] font-semibold text-stone-700">
                          {src.department}
                        </span>
                      </div>
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
                      {src.total_articles_collected} archived dispatches
                    </span>
                    <a
                      href={src.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 font-semibold text-amber-900 hover:underline"
                    >
                      <Globe className="h-3.5 w-3.5" aria-hidden="true" />
                      <span>{isSocial ? "Channel" : "Website"}</span>
                      <ExternalLink className="h-3 w-3" aria-hidden="true" />
                    </a>
                  </div>
                </article>
              );
            })}
          </div>
        )}
      </section>
    </div>
  );
}
