import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Badge } from '@/components/ui/badge';
import { Search, BookOpen, FileCheck, Wrench, FileSearch, BarChart, Sparkles, FileText, AlertTriangle, Lightbulb } from 'lucide-react';
import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';

const renderBadgeIfMatch = (text: string, originalChildren: React.ReactNode) => {
  const lowerText = text.toLowerCase().trim();
  let badgeProps = null;
  if (lowerText === "critical" || lowerText === "high" || lowerText === "high risk" || lowerText === "high severity") {
    badgeProps = "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300 border-red-200 dark:border-red-800";
  } else if (lowerText === "moderate" || lowerText === "medium" || lowerText === "warning") {
    badgeProps = "bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-300 border-orange-200 dark:border-orange-800";
  } else if (lowerText === "low" || lowerText === "low risk" || lowerText === "resolved" || lowerText === "healthy" || lowerText === "stable") {
    badgeProps = "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300 border-green-200 dark:border-green-800";
  } else if (lowerText === "open" || lowerText === "in progress" || lowerText === "active") {
    badgeProps = "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300 border-blue-200 dark:border-blue-800";
  }

  if (badgeProps) {
    return <span className={`inline-flex items-center justify-center rounded-md border px-2 py-0.5 text-xs font-medium whitespace-nowrap ${badgeProps}`}>{originalChildren}</span>;
  }
  return null;
};

export function MarkdownMessage({ content, intent, equipment }: { content: string, intent?: string, equipment?: string }) {
  if (!content) return null;

  const quickActions: any[] = [];
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
     quickActions.push({ label: 'View RCA', icon: Search, to: '/rca' });
     quickActions.push({ label: 'View Report', icon: FileText, to: '/documents' });
     quickActions.push({ label: 'Maintenance History', icon: Wrench, to: '/assets' });
     quickActions.push({ label: 'Inspection Report', icon: FileSearch, to: '/documents' });
     quickActions.push({ label: 'Asset Overview', icon: BarChart, to: '/assets' });
  }
  
  const uniqueActions = Array.from(new Set(quickActions.map(a => a.label)))
    .map(label => quickActions.find(a => a.label === label)!);

  // Pre-process content to convert document citations like [Manual (Page 2)] into links so our custom 'a' renderer catches it.
  const processedContent = content.replace(/\[([^\]]+?(?:Page|pdf).*?)\](?!\()/gi, '[$1](#citation)');

  return (
    <div className="rounded-2xl border border-primary/10 bg-card shadow-md hover:shadow-lg transition-shadow duration-300 overflow-hidden flex flex-col">
      <div className="p-6 pb-4">
        <div className="flex items-center gap-2 mb-4 pb-3 border-b border-border/50">
          <div className="bg-primary/10 p-1.5 rounded-lg">
            <Sparkles className="h-4 w-4 text-primary" />
          </div>
          <h3 className="font-semibold text-foreground text-sm tracking-tight">AI Analysis</h3>
        </div>
        <div className="text-sm">
          <ReactMarkdown 
            remarkPlugins={[remarkGfm]}
            components={{
              h1: ({node, ...props}) => <h1 className="text-xl font-bold mt-6 mb-4 text-foreground tracking-tight" {...props} />,
              h2: ({node, children, ...props}) => {
                const text = String(children);
                const lower = text.toLowerCase();
                
                let Icon = null;
                let bgClass = "";
                let textClass = "text-foreground";
                let borderClass = "border-border/50 border-b pb-2";
                
                if (lower.includes('recommendation') || lower.includes('action')) {
                  Icon = Wrench;
                  bgClass = "bg-blue-500/10";
                  textClass = "text-blue-700 dark:text-blue-400";
                  borderClass = "border-blue-500/20 border";
                } else if (lower.includes('warning') || lower.includes('alert') || lower.includes('critical')) {
                  Icon = AlertTriangle;
                  bgClass = "bg-red-500/10";
                  textClass = "text-red-700 dark:text-red-400";
                  borderClass = "border-red-500/20 border";
                } else if (lower.includes('summary') || lower.includes('finding') || lower.includes('root cause')) {
                  Icon = Lightbulb;
                  bgClass = "bg-indigo-500/10";
                  textClass = "text-indigo-700 dark:text-indigo-400";
                  borderClass = "border-indigo-500/20 border";
                } else if (lower.includes('source') || lower.includes('reference') || lower.includes('document')) {
                  Icon = BookOpen;
                  bgClass = "bg-emerald-500/10";
                  textClass = "text-emerald-700 dark:text-emerald-400";
                  borderClass = "border-emerald-500/20 border";
                }

                if (Icon) {
                  return (
                    <div className={`mt-6 mb-4 p-3 rounded-xl flex items-center gap-2.5 shadow-sm ${bgClass} ${borderClass}`}>
                      <div className="bg-background/80 p-1.5 rounded-md shadow-sm">
                        <Icon className={`h-4 w-4 ${textClass}`} />
                      </div>
                      <h2 className={`text-base font-bold m-0 ${textClass}`} {...props}>{children}</h2>
                    </div>
                  );
                }

                return <h2 className="text-base font-bold mt-6 mb-3 pb-2 border-b border-border/50 text-foreground" {...props}>{children}</h2>;
              },
              h3: ({node, ...props}) => <h3 className="text-sm font-bold mt-4 mb-2 text-foreground" {...props} />,
              p: ({node, ...props}) => <p className="mb-3 leading-relaxed text-muted-foreground" {...props} />,
              ul: ({node, ...props}) => <ul className="mb-4 list-disc pl-5 space-y-1.5 text-muted-foreground marker:text-primary/60" {...props} />,
              ol: ({node, ...props}) => <ol className="mb-4 list-decimal pl-5 space-y-1.5 text-muted-foreground marker:text-primary/60" {...props} />,
              li: ({node, ...props}) => <li className="leading-relaxed pl-1" {...props} />,
              strong: ({node, children, ...props}) => {
                const text = String(children);
                const badge = renderBadgeIfMatch(text, children);
                if (badge) return badge;
                return <strong className="font-semibold text-foreground" {...props}>{children}</strong>;
              },
              table: ({node, ...props}) => (
                <div className="overflow-x-auto my-5 rounded-xl border border-border/60 shadow-sm bg-card">
                  <table className="w-full text-sm border-collapse" {...props} />
                </div>
              ),
              th: ({node, ...props}) => <th className="bg-muted/60 p-3.5 font-semibold text-left text-foreground border-b border-border/60" {...props} />,
              td: ({node, children, ...props}) => {
                const text = String(children);
                const badge = renderBadgeIfMatch(text, children);
                return (
                  <td className="p-3.5 border-b border-border/40 text-muted-foreground align-middle" {...props}>
                    {badge ? badge : children}
                  </td>
                );
              },
              tr: ({node, ...props}) => <tr className="even:bg-muted/20 hover:bg-muted/40 transition-colors" {...props} />,
              blockquote: ({node, ...props}) => (
                <blockquote className="bg-primary/5 border-l-4 border-primary/60 p-4 rounded-r-xl italic my-5 text-foreground/90 shadow-sm" {...props} />
              ),
              a: ({node, ...props}) => {
                const childrenArray = props.children as any[];
                if (props.href === '#citation' || (childrenArray && childrenArray.length > 0 && typeof childrenArray[0] === 'string' && childrenArray[0].includes('Page'))) {
                  return (
                    <Badge variant="outline" className="mx-1 bg-primary/10 text-primary border-primary/20 text-[10px] inline-flex items-center gap-1 rounded-md px-1.5 py-0.5 cursor-pointer hover:bg-primary/20 transition-colors shadow-sm">
                      <FileText className="h-3 w-3" />
                      {props.children}
                    </Badge>
                  );
                }
                return <a className="text-primary hover:underline font-medium" {...props} />;
              }
            }}
          >
            {processedContent}
          </ReactMarkdown>
        </div>
      </div>
      
      {uniqueActions.length > 0 && (
        <div className="border-t border-border/40 bg-muted/20 px-6 py-4 flex flex-col sm:flex-row items-start sm:items-center gap-4 transition-colors hover:bg-muted/30">
          <div className="text-xs font-semibold tracking-wider text-primary flex items-center gap-2 shrink-0">
            <span className="text-primary/80">⚡</span> Quick Actions
          </div>
          <div className="flex flex-wrap gap-2">
            {uniqueActions.map(({ label, icon: Icon, to }) => (
              <Link key={label} to={to}>
                <Button variant="outline" size="sm" className="gap-2 bg-background hover:bg-muted hover:border-primary/40 rounded-lg text-xs h-8 border-border/60 shadow-sm transition-all">
                  <Icon className="h-3.5 w-3.5 text-primary/70" />
                  <span className="text-foreground font-medium">{label}</span>
                </Button>
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
