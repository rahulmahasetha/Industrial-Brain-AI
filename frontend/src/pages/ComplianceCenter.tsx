import { ShieldCheck, AlertTriangle, FileText } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Progress } from '@/components/ui/progress';

export default function ComplianceCenter() {
  return (
    <div className="space-y-8">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-foreground">Compliance Center</h1>
          <p className="text-sm text-muted-foreground mt-1.5">Automated regulatory adherence and risk alerts</p>
        </div>
        <Button>Run Audit Check</Button>
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        <Card className="bg-emerald-500/10 border-emerald-500/20">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-emerald-500 flex items-center gap-2">
              <ShieldCheck className="h-4 w-4" />
              Overall Compliance
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-emerald-500">92%</div>
            <Progress value={92} className="h-2 mt-3 bg-emerald-500/20 [&>div]:bg-emerald-500" />
          </CardContent>
        </Card>
        
        <Card className="bg-amber-500/10 border-amber-500/20">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-amber-500 flex items-center gap-2">
              <AlertTriangle className="h-4 w-4" />
              Identified Gaps
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-amber-500">3</div>
            <p className="text-xs text-amber-500/80 mt-2">Require attention in next 30 days</p>
          </CardContent>
        </Card>

        <Card className="bg-blue-500/10 border-blue-500/20">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-blue-500 flex items-center gap-2">
              <FileText className="h-4 w-4" />
              Standards Tracked
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-blue-500">14</div>
            <p className="text-xs text-blue-500/80 mt-2">Across 3 regulatory bodies</p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Compliance Gaps & Risks</CardTitle>
          <CardDescription>AI-identified deviations from uploaded regulatory standards</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Standard / Regulation</TableHead>
                <TableHead>Identified Gap</TableHead>
                <TableHead>Risk Level</TableHead>
                <TableHead>Related Asset</TableHead>
                <TableHead className="text-right">Action</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              <TableRow>
                <TableCell className="font-medium">ISO 22000 Clause 8.5</TableCell>
                <TableCell className="text-muted-foreground">Daily sanitation checklist missing sign-off for Line 2 filling zone.</TableCell>
                <TableCell><Badge variant="destructive">High</Badge></TableCell>
                <TableCell>Multiple Assets</TableCell>
                <TableCell className="text-right"><Button variant="outline" size="sm">Resolve</Button></TableCell>
              </TableRow>
              <TableRow>
                <TableCell className="font-medium">ISO 9001 Clause 8.6</TableCell>
                <TableCell className="text-muted-foreground">Final bottle quality inspection record missing for a released MangoDelight batch.</TableCell>
                <TableCell><Badge variant="secondary" className="bg-amber-500/20 text-amber-500">Medium</Badge></TableCell>
                <TableCell>CV101</TableCell>
                <TableCell className="text-right"><Button variant="outline" size="sm">Resolve</Button></TableCell>
              </TableRow>
              <TableRow>
                <TableCell className="font-medium">ISO 45001 Clause 8.1.2</TableCell>
                <TableCell className="text-muted-foreground">Hazard identification record for confined space entry not updated for 2026.</TableCell>
                <TableCell><Badge variant="secondary" className="bg-amber-500/20 text-amber-500">Medium</Badge></TableCell>
                <TableCell>Site Wide</TableCell>
                <TableCell className="text-right"><Button variant="outline" size="sm">Resolve</Button></TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
