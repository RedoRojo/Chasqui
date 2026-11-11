interface CoverageMeterProps {
  mainstreamCount: number;
  alternativeCount: number;
  regionalCount?: number;
  communityCount?: number;
  compact?: boolean;
}

export function CoverageMeter({
  mainstreamCount,
  alternativeCount,
  regionalCount = 0,
  communityCount = 0,
  compact = false,
}: CoverageMeterProps) {
  const nonMainstreamTotal = alternativeCount + regionalCount + communityCount;
  const total = Math.max(mainstreamCount + nonMainstreamTotal, 1);
  const nonMainPct = Math.round((nonMainstreamTotal / total) * 100);
  const mainPct = 100 - nonMainPct;

  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between text-xs">
        <span className="font-semibold text-amber-900">
          Alternativos / Comunitarios / Regionales: {nonMainstreamTotal} ({nonMainPct}%)
        </span>
        <span className="font-medium text-stone-600">
          Masivos: {mainstreamCount} ({mainPct}%)
        </span>
      </div>
      <div
        className="flex h-2 w-full overflow-hidden rounded-full bg-stone-200"
        role="img"
        aria-label={`Distribución de cobertura: ${nonMainPct}% medios alternativos, comunitarios y regionales frente a ${mainPct}% medios tradicionales`}
      >
        <div
          className="bg-amber-700 transition-all"
          style={{ width: `${nonMainPct}%` }}
        />
        <div
          className="bg-stone-500 transition-all"
          style={{ width: `${mainPct}%` }}
        />
      </div>
      {!compact ? (
        <div className="flex flex-wrap gap-2 pt-0.5 text-[11px] text-stone-600">
          {alternativeCount > 0 ? (
            <span className="rounded bg-amber-100/80 px-1.5 py-0.5 font-medium text-amber-950">
              {alternativeCount} Independientes
            </span>
          ) : null}
          {communityCount > 0 ? (
            <span className="rounded bg-emerald-100/80 px-1.5 py-0.5 font-medium text-emerald-950">
              {communityCount} Radios Comunitarias
            </span>
          ) : null}
          {regionalCount > 0 ? (
            <span className="rounded bg-sky-100/80 px-1.5 py-0.5 font-medium text-sky-950">
              {regionalCount} Regionales
            </span>
          ) : null}
          {mainstreamCount === 0 ? (
            <span className="rounded bg-rose-100 px-1.5 py-0.5 font-semibold text-rose-900">
              Punto ciego en TV/Prensa Masiva
            </span>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
