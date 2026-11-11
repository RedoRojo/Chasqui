import type { Metadata } from "next";
import "./globals.css";
import { Navbar } from "@/components/Navbar";

export const metadata: Metadata = {
  title: "Chasqui | Centralización y Evolución de Noticias de Bolivia",
  description:
    "Plataforma de centralización de noticias de Bolivia, seguimiento histórico de problemáticas y contraste entre medios tradicionales, alternativos, comunitarios y regionales.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="es">
      <body className=" flex min-h-screen flex-col antialiased">
        <Navbar />
        <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-6 sm:px-6">
          {children}
        </main>
        <footer className="mt-16 border-t border-stone-200 bg-stone-100/80 py-8 text-xs text-stone-600">
          <div className="mx-auto flex max-w-7xl flex-col items-start justify-between gap-4 px-4 sm:flex-row sm:items-center sm:px-6">
            <div>
              <p className="font-bold text-stone-900">
                CHASQUI · Memoria y Centralización Informativa de Bolivia
              </p>
              <p className="mt-1">
                Escaneo diario de medios alternativos, radios comunitarias, prensa regional y medios tradicionales en los 9 departamentos.
              </p>
            </div>
            <p className="font-medium text-stone-700">
              Actualización programada diariamente · Agrupación longitudinal por hilos
            </p>
          </div>
        </footer>
      </body>
    </html>
  );
}
