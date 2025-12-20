"use client";

import { useState } from "react";
import {
  motor3dCreateJobs,
  motor3dDiscover,
  motor3dListProducts,
  motor3dParse,
} from "@/lib/api-client";

export default function Motor3DPage() {
  const [sitemapUrl, setSitemapUrl] = useState("https://motor3dmodel.ir/wp-sitemap.xml");
  const [urlPrefix, setUrlPrefix] = useState("https://motor3dmodel.ir/product/");
  const [urls, setUrls] = useState<string[]>([]);
  const [discovering, setDiscovering] = useState(false);
  const [creating, setCreating] = useState(false);
  const [parsing, setParsing] = useState(false);
  const [parseUrl, setParseUrl] = useState("");
  const [parseResult, setParseResult] = useState<any>(null);
  const [projectId, setProjectId] = useState("");
  const [products, setProducts] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);

  const handleDiscover = async () => {
    setDiscovering(true);
    setError(null);
    try {
      const res = await motor3dDiscover({ sitemap_url: sitemapUrl, url_prefix: urlPrefix });
      setUrls(res.urls);
    } catch (e: any) {
      setError(e?.message || "Discover failed");
    } finally {
      setDiscovering(false);
    }
  };

  const handleCreateJobs = async () => {
    if (!projectId) {
      setError("Set a project id");
      return;
    }
    setCreating(true);
    setError(null);
    try {
      const res = await motor3dCreateJobs({ project_id: projectId, urls });
      setError(`Created ${res.created}, Rejected ${res.rejected.length}`);
    } catch (e: any) {
      setError(e?.message || "Create jobs failed");
    } finally {
      setCreating(false);
    }
  };

  const handleParse = async () => {
    setParsing(true);
    setError(null);
    try {
      const res = await motor3dParse({ url: parseUrl });
      setParseResult(res);
    } catch (e: any) {
      setError(e?.message || "Parse failed");
    } finally {
      setParsing(false);
    }
  };

  const loadProducts = async () => {
    try {
      const res = await motor3dListProducts();
      setProducts(res);
    } catch (e: any) {
      setError(e?.message || "Load products failed");
    }
  };

  return (
    <div className="space-y-6 p-4">
      <div>
        <h1 className="text-2xl font-semibold text-white">Motor3D Products</h1>
        <p className="text-sm text-slate-300">
          Discover product URLs, create scrape jobs, and parse sample pages.
        </p>
      </div>

      <section className="rounded-lg border border-white/10 bg-white/5 p-4 space-y-3">
        <h2 className="text-lg font-semibold text-white">1) Discover product URLs</h2>
        <div className="grid gap-2 md:grid-cols-2">
          <input
            className="rounded-md border border-white/10 bg-slate-900 px-3 py-2 text-sm text-white"
            value={sitemapUrl}
            onChange={(e) => setSitemapUrl(e.target.value)}
          />
          <input
            className="rounded-md border border-white/10 bg-slate-900 px-3 py-2 text-sm text-white"
            value={urlPrefix}
            onChange={(e) => setUrlPrefix(e.target.value)}
          />
        </div>
        <button
          onClick={handleDiscover}
          disabled={discovering}
          className="rounded-md bg-emerald-600 px-3 py-2 text-sm font-semibold text-white hover:bg-emerald-500 disabled:opacity-60"
        >
          {discovering ? "Discovering..." : "Discover"}
        </button>
        <p className="text-sm text-slate-300">Found: {urls.length}</p>
        {urls.length > 0 && (
          <div className="max-h-48 overflow-auto rounded-md border border-white/10 bg-slate-900/80 p-2 text-xs text-slate-200">
            {urls.slice(0, 50).map((u) => (
              <div key={u}>{u}</div>
            ))}
            {urls.length > 50 && <div>... (+{urls.length - 50} more)</div>}
          </div>
        )}
      </section>

      <section className="rounded-lg border border-white/10 bg-white/5 p-4 space-y-3">
        <h2 className="text-lg font-semibold text-white">2) Create jobs</h2>
        <input
          className="w-full rounded-md border border-white/10 bg-slate-900 px-3 py-2 text-sm text-white"
          placeholder="Project ID"
          value={projectId}
          onChange={(e) => setProjectId(e.target.value)}
        />
        <button
          onClick={handleCreateJobs}
          disabled={creating || urls.length === 0}
          className="rounded-md bg-emerald-600 px-3 py-2 text-sm font-semibold text-white hover:bg-emerald-500 disabled:opacity-60"
        >
          {creating ? "Creating..." : "Create jobs for discovered URLs"}
        </button>
      </section>

      <section className="rounded-lg border border-white/10 bg-white/5 p-4 space-y-3">
        <h2 className="text-lg font-semibold text-white">3) Parse sample URL</h2>
        <input
          className="w-full rounded-md border border-white/10 bg-slate-900 px-3 py-2 text-sm text-white"
          placeholder="https://motor3dmodel.ir/product/..."
          value={parseUrl}
          onChange={(e) => setParseUrl(e.target.value)}
        />
        <button
          onClick={handleParse}
          disabled={parsing || !parseUrl}
          className="rounded-md bg-emerald-600 px-3 py-2 text-sm font-semibold text-white hover:bg-emerald-500 disabled:opacity-60"
        >
          {parsing ? "Parsing..." : "Parse"}
        </button>
        {parseResult && (
          <pre className="max-h-64 overflow-auto rounded-md border border-white/10 bg-slate-900/80 p-3 text-xs text-slate-200">
            {JSON.stringify(parseResult, null, 2)}
          </pre>
        )}
      </section>

      <section className="rounded-lg border border-white/10 bg-white/5 p-4 space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-white">Parsed products (latest)</h2>
          <button
            onClick={loadProducts}
            className="rounded-md border border-white/10 bg-white/5 px-3 py-1 text-sm text-slate-100 hover:border-emerald-300/60"
          >
            Refresh
          </button>
        </div>
        {products.length === 0 && <p className="text-sm text-slate-300">None yet.</p>}
        {products.length > 0 && (
          <div className="overflow-auto rounded-md border border-white/10 bg-slate-900/80">
            <table className="min-w-full text-sm">
              <thead className="bg-white/10 text-slate-200">
                <tr>
                  <th className="px-2 py-1 text-left">Title</th>
                  <th className="px-2 py-1 text-left">Price</th>
                  <th className="px-2 py-1 text-left">URL</th>
                  <th className="px-2 py-1 text-left">Tags</th>
                </tr>
              </thead>
              <tbody>
                {products.map((p) => (
                  <tr key={p.url} className="border-t border-white/5">
                    <td className="px-2 py-1 text-white">{p.title}</td>
                    <td className="px-2 py-1 text-slate-200">{p.price_text}</td>
                    <td className="px-2 py-1 text-emerald-200 break-all">{p.url}</td>
                    <td className="px-2 py-1 text-slate-200">{p.tags?.join(", ")}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {error && <p className="text-sm text-amber-300">{error}</p>}
    </div>
  );
}
