'use client';

import { useQuery } from '@tanstack/react-query';
import { getJobResult, Result } from '@/lib/api-client';

export function useJobResult(jobId: string | undefined) {
  return useQuery<Result | null>({
    queryKey: ['jobResult', jobId],
    queryFn: async () => {
      if (!jobId) return null;
      try {
        return await getJobResult(jobId);
      } catch (err: any) {
        if (err?.status === 404) {
          return null;
        }
        throw err;
      }
    },
    enabled: Boolean(jobId),
    retry: false,
  });
}
