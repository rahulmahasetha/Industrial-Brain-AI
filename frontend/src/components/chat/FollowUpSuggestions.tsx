import { Lightbulb } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

export function FollowUpSuggestions({ suggestions, onSelect }: { suggestions?: string[], onSelect?: (s: string) => void }) {
  if (!suggestions || suggestions.length === 0) return null;
  
  return (
    <Card className="border-border/70 bg-card/80 mt-4">
      <CardHeader className="flex flex-row items-center gap-3 space-y-0 pb-3">
        <div className="flex h-9 w-9 items-center justify-center rounded-md bg-primary/10 text-primary">
          <Lightbulb className="h-4 w-4" />
        </div>
        <CardTitle className="text-base">Quick Actions</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex flex-wrap gap-2">
          {suggestions.map((s, index) => (
            <Badge 
              key={index} 
              variant="secondary" 
              className="cursor-pointer hover:bg-primary/20"
              onClick={() => onSelect?.(s)}
            >
              {s}
            </Badge>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
