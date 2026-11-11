import type { Metadata } from "next";
import "./globals.css";
import { Navbar } from "@/components/Navbar";

export const metadata: Metadata = {
  title: "Chasqui | Bolivian News Centralization & Longitudinal Intelligence",
  description:
    "Full-stack news aggregation, longitudinal story-thread tracking, and media blindspot analysis across mainstream, alternative, community, and regional outlets in Bolivia.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="flex min-h-screen flex-col antialiased">
        <Navbar />
        <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-6 sm:px-6">
          {children}
        </main>
        <footer className="mt-16 border-t border-stone-200 bg-stone-100/80 py-8 text-xs text-stone-600">
          <div className="mx-auto flex max-w-7xl flex-col items-start justify-between gap-4 px-4 sm:flex-row sm:items-center sm:px-6">
            <div>
              <p className="font-bold text-stone-900">
                CHASQUI · Bolivian News Centralization & Historical Memory
              </p>
              <p className="mt-1">
                Automated daily scanning across alternative media, community radio networks, regional press, and mainstream outlets in all 9 departments.
              </p>
            </div>
            <p className="font-medium text-stone-700">
              Scheduled daily updates · Longitudinal story-thread clustering
            </p>
          </div>
        </footer>
      </body>
    </html>
  );
}
