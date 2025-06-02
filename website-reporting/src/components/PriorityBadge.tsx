import { Badge } from '@/components/ui/badge';

interface PriorityBadgeProps {
  dpi: number;
}

export function getPriorityLevel(dpi: number): 'HIGH' | 'MEDIUM' | 'LOW' {
  if (dpi >= 10) return 'HIGH';
  if (dpi >= 5) return 'MEDIUM';
  return 'LOW';
}

export function getPriorityColor(priority: 'HIGH' | 'MEDIUM' | 'LOW'): string {
  switch (priority) {
    case 'HIGH':
      return '#ef4444'; // red-500
    case 'MEDIUM':
      return '#f59e0b'; // amber-500
    case 'LOW':
      return '#10b981'; // emerald-500
  }
}

export default function PriorityBadge({ dpi }: PriorityBadgeProps) {
  const priority = getPriorityLevel(dpi);
  
  const badgeVariant = priority === 'HIGH' 
    ? 'destructive' 
    : priority === 'MEDIUM' 
    ? 'secondary' 
    : 'secondary';

  const emoji = priority === 'HIGH' ? '🔴' : priority === 'MEDIUM' ? '🟡' : '🟢';

  return (
    <Badge variant={badgeVariant} className="font-medium">
      {emoji} {priority}
    </Badge>
  );
} 