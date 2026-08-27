import { ExecutiveSummary } from './ExecutiveSummary';
import { RootCause } from './RootCause';
import { TimelineCard } from './TimelineCard';
import { Evidence } from './Evidence';
import { CorrectiveActions } from './CorrectiveActions';
import { PreventiveActions } from './PreventiveActions';
import { SourceDocuments } from './SourceDocuments';
import { ConfidenceBadge } from './ConfidenceBadge';
import { FollowUpSuggestions } from './FollowUpSuggestions';

function toArray<T>(value: T | T[] | null | undefined): T[] {
  if (Array.isArray(value)) return value;
  return value === null || value === undefined || value === '' ? [] : [value];
}

export function EnterpriseDashboard({ data, onSuggestionSelect }: { data: any, onSuggestionSelect?: (s: string) => void }) {
  if (!data) return null;

  // Map the structured JSON to the enterprise components
  const summary = data.executive_summary || data.primary_answer;
  const rootCause = data.root_cause_analysis?.most_probable_root_cause || data.most_probable_root_cause || data.root_cause;
  const timeline = toArray(data.historical_incidents?.timeline);
  const evidence = toArray(data.evidence).map((item) =>
    typeof item === 'string' ? { excerpt: item } : item,
  );
  const correctiveActions = toArray(data.recommended_actions?.immediate_actions || data.corrective_actions);
  const preventiveActions = toArray(data.recommended_actions?.preventive_actions || data.preventive_actions);
  const confidence = data.confidence || data.root_cause_analysis?.confidence_score;
  const suggestions = toArray(data.follow_up_suggestions || data.related_questions);
  // Use citations from root or evidence if any exist
  const citations = data.citations || data.source_documents || evidence;

  return (
    <div className="w-full space-y-4 px-8 py-6 sm:px-10 sm:py-8">
      {/* Executive Summary with Confidence Badge inline if desired, or let Summary handle it. We can wrap it nicely */}
      <div className="flex flex-col gap-3">
        <div className="flex justify-end">
          <ConfidenceBadge score={confidence} />
        </div>
        <ExecutiveSummary summary={summary} agent={data.agent || 'Enterprise AI Dashboard'} />
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        <RootCause cause={rootCause} />
        <TimelineCard timeline={timeline} />
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        <CorrectiveActions actions={correctiveActions} />
        <PreventiveActions actions={preventiveActions} />
      </div>

      <Evidence evidence={evidence} />

      <SourceDocuments documents={citations} />

      <FollowUpSuggestions suggestions={suggestions} onSelect={onSuggestionSelect} />
    </div>
  );
}
