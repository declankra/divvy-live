import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { DPIStation } from '@/types/dpi';
import PriorityBadge from './PriorityBadge';

interface StationRankingsTableProps {
  data: DPIStation[];
}

export default function StationRankingsTable({ data }: StationRankingsTableProps) {
  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-16">Rank</TableHead>
            <TableHead>Station ID</TableHead>
            <TableHead className="text-right">Overflow/Dock</TableHead>
            <TableHead className="text-right">% Full</TableHead>
            <TableHead className="text-right">DPI</TableHead>
            <TableHead className="text-center">Priority</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {data.map((station, index) => (
            <TableRow 
              key={station.station_id}
              className="hover:bg-gray-50 transition-colors"
            >
              <TableCell className="font-medium text-gray-500">
                {index + 1}
              </TableCell>
              <TableCell className="font-mono text-sm">
                {station.station_id}
              </TableCell>
              <TableCell className="text-right font-mono">
                {station.overflow_per_dock.toFixed(2)}
              </TableCell>
              <TableCell className="text-right font-mono">
                {(station.pct_full * 100).toFixed(1)}%
              </TableCell>
              <TableCell className="text-right font-mono font-semibold">
                {station.dpi.toFixed(3)}
              </TableCell>
              <TableCell className="text-center">
                <PriorityBadge dpi={station.dpi} />
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
      
      {data.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          No station data available
        </div>
      )}
    </div>
  );
} 