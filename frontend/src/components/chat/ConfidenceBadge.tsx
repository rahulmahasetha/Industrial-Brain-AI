import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';

export function ConfidenceBadge({ score }: { score?: number | string }) {
  if (score === undefined || score === null) return null;
  
  const numScore = typeof score === 'string' ? parseInt(score, 10) : score;
  if (isNaN(numScore)) return null;

  let variant = 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30';
  let label = 'High';

  if (numScore < 70) {
    variant = 'bg-red-500/15 text-red-400 border-red-500/30';
    label = 'Low';
  } else if (numScore < 90) {
    variant = 'bg-amber-500/15 text-amber-400 border-amber-500/30';
    label = 'Medium';
  }

  return (
    <Badge variant="outline" className={cn(variant)}>
      {label} Confidence — {numScore}%
    </Badge>
  );
}
