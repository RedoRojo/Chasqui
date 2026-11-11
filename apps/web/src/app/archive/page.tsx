"use client";

import { useCallback, useEffect, useState } from "react";
import {
  Calendar,
  ExternalLink,
  History,
  MapPin,
  Search,
} from "lucide-react";
import type { Article, SourceTier } from "@/lib/types";
import {
  BOLIVIA_DEPARTMENTS,
  NEWS_CATEGORIES,
  TIER_LABELS,
} from "@/lib/types";
import { fetchArticles, formatShortDate } from "@/lib/api";

export default function HistoricalArchivePage() {
  const [articles, setArticles] = useState<Article[]>([]);
  const [query, setQuery] = useState<string>("");
  const [department, setDepartment] = useState<string>("All");
  const [category, setCategory] = useState<string>("All");
  const [tier, setTier] = useState<string>("all");
  const [fromDate, setFromDate] = useState<string>("");
  const [toDate, setToDate] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(true);

  const runSearch = useCallback(async () => {
    setLoading(true);
    try {
      const results = await fetchArticles({
        q: query,
        department,
        category,
        tier,
        from_date: fromDate || undefined,
        to_date: toDate || undefined,
      });
      setArticles(results);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [query, department, category, tier, fromDate, toDate]);

  useEffect(() => {
    runSearch();
  }, [runSearch]);

  return (
    <div className="space-y-8">
      <section className="rounded-2xl border border-stone-200 bg-white p-6 shadow-xs">
        <div className="flex items-center gap-2 text-xs font-semibold text-amber-900">
          <History className="h-4 w-4" aria-hidden="true" />
          <span>National News Memory</span>
        </div>
        <h1 className="mt-1.5 text-2xl font-extrabold text-stone-900 sm:text-3xl">
          Historical Archive & Semantic News Search
        </h1>
        <p className="mt-2 max-w-3xl text-sm text-stone-700">
          Explore the historical record of dispatches collected from alternative investigative outlets, community radio networks, regional press, and mainstream media across Bolivia.
        </p>

        <search className="mt-6">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              runSearch();
            }}
            className="grid grid-cols-1 gap-4 md:grid-cols-12"
          >
            <div className="md:col-span-5">
              <label
                htmlFor="archive-q"
                className="mb-1 block text-xs font-semibold text-stone-800"
              >
                Search by keyword or semantic concept
              </label>
              <div className="relative">
                <input
                  id="archive-q"
                  name="q"
                  type="search"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="e.g. mercury, Chiquiacá, tailings dam, Lake Uru Uru..."
                  autoCorrect="off"
                  autoCapitalize="none"
                  spellCheck={false}
                  className="w-full rounded-xl border border-stone-300 bg-stone-50 py-2.5 pr-4 pl-9 text-sm text-stone-900"
                />
                <Search
                  className="pointer-events-none absolute top-3 left-3 h-4 w-4 text-stone-500"
                  aria-hidden="true"
                />
              </div>
            </div>

            <div className="md:col-span-3">
              <label
                htmlFor="archive-dept"
                className="mb-1 block text-xs font-semibold text-stone-800"
              >
                Department
              </label>
              <select
                id="archive-dept"
                name="department"
                value={department}
                onChange={(e) => setDepartment(e.target.value)}
                className="w-full rounded-xl border border-stone-300 bg-stone-50 px-3 py-2.5 text-sm text-stone-900"
              >
                {BOLIVIA_DEPARTMENTS.map((d) => (
                  <option key={d} value={d}>
                    {d}
                  </option>
                ))}
              </select>
            </div>

            <div className="md:col-span-4">
              <label
                htmlFor="archive-tier"
                className="mb-1 block text-xs font-semibold text-stone-800"
              >
                Media source tier
              </label>
              <select
                id="archive-tier"
                name="tier"
                value={tier}
                onChange={(e) => setTier(e.target.value)}
                className="w-full rounded-xl border border-stone-300 bg-stone-50 px-3 py-2.5 text-sm text-stone-900"
              >
                <option value="all">All source tiers</option>
                <option value="alternative">
                  Alternative & Independent Investigation
                </option>
                <option value="community">
                  Community Radio & Grassroots Agencies
                </option>
                <option value="regional">
                  Regional / Departmental Press
                </option>
                <option value="mainstream">
                  Mainstream Mass Media
                </option>
              </select>
            </div>

            <div className="md:col-span-4">
              <label
                htmlFor="archive-cat"
                className="mb-1 block text-xs font-semibold text-stone-800"
              >
                Category
              </label>
              <select
                id="archive-cat"
                name="category"
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="w-full rounded-xl border border-stone-300 bg-stone-50 px-3 py-2.5 text-sm text-stone-900"
              >
                {NEWS_CATEGORIES.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            </div>

            <div className="md:col-span-3">
              <label
                htmlFor="archive-from"
                className="mb-1 block text-xs font-semibold text-stone-800"
              >
                From date
              </label>
              <input
                id="archive-from"
                name="from_date"
                type="date"
                value={fromDate}
                onChange={(e) => setFromDate(e.target.value)}
                className="w-full rounded-xl border border-stone-300 bg-stone-50 px-3 py-2 text-sm text-stone-900"
              />
            </div>

            <div className="md:col-span-3">
              <label
                htmlFor="archive-to"
                className="mb-1 block text-xs font-semibold text-stone-800"
              >
                To date
              </label>
              <input
                id="archive-to"
                name="to_date"
                type="date"
                value={toDate}
                onChange={(e) => setToDate(e.target.value)}
                className="w-full rounded-xl border border-stone-300 bg-stone-50 px-3 py-2 text-sm text-stone-900"
              />
            </div>

            <div className="flex items-end gap-2 md:col-span-2">
              <button
                type="submit"
                className="w-full rounded-xl bg-stone-900 px-4 py-2.5 text-xs font-bold text-white transition hover:bg-stone-800 cursor-pointer"
              >
                Filter archive
              </button>
            </div>
          </form>
        </search>
      </section>

      <section aria-label="Historical archive results">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-lg font-bold text-stone-900">
            Archived Articles ({articles.length})
          </h2>
        </div>

        {loading ? (
          <div className="rounded-2xl border border-stone-200 bg-white p-10 text-center text-sm text-stone-600">
            Querying historical archive...
          </div>
        ) : articles.length === 0 ? (
          <div className="rounded-2xl border border-stone-200 bg-white p-10 text-center text-sm text-stone-600">
            No archived articles matched your search criteria.
          </div>
        ) : (
          <div className="space-y-3">
            {articles.map((art, idx) => (
              <article
                key={art.id}
                className={`rounded-xl border border-stone-200 bg-white p-5 shadow-2xs ${
                  idx >= 5 ? "deferred-card" : ""
                }`}
              >
                <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-bold text-stone-900">
                      {art.source?.name || "Source"}
                    </span>
                    {art.source?.tier ? (
                      <span className="rounded-md bg-amber-100 px-2 py-0.5 font-semibold text-amber-950">
                        {TIER_LABELS[art.source.tier as SourceTier]}
                      </span>
                    ) : null}
                    <span className="inline-flex items-center gap-1 rounded-md bg-stone-100 px-2 py-0.5 font-medium text-stone-800">
                      <MapPin className="h-3 w-3 text-amber-800" aria-hidden="true" />
                      {art.department}
                    </span>
                    <span className="rounded-md bg-stone-100 px-2 py-0.5 text-stone-600">
                      {art.category}
                    </span>
                  </div>
                  <time
                    dateTime={art.published_at}
                    className="inline-flex items-center gap-1 font-medium text-stone-600"
                  >
                    <Calendar className="h-3.5 w-3.5" aria-hidden="true" />
                    {formatShortDate(art.published_at)}
                  </time>
                </div>

                <h3 className="mt-2 text-base font-bold text-stone-900">
                  {art.title}
                </h3>

                <p className="mt-1.5 text-sm leading-relaxed text-stone-700">
                  {art.content}
                </p>

                <div className="mt-3 flex flex-wrap items-center justify-between gap-2 border-t border-stone-100 pt-2.5 text-xs">
                  <div className="flex flex-wrap gap-1.5">
                    {art.entities?.map((ent) => (
                      <span
                        key={ent}
                        className="rounded bg-stone-100 px-2 py-0.5 text-[11px] font-medium text-stone-700"
                      >
                        {ent}
                      </span>
                    ))}
                  </div>
                  <a
                    href={art.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 font-semibold text-amber-900 hover:underline"
                  >
                    <span>View original publication</span>
                    <ExternalLink className="h-3.5 w-3.5" aria-hidden="true" />
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
