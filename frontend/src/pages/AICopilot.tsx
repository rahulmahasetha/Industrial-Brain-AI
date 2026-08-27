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
  Plus,
  Edit2,
  MessageSquarePlus,
  MoreVertical,
  PanelLeftClose,
  PanelLeftOpen,
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

import { API_ORIGIN } from '@/lib/config';

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

  let enterpriseData = msg.enterprise;
  if (!enterpriseData) {
    try {
      const parsed = JSON.parse(msg.content);
      if (parsed.enterprise) enterpriseData = parsed.enterprise;
      else if (typeof parsed === 'object') enterpriseData = parsed;
    } catch (e) {}
  }

  // Eager render of empty dashboard removed to allow proper Markdown fallback

  const mode = msg.mode || enterpriseData?.mode || (msg.response_type === 'concise' ? 'concise' : null);
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
        <MarkdownMessage content={msg.content} intent={msg.intent || msg.response_type} equipment={msg.equipment} />
      </div>
    );
  }

  if (!enterpriseData) {
    return <MarkdownMessage content={msg.content} intent={msg.intent || msg.response_type} equipment={msg.equipment} />;
  }

  const intent = msg.intent || enterpriseData.intent_routing?.intent || msg.response_type || null;
  const isProcedureIntent = ['startup_procedure', 'shutdown_procedure', 'sop'].includes(intent);
  const route = enterpriseData.intent_routing || {};
  const procedure = enterpriseData.procedure_response || enterpriseData || {};
  const evidence = enterpriseData.evidence || [];

  return (
    <div className="w-full space-y-4 px-8 py-6 sm:px-10 sm:py-8">
      {isProcedureIntent ? (
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
                  {(enterpriseData.reasoning_timeline || []).map((step: any, index: number) => (
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
      ) : msg.response_type === 'root_cause_analysis' || msg.response_type === 'predictive_maintenance' ? (
        <EnterpriseDashboard data={enterpriseData} onSuggestionSelect={onSendMessage} />
      ) : (
        <MarkdownMessage content={msg.content} intent={intent} equipment={msg.equipment} />
      )}
    </div>
  );
}

export default function AICopilot() {
  const { profile } = useUser();
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [sessions, setSessions] = useState<any[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<number | null>(null);
  const [messages, setMessages] = useState<any[]>([]);
  const [printMessageIndex, setPrintMessageIndex] = useState<number | null>(null);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [copiedId, setCopiedId] = useState<number | null>(null);
  const [regeneratingIndex, setRegeneratingIndex] = useState<number | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  const fetchSessions = async () => {
    try {
      const data = await apiClient.get('/chat/sessions');
      setSessions(data);
      if (data.length > 0 && !currentSessionId) {
        setCurrentSessionId(data[0].id);
      } else if (data.length === 0) {
        // Create initial session if none exist
        const newSession = await apiClient.post('/chat/sessions', { title: 'New Chat' });
        setSessions([newSession]);
        setCurrentSessionId(newSession.id);
      }
    } catch (e) {
      console.error('Failed to fetch sessions', e);
    }
  };

  useEffect(() => {
    fetchSessions();
  }, []);

  const loadSessionHistory = async (sessionId: number) => {
    try {
      const history = await apiClient.get(`/chat/history?session_id=${sessionId}`);
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
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    if (currentSessionId) {
      loadSessionHistory(currentSessionId);
    }
  }, [currentSessionId]);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
  }, [messages, isLoading]);

  const handleNewChat = async () => {
    try {
      const newSession = await apiClient.post('/chat/sessions', { title: 'New Chat' });
      setSessions(prev => [newSession, ...prev]);
      setCurrentSessionId(newSession.id);
    } catch (e) {
      console.error('Failed to create new chat', e);
    }
  };

  const handleRenameSession = async (id: number, newTitle: string) => {
    try {
      await apiClient.put(`/chat/sessions/${id}`, { title: newTitle });
      setSessions(prev => prev.map(s => s.id === id ? { ...s, title: newTitle } : s));
    } catch (e) {
      console.error('Failed to rename session', e);
    }
  };

  const handleDeleteSession = async (id: number) => {
    try {
      await apiClient.delete(`/chat/sessions/${id}`);
      setSessions(prev => prev.filter(s => s.id !== id));
      if (currentSessionId === id) {
        setCurrentSessionId(null); // will trigger load first session next time or blank
        setMessages([]);
        fetchSessions();
      }
    } catch (e) {
      console.error('Failed to delete session', e);
    }
  };

  const handleClearChat = async () => {
    if (currentSessionId) {
      try {
        await apiClient.delete(`/chat/sessions/${currentSessionId}`);
        handleNewChat(); // replace it
      } catch (error) {
        console.error('Failed to clear chat history:', error);
      }
    }
  };

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
    if (index === 0 || messages[index - 1].role !== 'user') return;
    
    const userQuery = messages[index - 1].content;
    const msgToRegenerate = messages[index];
    setRegeneratingIndex(index);
    
    if (msgToRegenerate.id) {
      try {
        await apiClient.delete(`/chat/history/${msgToRegenerate.id}`);
      } catch (error) {
        console.error('Failed to delete old regenerated message from backend:', error);
      }
    }
    
    try {
      const response = await apiClient.post('/chat', { message: userQuery, session_id: currentSessionId, history: [] });
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

    let activeSessionId = currentSessionId;
    if (!activeSessionId) {
      const newSession = await apiClient.post('/chat/sessions', { title: text.substring(0, 30) });
      setSessions(prev => [newSession, ...prev]);
      setCurrentSessionId(newSession.id);
      activeSessionId = newSession.id;
    }

    const userMsg = {
      role: 'user',
      content: text,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };
    setMessages(prev => [...prev, userMsg]);
    setInputMessage('');
    setIsLoading(true);

    try {
      const response = await apiClient.post('/chat', { message: text, session_id: activeSessionId, history: [] });
      setMessages(prev => [...prev, response]);
      
      // Auto-rename chat based on first query
      if (messages.length <= 1) {
          const newTitle = (response.intent || text).substring(0, 30);
          handleRenameSession(activeSessionId as number, newTitle);
      }
    } catch (error) {
      console.error('Chat error', error);
      setMessages(prev => [
        ...prev,
        { role: 'assistant', content: 'Sorry, I encountered an error communicating with the backend.', time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) }
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
    <div className="flex w-full h-full overflow-hidden bg-background">
      
      {/* Sidebar for Chat History */}
      {sidebarOpen && (
        <>
        <div className="md:hidden fixed inset-0 z-40 bg-background/80 backdrop-blur-sm" onClick={() => setSidebarOpen(false)} />
        <div className="w-64 border-r border-border/50 bg-muted/10 flex flex-col shrink-0 animate-in slide-in-from-left-4 duration-200 fixed inset-y-0 left-0 z-50 md:relative md:inset-auto h-[calc(100vh-5rem)] md:h-auto bg-background md:bg-muted/10">
          <div className="p-4 border-b border-border/50 flex items-center justify-between">
            <Button onClick={handleNewChat} className="flex-1 justify-start gap-2 mr-2" variant="outline">
              <Plus className="h-4 w-4" /> New Chat
            </Button>
            <Button variant="ghost" size="icon" onClick={() => setSidebarOpen(false)} className="h-9 w-9 shrink-0 text-muted-foreground hover:text-foreground">
              <PanelLeftClose className="h-4 w-4" />
            </Button>
          </div>
        <div className="flex-1 overflow-y-auto min-h-0 p-2 scroll-smooth">
          <div className="space-y-1">
            {sessions.map(session => (
              <div 
                key={session.id} 
                className={cn(
                  "group flex items-center justify-between p-2 rounded-lg text-sm cursor-pointer hover:bg-muted/50 transition-colors",
                  currentSessionId === session.id ? "bg-muted font-medium" : "text-muted-foreground"
                )}
                onClick={() => { setCurrentSessionId(session.id); if (window.innerWidth < 768) setSidebarOpen(false); }}
              >
                <div className="flex flex-col min-w-0 overflow-hidden">
                  <span className="truncate">{session.title}</span>
                  <span className="text-[10px] text-muted-foreground/70">{new Date(session.created_at).toLocaleDateString()}</span>
                </div>
                <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                   <button 
                     onClick={(e) => { 
                       e.stopPropagation(); 
                       const newName = prompt("Rename chat:", session.title); 
                       if (newName) handleRenameSession(session.id, newName); 
                     }}
                     className="p-1 hover:text-foreground text-muted-foreground rounded"
                   >
                     <Edit2 className="h-3.5 w-3.5" />
                   </button>
                   <button 
                     onClick={(e) => { 
                       e.stopPropagation(); 
                       if (confirm("Delete this chat?")) handleDeleteSession(session.id); 
                     }}
                     className="p-1 hover:text-red-500 text-muted-foreground rounded"
                   >
                     <Trash2 className="h-3.5 w-3.5" />
                   </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
      </>
      )}

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col min-w-0 min-h-0">
        <div className="flex shrink-0 items-center justify-between border-b border-border/50 bg-background/80 px-6 py-2.5 backdrop-blur-sm print:hidden">
          <div className="flex items-center gap-2">
            {!sidebarOpen && (
              <Button variant="ghost" size="icon" onClick={() => setSidebarOpen(true)} className="h-8 w-8 -ml-2 text-muted-foreground hover:text-foreground">
                <PanelLeftOpen className="h-4 w-4" />
              </Button>
            )}
            <div className="md:hidden flex h-7 w-7 items-center justify-center rounded-lg bg-muted text-muted-foreground">
              <MessageSquarePlus className="h-4 w-4" onClick={handleNewChat} />
            </div>
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-primary/10">
              <BrainCircuit className="h-4 w-4 text-primary" />
            </div>
            <span className="text-sm font-semibold">AI Copilot</span>
            <Badge variant="outline" className="ml-1 rounded-full border-emerald-500/40 bg-emerald-500/10 text-[10px] text-emerald-500">Live</Badge>
          </div>
          <div className="flex items-center gap-1">
            <Button variant="ghost" size="sm" onClick={handleClearChat} className="h-8 gap-1.5 text-xs text-muted-foreground hover:text-red-500">
              <Trash2 className="h-3.5 w-3.5" /> Clear Chat
            </Button>
            <Button variant="ghost" size="sm" onClick={() => { setPrintMessageIndex(null); setTimeout(() => window.print(), 100); }} className="h-8 gap-1.5 text-xs text-muted-foreground hover:text-foreground">
              <Download className="h-3.5 w-3.5" /> Export PDF
            </Button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto min-h-0 print:hidden scroll-smooth">
          <div className={cn("mx-auto w-full space-y-6 px-4 py-8 transition-all duration-300", sidebarOpen ? "max-w-4xl" : "max-w-7xl")}>

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
                    <div className="flex max-w-[85%] items-end gap-3 sm:max-w-[75%]">
                      <div className="flex flex-col items-end">
                        <div className="rounded-2xl rounded-tr-sm bg-primary px-5 py-3.5 text-[15px] leading-relaxed text-primary-foreground shadow-sm">
                          {msg.content}
                        </div>
                        <span className="mt-1.5 mr-1 text-[10px] text-muted-foreground/70">{msg.time}</span>
                      </div>
                      <div className="flex h-8 w-8 shrink-0 items-center justify-center overflow-hidden rounded-full border border-primary/20 bg-primary/10 sm:h-9 sm:w-9">
                        {profile?.photo_url ? (
                          <img src={profile.photo_url} alt="User" className="h-full w-full object-cover" />
                        ) : (
                          <span className="text-xs font-semibold text-primary">{profile?.name?.charAt(0) || 'U'}</span>
                        )}
                      </div>
                    </div>
                  ) : (
                    <div className="flex w-full max-w-[95%] items-start gap-3 sm:max-w-[85%]">
                      <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-primary/20 bg-primary/10 shadow-sm sm:h-9 sm:w-9">
                        <Bot className="h-4 w-4 text-primary sm:h-5 sm:w-5" />
                      </div>
                      <div className="flex flex-1 flex-col overflow-hidden">
                        <div className="rounded-2xl rounded-tl-sm border border-border/60 bg-card shadow-sm overflow-hidden">
                          {msg.isStreaming ? (
                            <div className="px-5 py-4 whitespace-pre-wrap leading-relaxed">
                               {msg.content}
                               <span className="ml-1 inline-block h-4 w-2 animate-pulse bg-primary align-middle" />
                            </div>
                          ) : msg.response_type === 'root_cause_analysis' || msg.response_type === 'predictive_maintenance' ? (
                            <EnterpriseResponse msg={msg} onSendMessage={sendMessage} />
                          ) : (
                            <div className="px-1 py-1">
                               <MarkdownMessage content={msg.content} intent={msg.intent} equipment={msg.enterprise?.equipment} />
                            </div>
                          )}
                          
                          {!msg.isStreaming && regeneratingIndex !== idx && (
                            <div className="flex items-center justify-between border-t border-border/40 bg-muted/20 px-4 sm:px-6 py-2.5 text-[10px] text-muted-foreground">
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
                      </div>
                    </div>
                  )}
                </div>
              );
            })}

            {isLoading && messages[messages.length-1]?.role !== 'assistant' && (
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
        </div>

        {/* Input Area */}
        <div className="shrink-0 border-t border-border/50 bg-background/90 px-4 pb-5 pt-3 print:hidden backdrop-blur-sm">
          <div className={cn("mx-auto w-full transition-all duration-300", sidebarOpen ? "max-w-4xl" : "max-w-7xl")}>
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
            
            <div className="relative flex items-end gap-2 rounded-2xl border border-border/60 bg-card p-1.5 shadow-sm focus-within:border-primary/50 focus-within:ring-1 focus-within:ring-primary/20 transition-all">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center">
                <Sparkles className="h-5 w-5 text-primary/70" />
              </div>
              <textarea
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    sendMessage(inputMessage);
                  }
                }}
                placeholder="Ask about equipment health, downtime RCA, or standard operating procedures..."
                className="max-h-32 min-h-[44px] w-full resize-none bg-transparent py-2.5 text-[15px] placeholder:text-muted-foreground/60 focus:outline-none"
                rows={1}
                disabled={isLoading}
              />
              <div className="flex items-center gap-2 pr-1 pb-1">
                <Button
                  size="icon"
                  className={cn('h-9 w-9 rounded-xl transition-all', inputMessage.trim() ? 'bg-primary text-primary-foreground shadow-md hover:bg-primary/90' : 'bg-muted text-muted-foreground hover:bg-muted')}
                  onClick={() => sendMessage(inputMessage)}
                  disabled={!inputMessage.trim() || isLoading}
                >
                  <Send className="h-4 w-4" />
                </Button>
              </div>
            </div>
            <div className="mt-2 text-center text-[10px] text-muted-foreground/70">
              Industrial Brain AI can make mistakes. Verify critical maintenance procedures.
            </div>
          </div>
        </div>
      </div>
      
      {/* Hidden Printable Report */}
      <div className="hidden print:block">
        {printMessageIndex !== null && messages[printMessageIndex] && (
          <PrintableReport message={messages[printMessageIndex]} />
        )}
      </div>
    </div>
  );
}
