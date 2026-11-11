"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Radio, History, Compass, Newspaper } from "lucide-react";

const NAV_ITEMS = [
  { href: "/", label: "Radar y Evolución", icon: Compass },
  { href: "/archivo", label: "Archivo Histórico", icon: History },
  { href: "/fuentes", label: "Fuentes e Ingesta", icon: Newspaper },
];

export function Navbar() {
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-30 border-b border-stone-200 bg-[#faf8f5]/95 backdrop-blur">
      <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4 px-4 py-3.5 sm:px-6">
        <div className="flex items-center gap-3">
          <Link
            href="/"
            className="flex items-center gap-2.5 text-stone-900 hover:opacity-90"
          >
            <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-amber-800 text-amber-50 shadow-xs">
              <Radio className="h-5 w-5" aria-hidden="true" />
            </span>
            <div>
              <span className="block text-xl font-bold tracking-tight text-stone-900">
                CHASQUI
              </span>
              <span className="block text-[11px] font-medium tracking-wider text-stone-600 uppercase">
                Observatorio y Memoria Informativa de Bolivia
              </span>
            </div>
          </Link>
        </div>

        <nav aria-label="Navegación principal">
          <ul className="flex items-center gap-1.5 sm:gap-2">
            {NAV_ITEMS.map((item) => {
              const Icon = item.icon;
              const isActive =
                item.href === "/"
                  ? pathname === "/" || pathname.startsWith("/hilos")
                  : pathname.startsWith(item.href);
              return (
                <li key={item.href}>
                  <Link
                    href={item.href}
                    aria-current={isActive ? "page" : undefined}
                    className={`inline-flex items-center gap-2 rounded-lg px-3.5 py-2 text-sm font-medium transition-colors ${
                      isActive
                        ? "bg-stone-900 text-stone-50"
                        : "text-stone-700 hover:bg-stone-200/70 hover:text-stone-900"
                    }`}
                  >
                    <Icon className="h-4 w-4" aria-hidden="true" />
                    <span>{item.label}</span>
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>
      </div>
    </header>
  );
}
