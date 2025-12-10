'use client';

import { useMemo, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { useCampaigns } from '@/hooks/useCampaigns';
import { useCampaignPages } from '@/hooks/useCampaignPages';
import { CrawledPage } from '@/lib/api-client';

export default function CampaignDetailPage() {
  const params = useParams<{ id: string }>();
  const id = params?.id;
  const { campaignQuery } = useCampaigns();
  const campaign = campaignQuery(id);
  const [search, setSearch] = useState('');
  const pagesQuery = useCampaignPages({ campaignId: id, search });
  const [selectedPage, setSelectedPage] = useState<CrawledPage | null>(null);

  const pages = useMemo(() => pagesQuery.data ?? [], [pagesQuery.data]);

  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-white/5 bg-white/5 p-5">
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-xs text-emerald-200/80 uppercase tracking-[0.16em]">Campaign</p>
            {campaign.isLoading && <p className="text-sm text-slate-300">Loading campaign...</p>}
            {campaign.data && (
              <>
                <h2 className="text-xl font-semibold text-white">{campaign.data.name}</h2>
                <p className="text-sm text-slate-300">{campaign.data.query}</p>
                <div className="mt-2 flex flex-wrap gap-3 text-xs text-slate-200">
                  <span className="rounded-lg border border-white/10 px-2 py-1">
                    Status: <StatusPill status={campaign.data.status} />
                  </span>
                  <span className="rounded-lg border border-white/10 px-2 py-1">
                    Pages: {campaign.data.pages_collected}/{campaign.data.max_pages}
                  </span>
                  <span className="rounded-lg border border-white/10 px-2 py-1">
                    Follow links: {campaign.data.follow_links ? 'Yes' : 'No'}
                  </span>
                </div>
              </>
            )}
            {campaign.isError && (
              <p className="text-sm text-amber-300">Failed: {(campaign.error as Error).message}</p>
            )}
          </div>
          <Link className="text-sm text-emerald-300 hover:underline" href="/campaigns">
            ← Back
          </Link>
        </div>
      </div>

      <div className="rounded-xl border border-white/5 bg-white/5 p-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h3 className="text-lg font-semibold text-white">Crawled Pages</h3>
            <p className="text-sm text-slate-300">Click a row to preview.</p>
          </div>
          <input
            className="w-full max-w-xs rounded-lg border border-white/10 bg-slate-900 px-3 py-2 text-sm text-white focus:border-emerald-400 focus:outline-none"
            placeholder="Search URL or text..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        {pagesQuery.isLoading && <p className="mt-3 text-sm text-slate-300">Loading pages...</p>}
        {pagesQuery.isError && (
          <p className="mt-3 text-sm text-amber-300">Failed to load pages: {(pagesQuery.error as Error).message}</p>
        )}
        {!pages.length && !pagesQuery.isLoading && <p className="mt-3 text-sm text-slate-300">No pages yet.</p>}
        {pages.length > 0 && (
          <div className="mt-3 overflow-x-auto">
            <table className="min-w-full divide-y divide-white/5 text-sm">
              <thead className="bg-white/5 text-left text-slate-200">
                <tr>
                  <th className="px-3 py-2">URL</th>
                  <th className="px-3 py-2">Status</th>
                  <th className="px-3 py-2">HTTP</th>
                  <th className="px-3 py-2">Title</th>
                  <th className="px-3 py-2">Created</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5 text-slate-100">
                {pages.map((p) => (
                  <tr
                    key={p.id}
                    className={`cursor-pointer hover:bg-white/5 ${selectedPage?.id === p.id ? 'bg-white/10' : ''}`}
                    onClick={() => setSelectedPage(p)}
                  >
                    <td className="px-3 py-2 max-w-[340px] truncate text-emerald-200">{p.url}</td>
                    <td className="px-3 py-2">
                      <PageStatusPill status={p.status} />
                    </td>
                    <td className="px-3 py-2 text-slate-200">{p.http_status ?? '-'}</td>
                    <td className="px-3 py-2 text-slate-300">{p.title ?? '-'}</td>
                    <td className="px-3 py-2 text-slate-400">{new Date(p.created_at).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {selectedPage && (
        <div className="rounded-xl border border-white/5 bg-white/5 p-5">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-slate-400">Selected Page</p>
              <h4 className="text-lg font-semibold text-white">{selectedPage.title ?? 'Untitled'}</h4>
              <p className="text-sm text-emerald-200 break-all">{selectedPage.url}</p>
            </div>
            <div className="text-right text-xs text-slate-400">
              <div>Status: <PageStatusPill status={selectedPage.status} /></div>
              <div>HTTP: {selectedPage.http_status ?? '-'}</div>
            </div>
          </div>
          <div className="mt-3 grid gap-3 md:grid-cols-2">
            <div className="rounded-lg border border-white/10 bg-slate-900/70 p-3">
              <p className="text-xs text-slate-400">Text content</p>
              <div className="mt-2 max-h-72 overflow-auto text-xs leading-relaxed text-slate-200 whitespace-pre-wrap">
                {selectedPage.text_content || 'No text captured'}
              </div>
            </div>
            <div className="rounded-lg border border-white/10 bg-slate-900/70 p-3">
              <p className="text-xs text-slate-400">Raw HTML (truncated)</p>
              <div className="mt-2 max-h-72 overflow-auto text-xs text-slate-200">
                {selectedPage.raw_html?.slice(0, 5000) ?? 'No HTML captured'}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function StatusPill({ status }: { status: string }) {
  const color =
    status === 'active'
      ? 'bg-emerald-500/20 text-emerald-100 border-emerald-300/40'
      : status === 'paused'
        ? 'bg-amber-500/20 text-amber-100 border-amber-300/50'
        : status === 'failed'
          ? 'bg-red-500/20 text-red-100 border-red-300/50'
          : 'bg-cyan-500/20 text-cyan-100 border-cyan-300/40';
  return (
    <span
      className={`inline-flex items-center rounded-full border px-3 py-1 text-xs font-semibold capitalize ${color}`}
    >
      {status}
    </span>
  );
}

function PageStatusPill({ status }: { status: string }) {
  const color =
    status === 'success'
      ? 'bg-emerald-500/20 text-emerald-100 border-emerald-300/40'
      : status === 'failed'
        ? 'bg-red-500/20 text-red-100 border-red-300/50'
        : 'bg-slate-500/20 text-slate-100 border-slate-300/50';
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2 py-0.5 text-[11px] font-semibold capitalize ${color}`}
    >
      {status}
    </span>
  );
}
