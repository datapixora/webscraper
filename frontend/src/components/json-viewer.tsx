'use client';

import dynamic from 'next/dynamic';

const DynamicJsonView = dynamic(
  () => import('json-view-react').then((mod: any) => mod.default || mod.JsonView),
  { ssr: false },
);

type JsonViewerProps = {
  data: unknown;
};

export function JsonViewer({ data }: JsonViewerProps) {
  return (
    <div className="rounded-lg border border-white/10 bg-white/5 p-3">
      <DynamicJsonView data={data} />
    </div>
  );
}
