'use client';

import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  Cell,
} from 'recharts';
import { DPIStation } from '@/types/dpi';
import { getPriorityLevel, getPriorityColor } from './PriorityBadge';

interface DPIScatterPlotProps {
  data: DPIStation[];
}

interface ChartDataPoint {
  x: number;
  y: number;
  dpi: number;
  station_id: string;
  station_name: string;
  priority: 'HIGH' | 'MEDIUM' | 'LOW';
}

interface TooltipProps {
  active?: boolean;
  payload?: Array<{
    payload: ChartDataPoint;
  }>;
}

const CustomTooltip = ({ active, payload }: TooltipProps) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="bg-white p-3 border rounded-lg shadow-lg">
        <p className="font-semibold text-gray-900">{data.station_name}</p>
        <p className="text-xs text-gray-500 font-mono mb-2">{`ID: ${data.station_id}`}</p>
        <p className="text-sm">{`Overflow/Dock: ${data.x.toFixed(2)}`}</p>
        <p className="text-sm">{`% Time Full: ${data.y.toFixed(1)}%`}</p>
        <p className="text-sm font-semibold">{`DPI: ${data.dpi.toFixed(3)}`}</p>
        <p className="text-sm">
          <span 
            className="inline-block w-3 h-3 rounded-full mr-1"
            style={{ backgroundColor: getPriorityColor(data.priority) }}
          />
          {data.priority} Priority
        </p>
      </div>
    );
  }
  return null;
};

export default function DPIScatterPlot({ data }: DPIScatterPlotProps) {
  // Transform data for the chart
  const chartData: ChartDataPoint[] = data.map(station => ({
    x: station.overflow_per_dock,
    y: station.pct_full * 100, // Convert to percentage
    dpi: station.dpi,
    station_id: station.station_id,
    station_name: station.station_name,
    priority: getPriorityLevel(station.dpi),
  }));

  // Calculate median values for reference lines
  const sortedByX = [...chartData].sort((a, b) => a.x - b.x);
  const sortedByY = [...chartData].sort((a, b) => a.y - b.y);
  const medianX = sortedByX[Math.floor(sortedByX.length / 2)]?.x || 0;
  const medianY = sortedByY[Math.floor(sortedByY.length / 2)]?.y || 50;

  return (
    <div className="w-full">
      {/* Quadrant Legend */}
      <div className="grid grid-cols-2 gap-4 mb-6 text-sm">
        <div className="bg-red-50 p-3 rounded-lg border border-red-200">
          <div className="font-semibold text-red-800 mb-1">🚲 Needs More Racks</div>
          <div className="text-red-600">High overflow + High % full</div>
          <div className="text-xs text-red-500 mt-1">Add docks + increase rebalancing</div>
        </div>
        <div className="bg-blue-50 p-3 rounded-lg border border-blue-200">
          <div className="font-semibold text-blue-800 mb-1">🚐 Needs More Vans</div>
          <div className="text-blue-600">Low overflow + High % full</div>
          <div className="text-xs text-blue-500 mt-1">More frequent rebalancing</div>
        </div>
        <div className="bg-yellow-50 p-3 rounded-lg border border-yellow-200">
          <div className="font-semibold text-yellow-800 mb-1">📊 Needs Usage Boost</div>
          <div className="text-yellow-600">High overflow + Low % full</div>
          <div className="text-xs text-yellow-500 mt-1">Marketing/pricing to increase usage</div>
        </div>
        <div className="bg-green-50 p-3 rounded-lg border border-green-200">
          <div className="font-semibold text-green-800 mb-1">✅ Optimal</div>
          <div className="text-green-600">Low overflow + Low % full</div>
          <div className="text-xs text-green-500 mt-1">Balanced usage and capacity</div>
        </div>
      </div>

      {/* Scatter Plot */}
      <div className="h-96 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <ScatterChart
            data={chartData}
            margin={{
              top: 20,
              right: 20,
              bottom: 60,
              left: 60,
            }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            
            {/* Reference lines for quadrants */}
            <ReferenceLine 
              x={medianX} 
              stroke="#9ca3af" 
              strokeDasharray="5 5"
              label={{ value: "Median Overflow", position: "top" }}
            />
            <ReferenceLine 
              y={medianY} 
              stroke="#9ca3af" 
              strokeDasharray="5 5"
              label={{ value: "Median % Full", position: "left" }}
            />
            
            <XAxis 
              type="number"
              dataKey="x"
              name="Overflow per Dock"
              label={{ 
                value: 'Overflow per Dock', 
                position: 'insideBottom', 
                offset: -10,
                style: { textAnchor: 'middle' }
              }}
              domain={['dataMin - 1', 'dataMax + 1']}
            />
            <YAxis 
              type="number"
              dataKey="y"
              name="% Time Full"
              label={{ 
                value: '% Time Full', 
                angle: -90, 
                position: 'insideLeft',
                style: { textAnchor: 'middle' }
              }}
              domain={[0, 100]}
            />
            
            <Tooltip content={<CustomTooltip />} />
            
            <Scatter dataKey="y" fill="#8884d8">
              {chartData.map((entry, index) => (
                <Cell 
                  key={`cell-${index}`} 
                  fill={getPriorityColor(entry.priority)}
                />
              ))}
            </Scatter>
          </ScatterChart>
        </ResponsiveContainer>
      </div>

      {/* Priority Legend */}
      <div className="flex justify-center gap-6 mt-4 text-sm">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-red-500"></div>
          <span>🔴 High Priority (DPI ≥ 20)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-amber-500"></div>
          <span>🟡 Medium Priority (DPI 5-20)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-emerald-500"></div>
          <span>🟢 Low Priority (DPI &lt; 5)</span>
        </div>
      </div>
    </div>
  );
} 