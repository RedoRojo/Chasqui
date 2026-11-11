import Link from "next/link";
import { AlertTriangle, Calendar, ExternalLink, MapPin, Layers } from "lucide-react";
import type { StoryEvent } from "@/lib/types";
import { TIER_LABELS } from "@/lib/types";
import { formatShortDate } from "@/lib/api";
import { CoverageMeter } from "./CoverageMeter";

interface EventCardProps {
  event: StoryEvent;
  showThreadLink?: boolean;
  isDeferred?: boolean;
}

export function EventCard({
  event,
  showThreadLink = true,
  isDeferred = false,
}: EventCardProps) {
  return (
    <article
      className={`rounded-xl border border-stone-200/90 bg-white p-5 shadow-xs transition-shadow hover:shadow-md ${
        isDeferred ? "deferred-card" : ""
      }`}
    >
      <div className="flex flex-wrap items-center justify-between gap-2 pb-2.5">
        <div className="flex flex-wrap items-center gap-2 text-xs">
          <span className="inline-flex items-center gap-1 rounded-md bg-stone-100 px-2.5 py-1 font-semibold text-stone-800">
            <MapPin className="h-3.5 w-3.5 text-amber-800" aria-hidden="true" />
            {event.primary_department}
          </span>
          <span className="rounded-md bg-stone-100 px-2.5 py-1 font-medium text-stone-700">
            {event.category}
          </span>
          {event.is_blindspot ? (
            <span className="inline-flex items-center gap-1 rounded-md bg-amber-100 px-2.5 py-1 font-semibold text-amber-950">
              <AlertTriangle className="h-3.5 w-3.5 text-amber-800" aria-hidden="true" />
              Mainstream Blindspot
            </span>
          ) : null}
        </div>
        <time
          dateTime={event.event_date}
          className="inline-flex items-center gap-1 text-xs font-medium text-stone-600"
        >
          <Calendar className="h-3.5 w-3.5" aria-hidden="true" />
          {formatShortDate(event.event_date)}
        </time>
      </div>

      <h3 className="text-lg font-bold leading-snug text-stone-900">
        {event.title}
      </h3>

      <p className="mt-2 text-sm leading-relaxed text-stone-700">
        {event.summary}
      </p>

      {showThreadLink && event.thread_slug ? (
        <div className="mt-3 rounded-lg border border-amber-200/80 bg-amber-50/60 px-3 py-2">
          <Link
            href={`/threads/${event.thread_slug}`}
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-amber-950 hover:underline"
          >
            <Layers className="h-3.5 w-3.5 text-amber-800" aria-hidden="true" />
            <span>
              Part of evolving thread: {event.thread_title || event.thread_slug}
            </span>
          </Link>
        </div>
      ) : null}

      <div className="mt-4 border-t border-stone-100 pt-3">
        <CoverageMeter
          mainstreamCount={event.mainstream_count}
          alternativeCount={event.alternative_count}
          regionalCount={event.regional_count}
          communityCount={event.community_count}
        />
      </div>

      {/* Modern Web Guidance: search-hidden-content & html
          Use native <details> and <summary> so collapsed source articles remain
          searchable via native browser Find-in-page without custom JS toggles. */}
      {event.articles && event.articles.length > 0 ? (
        <details className="mt-3.5 rounded-lg border border-stone-200 bg-stone-50/70 px-3.5 py-2">
          <summary className="cursor-pointer text-xs font-semibold text-stone-800 select-none">
            View the {event.articles.length} source(s) that reported this event
          </summary>
          <ul className="mt-2.5 divide-y divide-stone-200/80">
            {event.articles.map((art) => (
              <li key={art.id} className="py-2 first:pt-1 last:pb-1">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-stone-900">
                      {art.source?.name || "Registered source"}
                    </span>
                    {art.source?.tier ? (
                      <span className="rounded bg-stone-200/80 px-1.5 py-0.5 text-[10px] font-medium text-stone-700">
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
                    <span>Original article</span>
                    <ExternalLink className="h-3 w-3" aria-hidden="true" />
                  </a>
                </div>
                <p className="mt-1 text-xs font-medium text-stone-800">
                  {art.title}
                </p>
              </li>
            ))}
          </ul>
        </details>
      ) : null}
    </article>
  );
}
