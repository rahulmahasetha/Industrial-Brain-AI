import re

with open('frontend/src/components/chat/MarkdownMessage.tsx', 'r') as f:
    content = f.read()

# Update imports
imports = """import React from 'react';
import { Badge } from '@/components/ui/badge';
import { AlertTriangle, FileText, Search, BookOpen, FileCheck, Wrench, FileSearch, BarChart } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
"""

content = re.sub(r'import React.*?\nimport { cn } from \'@/lib/utils\';\n', imports, content, flags=re.DOTALL)

# Update component signature and logic
component_start = """export function MarkdownMessage({ content }: { content: string }) {
  if (!content) return null;

  const lines = content.split('\\n');"""

new_component_start = """export function MarkdownMessage({ content, intent, equipment }: { content: string, intent?: string, equipment?: string }) {
  if (!content) return null;

  let lines = content.split('\\n');
  const relatedQuestionsIndex = lines.findIndex(l => l.includes('💡 Related Questions') || l.includes('Related Questions'));
  if (relatedQuestionsIndex !== -1) {
    lines = lines.slice(0, relatedQuestionsIndex);
  }

  const quickActions = [];
  const textLower = content.toLowerCase();
  
  if (intent === 'RCA' || textLower.includes('incident')) {
    quickActions.push({ label: 'View RCA', icon: Search, to: '/rca' });
    quickActions.push({ label: 'View Report', icon: FileText, to: '/documents' });
  }
  if (intent === 'manual_lookup' || intent === 'sop' || textLower.includes('sop') || textLower.includes('manual')) {
    quickActions.push({ label: 'Open Manual', icon: BookOpen, to: '/documents' });
    quickActions.push({ label: 'View SOP', icon: FileCheck, to: '/page-index' });
  }
  if (intent === 'Predictive' || textLower.includes('maintenance') || textLower.includes('inspection')) {
    quickActions.push({ label: 'Maintenance History', icon: Wrench, to: '/assets' });
    quickActions.push({ label: 'Inspection Report', icon: FileSearch, to: '/documents' });
  }
  if (equipment || textLower.includes('asset') || textLower.includes('equipment')) {
    quickActions.push({ label: 'Asset Overview', icon: BarChart, to: '/assets' });
  }
  
  if (quickActions.length === 0) {
     quickActions.push({ label: 'View Report', icon: FileText, to: '/documents' });
     quickActions.push({ label: 'Asset Overview', icon: BarChart, to: '/assets' });
  }
  
  const uniqueActions = Array.from(new Set(quickActions.map(a => a.label)))
    .map(label => quickActions.find(a => a.label === label)!);
"""

content = content.replace(component_start, new_component_start)

# Update return statement
return_stmt = """  return (
    <div className="rounded-2xl border border-border bg-card/80 p-5 shadow-sm text-sm">
      {elements}
    </div>
  );
}"""

new_return_stmt = """  return (
    <div className="rounded-2xl border border-border bg-card/80 shadow-sm text-sm overflow-hidden">
      <div className="p-5">
        {elements}
      </div>
      
      {uniqueActions.length > 0 && (
        <div className="border-t border-border bg-muted/30 px-5 py-4">
          <div className="mb-3 text-xs font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-2">
            <span className="text-amber-500">⚡</span> Quick Actions
          </div>
          <div className="flex flex-wrap gap-2">
            {uniqueActions.map(({ label, icon: Icon, to }) => (
              <Link key={label} to={to}>
                <Button variant="outline" size="sm" className="gap-2 bg-background hover:bg-muted">
                  <Icon className="h-3.5 w-3.5" />
                  {label}
                </Button>
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}"""

content = content.replace(return_stmt, new_return_stmt)

with open('frontend/src/components/chat/MarkdownMessage.tsx', 'w') as f:
    f.write(content)

