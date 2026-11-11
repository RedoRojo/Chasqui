"use client";

import { use, useEffect, useState } from "react";
import Link from "next/link";
import {
  AlertTriangle,
  ArrowLeft,
  ArrowUpDown,
  Calendar,
  ExternalLink,
  Layers,
  MapPin,
} from "lucide-react";
import type { StoryThreadDetail } from "@/lib/types";
import { TIER_LABELS } from "@/lib/types";
import { fetchThreadBySlug, formatShortDate } from "@/lib/api";
import { CoverageMeter } from "@/components/CoverageMeter";

export default function ThreadTimelinePage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = use(params);
  const [thread, setThread] = useState<StoryThreadDetail | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [chronologicalOrder, setChronologicalOrder] = useState<"desc" | "asc">(
    "desc"
  );

  useEffect(() => {
    setLoading(true);
    fetchThreadBySlug(slug)
      .then((data) => setThread(data))
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, [slug]);

  if (loading) {
    return (
      <div className="rounded-2xl border border-stone-200 bg-white p-12 text-center text-sm font-medium text-stone-600">
        Loading story thread timeline and historical milestones...
      </div>
    );
  }

  if (!thread) {
    return (
      <div className="rounded-2xl border border-stone-200 bg-white p-12 text-center">
        <h1 className="text-xl font-bold text-stone-900">
          Story thread not found
        </h1>
        <Link
          href="/"
          className="mt-4 inline-flex items-center gap-2 rounded-xl bg-stone-900 px-4 py-2 text-xs font-semibold text-white"
        >
          <ArrowLeft className="h-4 w-4" aria-hidden="true" />
          <span>Back to main radar</span>
        </Link>
      </div>
    );
  }

  const orderedEvents = [...(thread.events || [])].sort((a, b) => {
    const tA = new Date(a.event_date).getTime();
    const tB = new Date(b.event_date).getTime();
    return chronologicalOrder === "desc" ? tB - tA : tA - tB;
  });

  return (
    <div className="space-y-8">
      <nav aria-label="Breadcrumb navigation">
        <Link
          href="/"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-stone-700 hover:text-amber-900"
        >
          <ArrowLeft className="h-3.5 w-3.5" aria-hidden="true" />
          <span>Back to Story Threads & Daily Radar</span>
        </Link>
      </nav>

      {/* Story Thread Summary Card */}
      <section className="rounded-2xl border border-stone-200 bg-white p-6 shadow-xs sm:p-8">
        <div className="flex flex-wrap items-center gap-2 text-xs">
          <span className="inline-flex items-center gap-1 rounded-md bg-stone-900 px-2.5 py-1 font-semibold text-stone-50">
            <MapPin className="h-3.5 w-3.5 text-amber-400" aria-hidden="true" />
            {thread.primary_department}
          </span>
          {thread.departments_affected
            ?.filter((d) => d !== thread.primary_department)
            .map((dept) => (
              <span
                key={dept}
                className="rounded-md bg-stone-100 px-2.5 py-1 font-medium text-stone-700"
              >
                + {dept}
              </span>
            ))}
          <span className="rounded-md bg-amber-100/80 px-2.5 py-1 font-semibold text-amber-950">
            {thread.category}
          </span>
        </div>

        <h1 className="mt-3 text-2xl font-extrabold tracking-tight text-stone-900 sm:text-3xl">
          {thread.title}
        </h1>

        <p className="mt-3 max-w-4xl text-base leading-relaxed text-stone-700">
          {thread.current_summary}
        </p>

        {thread.key_entities && thread.key_entities.length > 0 ? (
          <div className="mt-4 flex flex-wrap items-center gap-1.5">
            <span className="text-xs font-semibold text-stone-600">
              Linked actors, institutions, and locations:
            </span>
            {thread.key_entities.map((ent) => (
              <span
                key={ent}
                className="rounded-md border border-stone-200 bg-stone-50 px-2.5 py-0.5 text-xs font-medium text-stone-800"
              >
                {ent}
              </span>
            ))}
          </div>
        ) : null}

        <div className="mt-6 grid grid-cols-1 gap-6 border-t border-stone-100 pt-5 md:grid-cols-12">
          <div className="md:col-span-6">
            <CoverageMeter
              mainstreamCount={thread.mainstream_count}
              alternativeCount={thread.alternative_count}
            />
          </div>
          <dl className="grid grid-cols-3 gap-3 md:col-span-6">
            <div className="rounded-xl bg-stone-50 p-3">
              <dt className="text-[11px] font-medium text-stone-600">
                First recorded
              </dt>
              <dd className="mt-0.5 text-sm font-bold text-stone-900">
                {formatShortDate(thread.first_seen_at)}
              </dd>
            </div>
            <div className="rounded-xl bg-stone-50 p-3">
              <dt className="text-[11px] font-medium text-stone-600">
                Latest milestone
              </dt>
              <dd className="mt-0.5 text-sm font-bold text-stone-900">
                {formatShortDate(thread.last_updated_at)}
              </dd>
            </div>
            <div className="rounded-xl bg-amber-50/70 p-3">
              <dt className="text-[11px] font-medium text-amber-950">
                Milestones / Sources
              </dt>
              <dd className="mt-0.5 text-sm font-bold text-amber-950">
                {thread.events_count} milestones ({thread.articles_count} articles)
              </dd>
            </div>
          </dl>
        </div>
      </section>

      {/* Timeline Header */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Layers className="h-5 w-5 text-amber-800" aria-hidden="true" />
          <h2 className="text-xl font-bold text-stone-900">
            Longitudinal Timeline & Case Evolution ({orderedEvents.length} milestones)
          </h2>
        </div>

        <button
          type="button"
          onClick={() =>
            setChronologicalOrder((prev) => (prev === "desc" ? "asc" : "desc"))
          }
          className="inline-flex items-center gap-2 rounded-xl border border-stone-300 bg-white px-3.5 py-2 text-xs font-semibold text-stone-800 shadow-2xs transition hover:bg-stone-50 cursor-pointer"
        >
          <ArrowUpDown className="h-3.5 w-3.5 text-amber-800" aria-hidden="true" />
          <span>
            {chronologicalOrder === "desc"
              ? "Showing: Latest to earliest origin"
              : "Showing: Earliest origin to latest"}
          </span>
        </button>
      </div>

      {/* Timeline Nodes */}
      <ol className="relative ml-3 space-y-6 border-l-2 border-amber-700/40 pl-6 sm:ml-6 sm:pl-8">
        {orderedEvents.map((ev, idx) => (
          <li
            key={ev.id}
            className={`relative rounded-2xl border border-stone-200 bg-white p-5 shadow-xs sm:p-6 ${
              idx >= 3 ? "deferred-card" : ""
            }`}
          >
            {/* Circular timeline marker */}
            <span
              className="absolute top-6 -left-[33px] flex h-4 w-4 items-center justify-center rounded-full border-2 border-amber-800 bg-[#faf8f5] sm:-left-[41px]"
              aria-hidden="true"
            >
              <span className="h-2 w-2 rounded-full bg-amber-800" />
            </span>

            <div className="flex flex-wrap items-center justify-between gap-2 pb-2">
              <div className="flex flex-wrap items-center gap-2 text-xs">
                <time
                  dateTime={ev.event_date}
                  className="inline-flex items-center gap-1 rounded-md bg-stone-900 px-2.5 py-1 font-bold text-stone-50"
                >
                  <Calendar className="h-3.5 w-3.5 text-amber-400" aria-hidden="true" />
                  {formatShortDate(ev.event_date)}
                </time>
                <span className="rounded-md bg-stone-100 px-2.5 py-1 font-semibold text-stone-800">
                  {ev.primary_department}
                </span>
                {ev.is_blindspot ? (
                  <span className="inline-flex items-center gap-1 rounded-md bg-amber-100 px-2.5 py-1 font-semibold text-amber-950">
                    <AlertTriangle
                      className="h-3.5 w-3.5 text-amber-800"
                      aria-hidden="true"
                    />
                    Reported by alternative / community / regional outlets
                  </span>
                ) : null}
              </div>
              <span className="text-xs font-medium text-stone-500">
                Milestone #{chronologicalOrder === "desc" ? orderedEvents.length - idx : idx + 1}
              </span>
            </div>

            <h3 className="mt-1 text-lg font-bold text-stone-900">
              {ev.title}
            </h3>

            <p className="mt-2 text-sm leading-relaxed text-stone-700">
              {ev.summary}
            </p>

            {/* Sources that covered this milestone */}
            <div className="mt-4 rounded-xl border border-stone-200/80 bg-stone-50/80 p-4">
              <h4 className="text-xs font-bold tracking-wide text-stone-700 uppercase">
                Source coverage for this milestone ({ev.articles.length})
              </h4>
              <ul className="mt-3 divide-y divide-stone-200/80">
                {ev.articles.map((art) => (
                  <li key={art.id} className="py-2.5 first:pt-1 last:pb-1">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="text-xs font-bold text-stone-900">
                          {art.source?.name || "News Outlet"}
                        </span>
                        {art.source?.tier ? (
                          <span className="rounded bg-amber-100/80 px-2 py-0.5 text-[11px] font-semibold text-amber-950">
                            {TIER_LABELS[art.source.tier]}
                          </span>
                        ) : null}
                      </div>
                      <a
                        href={art.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 text-xs font-semibold text-amber-900 hover:underline"
                      >
                        <span>Open original source</span>
                        <ExternalLink className="h-3 w-3" aria-hidden="true" />
                      </a>
                    </div>
                    <p className="mt-1 text-sm font-semibold text-stone-800">
                      {art.title}
                    </p>
                    <p className="mt-1 text-xs leading-relaxed text-stone-600">
                      {art.summary}
                    </p>
                  </li>
                ))}
              </ul>
            </div>
          </li>
        ))}
      </ol>
    </div>
  );
}
