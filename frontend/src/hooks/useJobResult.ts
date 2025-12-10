'use client';

import { useQuery } from '@tanstack/react-query';
import { getJobResult, Result } from '@/lib/api-client';

export function useJobResult(jobId: string | undefined) {
  return useQuery<Result>({
    queryKey: ['jobResult', jobId],
    queryFn: () => getJobResult(jobId as string),
    enabled: Boolean(jobId),
  });
}
