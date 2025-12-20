"use client";

import { useEffect, useState } from "react";
import { createDomainPolicy, DomainPolicy, listDomainPolicies, updateDomainPolicy } from "@/lib/api-client";

type FormState = {
  domain: string;
  enabled: boolean;
  configText: string;
  editingId?: string;
};

const emptyForm: FormState = {
  domain: "",
  enabled: true,
  configText: JSON.stringify(
    {
      concurrency: 1,
      delay_min_ms: 1000,
      delay_max_ms: 2500,
      retries: 2,
      timeout_s: 30,
      method_preference: "http_first",
      proxy_policy: "auto_from_env",
    },
    null,
    2,
  ),
};

export default function DomainPoliciesPage() {
  const [policies, setPolicies] = useState<DomainPolicy[]>([]);
  const [form, setForm] = useState<FormState>(emptyForm);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    setError(null);
    try {
      const data = await listDomainPolicies();
      setPolicies(data);
    } catch (e: any) {
      setError(e.message || "Failed to load policies");
    }
  };

  useEffect(() => {
    load();
  }, []);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const parsed = form.configText ? JSON.parse(form.configText) : {};
      if (form.editingId) {
        await updateDomainPolicy(form.editingId, { enabled: form.enabled, config: parsed });
      } else {
        await createDomainPolicy({ domain: form.domain, enabled: form.enabled, config: parsed });
      }
      setForm(emptyForm);
      await load();
    } catch (err: any) {
      setError(err.message || "Failed to save policy");
    } finally {
      setLoading(false);
    }
  };

  const startEdit = (p: DomainPolicy) => {
    setForm({
      domain: p.domain,
      enabled: p.enabled,
      configText: JSON.stringify(p.config || {}, null, 2),
      editingId: p.id,
    });
  };

  return (
    <div className="space-y-6 p-4">
      <div>
        <h1 className="text-2xl font-semibold text-white">Domain Policies</h1>
        <p className="text-sm text-slate-300">
          Admin-only: throttle, proxy, and method preferences per domain. Overrides apply when domain matches the job URL.
        </p>
      </div>

      <form onSubmit={onSubmit} className="space-y-3 rounded-lg border border-white/10 bg-white/5 p-4">
        <div className="flex flex-col gap-2">
          <label className="text-sm text-slate-200">Domain</label>
          <input
            className="rounded-md border border-white/10 bg-slate-900 px-3 py-2 text-sm text-white"
            value={form.domain}
            onChange={(e) => setForm({ ...form, domain: e.target.value })}
            placeholder="example.com"
            required={!form.editingId}
            disabled={!!form.editingId}
          />
        </div>
        <label className="flex items-center gap-2 text-sm text-slate-200">
          <input
            type="checkbox"
            checked={form.enabled}
            onChange={(e) => setForm({ ...form, enabled: e.target.checked })}
          />
          Enabled
        </label>
        <div className="flex flex-col gap-2">
          <label className="text-sm text-slate-200">Config (JSON)</label>
          <textarea
            className="min-h-[160px] rounded-md border border-white/10 bg-slate-900 px-3 py-2 text-sm text-white"
            value={form.configText}
            onChange={(e) => setForm({ ...form, configText: e.target.value })}
          />
        </div>
        {error && <p className="text-sm text-amber-300">{error}</p>}
        <div className="flex gap-2">
          <button
            type="submit"
            disabled={loading}
            className="rounded-md bg-emerald-600 px-3 py-2 text-sm font-semibold text-white hover:bg-emerald-500 disabled:opacity-60"
          >
            {form.editingId ? "Update policy" : "Create policy"}
          </button>
          {form.editingId && (
            <button
              type="button"
              className="text-sm text-slate-300 underline"
              onClick={() => setForm(emptyForm)}
            >
              Cancel edit
            </button>
          )}
        </div>
      </form>

      <div className="space-y-2">
        <h2 className="text-lg font-semibold text-white">Existing policies</h2>
        {policies.length === 0 && <p className="text-sm text-slate-300">No policies yet.</p>}
        <div className="space-y-2">
          {policies.map((p) => (
            <div
              key={p.id}
              className="flex items-start justify-between gap-3 rounded-lg border border-white/10 bg-white/5 p-3"
            >
              <div className="space-y-1">
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
                <pre className="max-h-40 overflow-auto rounded bg-slate-900/80 p-2 text-xs text-slate-200">
                  {JSON.stringify(p.config || {}, null, 2)}
                </pre>
              </div>
              <button
                className="rounded-md border border-white/20 px-3 py-1 text-xs text-slate-100 hover:border-emerald-300/60"
                onClick={() => startEdit(p)}
              >
                Edit
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
