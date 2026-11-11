"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  Clock,
  Filter,
  Layers,
  MapPin,
  RefreshCw,
  Search,
  Sparkles,
} from "lucide-react";
import type {
  DashboardOverview,
  StoryEvent,
  StoryThread,
} from "@/lib/types";
import { BOLIVIA_DEPARTMENTS, NEWS_CATEGORIES } from "@/lib/types";
import {
  fetchEvents,
  fetchOverview,
  fetchThreads,
  formatRelativeDays,
  formatShortDate,
  triggerDailyScrape,
} from "@/lib/api";
import { CoverageMeter } from "@/components/CoverageMeter";
import { EventCard } from "@/components/EventCard";

export default function HomePage() {
  const [overview, setOverview] = useState<DashboardOverview | null>(null);
  const [threads, setThreads] = useState<StoryThread[]>([]);
  const [events, setEvents] = useState<StoryEvent[]>([]);
  const [department, setDepartment] = useState<string>("All");
  const [category, setCategory] = useState<string>("All");
  const [blindspotOnly, setBlindspotOnly] = useState<boolean>(false);
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [activeTab, setActiveTab] = useState<"threads" | "events">("threads");
  const [loading, setLoading] = useState<boolean>(true);
  const [scraping, setScraping] = useState<boolean>(false);
  const [scrapeMessage, setScrapeMessage] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      // react-best-practices: async-parallel (use Promise.all for independent operations)
      const [ovData, thData, evData] = await Promise.all([
        fetchOverview(),
        fetchThreads({
          department,
          category,
          blindspot_only: blindspotOnly,
          q: searchQuery,
        }),
        fetchEvents({
          department,
          category,
          blindspot_only: blindspotOnly,
          limit: 20,
        }),
      ]);
      setOverview(ovData);
      setThreads(thData);
      setEvents(evData);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [department, category, blindspotOnly, searchQuery]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  async function handleRunDailyScan() {
    setScraping(true);
    setScrapeMessage(null);
    try {
      const result = await triggerDailyScrape(true);
      setScrapeMessage(
        `Live scan completed (${result.sources_scanned} Bolivian sources scanned): +${result.new_articles} new articles, +${result.new_events} events linked to story timelines.`
      );
      await loadData();
    } catch {
      setScrapeMessage("Could not complete the live scan at this moment.");
    } finally {
      setScraping(false);
    }
  }

  return (
    <div className="space-y-8">
      {/* Main Hero & Daily Intelligence Indicators */}
      <section className="rounded-2xl border border-stone-200 bg-white p-6 shadow-xs">
        <div className="flex flex-col justify-between gap-4 lg:flex-row lg:items-center">
          <div className="max-w-3xl">
            <div className="inline-flex items-center gap-2 rounded-full bg-amber-100/90 px-3 py-1 text-xs font-semibold text-amber-950">
              <Sparkles className="h-3.5 w-3.5 text-amber-800" aria-hidden="true" />
              <span>National Centralization & Longitudinal Issue Tracking</span>
            </div>
            <h1 className="mt-2.5 text-2xl font-extrabold tracking-tight text-stone-900 sm:text-3xl">
              What is happening across Bolivia and how stories evolve over time
            </h1>
            <p className="mt-2 text-sm leading-relaxed text-stone-700">
              Chasqui aggregates daily dispatches from{" "}
              <strong>
                community radio networks, independent investigative outlets, regional press, and mainstream media
              </strong>{" "}
              so that regional and civic developments are never left invisible or forgotten once they leave the front page.
            </p>
          </div>

          <div className="flex flex-col items-start gap-2 sm:items-end">
            <button
              type="button"
              onClick={handleRunDailyScan}
              disabled={scraping}
              className="inline-flex items-center gap-2 rounded-xl bg-amber-800 px-4 py-2.5 text-sm font-semibold text-amber-50 shadow-xs transition hover:bg-amber-900 disabled:opacity-60 cursor-pointer"
            >
              <RefreshCw
                className={`h-4 w-4 ${scraping ? "animate-spin" : ""}`}
                aria-hidden="true"
              />
              <span>
                {scraping ? "Scanning sources..." : "Run Daily Scan Now"}
              </span>
            </button>
            {overview?.last_scrape ? (
              <span className="text-xs text-stone-600">
                Last scan: {formatRelativeDays(overview.last_scrape.started_at)} (
                {overview.total_sources} active sources)
              </span>
            ) : null}
          </div>
        </div>

        {scrapeMessage ? (
          <div
            role="status"
            aria-live="polite"
            className="mt-4 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-xs font-semibold text-emerald-950"
          >
            {scrapeMessage}
          </div>
        ) : null}

        {overview ? (
          <dl className="mt-6 grid grid-cols-2 gap-3 border-t border-stone-100 pt-5 sm:grid-cols-4">
            <div className="rounded-xl bg-stone-50 p-3.5">
              <dt className="text-xs font-medium text-stone-600">
                Active Story Threads
              </dt>
              <dd className="mt-1 text-2xl font-extrabold text-stone-900">
                {overview.total_threads}
              </dd>
            </div>
            <div className="rounded-xl bg-stone-50 p-3.5">
              <dt className="text-xs font-medium text-stone-600">
                Chronological Milestones
              </dt>
              <dd className="mt-1 text-2xl font-extrabold text-stone-900">
                {overview.total_events}
              </dd>
            </div>
            <div className="rounded-xl bg-amber-50/80 p-3.5">
              <dt className="text-xs font-medium text-amber-950">
                Media Blindspot Events
              </dt>
              <dd className="mt-1 text-2xl font-extrabold text-amber-900">
                {overview.blindspot_events_count}
              </dd>
            </div>
            <div className="rounded-xl bg-stone-50 p-3.5">
              <dt className="text-xs font-medium text-stone-600">
                Alternative, Community & Regional Share
              </dt>
              <dd className="mt-1 text-2xl font-extrabold text-stone-900">
                {overview.alternative_coverage_share}%
              </dd>
            </div>
          </dl>
        ) : null}
      </section>

      {/* Search & Filters Across Bolivia's 9 Departments and Categories */}
      <search className="rounded-2xl border border-stone-200 bg-white p-5 shadow-xs">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            loadData();
          }}
          className="space-y-4"
        >
          <div className="grid grid-cols-1 gap-4 md:grid-cols-12">
            <div className="md:col-span-5">
              <label
                htmlFor="radar-search"
                className="mb-1 block text-xs font-semibold text-stone-800"
              >
                Search issue, municipality, river, reserve, or public actor
              </label>
              <div className="relative">
                <input
                  id="radar-search"
                  name="q"
                  type="search"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="e.g. Tariquía, Beni River mercury, Pilcomayo, diesel..."
                  autoCorrect="off"
                  autoCapitalize="none"
                  spellCheck={false}
                  className="w-full rounded-xl border border-stone-300 bg-stone-50 py-2.5 pr-4 pl-9 text-sm text-stone-900 placeholder:text-stone-500"
                />
                <Search
                  className="pointer-events-none absolute top-3 left-3 h-4 w-4 text-stone-500"
                  aria-hidden="true"
                />
              </div>
            </div>

            <div className="md:col-span-4">
              <label
                htmlFor="filter-category"
                className="mb-1 block text-xs font-semibold text-stone-800"
              >
                Thematic category
              </label>
              <div className="relative">
                <select
                  id="filter-category"
                  name="category"
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  className="w-full rounded-xl border border-stone-300 bg-stone-50 px-3 py-2.5 text-sm text-stone-900"
                >
                  {NEWS_CATEGORIES.map((cat) => (
                    <option key={cat} value={cat}>
                      {cat}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="flex items-end md:col-span-3">
              <div className="flex w-full items-center gap-2.5 rounded-xl border border-amber-200 bg-amber-50/70 px-3.5 py-2.5">
                <input
                  id="blindspot-toggle"
                  name="blindspot_only"
                  type="checkbox"
                  checked={blindspotOnly}
                  onChange={(e) => setBlindspotOnly(e.target.checked)}
                  className="h-4 w-4 accent-amber-800"
                />
                <label
                  htmlFor="blindspot-toggle"
                  className="cursor-pointer text-xs font-semibold text-amber-950 select-none"
                >
                  Blindspots only (no mainstream TV/press)
                </label>
              </div>
            </div>
          </div>

          <fieldset>
            <legend className="mb-2 flex items-center gap-1.5 text-xs font-semibold text-stone-700">
              <Filter className="h-3.5 w-3.5 text-amber-800" aria-hidden="true" />
              <span>Filter by Bolivian Department</span>
            </legend>
            <div className="flex flex-wrap gap-1.5">
              {BOLIVIA_DEPARTMENTS.map((dept) => {
                const selected = department === dept;
                return (
                  <button
                    key={dept}
                    type="button"
                    onClick={() => setDepartment(dept)}
                    aria-pressed={selected}
                    className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition cursor-pointer ${
                      selected
                        ? "bg-stone-900 text-stone-50"
                        : "bg-stone-100 text-stone-700 hover:bg-stone-200"
                    }`}
                  >
                    {dept}
                  </button>
                );
              })}
            </div>
          </fieldset>
        </form>
      </search>

      {/* View Switcher: Evolving Story Threads vs. Recent Milestones */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-stone-200 pb-3">
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setActiveTab("threads")}
            aria-pressed={activeTab === "threads"}
            className={`inline-flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-bold transition cursor-pointer ${
              activeTab === "threads"
                ? "bg-amber-800 text-amber-50"
                : "bg-stone-200/70 text-stone-800 hover:bg-stone-200"
            }`}
          >
            <Layers className="h-4 w-4" aria-hidden="true" />
            <span>Evolving Story Threads ({threads.length})</span>
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("events")}
            aria-pressed={activeTab === "events"}
            className={`inline-flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-bold transition cursor-pointer ${
              activeTab === "events"
                ? "bg-amber-800 text-amber-50"
                : "bg-stone-200/70 text-stone-800 hover:bg-stone-200"
            }`}
          >
            <Activity className="h-4 w-4" aria-hidden="true" />
            <span>Recent Chronological Events ({events.length})</span>
          </button>
        </div>
        <span className="text-xs font-medium text-stone-600">
          Click any story thread to inspect its full historical timeline
        </span>
      </div>

      {loading ? (
        <div className="rounded-2xl border border-stone-200 bg-white p-12 text-center text-sm font-medium text-stone-600">
          Loading Bolivian story threads and chronological events...
        </div>
      ) : activeTab === "threads" ? (
        <section aria-label="Evolving story threads">
          {threads.length === 0 ? (
            <div className="rounded-2xl border border-stone-200 bg-white p-10 text-center text-sm text-stone-600">
              No story threads matched the selected filters.
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
              {threads.map((thread, idx) => (
                <article
                  key={thread.id}
                  className={`flex flex-col justify-between rounded-2xl border border-stone-200 bg-white p-6 shadow-xs transition hover:border-amber-700/60 hover:shadow-md ${
                    idx >= 4 ? "deferred-card" : ""
                  }`}
                >
                  <div>
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div className="flex flex-wrap items-center gap-1.5 text-xs">
                        <span className="inline-flex items-center gap-1 rounded-md bg-stone-900 px-2.5 py-1 font-semibold text-stone-50">
                          <MapPin className="h-3 w-3 text-amber-400" aria-hidden="true" />
                          {thread.primary_department}
                        </span>
                        <span className="rounded-md bg-stone-100 px-2.5 py-1 font-medium text-stone-700">
                          {thread.category}
                        </span>
                        {thread.blindspot_ratio >= 80 ? (
                          <span className="inline-flex items-center gap-1 rounded-md bg-amber-100 px-2.5 py-1 font-semibold text-amber-950">
                            <AlertTriangle
                              className="h-3.5 w-3.5 text-amber-800"
                              aria-hidden="true"
                            />
                            Highlighted by alternative/regional press
                          </span>
                        ) : null}
                      </div>
                      <span className="inline-flex items-center gap-1 text-xs font-medium text-stone-600">
                        <Clock className="h-3.5 w-3.5" aria-hidden="true" />
                        Updated: {formatRelativeDays(thread.last_updated_at)}
                      </span>
                    </div>

                    <h2 className="mt-3 text-xl font-bold leading-snug text-stone-900">
                      <Link
                        href={`/threads/${thread.slug}`}
                        className="hover:text-amber-900 hover:underline"
                      >
                        {thread.title}
                      </Link>
                    </h2>

                    <p className="mt-2.5 text-sm leading-relaxed text-stone-700">
                      {thread.current_summary}
                    </p>

                    {thread.key_entities && thread.key_entities.length > 0 ? (
                      <div className="mt-3 flex flex-wrap gap-1.5">
                        {thread.key_entities.slice(0, 5).map((ent) => (
                          <span
                            key={ent}
                            className="rounded-md border border-stone-200 bg-stone-50 px-2 py-0.5 text-[11px] font-medium text-stone-700"
                          >
                            {ent}
                          </span>
                        ))}
                      </div>
                    ) : null}
                  </div>

                  <div className="mt-5 space-y-3 border-t border-stone-100 pt-4">
                    <CoverageMeter
                      mainstreamCount={thread.mainstream_count}
                      alternativeCount={thread.alternative_count}
                      compact
                    />

                    <div className="flex flex-wrap items-center justify-between gap-2 pt-1 text-xs">
                      <span className="font-medium text-stone-600">
                        Tracked since {formatShortDate(thread.first_seen_at)} ·{" "}
                        <strong className="text-stone-900">
                          {thread.events_count} milestones
                        </strong>{" "}
                        ({thread.articles_count} articles)
                      </span>
                      <Link
                        href={`/threads/${thread.slug}`}
                        className="inline-flex items-center gap-1.5 rounded-lg bg-amber-50 px-3 py-1.5 font-bold text-amber-950 transition hover:bg-amber-100"
                      >
                        <span>View timeline</span>
                        <ArrowRight className="h-3.5 w-3.5" aria-hidden="true" />
                      </Link>
                    </div>
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>
      ) : (
        <section aria-label="Recent clustered events">
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            {events.map((ev, idx) => (
              <EventCard
                key={ev.id}
                event={ev}
                showThreadLink
                isDeferred={idx >= 4}
              />
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
