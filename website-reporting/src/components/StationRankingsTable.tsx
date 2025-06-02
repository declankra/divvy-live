import { useState, useMemo } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { DPIStation } from '@/types/dpi';
import { ChevronDown, ChevronUp } from 'lucide-react';
import PriorityBadge from './PriorityBadge';

interface StationRankingsTableProps {
  data: DPIStation[];
}

type SortField = 'dpi' | 'pct_full' | 'overflow_per_dock';
type SortDirection = 'asc' | 'desc';

export default function StationRankingsTable({ data }: StationRankingsTableProps) {
  const [sortField, setSortField] = useState<SortField>('dpi');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      // Toggle direction if same field
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      // Set new field with desc as default
      setSortField(field);
      setSortDirection('desc');
    }
  };

  const sortedAndFilteredData = useMemo(() => {
    const sorted = [...data].sort((a, b) => {
      let aValue: number;
      let bValue: number;

      switch (sortField) {
        case 'dpi':
          aValue = a.dpi;
          bValue = b.dpi;
          break;
        case 'pct_full':
          aValue = a.pct_full;
          bValue = b.pct_full;
          break;
        case 'overflow_per_dock':
          aValue = a.overflow_per_dock;
          bValue = b.overflow_per_dock;
          break;
        default:
          return 0;
      }

      if (sortDirection === 'asc') {
        return aValue - bValue;
      } else {
        return bValue - aValue;
      }
    });

    // Return top 20 results
    return sorted.slice(0, 20);
  }, [data, sortField, sortDirection]);

  const SortIcon = ({ field }: { field: SortField }) => {
    if (sortField !== field) {
      return <ChevronDown className="w-4 h-4 text-gray-400 opacity-50" />;
    }
    return sortDirection === 'desc' ? 
      <ChevronDown className="w-4 h-4 text-gray-600" /> : 
      <ChevronUp className="w-4 h-4 text-gray-600" />;
  };

  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-16">Rank</TableHead>
            <TableHead>Station Name</TableHead>
            <TableHead 
              className="text-right cursor-pointer hover:bg-gray-50 select-none"
              onClick={() => handleSort('overflow_per_dock')}
            >
              <div className="flex items-center justify-end gap-1">
                Overflow/Dock
                <SortIcon field="overflow_per_dock" />
              </div>
            </TableHead>
            <TableHead 
              className="text-right cursor-pointer hover:bg-gray-50 select-none"
              onClick={() => handleSort('pct_full')}
            >
              <div className="flex items-center justify-end gap-1">
                % Full
                <SortIcon field="pct_full" />
              </div>
            </TableHead>
            <TableHead 
              className="text-right cursor-pointer hover:bg-gray-50 select-none"
              onClick={() => handleSort('dpi')}
            >
              <div className="flex items-center justify-end gap-1">
                DPI
                <SortIcon field="dpi" />
              </div>
            </TableHead>
            <TableHead className="text-center">Priority</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {sortedAndFilteredData.map((station, index) => (
            <TableRow 
              key={station.station_id}
              className="hover:bg-gray-50 transition-colors"
            >
              <TableCell className="font-medium text-gray-500">
                {index + 1}
              </TableCell>
              <TableCell className="font-medium">
                <div className="max-w-xs">
                  <div className="font-medium text-gray-900 truncate">
                    {station.station_name}
                  </div>
                  <div className="text-xs text-gray-500 font-mono">
                    ID: {station.station_id}
                  </div>
                </div>
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
      
      {sortedAndFilteredData.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          No station data available
        </div>
      )}
      
      {data.length > 20 && (
        <div className="text-center py-2 text-sm text-gray-500 border-t">
          Showing top 20 of {data.length} stations
        </div>
      )}
    </div>
  );
} 