import type { Metadata } from 'next';
import Link from 'next/link';
import './globals.css';
import ClientProviders from './providers';

export const metadata: Metadata = {
  title: 'WebScraper Platform',
  description: 'Admin dashboard scaffold for the web scraping platform',
};

const navItems = [
  { href: '/dashboard', label: 'Dashboard' },
  { href: '/projects', label: 'Projects' },
  { href: '/jobs', label: 'Jobs' },
  { href: '/campaigns', label: 'Campaigns' },
  { href: '/topics', label: 'Topics' },
  { href: '/admin/policies', label: 'Scrape Policies' },
  { href: process.env.NEXT_PUBLIC_API_BASE_URL ? `${process.env.NEXT_PUBLIC_API_BASE_URL}/docs` : 'http://localhost:8000/docs', label: 'API Docs', external: true },
];

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-950 text-slate-100 antialiased">
        <ClientProviders>
          <div className="mx-auto flex min-h-screen max-w-6xl flex-col px-6 py-8">
            <header className="mb-8 flex items-center justify-between rounded-xl border border-white/5 bg-white/5 px-4 py-3 backdrop-blur">
              <div>
                <p className="text-sm font-semibold uppercase tracking-[0.14em] text-emerald-200/80">
                  WebScraper
                </p>
                <h1 className="text-2xl font-semibold text-white">Operations Dashboard</h1>
              </div>
              <nav className="flex flex-wrap items-center gap-2 text-sm text-slate-200">
                {navItems.map((item) =>
                  item.external ? (
                    <a
                      key={item.href}
                      className="rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 transition hover:border-emerald-300/40 hover:text-white"
                      href={item.href}
                      target="_blank"
                      rel="noreferrer"
                    >
                      {item.label}
                    </a>
                  ) : (
                    <Link
                      key={item.href}
                      className="rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 transition hover:border-emerald-300/40 hover:text-white"
                      href={item.href}
                    >
                      {item.label}
                    </Link>
                  ),
                )}
              </nav>
            </header>
            <main className="flex-1">{children}</main>
            <footer className="mt-10 border-t border-white/5 pt-4 text-xs text-slate-400">
              Tailor this dashboard to your scraping workloads. API Base:{' '}
              {process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000'}
            </footer>
          </div>
        </ClientProviders>
      </body>
    </html>
  );
}
