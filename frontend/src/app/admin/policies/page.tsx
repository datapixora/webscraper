"use client";

import { useEffect, useMemo, useState } from "react";
import {
  createDomainPolicy,
  DomainPolicy,
  listDomainPolicies,
  updateDomainPolicy,
} from "@/lib/api-client";

type FormState = {
  id?: string;
  domain: string;
  enabled: boolean;
  method: "auto" | "http" | "playwright";
  use_proxy: boolean;
  request_delay_ms: number;
  max_concurrency: number;
  user_agent: string;
  block_resources: boolean;
};

const emptyForm: FormState = {
  id: undefined,
  domain: "",
  enabled: true,
  method: "auto",
  use_proxy: false,
  request_delay_ms: 1000,
  max_concurrency: 2,
  user_agent: "",
  block_resources: true,
};

export default function ScrapePoliciesPage() {
  const [policies, setPolicies] = useState<DomainPolicy[]>([]);
  const [form, setForm] = useState<FormState>(emptyForm);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const editing = useMemo(() => Boolean(form.id), [form.id]);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await listDomainPolicies();
      setPolicies(data);
    } catch (e: any) {
      setError(e?.message || "Failed to load policies");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      const payload = {
        domain: form.domain.trim(),
        enabled: form.enabled,
        method: form.method,
        use_proxy: form.use_proxy,
        request_delay_ms: Number(form.request_delay_ms) || 0,
        max_concurrency: Number(form.max_concurrency) || 1,
        user_agent: form.user_agent.trim() || undefined,
        block_resources: form.block_resources,
      };
      if (editing && form.id) {
        await updateDomainPolicy(form.id, payload);
      } else {
        await createDomainPolicy(payload);
      }
      setForm(emptyForm);
      await load();
    } catch (err: any) {
      setError(err?.message || "Failed to save policy");
    } finally {
      setSaving(false);
    }
  };

  const startEdit = (p: DomainPolicy) => {
    setForm({
      id: p.id,
      domain: p.domain,
      enabled: p.enabled,
      method: p.method,
      use_proxy: p.use_proxy,
      request_delay_ms: p.request_delay_ms,
      max_concurrency: p.max_concurrency,
      user_agent: p.user_agent || "",
      block_resources: p.block_resources,
    });
  };

  const cancelEdit = () => setForm(emptyForm);

  return (
    <div className="space-y-6 p-4">
      <div>
        <h1 className="text-2xl font-semibold text-white">Scrape Policies</h1>
        <p className="text-sm text-slate-300">
          Configure per-domain scraping behavior: method selection, proxy use, throttling, and resource blocking.
        </p>
      </div>

      <form
        onSubmit={handleSubmit}
        className="space-y-3 rounded-lg border border-white/10 bg-white/5 p-4 shadow-lg"
      >
        <div className="grid gap-3 md:grid-cols-2">
          <div className="space-y-1">
            <label className="text-sm text-slate-200">Domain</label>
            <input
              className="w-full rounded-md border border-white/10 bg-slate-900 px-3 py-2 text-sm text-white"
              value={form.domain}
              onChange={(e) => setForm({ ...form, domain: e.target.value })}
              placeholder="example.com"
              required={!editing}
              disabled={editing}
            />
          </div>
          <div className="space-y-1">
            <label className="text-sm text-slate-200">Method</label>
            <select
              className="w-full rounded-md border border-white/10 bg-slate-900 px-3 py-2 text-sm text-white"
              value={form.method}
              onChange={(e) => setForm({ ...form, method: e.target.value as FormState["method"] })}
            >
              <option value="auto">Auto (HTTP then fallback)</option>
              <option value="http">HTTP only</option>
              <option value="playwright">Playwright (browser)</option>
            </select>
          </div>
          <div className="space-y-1">
            <label className="text-sm text-slate-200">Request delay (ms)</label>
            <input
              type="number"
              min={0}
              className="w-full rounded-md border border-white/10 bg-slate-900 px-3 py-2 text-sm text-white"
              value={form.request_delay_ms}
              onChange={(e) => setForm({ ...form, request_delay_ms: Number(e.target.value) })}
            />
          </div>
          <div className="space-y-1">
            <label className="text-sm text-slate-200">Max concurrency</label>
            <input
              type="number"
              min={1}
              className="w-full rounded-md border border-white/10 bg-slate-900 px-3 py-2 text-sm text-white"
              value={form.max_concurrency}
              onChange={(e) => setForm({ ...form, max_concurrency: Number(e.target.value) })}
            />
          </div>
          <div className="space-y-1">
            <label className="text-sm text-slate-200">User agent (optional)</label>
            <input
              className="w-full rounded-md border border-white/10 bg-slate-900 px-3 py-2 text-sm text-white"
              value={form.user_agent}
              onChange={(e) => setForm({ ...form, user_agent: e.target.value })}
              placeholder="Mozilla/5.0 ..."
            />
          </div>
          <div className="space-y-1">
            <label className="text-sm text-slate-200">Flags</label>
            <div className="flex flex-col gap-2 text-sm text-slate-200">
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={form.enabled}
                  onChange={(e) => setForm({ ...form, enabled: e.target.checked })}
                />
                Enabled
              </label>
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={form.use_proxy}
                  onChange={(e) => setForm({ ...form, use_proxy: e.target.checked })}
                />
                Use proxy
              </label>
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={form.block_resources}
                  onChange={(e) => setForm({ ...form, block_resources: e.target.checked })}
                />
                Block heavy resources (Playwright)
              </label>
            </div>
          </div>
        </div>

        {error && <p className="text-sm text-amber-300">{error}</p>}
        <div className="flex gap-2">
          <button
            type="submit"
            disabled={saving}
            className="rounded-md bg-emerald-600 px-3 py-2 text-sm font-semibold text-white hover:bg-emerald-500 disabled:opacity-60"
          >
            {editing ? "Update policy" : "Create policy"}
          </button>
          {editing && (
            <button
              type="button"
              className="text-sm text-slate-300 underline"
              onClick={cancelEdit}
            >
              Cancel
            </button>
          )}
        </div>
      </form>

      <div className="space-y-2">
        <h2 className="text-lg font-semibold text-white">Existing policies</h2>
        {loading && <p className="text-sm text-slate-300">Loading...</p>}
        {!loading && policies.length === 0 && <p className="text-sm text-slate-300">No policies yet.</p>}
        <div className="space-y-2">
          {policies.map((p) => (
            <div
              key={p.id}
              className="flex flex-col gap-2 rounded-lg border border-white/10 bg-white/5 p-3 md:flex-row md:items-start md:justify-between"
            >
              <div className="space-y-1 text-sm">
                <div className="flex items-center gap-2">
                  <p className="font-semibold text-white">{p.domain}</p>
                  <span
                    className={`rounded-full px-2 py-0.5 text-xs ${
                      p.enabled ? "bg-emerald-500/20 text-emerald-100" : "bg-slate-600/30 text-slate-200"
                    }`}
                  >
                    {p.enabled ? "enabled" : "disabled"}
                  </span>
                </div>
                <p className="text-slate-300">Method: {p.method}</p>
                <p className="text-slate-300">Proxy: {p.use_proxy ? "on" : "off"}</p>
                <p className="text-slate-300">Delay: {p.request_delay_ms} ms · Concurrency: {p.max_concurrency}</p>
                {p.user_agent && <p className="text-slate-300">UA: {p.user_agent}</p>}
                <p className="text-slate-300">Block resources: {p.block_resources ? "yes" : "no"}</p>
                <p className="text-[11px] text-slate-500">Updated: {new Date(p.updated_at).toLocaleString()}</p>
              </div>
              <div className="flex gap-2">
                <button
                  className="rounded-md border border-white/20 px-3 py-1 text-xs text-slate-100 hover:border-emerald-300/60"
                  onClick={() => startEdit(p)}
                >
                  Edit
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
