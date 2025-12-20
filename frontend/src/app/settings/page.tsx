'use client';

import { useEffect, useState } from 'react';
import { useSetting } from '@/hooks/useSettings';
import { useProxySettings } from '@/hooks/useProxySettings';

export default function SettingsPage() {
  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-white/5 bg-white/5 p-6">
        <h1 className="text-2xl font-bold text-white mb-2">Settings</h1>
        <p className="text-sm text-slate-300 mb-6">
          Configure application settings including proxy configuration for web scraping.
        </p>

        <div className="space-y-8">
          <SmartProxySettings />
          <hr className="border-white/10" />
          <ProxySettings />
        </div>
      </div>
    </div>
  );
}

function SmartProxySettings() {
  const { settingQuery, updateMutation } = useSetting('smartproxy');

  const [enabled, setEnabled] = useState(false);
  const [host, setHost] = useState('gate.smartproxy.com');
  const [port, setPort] = useState(7000);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [country, setCountry] = useState('');

  // Load existing values when query succeeds
  useEffect(() => {
    if (settingQuery.data?.value) {
      const value = settingQuery.data.value;
      setEnabled(value.enabled ?? false);
      setHost(value.host ?? 'gate.smartproxy.com');
      setPort(value.port ?? 7000);
      setUsername(value.username ?? '');
      setPassword(value.password ?? '');
      setCountry(value.country ?? '');
    }
  }, [settingQuery.data]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    updateMutation.mutate({
      value: {
        enabled,
        host,
        port,
        username,
        password,
        country,
      },
      description: 'SmartProxy configuration for web scraping',
    });
  };

  if (settingQuery.isLoading) {
    return <p className="text-sm text-slate-300">Loading proxy settings...</p>;
  }

  if (settingQuery.isError) {
    return (
      <p className="text-sm text-amber-300">
        Failed to load settings: {(settingQuery.error as Error).message}
      </p>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-white mb-3">SmartProxy Configuration</h2>
        <p className="text-sm text-slate-400 mb-4">
          Configure SmartProxy to route all search and scraping traffic through a proxy server.
          This is useful for bypassing rate limits and accessing geo-restricted content.
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Enable/Disable Toggle */}
          <div className="flex items-center gap-3 p-4 rounded-lg bg-slate-900/50 border border-white/5">
            <input
              type="checkbox"
              id="proxy-enabled"
              checked={enabled}
              onChange={(e) => setEnabled(e.target.checked)}
              className="w-4 h-4 rounded border-white/20 bg-slate-800 text-emerald-500 focus:ring-2 focus:ring-emerald-400 focus:ring-offset-0"
            />
            <label htmlFor="proxy-enabled" className="text-sm font-medium text-white cursor-pointer">
              Enable SmartProxy
            </label>
            <span className="ml-auto text-xs text-slate-400">
              {enabled ? 'Enabled' : 'Disabled'}
            </span>
          </div>

          {/* Proxy Configuration Fields */}
          <div className="space-y-4 pt-2">
            <div className="space-y-1">
              <label className="text-sm font-medium text-slate-200">Proxy Host</label>
              <input
                type="text"
                value={host}
                onChange={(e) => setHost(e.target.value)}
                className="w-full rounded-lg border border-white/10 bg-slate-900 px-3 py-2 text-sm text-white focus:border-emerald-400 focus:outline-none disabled:opacity-50"
                placeholder="gate.smartproxy.com"
                disabled={!enabled}
              />
              <p className="text-xs text-slate-400">SmartProxy server hostname</p>
            </div>

            <div className="space-y-1">
              <label className="text-sm font-medium text-slate-200">Port</label>
              <input
                type="number"
                value={port}
                onChange={(e) => setPort(parseInt(e.target.value) || 7000)}
                className="w-full rounded-lg border border-white/10 bg-slate-900 px-3 py-2 text-sm text-white focus:border-emerald-400 focus:outline-none disabled:opacity-50"
                placeholder="7000"
                disabled={!enabled}
              />
              <p className="text-xs text-slate-400">Default: 7000</p>
            </div>

            <div className="space-y-1">
              <label className="text-sm font-medium text-slate-200">Username</label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full rounded-lg border border-white/10 bg-slate-900 px-3 py-2 text-sm text-white focus:border-emerald-400 focus:outline-none disabled:opacity-50"
                placeholder="Your SmartProxy username"
                disabled={!enabled}
              />
            </div>

            <div className="space-y-1">
              <label className="text-sm font-medium text-slate-200">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full rounded-lg border border-white/10 bg-slate-900 px-3 py-2 text-sm text-white focus:border-emerald-400 focus:outline-none disabled:opacity-50"
                placeholder="Your SmartProxy password"
                disabled={!enabled}
              />
            </div>

            <div className="space-y-1">
              <label className="text-sm font-medium text-slate-200">Country Code (Optional)</label>
              <input
                type="text"
                value={country}
                onChange={(e) => setCountry(e.target.value.toLowerCase())}
                className="w-full rounded-lg border border-white/10 bg-slate-900 px-3 py-2 text-sm text-white focus:border-emerald-400 focus:outline-none disabled:opacity-50"
                placeholder="us, uk, de, etc."
                disabled={!enabled}
                maxLength={2}
              />
              <p className="text-xs text-slate-400">
                Route traffic through a specific country (e.g., us, uk, de)
              </p>
            </div>
          </div>

          {/* Save Button */}
          <div className="pt-2">
            <button
              type="submit"
              disabled={updateMutation.isPending}
              className="w-full rounded-lg bg-emerald-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-400 focus:ring-offset-2 focus:ring-offset-slate-900 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {updateMutation.isPending ? 'Saving...' : 'Save Settings'}
            </button>
          </div>

          {/* Success/Error Messages */}
          {updateMutation.isSuccess && (
            <div className="rounded-lg bg-emerald-500/10 border border-emerald-500/20 px-4 py-3">
              <p className="text-sm text-emerald-400">Settings saved successfully!</p>
            </div>
          )}

          {updateMutation.isError && (
            <div className="rounded-lg bg-red-500/10 border border-red-500/20 px-4 py-3">
              <p className="text-sm text-red-400">
                Failed to save settings: {(updateMutation.error as Error).message}
              </p>
            </div>
          )}
        </form>
      </div>

      {/* Info Section */}
      <div className="rounded-lg bg-blue-500/5 border border-blue-500/10 p-4">
        <h3 className="text-sm font-semibold text-blue-300 mb-2">Bandwidth Optimization</h3>
        <p className="text-xs text-slate-400">
          When SmartProxy is enabled, browser-based scraping automatically blocks images, fonts,
          stylesheets, and analytics scripts to reduce bandwidth usage by up to 70-90%.
        </p>
      </div>

      {/* Warning Section */}
      <div className="rounded-lg bg-amber-500/5 border border-amber-500/10 p-4">
        <h3 className="text-sm font-semibold text-amber-300 mb-2">Important Notes</h3>
        <ul className="text-xs text-slate-400 space-y-1 list-disc list-inside">
          <li>Changes take effect immediately for new scraping jobs</li>
          <li>Proxy credentials are stored securely and never logged</li>
          <li>Database settings override environment variables</li>
          <li>Restart backend if you encounter connection issues after changing settings</li>
        </ul>
      </div>
    </div>
  );
}

function ProxySettings() {
  const { settingsQuery, updateMutation } = useProxySettings();

  const [proxyEnabled, setProxyEnabled] = useState(false);
  const [proxyProvider, setProxyProvider] = useState('smartproxy');
  const [proxyType, setProxyType] = useState('residential');
  const [proxyCountry, setProxyCountry] = useState('us');
  const [proxyStickyEnabled, setProxyStickyEnabled] = useState(false);
  const [proxyStickyTtlSec, setProxyStickyTtlSec] = useState(300);
  const [proxyRotationStrategy, setProxyRotationStrategy] = useState<'per_job' | 'on_failure' | 'per_request'>('per_job');
  const [proxyRetryCount, setProxyRetryCount] = useState(3);
  const [requestDelayMinMs, setRequestDelayMinMs] = useState(500);
  const [requestDelayMaxMs, setRequestDelayMaxMs] = useState(2000);
  const [scrapeMethodPolicy, setScrapeMethodPolicy] = useState<'http' | 'browser' | 'auto'>('auto');

  // Load existing values when query succeeds
  useEffect(() => {
    if (settingsQuery.data) {
      const data = settingsQuery.data;
      setProxyEnabled(data.proxy_enabled ?? false);
      setProxyProvider(data.proxy_provider ?? 'smartproxy');
      setProxyType(data.proxy_type ?? 'residential');
      setProxyCountry(data.proxy_country ?? 'us');
      setProxyStickyEnabled(data.proxy_sticky_enabled ?? false);
      setProxyStickyTtlSec(data.proxy_sticky_ttl_sec ?? 300);
      setProxyRotationStrategy(data.proxy_rotation_strategy ?? 'per_job');
      setProxyRetryCount(data.proxy_retry_count ?? 3);
      setRequestDelayMinMs(data.request_delay_min_ms ?? 500);
      setRequestDelayMaxMs(data.request_delay_max_ms ?? 2000);
      setScrapeMethodPolicy(data.scrape_method_policy ?? 'auto');
    }
  }, [settingsQuery.data]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    updateMutation.mutate({
      proxy_enabled: proxyEnabled,
      proxy_provider: proxyProvider,
      proxy_type: proxyType,
      proxy_country: proxyCountry,
      proxy_sticky_enabled: proxyStickyEnabled,
      proxy_sticky_ttl_sec: proxyStickyTtlSec,
      proxy_rotation_strategy: proxyRotationStrategy,
      proxy_retry_count: proxyRetryCount,
      request_delay_min_ms: requestDelayMinMs,
      request_delay_max_ms: requestDelayMaxMs,
      scrape_method_policy: scrapeMethodPolicy,
    });
  };

  if (settingsQuery.isLoading) {
    return <p className="text-sm text-slate-300">Loading proxy settings...</p>;
  }

  if (settingsQuery.isError) {
    return (
      <p className="text-sm text-amber-300">
        Failed to load settings: {(settingsQuery.error as Error).message}
      </p>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-white mb-3">Advanced Proxy Settings</h2>
        <p className="text-sm text-slate-400 mb-4">
          Configure advanced proxy behavior including rotation, retries, delays, and scraping methods.
        </p>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Enable/Disable Toggle */}
          <div className="flex items-center gap-3 p-4 rounded-lg bg-slate-900/50 border border-white/5">
            <input
              type="checkbox"
              id="advanced-proxy-enabled"
              checked={proxyEnabled}
              onChange={(e) => setProxyEnabled(e.target.checked)}
              className="w-4 h-4 rounded border-white/20 bg-slate-800 text-emerald-500 focus:ring-2 focus:ring-emerald-400 focus:ring-offset-0"
            />
            <label htmlFor="advanced-proxy-enabled" className="text-sm font-medium text-white cursor-pointer">
              Enable Advanced Proxy Features
            </label>
            <span className="ml-auto text-xs text-slate-400">
              {proxyEnabled ? 'Enabled' : 'Disabled'}
            </span>
          </div>

          {/* Proxy Configuration */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1">
              <label className="text-sm font-medium text-slate-200">Proxy Provider</label>
              <input
                type="text"
                value={proxyProvider}
                onChange={(e) => setProxyProvider(e.target.value)}
                className="w-full rounded-lg border border-white/10 bg-slate-900 px-3 py-2 text-sm text-white focus:border-emerald-400 focus:outline-none disabled:opacity-50"
                disabled={!proxyEnabled}
              />
            </div>

            <div className="space-y-1">
              <label className="text-sm font-medium text-slate-200">Proxy Type</label>
              <select
                value={proxyType}
                onChange={(e) => setProxyType(e.target.value)}
                className="w-full rounded-lg border border-white/10 bg-slate-900 px-3 py-2 text-sm text-white focus:border-emerald-400 focus:outline-none disabled:opacity-50"
                disabled={!proxyEnabled}
              >
                <option value="residential">Residential</option>
                <option value="datacenter">Datacenter</option>
                <option value="mobile">Mobile</option>
              </select>
            </div>

            <div className="space-y-1">
              <label className="text-sm font-medium text-slate-200">Country</label>
              <input
                type="text"
                value={proxyCountry}
                onChange={(e) => setProxyCountry(e.target.value.toLowerCase())}
                className="w-full rounded-lg border border-white/10 bg-slate-900 px-3 py-2 text-sm text-white focus:border-emerald-400 focus:outline-none disabled:opacity-50"
                maxLength={2}
                disabled={!proxyEnabled}
              />
              <p className="text-xs text-slate-400">2-letter country code (e.g., us, uk, de)</p>
            </div>

            <div className="space-y-1">
              <label className="text-sm font-medium text-slate-200">Rotation Strategy</label>
              <select
                value={proxyRotationStrategy}
                onChange={(e) => setProxyRotationStrategy(e.target.value as any)}
                className="w-full rounded-lg border border-white/10 bg-slate-900 px-3 py-2 text-sm text-white focus:border-emerald-400 focus:outline-none disabled:opacity-50"
                disabled={!proxyEnabled}
              >
                <option value="per_job">Per Job</option>
                <option value="on_failure">On Failure (403/429/503)</option>
                <option value="per_request">Per Request</option>
              </select>
            </div>
          </div>

          {/* Sticky Sessions */}
          <div className="space-y-3">
            <div className="flex items-center gap-3">
              <input
                type="checkbox"
                id="sticky-enabled"
                checked={proxyStickyEnabled}
                onChange={(e) => setProxyStickyEnabled(e.target.checked)}
                className="w-4 h-4 rounded border-white/20 bg-slate-800 text-emerald-500 focus:ring-2 focus:ring-emerald-400 focus:ring-offset-0"
                disabled={!proxyEnabled}
              />
              <label htmlFor="sticky-enabled" className="text-sm font-medium text-slate-200">
                Enable Sticky Sessions
              </label>
            </div>

            {proxyStickyEnabled && (
              <div className="space-y-1 pl-7">
                <label className="text-sm font-medium text-slate-200">Session TTL (seconds)</label>
                <input
                  type="number"
                  value={proxyStickyTtlSec}
                  onChange={(e) => setProxyStickyTtlSec(parseInt(e.target.value) || 300)}
                  min={0}
                  max={3600}
                  className="w-full rounded-lg border border-white/10 bg-slate-900 px-3 py-2 text-sm text-white focus:border-emerald-400 focus:outline-none disabled:opacity-50"
                  disabled={!proxyEnabled}
                />
                <p className="text-xs text-slate-400">Keep same IP for this duration (0-3600 seconds)</p>
              </div>
            )}
          </div>

          {/* Retry & Delays */}
          <div className="grid grid-cols-3 gap-4">
            <div className="space-y-1">
              <label className="text-sm font-medium text-slate-200">Retry Count</label>
              <input
                type="number"
                value={proxyRetryCount}
                onChange={(e) => setProxyRetryCount(parseInt(e.target.value) || 3)}
                min={0}
                max={10}
                className="w-full rounded-lg border border-white/10 bg-slate-900 px-3 py-2 text-sm text-white focus:border-emerald-400 focus:outline-none disabled:opacity-50"
                disabled={!proxyEnabled}
              />
              <p className="text-xs text-slate-400">Max retries on failure</p>
            </div>

            <div className="space-y-1">
              <label className="text-sm font-medium text-slate-200">Min Delay (ms)</label>
              <input
                type="number"
                value={requestDelayMinMs}
                onChange={(e) => setRequestDelayMinMs(parseInt(e.target.value) || 0)}
                min={0}
                max={60000}
                className="w-full rounded-lg border border-white/10 bg-slate-900 px-3 py-2 text-sm text-white focus:border-emerald-400 focus:outline-none disabled:opacity-50"
                disabled={!proxyEnabled}
              />
              <p className="text-xs text-slate-400">Minimum delay</p>
            </div>

            <div className="space-y-1">
              <label className="text-sm font-medium text-slate-200">Max Delay (ms)</label>
              <input
                type="number"
                value={requestDelayMaxMs}
                onChange={(e) => setRequestDelayMaxMs(parseInt(e.target.value) || 2000)}
                min={0}
                max={60000}
                className="w-full rounded-lg border border-white/10 bg-slate-900 px-3 py-2 text-sm text-white focus:border-emerald-400 focus:outline-none disabled:opacity-50"
                disabled={!proxyEnabled}
              />
              <p className="text-xs text-slate-400">Maximum delay</p>
            </div>
          </div>

          {/* Scrape Method Policy */}
          <div className="space-y-1">
            <label className="text-sm font-medium text-slate-200">Scrape Method Policy</label>
            <select
              value={scrapeMethodPolicy}
              onChange={(e) => setScrapeMethodPolicy(e.target.value as any)}
              className="w-full rounded-lg border border-white/10 bg-slate-900 px-3 py-2 text-sm text-white focus:border-emerald-400 focus:outline-none disabled:opacity-50"
              disabled={!proxyEnabled}
            >
              <option value="auto">Auto (try HTTP, fallback to browser)</option>
              <option value="http">HTTP only (faster, less reliable)</option>
              <option value="browser">Browser only (slower, more reliable)</option>
            </select>
            <p className="text-xs text-slate-400">
              Choose how pages should be scraped. Auto is recommended for best balance.
            </p>
          </div>

          {/* Save Button */}
          <div className="pt-2">
            <button
              type="submit"
              disabled={updateMutation.isPending}
              className="w-full rounded-lg bg-emerald-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-400 focus:ring-offset-2 focus:ring-offset-slate-900 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {updateMutation.isPending ? 'Saving...' : 'Save Advanced Settings'}
            </button>
          </div>

          {/* Success/Error Messages */}
          {updateMutation.isSuccess && (
            <div className="rounded-lg bg-emerald-500/10 border border-emerald-500/20 px-4 py-3">
              <p className="text-sm text-emerald-400">Advanced settings saved successfully!</p>
            </div>
          )}

          {updateMutation.isError && (
            <div className="rounded-lg bg-red-500/10 border border-red-500/20 px-4 py-3">
              <p className="text-sm text-red-400">
                Failed to save settings: {(updateMutation.error as Error).message}
              </p>
            </div>
          )}
        </form>
      </div>

      {/* Info Sections */}
      <div className="grid grid-cols-2 gap-4">
        <div className="rounded-lg bg-blue-500/5 border border-blue-500/10 p-4">
          <h3 className="text-sm font-semibold text-blue-300 mb-2">Rotation Strategies</h3>
          <ul className="text-xs text-slate-400 space-y-1">
            <li><strong>Per Job:</strong> Each job uses same IP throughout</li>
            <li><strong>On Failure:</strong> Rotate only when blocked (403/429/503)</li>
            <li><strong>Per Request:</strong> Every request gets new IP</li>
          </ul>
        </div>

        <div className="rounded-lg bg-purple-500/5 border border-purple-500/10 p-4">
          <h3 className="text-sm font-semibold text-purple-300 mb-2">Sticky Sessions</h3>
          <p className="text-xs text-slate-400">
            When enabled, maintains the same IP address for the configured TTL duration.
            Useful for sites that track session state by IP.
          </p>
        </div>
      </div>
    </div>
  );
}
