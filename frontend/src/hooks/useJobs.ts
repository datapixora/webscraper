'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { createJob, getJob, getJobs, Job } from '@/lib/api-client';

export function useJobs() {
  const queryClient = useQueryClient();
  const jobsQuery = useQuery<Job[]>({
    queryKey: ['jobs'],
    queryFn: getJobs,
  });

  const createJobMutation = useMutation({
    mutationFn: createJob,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
    },
  });

  const jobQuery = (jobId: string) =>
    useQuery<Job>({
      queryKey: ['jobs', jobId],
      queryFn: () => getJob(jobId),
      enabled: Boolean(jobId),
    });

  return { jobsQuery, createJobMutation, jobQuery };
}
