import { ExecutiveSummary } from './ExecutiveSummary';
import { RootCause } from './RootCause';
import { TimelineCard } from './TimelineCard';
import { Evidence } from './Evidence';
import { CorrectiveActions } from './CorrectiveActions';
import { PreventiveActions } from './PreventiveActions';
import { SourceDocuments } from './SourceDocuments';
import { ConfidenceBadge } from './ConfidenceBadge';
import { FollowUpSuggestions } from './FollowUpSuggestions';

export function EnterpriseDashboard({ data, onSuggestionSelect }: { data: any, onSuggestionSelect?: (s: string) => void }) {
  if (!data) return null;

  // Map the structured JSON to the enterprise components
  const summary = data.executive_summary || data.primary_answer;
  const rootCause = data.root_cause_analysis?.most_probable_root_cause;
  const timeline = data.historical_incidents?.timeline || [];
  const evidence = data.evidence || [];
  const correctiveActions = data.recommended_actions?.immediate_actions || [];
  const preventiveActions = data.recommended_actions?.preventive_actions || [];
  const confidence = data.confidence || data.root_cause_analysis?.confidence_score;
  const suggestions = data.follow_up_suggestions || [];
  // Use citations from root or evidence if any exist
  const citations = data.citations || evidence; 

  return (
    <div className="w-full space-y-4">
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
