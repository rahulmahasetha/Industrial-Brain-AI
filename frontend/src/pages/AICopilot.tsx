import { useEffect, useMemo, useRef, useState, type ReactNode } from 'react';
import {
  Activity,
  AlertTriangle,
  Bot,
  BrainCircuit,
  Check,
  CheckCircle2,
  ClipboardCheck,
  Copy,
  ExternalLink,
  FileSearch,
  FileText,
  Gauge,
  History,
  Lightbulb,
  Network,
  Route,
  RefreshCcw,
  Send,
  MessageSquare,
  ShieldCheck,
  Sparkles,
  Download,
  Wrench,
  Trash2,
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { apiClient } from '@/lib/api';
import { cn } from '@/lib/utils';
import { EnterpriseDashboard } from '@/components/chat/EnterpriseDashboard';
import { MarkdownMessage } from '@/components/chat/MarkdownMessage';
import { PrintableReport } from '@/components/chat/PrintableReport';
import { useUser } from '@/contexts/UserContext';

const API_ORIGIN = import.meta.env.VITE_API_URL ? import.meta.env.VITE_API_URL.replace('/api', '') : 'https://industrial-brain-ai-zad4.onrender.com';

async function submitResponseFeedback(messageId: number, rating: number, comment = '') {
  await apiClient.post('/chat/feedback', { message_id: messageId, rating, comment });
}

const sectionIcons: Record<string, any> = {
  asset: Gauge,
  root: AlertTriangle,
  incidents: History,
  maintenance: Wrench,
  inspection: ClipboardCheck,
  manual: FileSearch,
  expert: Lightbulb,
  risk: Activity,
  actions: CheckCircle2,
};

function riskClasses(level?: string) {
  const value = (level || '').toLowerCase();
  if (value.includes('critical')) return 'bg-red-500/15 text-red-400 border-red-500/30';
  if (value.includes('high')) return 'bg-orange-500/15 text-orange-400 border-orange-500/30';
  if (value.includes('medium')) return 'bg-amber-500/15 text-amber-400 border-amber-500/30';
  if (value.includes('low')) return 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30';
  return 'bg-slate-500/15 text-slate-300 border-slate-500/30';
}

function asList(value: any): string[] {
  if (!value) return [];
  if (Array.isArray(value)) return value.filter(Boolean).map(String);
  return [String(value)];
}

function Field({ label, value }: { label: string; value: any }) {
  return (
    <div className="min-w-0">
      <div className="text-[11px] uppercase tracking-wide text-muted-foreground">{label}</div>
      <div className="mt-1 text-sm font-medium break-words">{value || 'N/A'}</div>
    </div>
  );
}

function EnterpriseCard({
  title,
  icon: Icon,
  children,
  className,
}: {
  title: string;
  icon: any;
  children: ReactNode;
  className?: string;
}) {
  return (
    <Card className={cn('border-border/70 bg-card/80', className)}>
      <CardHeader className="flex flex-row items-center gap-3 space-y-0 pb-3">
        <div className="flex h-9 w-9 items-center justify-center rounded-md bg-primary/10 text-primary">
          <Icon className="h-4 w-4" />
        </div>
        <CardTitle className="text-base">{title}</CardTitle>
      </CardHeader>
      <CardContent>{children}</CardContent>
    </Card>
  );
}

function Timeline({ items }: { items: any[] }) {
  if (!items?.length) {
    return <p className="text-sm text-muted-foreground">No timeline available.</p>;
  }
  return (
    <div className="space-y-3">
      {items.map((item, index) => (
        <div key={`${item.date}-${index}`} className="grid grid-cols-[88px_1fr] gap-3 text-sm">
          <div className="text-muted-foreground">{item.date}</div>
          <div className="rounded-md border bg-background/60 p-3">
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-medium">{item.title}</span>
              <Badge variant="outline" className={riskClasses(item.severity)}>{item.severity || 'N/A'}</Badge>
            </div>
            <p className="mt-1 text-muted-foreground">{item.root_cause}</p>
          </div>
        </div>
      ))}
    </div>
  );
}

// ── Applicable Equipment Badges ───────────────────────────────────────────────
function ApplicableEquipmentBadges({ equipment }: { equipment: string[] }) {
  if (!equipment?.length) return <span className="text-sm text-muted-foreground">N/A</span>;
  const colorMap: Record<string, string> = {
    Pump: 'bg-blue-500/15 text-blue-400 border-blue-500/30',
    Motor: 'bg-violet-500/15 text-violet-400 border-violet-500/30',
    Compressor: 'bg-amber-500/15 text-amber-400 border-amber-500/30',
    Boiler: 'bg-red-500/15 text-red-400 border-red-500/30',
    Cooling: 'bg-cyan-500/15 text-cyan-400 border-cyan-500/30',
  };
  return (
    <div className="flex flex-wrap gap-2">
      {equipment.map((eq) => {
        const key = Object.keys(colorMap).find((k) => eq.startsWith(k)) ?? '';
        return (
          <Badge key={eq} variant="outline" className={cn(colorMap[key] ?? 'bg-slate-500/15 text-slate-400 border-slate-500/30')}>
            {eq}
          </Badge>
        );
      })}
      {equipment.length > 1 && (
        <span className="self-center text-xs text-muted-foreground">Applies to {equipment.length} assets</span>
      )}
    </div>
  );
}



// ── SOP Card ──────────────────────────────────────────────────────────────────
function SOPCard({
  messageId,
  procedure,
  route,
  evidence,
  onOpenCitation,
  isOpeningCitation,
  onQuickAction,
}: {
  messageId?: number;
  procedure: any;
  route: any;
  evidence: any[];
  onOpenCitation: (item: any, index: number) => void;
  isOpeningCitation: number | null;
  onQuickAction?: (action: string) => void;
  suggestions?: string[];
}) {
  const confidence: number = procedure.confidence ?? 0;
  const contentStatus: string = procedure.content_status ?? 'complete';
  const isPartial = contentStatus === 'partial';
  const isNotFound = contentStatus === 'not_found';

  const confidenceBadgeCls =
    confidence >= 90
      ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30'
      : confidence >= 70
        ? 'bg-amber-500/15 text-amber-400 border-amber-500/30'
        : 'bg-red-500/15 text-red-400 border-red-500/30';
  const confidenceLabel = confidence >= 90 ? 'High' : confidence >= 70 ? 'Medium' : 'Low';

  const steps: string[] = asList(procedure.step_by_step_instructions);
  const warnings: string[] = [...asList(procedure.warnings), ...asList(procedure.safety_checks)].slice(0, 6);
  const criteria: string[] = asList(procedure.completion_criteria);
  const prereqs: string[] = asList(procedure.prerequisites);
  const ppe: string[] = asList(procedure.required_ppe);
  const [feedbackSubmitted, setFeedbackSubmitted] = useState(false);
  const [feedbackRating, setFeedbackRating] = useState<number | null>(null);

  const handleFeedback = async (rating: number) => {
    if (feedbackSubmitted || !messageId) return;
    await submitResponseFeedback(messageId, rating);
    setFeedbackRating(rating);
    setFeedbackSubmitted(true);
  };

  return (
    <div className="w-full space-y-4">
      {/* ── Header ── */}
      <Card className="border-primary/30 bg-primary/5">
        <CardContent className="space-y-3 p-4">
          <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
            <div className="min-w-0">
              <div className="mb-1 flex items-center gap-2 text-sm font-medium text-primary">
                <Sparkles className="h-4 w-4" />
                {route.agent ?? 'SOP Agent'}
              </div>
              <h2 className="text-lg font-semibold leading-7">
                {procedure.sop_name ?? procedure.relevant_procedure ?? 'Standard Operating Procedure'}
              </h2>
              {procedure.purpose && (
                <p className="mt-1 text-sm text-muted-foreground">{procedure.purpose}</p>
              )}
            </div>
            <div className="flex shrink-0 flex-wrap gap-2">
              {route.label && <Badge variant="outline">{route.label}</Badge>}
              <Badge variant="outline" className={confidenceBadgeCls}>
                {confidenceLabel} — {confidence}%
              </Badge>
            </div>
          </div>

          <div>
            <div className="mb-1.5 text-xs font-medium uppercase tracking-wide text-muted-foreground">
              Applicable Equipment
            </div>
            <ApplicableEquipmentBadges equipment={procedure.applicable_equipment ?? []} />
          </div>

          {isPartial && (
            <div className="flex items-center gap-2 rounded-md border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-sm text-amber-400">
              <AlertTriangle className="h-4 w-4 shrink-0" />
              Procedure document found. Detailed content is partially indexed.
            </div>
          )}
        </CardContent>
      </Card>

      {/* ── Prerequisites + Required PPE ── */}
      <div className="grid gap-4 lg:grid-cols-2">
        <div className="rounded-md border bg-card/80 p-4">
          <div className="mb-3 flex items-center gap-2 text-sm font-semibold">
            <ClipboardCheck className="h-4 w-4 text-primary" /> Prerequisites
          </div>
          <ul className="space-y-2 text-sm text-muted-foreground">
            {prereqs.map((item, i) => (
              <li key={i} className="flex gap-2">
                <span className="mt-0.5 shrink-0 text-primary">•</span>{item}
              </li>
            ))}
          </ul>
        </div>
        <div className="rounded-md border bg-card/80 p-4">
          <div className="mb-3 flex items-center gap-2 text-sm font-semibold">
            <ShieldCheck className="h-4 w-4 text-primary" /> Required PPE
          </div>
          <ul className="space-y-2 text-sm text-muted-foreground">
            {ppe.map((item, i) => (
              <li key={i} className="flex gap-2">
                <span className="mt-0.5 shrink-0 text-primary">•</span>{item}
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* ── Step-by-Step + Safety Warnings ── */}
      <div className="grid gap-4 lg:grid-cols-2">
        <div className="rounded-md border bg-card/80 p-4">
          <div className="mb-3 text-sm font-semibold">Step-by-Step Procedure</div>
          {steps.length > 0 ? (
            <ol className="space-y-3 text-sm text-muted-foreground">
              {steps.map((step, i) => (
                <li key={i} className="grid grid-cols-[28px_1fr] gap-2">
                  <span className="flex h-6 w-6 items-center justify-center rounded-full bg-primary/10 text-xs font-semibold text-primary">
                    {i + 1}
                  </span>
                  <span>{step}</span>
                </li>
              ))}
            </ol>
          ) : isNotFound ? (
            <p className="text-sm text-muted-foreground">No procedure document found for this asset.</p>
          ) : (
            <p className="text-sm text-muted-foreground">
              Procedure document found. Detailed content is partially indexed.
            </p>
          )}
        </div>
        <div className="rounded-md border border-amber-500/20 bg-amber-500/5 p-4">
          <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-amber-400">
            <AlertTriangle className="h-4 w-4" /> Safety Warnings
          </div>
          <ul className="space-y-2 text-sm text-amber-300/80">
            {warnings.map((item, i) => (
              <li key={i} className="flex gap-2">
                <span className="shrink-0">⚠</span>{item}
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* ── Completion Criteria ── */}
      <div className="rounded-md border bg-card/80 p-4">
        <div className="mb-3 flex items-center gap-2 text-sm font-semibold">
          <CheckCircle2 className="h-4 w-4 text-emerald-400" /> Completion Criteria
        </div>
        <ul className="grid gap-2 text-sm text-muted-foreground sm:grid-cols-2">
          {criteria.map((item, i) => (
            <li key={i} className="flex gap-2">
              <span className="shrink-0 text-emerald-400">✓</span>{item}
            </li>
          ))}
        </ul>
      </div>

      {/* ── Document Reference ── */}
      <div className="rounded-md border bg-card/80 p-4">
        <div className="mb-3 flex items-center gap-2 text-sm font-semibold">
          <FileText className="h-4 w-4 text-primary" /> Document Reference
        </div>
        <div className="grid gap-4 sm:grid-cols-4">
          <Field label="Document Name" value={procedure.document} />
          <Field label="Page Number" value={procedure.page_number} />
          <Field label="Section" value={procedure.section} />
          <Field label="Confidence" value={`${confidence}% (${confidenceLabel})`} />
        </div>
        {evidence.length > 0 && (
          <div className="mt-4 space-y-2">
            {evidence.slice(0, 3).map((item: any, index: number) => (
              <div
                key={`${item.document_name}-${index}`}
                className="flex items-center justify-between rounded-md border bg-background/60 px-3 py-2 text-sm"
              >
                <div className="min-w-0 truncate">
                  <span className="font-medium">{item.document_name}</span>
                  <span className="ml-2 text-muted-foreground">
                    p.{item.page_number ?? 'N/A'} • {item.section ?? 'N/A'}
                  </span>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  className="ml-3 shrink-0"
                  disabled={!item.page_index_id || isOpeningCitation === index}
                  onClick={() => onOpenCitation(item, index)}
                >
                  <ExternalLink className="mr-1.5 h-3.5 w-3.5" />
                  Open
                </Button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* ── Quick Actions ── */}
      {(suggestions?.length > 0) && (
        <div className="rounded-md border bg-card/80 p-4">
          <div className="mb-3 text-xs font-medium uppercase tracking-wide text-muted-foreground">Quick Actions</div>
          <div className="flex flex-wrap gap-2">
            {suggestions.map((question: string, idx: number) => (
              <Button key={idx} variant="outline" size="sm" className="gap-2" onClick={() => onQuickAction && onQuickAction(question)}>
                <MessageSquare className="h-3.5 w-3.5" />
                {question}
              </Button>
            ))}
          </div>
        </div>
      )}
      {messageId && (
        <div className="rounded-md border border-border bg-muted/80 p-3 text-sm">
          <div className="mb-2 text-xs uppercase tracking-wide text-muted-foreground">Response Feedback</div>
          <div className="flex items-center gap-2">
            <Button
              variant={feedbackRating === 1 ? 'secondary' : 'outline'}
              size="sm"
              onClick={() => handleFeedback(1)}
              disabled={feedbackSubmitted}
            >
              Helpful
            </Button>
            <Button
              variant={feedbackRating === 0 ? 'secondary' : 'outline'}
              size="sm"
              onClick={() => handleFeedback(0)}
              disabled={feedbackSubmitted}
            >
              Not helpful
            </Button>
          </div>
          {feedbackSubmitted && (
            <p className="mt-2 text-xs text-muted-foreground">Thanks for your feedback.</p>
          )}
        </div>
      )}
    </div>
  );
}

function EnterpriseResponse({ msg, onSendMessage }: { msg: any; onSendMessage?: (text: string) => void }) {
  const data = msg.enterprise;
  const [isOpeningCitation, setIsOpeningCitation] = useState<number | null>(null);

  const openCitation = async (item: any, index: number) => {
    if (!item.page_index_id) return;
    setIsOpeningCitation(index);
    try {
      const viewer = await apiClient.get(`/page-index/${item.page_index_id}/viewer`);
      if (viewer?.pdf_url) {
        window.open(`${API_ORIGIN}${viewer.pdf_url}`, '_blank', 'noopener,noreferrer');
      }
    } catch (error) {
      console.error('Failed to open citation', error);
    } finally {
      setIsOpeningCitation(null);
    }
  };

  if (!data) {
    let parsedJson = null;
    try {
      parsedJson = JSON.parse(msg.content);
    } catch (e) {
      // not json
    }

    if (parsedJson && typeof parsedJson === 'object') {
      return <EnterpriseDashboard data={parsedJson} />;
    }

    return <MarkdownMessage content={msg.content} intent={msg.intent} equipment={msg.equipment} />;
  }

  const mode = msg.mode || data?.mode;
  if (mode === 'concise') {
    return (
      <div className="w-full space-y-2 px-8 py-6 sm:px-10 sm:py-8">
        <div className="flex items-center justify-between gap-2">
          <div className="text-sm font-semibold text-primary/80">Quick Answer</div>
          {msg.routing?.reasoning && (
            <Badge variant="outline" className="text-xs uppercase tracking-wide text-muted-foreground">
              {msg.routing.reasoning}
            </Badge>
          )}
        </div>
        <MarkdownMessage content={msg.content} intent={msg.intent} equipment={msg.equipment} />
      </div>
    );
  }

  const asset = data.asset_information || {};
  const rca = data.root_cause_analysis || {};
  const incidents = data.historical_incidents || {};
  const maintenance = data.maintenance_history || {};
  const inspection = data.inspection_findings || {};
  const manual = data.manual_recommendation || {};
  const expert = data.expert_recommendation || {};
  const risk = data.predictive_risk || {};
  const actions = data.recommended_actions || {};
  const evidence = data.evidence || [];
  const covered = data.sources_covered || {};
  const route = data.intent_routing || {};
  const procedure = data.procedure_response || {};
  const isProcedureIntent = ['startup_procedure', 'shutdown_procedure', 'sop'].includes(route.intent);

  return (
    <div className="w-full space-y-4 px-8 py-6 sm:px-10 sm:py-8">
      {isProcedureIntent ? (
        // ── SOP-focused layout (clean, no RCA/maintenance/predictive cards) ──
        <>
          <SOPCard
            messageId={msg.message_id}
            procedure={procedure}
            route={route}
            evidence={evidence}
            onOpenCitation={openCitation}
            isOpeningCitation={isOpeningCitation}
            onQuickAction={onSendMessage}
            suggestions={msg.follow_up_suggestions}
          />
          <Accordion type="multiple" className="rounded-md border bg-card px-4">
            <AccordionItem value="timeline">
              <AccordionTrigger>
                <span className="flex items-center gap-2">
                  <Route className="h-4 w-4 text-primary" />
                  AI Reasoning Timeline
                </span>
              </AccordionTrigger>
              <AccordionContent>
                <div className="space-y-3">
                  {(data.reasoning_timeline || []).map((step: any, index: number) => (
                    <div key={step.step} className="grid grid-cols-[28px_1fr] gap-3">
                      <div className="flex h-7 w-7 items-center justify-center rounded-full bg-primary/10 text-xs font-semibold text-primary">
                        {index + 1}
                      </div>
                      <div>
                        <div className="text-sm font-medium">{step.step}</div>
                        <div className="text-sm text-muted-foreground">{step.detail}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </AccordionContent>
            </AccordionItem>
          </Accordion>
        </>
      ) : (
        // ── Full enterprise layout (RCA, Maintenance, Predictive, etc.) ──
        <>
          <Card className="border-primary/30 bg-primary/5">
            <CardContent className="p-4">
              <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                <div>
                  <div className="mb-2 flex items-center gap-2 text-sm font-medium text-primary">
                    <Sparkles className="h-4 w-4" />
                    {route.agent || 'Enterprise Industrial Intelligence Assistant'}
                  </div>
                  <h2 className="text-lg font-semibold leading-7">{data.executive_summary}</h2>
                </div>
                <div className="flex flex-wrap gap-2">
                  {route.label && <Badge variant="outline">{route.label}</Badge>}
                  <Badge variant="outline" className={riskClasses(risk.risk_level)}>{risk.risk_level || 'Unknown'} Risk</Badge>
                  <Badge variant="secondary">{rca.confidence_score || msg.confidence || 0}% Confidence</Badge>
                </div>
              </div>
              {route.retrieval_priority?.length > 0 && (
                <div className="mt-4 rounded-md border bg-background/60 p-3">
                  <div className="mb-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">Retrieval Priority</div>
                  <div className="flex flex-wrap gap-2">
                    {route.retrieval_priority.map((item: string, index: number) => (
                      <Badge key={item} variant="secondary">{index + 1}. {item}</Badge>
                    ))}
                  </div>
                </div>
              )}
              <div className="mt-4 grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
                {Object.entries(covered).map(([key, value]) => (
                  <Badge
                    key={key}
                    variant="outline"
                    className={cn('justify-center py-1', value ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-400' : 'border-muted text-muted-foreground')}
                  >
                    {value ? <CheckCircle2 className="mr-1 h-3 w-3" /> : <AlertTriangle className="mr-1 h-3 w-3" />}
                    {key.replaceAll('_', ' ')}
                  </Badge>
                ))}
              </div>
            </CardContent>
          </Card>

          {procedure.primary_answer && (
            <EnterpriseCard title="Primary Answer" icon={Route} className="border-primary/30 bg-primary/5">
              <div className="space-y-5">
                <p className="text-base font-semibold leading-7">{procedure.primary_answer}</p>
                <div className="grid gap-4 md:grid-cols-2">
                  <Field label="Relevant Procedure" value={procedure.relevant_procedure} />
                  <Field label="Related SOP" value={procedure.related_sop} />
                  <Field label="Document" value={procedure.document} />
                  <Field label="Page Number" value={procedure.page_number} />
                  <Field label="Section" value={procedure.section} />
                  <Field label="Estimated Duration" value={procedure.estimated_duration} />
                </div>
                <div className="grid gap-4 lg:grid-cols-2">
                  <div className="rounded-md border bg-background/60 p-4">
                    <div className="mb-3 text-sm font-semibold">Prerequisites</div>
                    <ul className="space-y-2 text-sm text-muted-foreground">
                      {asList(procedure.prerequisites).map((item, index) => <li key={index}>- {item}</li>)}
                    </ul>
                  </div>
                  <div className="rounded-md border bg-background/60 p-4">
                    <div className="mb-3 text-sm font-semibold">Warnings</div>
                    <ul className="space-y-2 text-sm text-muted-foreground">
                      {asList(procedure.warnings).map((warning, index) => <li key={index}>- {warning}</li>)}
                    </ul>
                  </div>
                </div>
                <div className="grid gap-4 lg:grid-cols-2">
                  <div className="rounded-md border bg-background/60 p-4">
                    <div className="mb-3 text-sm font-semibold">Step-by-Step Instructions</div>
                    {asList(procedure.step_by_step_instructions).length > 0 ? (
                      <ol className="space-y-2 text-sm text-muted-foreground">
                        {asList(procedure.step_by_step_instructions).map((step, index) => (
                          <li key={index} className="grid grid-cols-[22px_1fr] gap-2">
                            <span className="flex h-5 w-5 items-center justify-center rounded-full bg-primary/10 text-xs text-primary">{index + 1}</span>
                            <span>{step}</span>
                          </li>
                        ))}
                      </ol>
                    ) : (
                      <p className="text-sm text-muted-foreground">No verified step list is available for this procedure.</p>
                    )}
                  </div>
                  <div className="rounded-md border bg-background/60 p-4">
                    <div className="mb-3 text-sm font-semibold">Safety Checks</div>
                    <ul className="space-y-2 text-sm text-muted-foreground">
                      {asList(procedure.safety_checks).map((check, index) => <li key={index}>- {check}</li>)}
                    </ul>
                  </div>
                </div>
              </div>
            </EnterpriseCard>
          )}

          <div className="grid gap-4 xl:grid-cols-2">
            <EnterpriseCard title="Asset Information" icon={sectionIcons.asset}>
              <div className="grid gap-4 sm:grid-cols-2">
                <Field label="Asset Name" value={asset.asset_name} />
                <Field label="Asset Type" value={asset.asset_type} />
                <Field label="Department" value={asset.department} />
                <Field label="Current Health" value={asset.current_health} />
                <Field label="Operational Status" value={asset.operational_status} />
                <Field label="Vibration" value={asset.sensor_snapshot?.vibration} />
              </div>
            </EnterpriseCard>

            <EnterpriseCard title="Root Cause Analysis" icon={sectionIcons.root}>
              <div className="space-y-3">
                <Field label="Most Probable Root Cause" value={rca.most_probable_root_cause} />
                <Badge variant="outline" className="bg-blue-500/10 text-blue-400 border-blue-500/30">
                  {rca.confidence_score || 0}% Confidence
                </Badge>
                <ul className="space-y-2 text-sm text-muted-foreground">
                  {asList(rca.supporting_evidence).map((item, index) => <li key={index}>- {item}</li>)}
                </ul>
              </div>
            </EnterpriseCard>

            <EnterpriseCard title="Historical Incidents" icon={sectionIcons.incidents} className="xl:col-span-2">
              <div className="mb-4 grid gap-3 sm:grid-cols-2">
                <Field label="Frequency" value={incidents.frequency} />
                <Field label="Trend" value={incidents.trend} />
              </div>
              <Timeline items={incidents.timeline || []} />
            </EnterpriseCard>

            <EnterpriseCard title="Maintenance History" icon={sectionIcons.maintenance}>
              <div className="grid gap-4">
                <Field label="Recent Maintenance" value={maintenance.recent_maintenance} />
                <Field label="Pending Maintenance" value={maintenance.pending_maintenance} />
                <Field label="Technician" value={maintenance.technician} />
              </div>
            </EnterpriseCard>

            <EnterpriseCard title="Inspection Findings" icon={sectionIcons.inspection}>
              <div className="grid gap-4">
                <Field label="Latest Inspection" value={inspection.latest_inspection} />
                <Field label="Observations" value={inspection.observations} />
                <div>
                  <div className="text-[11px] uppercase tracking-wide text-muted-foreground">Risk Level</div>
                  <Badge variant="outline" className={cn('mt-1', riskClasses(inspection.risk_level))}>{inspection.risk_level || 'N/A'}</Badge>
                </div>
              </div>
            </EnterpriseCard>

            <EnterpriseCard title="Manual Recommendation" icon={sectionIcons.manual}>
              <div className="grid gap-4">
                <Field label="Relevant Procedure" value={manual.relevant_maintenance_procedure} />
                <div className="grid gap-3 sm:grid-cols-3">
                  <Field label="Document" value={manual.document} />
                  <Field label="Page Number" value={manual.page_number} />
                  <Field label="Section" value={manual.section} />
                </div>
              </div>
            </EnterpriseCard>

            <EnterpriseCard title="Expert Recommendation" icon={sectionIcons.expert}>
              <ul className="space-y-2 text-sm text-muted-foreground">
                {asList(expert.best_practices).map((item, index) => <li key={index}>- {item}</li>)}
              </ul>
            </EnterpriseCard>

            <EnterpriseCard title="Predictive Risk" icon={sectionIcons.risk}>
              <div className="grid gap-4 sm:grid-cols-2">
                <Field label="Failure Probability" value={risk.failure_probability} />
                <div>
                  <div className="text-[11px] uppercase tracking-wide text-muted-foreground">Risk Level</div>
                  <Badge variant="outline" className={cn('mt-1', riskClasses(risk.risk_level))}>{risk.risk_level || 'N/A'}</Badge>
                </div>
                <Field label="Estimated RUL" value={risk.estimated_remaining_useful_life} />
                <Field label="Next Inspection" value={risk.recommended_next_inspection} />
              </div>
            </EnterpriseCard>

            <EnterpriseCard title="Recommended Actions" icon={sectionIcons.actions} className="xl:col-span-2">
              <div className="grid gap-4 lg:grid-cols-3">
                {[
                  ['Immediate Actions', actions.immediate_actions],
                  ['Preventive Actions', actions.preventive_actions],
                  ['Long-term Improvements', actions.long_term_improvements],
                ].map(([title, items]: any) => (
                  <div key={title} className="rounded-md border bg-background/60 p-4">
                    <div className="mb-2 text-sm font-semibold">{title}</div>
                    <ul className="space-y-2 text-sm text-muted-foreground">
                      {asList(items).map((item, index) => <li key={index}>- {item}</li>)}
                    </ul>
                  </div>
                ))}
              </div>
            </EnterpriseCard>
          </div>

          <Accordion type="multiple" className="rounded-md border bg-card px-4">
            <AccordionItem value="evidence">
              <AccordionTrigger>
                <span className="flex items-center gap-2">
                  <ShieldCheck className="h-4 w-4 text-primary" />
                  Evidence Panel ({evidence.length})
                </span>
              </AccordionTrigger>
              <AccordionContent>
                <div className="space-y-3">
                  {evidence.map((item: any, index: number) => (
                    <div key={`${item.document_name}-${index}`} className="rounded-md border bg-background/60 p-3">
                      <div className="flex flex-col gap-2 md:flex-row md:items-start md:justify-between">
                        <div>
                          <div className="font-medium">{item.document_name}</div>
                          <div className="text-xs text-muted-foreground">
                            Page {item.page_number || 'N/A'} • {item.section || 'N/A'} • Confidence {item.confidence}%
                          </div>
                        </div>
                        <Button
                          variant="outline"
                          size="sm"
                          disabled={!item.page_index_id || isOpeningCitation === index}
                          onClick={() => openCitation(item, index)}
                        >
                          <ExternalLink className="mr-2 h-3.5 w-3.5" />
                          Open Page
                        </Button>
                      </div>
                      <p className="mt-2 text-sm text-muted-foreground">{item.excerpt}</p>
                      <div className="mt-2 flex flex-wrap gap-2">
                        {item.incident_id && <Badge variant="outline">Incident {item.incident_id}</Badge>}
                        {item.maintenance_id && <Badge variant="outline">Maintenance {item.maintenance_id}</Badge>}
                        {item.inspection_id && <Badge variant="outline">Inspection {item.inspection_id}</Badge>}
                      </div>
                    </div>
                  ))}
                </div>
              </AccordionContent>
            </AccordionItem>

            <AccordionItem value="graph">
              <AccordionTrigger>
                <span className="flex items-center gap-2">
                  <Network className="h-4 w-4 text-primary" />
                  Knowledge Graph Nodes Used ({data.knowledge_graph_nodes_used?.length || 0})
                </span>
              </AccordionTrigger>
              <AccordionContent>
                <div className="flex flex-wrap gap-2">
                  {(data.knowledge_graph_nodes_used || []).map((node: any) => (
                    <Badge key={node.id} variant="secondary" className="gap-1">
                      <Network className="h-3 w-3" />
                      {node.label || node.id}
                      <span className="text-muted-foreground">({node.type})</span>
                    </Badge>
                  ))}
                </div>
              </AccordionContent>
            </AccordionItem>

            <AccordionItem value="timeline">
              <AccordionTrigger>
                <span className="flex items-center gap-2">
                  <Route className="h-4 w-4 text-primary" />
                  AI Reasoning Timeline
                </span>
              </AccordionTrigger>
              <AccordionContent>
                <div className="space-y-3">
                  {(data.reasoning_timeline || []).map((step: any, index: number) => (
                    <div key={step.step} className="grid grid-cols-[28px_1fr] gap-3">
                      <div className="flex h-7 w-7 items-center justify-center rounded-full bg-primary/10 text-xs font-semibold text-primary">
                        {index + 1}
                      </div>
                      <div>
                        <div className="text-sm font-medium">{step.step}</div>
                        <div className="text-sm text-muted-foreground">{step.detail}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </AccordionContent>
            </AccordionItem>
          </Accordion>
          
          {/* ── Quick Actions (Enterprise Layout) ── */}
          {(msg.follow_up_suggestions?.length > 0) && (
            <div className="rounded-md border bg-card/80 p-4 mt-4">
              <div className="mb-3 text-xs font-medium uppercase tracking-wide text-muted-foreground">Quick Actions</div>
              <div className="flex flex-wrap gap-2">
                {msg.follow_up_suggestions.map((question: string, idx: number) => (
                  <Button key={idx} variant="outline" size="sm" className="gap-2" onClick={() => onSendMessage(question)}>
                    <MessageSquare className="h-3.5 w-3.5" />
                    {question}
                  </Button>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

export default function AICopilot() {
  const { profile } = useUser();
  const [messages, setMessages] = useState<any[]>([]);
  const [printMessageIndex, setPrintMessageIndex] = useState<number | null>(null);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [copiedId, setCopiedId] = useState<number | null>(null);
  const [regeneratingIndex, setRegeneratingIndex] = useState<number | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    apiClient.get('/chat/history').then(history => {
      if (history && history.length > 0) {
        setMessages(history);
      } else {
        setMessages([
          {
            role: 'assistant',
            content: 'Hello! I am your FreshFlow Beverages Enterprise Intelligence Assistant. Ask me about equipment failures, maintenance risk, SOPs, inspections, food safety compliance, or expert recommendations.',
            time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          },
        ]);
      }
    }).catch(console.error);
  }, []);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
  }, [messages, isLoading]);

  const handleCopy = (text: string, id: number) => {
    let copyText = text;
    try {
      const parsed = JSON.parse(text);
      if (parsed && typeof parsed === 'object') {
        if (parsed.answer) copyText = parsed.answer;
        else copyText = JSON.stringify(parsed, null, 2);
      }
    } catch(e) {}
    
    navigator.clipboard.writeText(copyText);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 1000);
  };

  const handleDelete = async (index: number) => {
    let deletedIds: (number | undefined)[] = [];
    
    setMessages(prev => {
      const newMessages = [...prev];
      if (newMessages[index].role === 'user' && index + 1 < newMessages.length && newMessages[index + 1].role === 'assistant') {
        deletedIds = [newMessages[index].id, newMessages[index + 1].id];
        newMessages.splice(index, 2);
      } else {
        deletedIds = [newMessages[index].id];
        newMessages.splice(index, 1);
      }
      return newMessages;
    });

    for (const id of deletedIds) {
      if (id) {
        try {
          await apiClient.delete(`/chat/history/${id}`);
        } catch (error) {
          console.error('Failed to delete message from backend:', error);
        }
      }
    }
  };

  const handleRegenerate = async (index: number) => {
    const msgToRegenerate = messages[index];
    if (msgToRegenerate.role !== 'assistant' || isLoading || regeneratingIndex !== null) return;
    
    let userQuery = '';
    for (let i = index - 1; i >= 0; i--) {
      if (messages[i].role === 'user') {
        userQuery = messages[i].content;
        break;
      }
    }
    
    if (!userQuery) return;
    
    setRegeneratingIndex(index);
    
    if (msgToRegenerate.id) {
      try {
        await apiClient.delete(`/chat/history/${msgToRegenerate.id}`);
      } catch (error) {
        console.error('Failed to delete old regenerated message from backend:', error);
      }
    }
    
    try {
      const response = await apiClient.post('/chat', { message: userQuery, history: [] });
      setMessages(prev => {
        const newMsgs = [...prev];
        newMsgs[index] = response;
        return newMsgs;
      });
    } catch (error) {
      console.error('Regenerate error', error);
      setMessages(prev => {
        const newMsgs = [...prev];
        newMsgs[index] = { role: 'assistant', content: 'Sorry, I encountered an error.', time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) };
        return newMsgs;
      });
    } finally {
      setRegeneratingIndex(null);
    }
  };

  const sendMessage = async (text: string) => {
    if (!text.trim() || isLoading) return;

    const userMsg = {
      role: 'user',
      content: text,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };
    setMessages(prev => [...prev, userMsg]);
    setInputMessage('');
    setIsLoading(true);

    try {
      const response = await apiClient.post('/chat', { message: text, history: [] });
      setMessages(prev => [...prev, response]);
    } catch (error) {
      console.error('Chat error', error);
      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          content: 'Sorry, I encountered an error communicating with the backend.',
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const suggestions = useMemo(() => [
    'Why did Bottle Filling Machine FM101 stop?',
    'What is the predictive risk for Air Compressor AC101?',
    'Show incidents related to bottle jam failures',
    'Show startup SOP for Bottle Filling Machine FM101.',
  ], []);

  return (
    <div className="flex h-[calc(100vh-5rem)] flex-col bg-background">
      <div className="flex shrink-0 items-center justify-between border-b border-border/50 bg-background/80 px-6 py-2.5 backdrop-blur-sm print:hidden">
        <div className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-primary/10">
            <BrainCircuit className="h-4 w-4 text-primary" />
          </div>
          <span className="text-sm font-semibold">AI Copilot</span>
          <Badge variant="outline" className="ml-1 rounded-full border-emerald-500/40 bg-emerald-500/10 text-[10px] text-emerald-500">Live</Badge>
        </div>
        <div className="flex items-center gap-1">
          <Button variant="ghost" size="sm" onClick={() => { setPrintMessageIndex(null); setTimeout(() => window.print(), 100); }} className="h-8 gap-1.5 text-xs text-muted-foreground hover:text-foreground">
            <Download className="h-3.5 w-3.5" /> Export PDF
          </Button>
        </div>
      </div>

      <ScrollArea className="flex-1 print:hidden">
        <div className="mx-auto w-full max-w-5xl space-y-6 px-4 py-8">

          {/* Welcome Header */}
          {messages.length <= 1 && (
            <div className="mb-8 mt-6 text-center">
              <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-primary/25 to-primary/5 ring-1 ring-primary/20 text-primary shadow-md">
                <BrainCircuit className="h-7 w-7" />
              </div>
              <h1 className="text-2xl font-bold tracking-tight">Industrial Brain AI Copilot</h1>
              <p className="mt-1.5 text-sm text-muted-foreground">Enterprise GraphRAG · Equipment, SOPs, incidents, and predictive risk</p>
            </div>
          )}

          {messages.map((msg, idx) => {
            const isUser = msg.role === 'user';
            if (!isUser && idx === 0 && messages.length === 1) return null;

            return (
              <div key={idx} className={cn('flex w-full', isUser ? 'justify-end' : 'justify-start')}>
                {isUser ? (
                  <div className="group flex max-w-[68%] flex-col items-end gap-1">
                    <div className="rounded-2xl rounded-tr-sm bg-primary px-4 py-3 text-sm leading-relaxed text-primary-foreground shadow-sm">
                      {msg.content}
                    </div>
                    <div className="flex items-center gap-2 opacity-0 transition-opacity group-hover:opacity-100 px-1">
                      <span className="text-[10px] text-muted-foreground mr-1">{msg.time}</span>
                      <button onClick={() => handleCopy(msg.content, idx)} className="text-muted-foreground hover:text-foreground transition-colors" title="Copy message">
                        {copiedId === idx ? <Check className="h-3.5 w-3.5 text-emerald-500" /> : <Copy className="h-3.5 w-3.5" />}
                      </button>
                      <button onClick={() => handleDelete(idx)} className="text-muted-foreground hover:text-red-500 transition-colors" title="Delete message">
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="flex w-full gap-3">
                    <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-primary/20 bg-primary/10 shadow-sm">
                      <Bot className="h-4 w-4 text-primary" />
                    </div>
                    <div className="min-w-0 flex-1 overflow-hidden rounded-2xl rounded-tl-sm border border-border/60 bg-card shadow-sm">
                      {regeneratingIndex === idx ? (
                        <div className="flex items-center gap-1.5 px-8 py-6 sm:px-10">
                          <div className="h-2 w-2 rounded-full bg-primary/70 animate-bounce" />
                          <div className="h-2 w-2 rounded-full bg-primary/70 animate-bounce [animation-delay:-.25s]" />
                          <div className="h-2 w-2 rounded-full bg-primary/70 animate-bounce [animation-delay:-.5s]" />
                          <span className="ml-2 text-xs text-muted-foreground">Regenerating response…</span>
                        </div>
                      ) : (
                        <EnterpriseResponse msg={msg} onSendMessage={sendMessage} />
                      )}
                      
                      {regeneratingIndex !== idx && (
                        <div className="flex items-center justify-between border-t border-border/40 bg-muted/20 px-8 sm:px-10 py-3 text-[10px] text-muted-foreground">
                          <span>{msg.time}</span>
                          <div className="flex items-center gap-3.5">
                            <button onClick={() => handleCopy(msg.content, idx)} className="flex items-center gap-1.5 hover:text-foreground transition-colors">
                              {copiedId === idx ? <Check className="h-3.5 w-3.5 text-emerald-500" /> : <Copy className="h-3.5 w-3.5" />}
                              <span>{copiedId === idx ? 'Copied' : 'Copy'}</span>
                            </button>
                            {idx > 0 && (
                              <button onClick={() => handleRegenerate(idx)} disabled={isLoading || regeneratingIndex !== null} className="flex items-center gap-1.5 hover:text-foreground transition-colors disabled:opacity-50">
                                <RefreshCcw className="h-3.5 w-3.5" />
                                <span>Regenerate</span>
                              </button>
                            )}
                            <button onClick={() => { setPrintMessageIndex(idx); setTimeout(() => window.print(), 100); }} className="flex items-center gap-1.5 hover:text-foreground transition-colors">
                              <Download className="h-3.5 w-3.5" />
                              <span>PDF</span>
                            </button>
                          </div>
                        </div>
                      )}
                    </div>
                    <div className="w-8 shrink-0 hidden sm:block" />
                  </div>
                )}
              </div>
            );
          })}

          {isLoading && (
            <div className="flex w-full gap-3">
              <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-primary/20 bg-primary/10 shadow-sm">
                <Bot className="h-4 w-4 text-primary animate-pulse" />
              </div>
              <div className="flex items-center gap-1.5 rounded-2xl rounded-tl-sm border border-border/60 bg-card px-5 py-3.5 shadow-sm">
                <div className="h-2 w-2 rounded-full bg-primary/70 animate-bounce" />
                <div className="h-2 w-2 rounded-full bg-primary/70 animate-bounce [animation-delay:-.25s]" />
                <div className="h-2 w-2 rounded-full bg-primary/70 animate-bounce [animation-delay:-.5s]" />
                <span className="ml-2 text-xs text-muted-foreground">Analyzing plant data…</span>
              </div>
            </div>
          )}
          <div ref={scrollRef} className="h-2" />
        </div>
      </ScrollArea>

      {/* Input Area */}
      <div className="shrink-0 border-t border-border/50 bg-background/90 px-4 pb-5 pt-3 print:hidden backdrop-blur-sm">
        <div className="mx-auto w-full max-w-5xl">
          {/* Quick Suggestions */}
          {messages.length <= 1 && (
            <div className="mb-3 flex flex-wrap gap-2">
              {suggestions.map((q) => (
                <button
                  key={q}
                  onClick={() => sendMessage(q)}
                  className="rounded-full border border-border/60 bg-muted/40 px-3 py-1 text-xs text-muted-foreground transition-all hover:border-border hover:bg-muted hover:text-foreground"
                >
                  {q}
                </button>
              ))}
            </div>
          )}

          {/* Input Box */}
          <div className="flex items-center gap-2 rounded-2xl border border-border/60 bg-background px-4 py-2.5 shadow-sm transition-shadow focus-within:border-primary/40 focus-within:shadow-md">
            <Input
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && sendMessage(inputMessage)}
              placeholder="Ask about equipment, incidents, SOPs, or predictive risk…"
              className="flex-1 border-0 bg-transparent py-1 text-sm shadow-none focus-visible:ring-0 placeholder:text-muted-foreground/60"
            />
            <Button
              onClick={() => sendMessage(inputMessage)}
              disabled={isLoading || !inputMessage.trim()}
              size="icon"
              className="h-8 w-8 shrink-0 rounded-xl bg-primary transition-all active:scale-95 disabled:opacity-40"
            >
              <Send className="h-3.5 w-3.5" />
            </Button>
          </div>
          <p className="mt-1.5 text-center text-[10px] text-muted-foreground/60">
            AI Copilot can make mistakes. Verify critical engineering decisions.
          </p>
        </div>
      </div>
      
      {/* Printable Report (only visible during window.print) */}
      <PrintableReport messages={messages} user={profile} printMessageIndex={printMessageIndex} />
    </div>
  );
}
