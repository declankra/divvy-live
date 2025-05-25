'use client';

import { Suspense } from 'react';
import SummaryCards from '../components/SummaryCards';
import StationRankingsTable from '../components/StationRankingsTable';
import DPIScatterPlot from '../components/DPIScatterPlot';
import { useDPIData } from '@/hooks/useDPIData';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { AlertCircle, Loader2 } from 'lucide-react';

export default function Dashboard() {
  const { data, error, isLoading } = useDPIData();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="flex items-center gap-2">
          <Loader2 className="h-6 w-6 animate-spin" />
          <span className="text-lg">Loading DPI data...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Card className="w-full max-w-md">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-red-600">
              <AlertCircle className="h-5 w-5" />
              Error Loading Data
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-gray-600">
              Failed to load DPI data. Please try refreshing the page.
            </p>
            <p className="text-sm text-gray-500 mt-2">
              Error: {error.message}
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-lg text-gray-600">No data available</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            🚲 Divvy Live Dashboard
          </h1>
          <p className="text-gray-600">
            Real-time station analysis and DPI (Dock Priority Index) rankings
          </p>
        </div>

        {/* Summary Cards */}
        <div className="mb-8">
          <SummaryCards data={data} />
        </div>

        {/* Station Rankings */}
        <div className="mb-8">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                🏆 Station Rankings (Top 20)
              </CardTitle>
            </CardHeader>
            <CardContent>
              <StationRankingsTable data={data.stations.slice(0, 20)} />
            </CardContent>
          </Card>
        </div>

        {/* Scatter Plot Analysis */}
        <div className="mb-8">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                📈 Station Analysis Scatter Plot
              </CardTitle>
              <p className="text-sm text-gray-600">
                Strategic insights: Quadrant analysis for operational decisions
              </p>
            </CardHeader>
            <CardContent>
              <DPIScatterPlot data={data.stations} />
            </CardContent>
          </Card>
        </div>

        {/* Footer */}
        <div className="text-center text-sm text-gray-500">
          <p>
            Data updated: {new Date(data.metadata.last_updated).toLocaleString()}
          </p>
          <p>
            Total stations: {data.metadata.total_stations} | 
            Top DPI: {data.metadata.top_dpi.toFixed(3)}
          </p>
        </div>
      </div>
    </div>
  );
}
