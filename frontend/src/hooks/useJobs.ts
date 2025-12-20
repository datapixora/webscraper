'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { createJob, createJobsBatch, getJob, getJobs, Job } from '@/lib/api-client';

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

  const createBatchJobsMutation = useMutation({
    mutationFn: async (payload: {
      project_id?: string;
      topic_id?: string;
      urls?: string[];
      name_prefix?: string;
      allow_duplicates?: boolean;
    }) => {
      if (!payload?.project_id) {
        throw new Error('Project is required to create jobs.');
      }
      if (!payload?.urls || payload.urls.length === 0) {
        throw new Error('Provide at least one URL to create jobs.');
      }
      return createJobsBatch({
        project_id: payload.project_id,
        topic_id: payload.topic_id,
        urls: payload.urls,
        name_prefix: payload.name_prefix,
        allow_duplicates: payload.allow_duplicates,
      });
    },
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

  return { jobsQuery, createJobMutation, createBatchJobsMutation, jobQuery };
}
