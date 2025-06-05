'use client';


import SummaryCards from '../components/SummaryCards';
import StationRankingsTable from '../components/StationRankingsTable';
import DPIScatterPlot from '../components/DPIScatterPlot';
import Footer from '../components/Footer';
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
            🚲 Divvy Live: Dock Pressure Index Dashboard
          </h1>
          <p className="text-gray-600">
            Real-time station analysis and DPI (Dock Priority Index) rankings
          </p>
          <div className="mt-3">
            <a 
              href="/Divvy-Bike-Business-Case-Review.pdf" 
              target="_blank" 
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 text-blue-600 hover:text-blue-800 font-medium underline"
            >
              📄 View the Business Case Report
            </a>
          </div>
        </div>

        {/* Project Context & Purpose */}
        <div className="mb-8">
          <Card className="bg-blue-50 border-blue-200">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-blue-900">
                🤔 What is this?
              </CardTitle>
            </CardHeader>
            <CardContent className="text-blue-800">
              <p className="mb-4">
                <strong>The Question:</strong> Which Divvy bike station needs more racks?
              </p>
              <p className="mb-4">
                As a curious Chicago resident who bikes everywhere, I&apos;ve always wondered which stations are truly overwhelmed and would benefit from additional docks. This dashboard answers that question using real data!
              </p>
              <div className="bg-white/50 rounded-lg p-4 mb-4">
                <h4 className="font-semibold mb-2">How we measure &quot;dock pressure&quot;:</h4>
                <ul className="space-y-2 text-sm">
                  <li><strong>🚲 Net bike accumulation:</strong> Stations that collect more bikes than they release</li>
                  <li><strong>⏰ Time spent full:</strong> How often riders actually hit a &quot;no docks available&quot; wall</li>
                  <li><strong>📊 DPI Score:</strong> Combines both metrics - higher score = stronger case for more racks</li>
                </ul>
              </div>
              <p className="text-sm mb-2">
                <strong>Data sources:</strong> Live GBFS feeds (updated every 20 minutes) + 12 months of historical trip data from Chicago&apos;s Open Data Portal
              </p>
              <p className="text-xs">
                <a 
                  href="https://github.com/declankra/divvy-live" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-blue-600 hover:text-blue-800 underline"
                >
                  📂 View project source code on GitHub
                </a>
              </p>
            </CardContent>
          </Card>
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

        {/* Data Info */}
        <div className="text-center text-sm text-gray-500 mb-8">
          <p>
            Data updated: {new Date(data.metadata.last_updated).toLocaleString()}
          </p>
          <p>
            Total stations: {data.metadata.total_stations} | 
            Top DPI: {data.metadata.top_dpi.toFixed(3)} ({data.metadata.top_station_name})
          </p>
        </div>
      </div>
      
      <Footer />
    </div>
  );
}
