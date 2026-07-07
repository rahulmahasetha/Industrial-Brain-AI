import { Sparkles } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';

export function ExecutiveSummary({ 
  summary, 
  agent = 'Enterprise AI Assistant' 
}: { 
  summary?: string; 
  agent?: string; 
}) {
  if (!summary) return null;
  return (
    <Card className="border-primary/30 bg-primary/5">
      <CardContent className="p-4">
        <div className="mb-2 flex items-center gap-2 text-sm font-medium text-primary">
          <Sparkles className="h-4 w-4" />
          {agent}
        </div>
        <h2 className="text-lg font-semibold leading-7">{summary}</h2>
      </CardContent>
    </Card>
  );
}
