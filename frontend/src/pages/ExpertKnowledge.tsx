import { Mic, Play, Plus, Network, UserCog, Send } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';

export default function ExpertKnowledge() {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-foreground">Expert Knowledge Capture</h1>
        <p className="text-sm text-muted-foreground mt-1.5">Convert tacit expert experience into structured graph data</p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Mic className="h-5 w-5 text-primary" />
              Capture Experience
            </CardTitle>
            <CardDescription>Record voice notes or type operational knowledge</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="h-32 rounded-lg border-2 border-dashed flex flex-col items-center justify-center bg-muted/30 cursor-pointer hover:bg-muted/30 transition-colors">
              <div className="w-12 h-12 rounded-full bg-primary/20 flex items-center justify-center mb-2">
                <Mic className="h-6 w-6 text-primary" />
              </div>
              <p className="text-sm font-medium">Click to start recording</p>
            </div>
            
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <span className="w-full border-t border-border" />
              </div>
              <div className="relative flex justify-center text-xs uppercase">
                <span className="bg-card px-2 text-muted-foreground">Or type manually</span>
              </div>
            </div>

            <Textarea 
              placeholder='e.g., "If conveyor vibration exceeds 6 mm/s, inspect belt alignment before replacing bearings."' 
              className="min-h-[100px] bg-background"
            />
          </CardContent>
          <CardFooter className="justify-end">
            <Button className="gap-2">
              <Send className="h-4 w-4" />
              Extract Knowledge
            </Button>
          </CardFooter>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Network className="h-5 w-5 text-emerald-500" />
              Extracted Knowledge
            </CardTitle>
            <CardDescription>AI-structured data ready for the Knowledge Graph</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="rounded-lg border bg-card p-4 shadow-sm">
                <div className="flex justify-between items-start mb-4">
                  <Badge variant="outline" className="bg-primary/10 text-primary border-primary/20">Condition → Action</Badge>
                  <Button variant="ghost" size="sm" className="h-8 px-2 text-emerald-500 hover:text-emerald-600 hover:bg-emerald-500/10">Approve</Button>
                </div>
                
                <div className="flex items-center gap-2 text-sm flex-wrap">
                  <div className="px-3 py-1.5 rounded-md bg-muted border font-medium">
                    <span className="text-xs text-muted-foreground block mb-1">Condition</span>
                    Conveyor vibration {'>'} 6 mm/s
                  </div>
                  <Plus className="h-4 w-4 text-muted-foreground shrink-0 hidden sm:block" />
                  <div className="px-3 py-1.5 rounded-md bg-muted border font-medium">
                    <span className="text-xs text-muted-foreground block mb-1">Asset Target</span>
                    CV101 Conveyor Belt
                  </div>
                  <Play className="h-4 w-4 text-muted-foreground shrink-0 hidden sm:block" />
                  <div className="px-3 py-1.5 rounded-md bg-primary/10 border border-primary/20 text-primary font-medium">
                    <span className="text-xs text-primary/70 block mb-1">Action</span>
                    Inspect belt alignment
                  </div>
                </div>

                <div className="mt-4 flex items-center gap-2 text-xs text-muted-foreground">
                  <UserCog className="h-3 w-3" />
                  <span>Source: Rahul M. (Voice Note)</span>
                  <span className="mx-1">•</span>
                  <span>Confidence: 98%</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
