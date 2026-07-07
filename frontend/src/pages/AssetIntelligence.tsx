import { Activity, Thermometer, Droplets, Zap } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const sensorData = [
  { time: '00:00', temp: 4, vib: 2.1 },
  { time: '04:00', temp: 4, vib: 2.3 },
  { time: '08:00', temp: 5, vib: 3.5 },
  { time: '12:00', temp: 6, vib: 5.2 },
  { time: '16:00', temp: 8, vib: 6.8 },
  { time: '20:00', temp: 4, vib: 2.8 },
];

export default function AssetIntelligence() {
  return (
    <div className="space-y-8">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-foreground">Asset Intelligence</h1>
          <p className="text-sm text-muted-foreground mt-1.5">Deep dive into equipment health and predictive maintenance</p>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-4">
        <Card className="md:col-span-1">
          <CardHeader>
            <CardTitle>Asset Hierarchy</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="space-y-1 pb-4">
              <div className="px-4 py-2 hover:bg-muted cursor-pointer font-medium text-sm">Main Plant</div>
              <div className="px-4 py-2 pl-8 hover:bg-muted cursor-pointer font-medium text-sm">Unit 1 - Processing</div>
              <div className="px-4 py-2 pl-12 bg-primary/10 text-primary border-r-2 border-primary cursor-pointer font-medium text-sm flex justify-between items-center">
                FM101 Bottle Filling Machine
                <Badge variant="destructive" className="h-5 text-[10px]">Alert</Badge>
              </div>
              <div className="px-4 py-2 pl-12 hover:bg-muted cursor-pointer text-sm text-muted-foreground">BW101 Bottle Washing Machine</div>
              <div className="px-4 py-2 pl-12 hover:bg-muted cursor-pointer text-sm text-muted-foreground">CM101 Bottle Capping Machine</div>
              <div className="px-4 py-2 pl-8 hover:bg-muted cursor-pointer font-medium text-sm">Unit 2 - Utilities</div>
            </div>
          </CardContent>
        </Card>

        <div className="md:col-span-3 space-y-6">
          <Card>
            <CardHeader className="pb-4 border-b">
              <div className="flex justify-between items-start">
                <div>
                  <div className="flex items-center gap-2">
                    <CardTitle className="text-2xl">FM101 Bottle Filling Machine</CardTitle>
                    <Badge variant="outline">Rotary Bottle Filling Machine</Badge>
                  </div>
                  <CardDescription className="mt-1">Installed: Jan 2023 • Last PM: 45 days ago</CardDescription>
                </div>
                <div className="text-right">
                  <div className="text-3xl font-bold text-amber-500">58%</div>
                  <div className="text-xs text-muted-foreground uppercase tracking-wider font-semibold">Health Score</div>
                </div>
              </div>
            </CardHeader>
            <CardContent className="pt-6">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
                <div className="flex flex-col gap-1 p-3 bg-muted rounded-lg border">
                  <span className="text-xs text-muted-foreground flex items-center gap-1"><Thermometer className="h-3 w-3" /> Temperature</span>
                  <span className="text-xl font-bold text-destructive">8°C <span className="text-xs font-normal text-muted-foreground">/ 6°C limit</span></span>
                </div>
                <div className="flex flex-col gap-1 p-3 bg-muted rounded-lg border">
                  <span className="text-xs text-muted-foreground flex items-center gap-1"><Activity className="h-3 w-3" /> Vibration</span>
                  <span className="text-xl font-bold text-destructive">8.5 mm/s</span>
                </div>
                <div className="flex flex-col gap-1 p-3 bg-muted rounded-lg border">
                  <span className="text-xs text-muted-foreground flex items-center gap-1"><Droplets className="h-3 w-3" /> Fill Level</span>
                  <span className="text-xl font-bold text-amber-500">Low</span>
                </div>
                <div className="flex flex-col gap-1 p-3 bg-muted rounded-lg border">
                  <span className="text-xs text-muted-foreground flex items-center gap-1"><Zap className="h-3 w-3" /> Power Draw</span>
                  <span className="text-xl font-bold">22 kW</span>
                </div>
              </div>

              <h4 className="text-sm font-semibold mb-4">Sensor Trends (Last 24h)</h4>
              <div className="h-[250px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={sensorData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                    <XAxis dataKey="time" stroke="#888" fontSize={12} tickLine={false} axisLine={false} />
                    <YAxis yAxisId="left" stroke="#888" fontSize={12} tickLine={false} axisLine={false} />
                    <YAxis yAxisId="right" orientation="right" stroke="#888" fontSize={12} tickLine={false} axisLine={false} />
                    <Tooltip contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #1e293b' }} />
                    <Line yAxisId="left" type="monotone" dataKey="temp" stroke="#f59e0b" strokeWidth={2} name="Temp (°C)" dot={false} />
                    <Line yAxisId="right" type="monotone" dataKey="vib" stroke="#ef4444" strokeWidth={2} name="Vibration (mm/s)" dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
