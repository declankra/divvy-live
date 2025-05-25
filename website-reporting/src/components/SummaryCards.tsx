import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { DPIResponse } from '@/types/dpi';
import { formatDistanceToNow } from 'date-fns';
import { BarChart3, Clock, TrendingUp } from 'lucide-react';

interface SummaryCardsProps {
  data: DPIResponse;
}

export default function SummaryCards({ data }: SummaryCardsProps) {
  const { metadata } = data;
  
  const timeAgo = formatDistanceToNow(new Date(metadata.last_updated), {
    addSuffix: true,
  });

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      {/* Total Stations Card */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium text-gray-600">
            Total Stations
          </CardTitle>
          <BarChart3 className="h-4 w-4 text-blue-600" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-gray-900">
            {metadata.total_stations.toLocaleString()}
          </div>
          <p className="text-xs text-gray-500 mt-1">
            Active Divvy stations
          </p>
        </CardContent>
      </Card>

      {/* Top DPI Card */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium text-gray-600">
            Highest DPI
          </CardTitle>
          <TrendingUp className="h-4 w-4 text-red-600" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-red-600">
            {metadata.top_dpi.toFixed(3)}
          </div>
          <p className="text-xs text-gray-500 mt-1">
            Most urgent station
          </p>
        </CardContent>
      </Card>

      {/* Last Updated Card */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium text-gray-600">
            Last Updated
          </CardTitle>
          <Clock className="h-4 w-4 text-green-600" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-green-600">
            {timeAgo}
          </div>
          <p className="text-xs text-gray-500 mt-1">
            {new Date(metadata.last_updated).toLocaleString()}
          </p>
        </CardContent>
      </Card>
    </div>
  );
} 