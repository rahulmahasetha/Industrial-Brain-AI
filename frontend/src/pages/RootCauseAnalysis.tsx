import { useState } from 'react';
import { Activity, ShieldAlert } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { apiClient } from '@/lib/api';

export default function RootCauseAnalysis() {
  const [description, setDescription] = useState("Bottle Filling Machine FM101 stopped due to low fill level and nozzle blockage");
  const [assetTag, setAssetTag] = useState("FM101");
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [result, setResult] = useState<any>(null);

  const handleAnalyze = async () => {
    setIsAnalyzing(true);
    try {
      const response = await apiClient.post('/rca/analyze', {
        description: description,
        asset_tag: assetTag
      });
      setResult(response);
    } catch (error) {
      console.error("Failed to analyze", error);
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-foreground">Root Cause Analysis</h1>
        <p className="text-sm text-muted-foreground mt-1.5">AI-driven anomaly investigation and resolution recommendations</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Describe Anomaly</CardTitle>
          <CardDescription>Enter the symptom or issue to generate a root cause tree</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4 mb-4">
            <Input 
              placeholder="Asset Tag (e.g. FM101)" 
              value={assetTag}
              onChange={(e) => setAssetTag(e.target.value)}
              className="w-32"
            />
            <Input 
              placeholder="e.g., Bottle Filling Machine FM101 stopped due to low fill level..." 
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="flex-1"
            />
            <Button className="w-32" onClick={handleAnalyze} disabled={isAnalyzing || !description}>
              {isAnalyzing ? "Analyzing..." : "Analyze Issue"}
            </Button>
          </div>
        </CardContent>
      </Card>

      {result && (
        <div className="grid gap-6 md:grid-cols-3">
          <Card className="md:col-span-2">
            <CardHeader>
              <CardTitle>Probable Root Causes</CardTitle>
              <CardDescription>Ranked by AI confidence based on historical data and manuals</CardDescription>
            </CardHeader>
            <CardContent className="space-y-8">
              {result.causes?.map((cause: any, idx: number) => (
                <div key={idx} className={`space-y-2 ${idx > 0 ? 'pt-4 border-t border-border' : ''}`}>
                  <div className="flex justify-between items-center">
                    <div className="flex items-center gap-2">
                      <Badge variant={cause.probability > 70 ? 'destructive' : cause.probability > 30 ? 'secondary' : 'outline'}
                             className={cause.probability > 30 && cause.probability <= 70 ? "bg-amber-500/20 text-amber-500 hover:bg-amber-500/30" : ""}>
                        {cause.probability}% Probability
                      </Badge>
                      <span className="font-semibold text-lg">{cause.description}</span>
                    </div>
                  </div>
                  <Progress value={cause.probability} className={`h-2 ${cause.probability > 70 ? 'bg-destructive/20 [&>div]:bg-destructive' : cause.probability > 30 ? 'bg-amber-500/20 [&>div]:bg-amber-500' : 'bg-blue-500/20 [&>div]:bg-blue-500'}`} />
                </div>
              ))}
            </CardContent>
          </Card>

          <div className="space-y-8">
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-lg flex items-center gap-2">
                  <ShieldAlert className="h-5 w-5 text-amber-500" />
                  Recommended Actions
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {result.recommendations?.map((rec: string, idx: number) => (
                  <div key={idx} className="flex gap-3 items-start">
                    <div className="bg-primary/20 text-primary rounded-full w-6 h-6 flex items-center justify-center shrink-0 text-sm font-bold">{idx + 1}</div>
                    <p className="text-sm">{rec}</p>
                  </div>
                ))}
                <Button className="w-full mt-2" variant="outline">Create Work Order</Button>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-lg flex items-center gap-2">
                  <Activity className="h-5 w-5 text-blue-500" />
                  Event Timeline
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex gap-3">
                    <div className="mt-1 w-3 h-3 rounded-full bg-amber-500 shrink-0" />
                    <div>
                      <p className="text-sm font-medium">Anomaly Detected</p>
                      <p className="text-xs text-muted-foreground">Recent</p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
}
