import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Badge } from '@/components/ui/badge';
import { Search, BookOpen, FileCheck, Wrench, FileSearch, BarChart, Sparkles, FileText, AlertTriangle, Lightbulb, ExternalLink } from 'lucide-react';
import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

const citationText = (value: any, fallback = 'N/A') => {
  if (value === null || value === undefined || value === '') return fallback;
  return String(value);
};

const citationSection = (item: any) => citationText(item?.section || item?.section_title, '');

const citationConfidenceClass = (confidence: number) => cn(
  'border text-[11px] font-semibold',
  confidence >= 90 ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400' :
  confidence >= 70 ? 'border-amber-500/30 bg-amber-500/10 text-amber-600 dark:text-amber-400' :
  'border-slate-300 bg-slate-500/10 text-slate-600 dark:border-slate-700 dark:text-slate-300'
);

const renderBadgeIfMatch = (text: string, originalChildren: React.ReactNode) => {
  const lowerText = text.toLowerCase().trim();
  let textClass = null;
  if (lowerText === "critical" || lowerText === "high" || lowerText === "high risk" || lowerText === "high severity") {
    textClass = "text-red-600 dark:text-red-400";
  } else if (lowerText === "moderate" || lowerText === "medium" || lowerText === "warning") {
    textClass = "text-orange-600 dark:text-orange-400";
  } else if (lowerText === "low" || lowerText === "low risk" || lowerText === "resolved" || lowerText === "healthy" || lowerText === "stable") {
    textClass = "text-green-600 dark:text-green-400";
  } else if (lowerText === "open" || lowerText === "in progress" || lowerText === "active") {
    textClass = "text-blue-600 dark:text-blue-400";
  }

  if (textClass) {
    return <strong className={`font-bold ${textClass}`}>{originalChildren}</strong>;
  }
  return null;
};

const renderWithBr = (children: React.ReactNode): React.ReactNode => {
  if (typeof children === 'string') {
    return children.split(/<br\s*\/?>/i).map((part, i) => (
      <React.Fragment key={i}>
        {i > 0 && <br />}
        {part}
      </React.Fragment>
    ));
  }
  if (Array.isArray(children)) {
    return children.map((child, i) => <React.Fragment key={i}>{renderWithBr(child)}</React.Fragment>);
  }
  return children;
};

export function MarkdownMessage({ 
  content, 
  intent, 
  equipment,
  confidence,
  citations,
  onOpenCitation,
  isOpeningCitation
}: { 
  content: string; 
  intent?: string; 
  equipment?: string;
  confidence?: number;
  citations?: any[];
  onOpenCitation?: (item: any, index: number) => void;
  isOpeningCitation?: number | null;
}) {
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
    <div className="flex w-full flex-col">
      <div className="px-8 py-6 sm:px-10 sm:py-8">
        <div className="w-full">
        <div className="flex items-center gap-2 mb-4 pb-3 border-b border-border/50 justify-between">
          <div className="flex items-center gap-2">
            <div className="bg-primary/10 p-1.5 rounded-lg">
              <Sparkles className="h-4 w-4 text-primary" />
            </div>
            <h3 className="font-semibold text-foreground text-sm tracking-tight">AI Analysis</h3>
          </div>
          {confidence !== undefined && (
            <Badge variant="outline" className={cn(
              confidence >= 90 ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30' :
              confidence >= 70 ? 'bg-amber-500/15 text-amber-400 border-amber-500/30' :
              'bg-red-500/15 text-red-400 border-red-500/30'
            )}>
              {confidence >= 90 ? 'High' : confidence >= 70 ? 'Medium' : 'Low'} Confidence ({confidence}%)
            </Badge>
          )}
        </div>
        <div className="w-full text-base">
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
              h3: ({node, ...props}) => <h3 className="mb-2 mt-4 text-base font-bold text-foreground" {...props} />,
              p: ({node, children, ...props}) => <p className="mb-4 leading-relaxed text-foreground/90" {...props}>{renderWithBr(children)}</p>,
              ul: ({node, ...props}) => <ul className="mb-5 list-outside list-disc space-y-2 pl-5 text-foreground/90 marker:text-primary/60" {...props} />,
              ol: ({node, ...props}) => <ol className="mb-5 list-outside list-decimal space-y-2 pl-5 text-foreground/90 marker:text-primary/60" {...props} />,
              li: ({node, ...props}) => <li className="pl-1.5 leading-relaxed" {...props} />,
              strong: ({node, children, ...props}) => {
                const text = String(children);
                const badge = renderBadgeIfMatch(text, children);
                if (badge) return badge;
                return <strong className="font-semibold text-foreground" {...props}>{children}</strong>;
              },
              table: ({node, ...props}) => (
                <div className="overflow-x-auto print:overflow-visible my-5 rounded-xl border border-border/60 shadow-sm bg-card">
                  <table className="w-full text-base print:text-[11px] border-collapse" {...props} />
                </div>
              ),
              th: ({node, ...props}) => <th className="bg-muted/60 p-3.5 print:p-2 font-semibold text-left text-foreground border-b border-border/60" {...props} />,
              td: ({node, children, ...props}) => {
                const text = String(children);
                const badge = renderBadgeIfMatch(text, children);
                return (
                  <td className="p-3.5 print:p-2 border-b border-border/40 text-muted-foreground align-middle print:break-words" {...props}>
                    {badge ? badge : renderWithBr(children)}
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
      </div>
      
      {citations && citations.length > 0 && (
        <div className="border-t border-border/40 bg-muted/10 px-8 py-6 sm:px-10">
          <div className="w-full">
          <div className="mb-3 flex items-center justify-between gap-3">
            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              <FileCheck className="h-4 w-4" />
              Source Documents
            </div>
            <Badge variant="outline" className="rounded-md bg-background/70 text-[11px] text-muted-foreground">
              {citations.length} cited
            </Badge>
          </div>
          <div className="grid gap-2">
            {citations.map((item, index) => (
              <div
                key={`${item.document_name || item.title || 'source'}-${index}`}
                className="rounded-lg border border-border/70 bg-background/80 p-3 text-sm shadow-sm transition-colors hover:border-primary/30 hover:bg-background"
              >
                <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                  <div className="flex min-w-0 gap-3">
                    <div className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-md bg-primary/10 text-xs font-semibold text-primary">
                      {index + 1}
                    </div>
                    <div className="min-w-0">
                      <div className="flex min-w-0 flex-wrap items-center gap-2">
                        <FileText className="h-4 w-4 shrink-0 text-muted-foreground" />
                        <span className="break-words font-semibold text-foreground">
                          {citationText(item.document_name || item.title || item.document_id, 'Document')}
                        </span>
                      </div>
                      <div className="mt-2 flex flex-wrap items-center gap-1.5">
                        <Badge variant="outline" className="rounded-md bg-primary/5 text-[11px] text-primary">
                          Page {citationText(item.page_number)}
                        </Badge>
                        {citationSection(item) && (
                          <Badge variant="outline" className="max-w-full rounded-md bg-muted/60 text-[11px] text-muted-foreground">
                            <span className="truncate">Section: {citationSection(item)}</span>
                          </Badge>
                        )}
                        {item.confidence !== undefined && item.confidence !== null && (
                          <Badge variant="outline" className={citationConfidenceClass(Number(item.confidence) || 0)}>
                            {item.confidence}% match
                          </Badge>
                        )}
                      </div>
                      {item.excerpt && (
                        <p className="mt-2 line-clamp-2 text-xs leading-relaxed text-muted-foreground">
                          {item.excerpt}
                        </p>
                      )}
                    </div>
                  </div>
                  {onOpenCitation && item.page_index_id && (
                    <Button
                      variant="outline"
                      size="sm"
                      className="h-8 shrink-0 gap-1.5 rounded-md text-xs"
                      disabled={isOpeningCitation === index}
                      onClick={() => onOpenCitation(item, index)}
                    >
                      <ExternalLink className="h-3.5 w-3.5" />
                      Open Page
                    </Button>
                  )}
                </div>
              </div>
            ))}
          </div>
          </div>
        </div>
      )}

      {uniqueActions.length > 0 && (
        <div className="flex flex-col gap-4 border-t border-border/40 bg-muted/20 px-8 py-5 transition-colors hover:bg-muted/30 sm:flex-row sm:items-center sm:px-10">
          <div className="mx-auto flex w-full max-w-5xl flex-col gap-4 sm:flex-row sm:items-center">
            <div className="flex shrink-0 items-center gap-2 text-xs font-semibold tracking-wider text-primary">
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
        </div>
      )}
    </div>
  );
}
