import useSWR from 'swr';
import { DPIResponse } from '@/types/dpi';

const fetcher = async (url: string): Promise<DPIResponse> => {
  const response = await fetch(url);
  
  if (!response.ok) {
    throw new Error(`Failed to fetch DPI data: ${response.status} ${response.statusText}`);
  }
  
  return response.json();
};

export function useDPIData() {
  const { data, error, isLoading, mutate } = useSWR<DPIResponse>(
    '/api/dpi',
    fetcher,
    {
      // 24-hour cache strategy
      refreshInterval: 0, // Disable auto-refresh
      revalidateOnFocus: false,
      revalidateOnReconnect: false,
      dedupingInterval: 24 * 60 * 60 * 1000, // 24 hours
      errorRetryCount: 3,
      errorRetryInterval: 5000,
    }
  );

  return {
    data,
    error,
    isLoading,
    refresh: mutate, // Manual refresh function
  };
} 