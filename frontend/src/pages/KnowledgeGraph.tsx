import { useEffect, useState, useCallback } from 'react';
import ReactFlow, { MiniMap, Controls, Background, useNodesState, useEdgesState, MarkerType, Node, Edge } from 'reactflow';
import 'reactflow/dist/style.css';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { FileText, Activity, User, Settings, Loader2, Maximize, Minimize } from 'lucide-react';
import { apiClient } from '@/lib/api';
import { Button } from '@/components/ui/button';

const NODE_COLORS: Record<string, string> = {
  asset: '#3b82f6',
  document: '#8b5cf6',
  incident: '#ef4444',
  person: '#10b981',
  maintenance: '#f59e0b',
  sensor: '#06b6d4',
};

function buildReactFlowData(rawNodes: any[], rawEdges: any[]) {
  // 1. Smart Filtering: get a mix of assets and other node types
  const assets = rawNodes.filter(n => n.type === 'asset').slice(0, 15);
  const others = rawNodes.filter(n => n.type !== 'asset').slice(0, 10);
  const visibleNodes = [...assets, ...others];
  const visibleNodeIds = new Set(visibleNodes.map((n: any) => n.id));

  // 2. Structured Grid Layout (by type)
  let assetCount = 0;
  let otherCount = 0;

  const rfNodes: Node[] = visibleNodes.map((n: any) => {
    const isAsset = n.type === 'asset';
    const color = NODE_COLORS[isAsset ? 'asset' : 'document'] || '#6b7280';
    
    // Position assets in the middle row, others in top/bottom rows
    let x, y;
    if (isAsset) {
      x = (assetCount % 5) * 200 + 100;
      y = Math.floor(assetCount / 5) * 150 + 250;
      assetCount++;
    } else {
      x = (otherCount % 4) * 250 + 150;
      y = (otherCount % 2 === 0) ? 50 : 550; // alternate top and bottom
      otherCount++;
    }

    return {
      id: String(n.id),
      position: { x, y },
      data: { label: n.label || n.id },
      style: {
        background: `${color}15`,
        border: `2px solid ${color}`,
        borderRadius: '8px',
        color: '#e2e8f0',
        fontSize: '12px',
        fontWeight: 600,
        padding: '10px',
        width: 150,
        textAlign: 'center',
        boxShadow: `0 4px 6px -1px ${color}20`,
      },
    };
  });

  // 3. Smart Edge Filtering
  // Only connect visible nodes, and strictly limit edges per node to avoid hairballs
  const edgeCounts: Record<string, number> = {};
  const rfEdges: Edge[] = [];
  
  for (const e of rawEdges) {
    if (visibleNodeIds.has(e.source) && visibleNodeIds.has(e.target)) {
      // Allow max 2 edges originating from any node to keep graph clean
      edgeCounts[e.source] = (edgeCounts[e.source] || 0) + 1;
      if (edgeCounts[e.source] <= 2) {
        rfEdges.push({
          id: `e-${e.source}-${e.target}`,
          source: String(e.source),
          target: String(e.target),
          label: (e.label || '').replace(/_/g, ' ').toLowerCase(),
          animated: true,
          markerEnd: { type: MarkerType.ArrowClosed, color: '#475569' },
          style: { stroke: '#475569', strokeWidth: 1.5, opacity: 0.6 },
          labelStyle: { fill: '#94a3b8', fontSize: 10, fontWeight: 500 },
          labelBgStyle: { fill: '#0f172a', fillOpacity: 0.8 },
        });
      }
    }
    if (rfEdges.length >= 35) break; // Hard cap total edges
  }

  return { rfNodes, rfEdges };
}

export default function KnowledgeGraph() {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [loading, setLoading] = useState(true);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [graphStats, setGraphStats] = useState({ nodes: 0, edges: 0 });

  useEffect(() => {
    apiClient.get('/knowledge-graph/').then((data: any) => {
      const { rfNodes, rfEdges } = buildReactFlowData(data.nodes || [], data.edges || []);
      setNodes(rfNodes);
      setEdges(rfEdges);
      setGraphStats({ nodes: data.nodes?.length || 0, edges: data.edges?.length || 0 });
    }).catch(console.error).finally(() => setLoading(false));
  }, []);

  const onNodeClick = useCallback((_: any, node: Node) => {
    setSelectedNode(node);
  }, []);

  return (
    <div className={isFullscreen 
      ? "fixed inset-0 z-50 bg-background flex flex-col p-6 space-y-4" 
      : "h-[calc(100vh-8rem)] flex flex-col space-y-4"}>
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-foreground">Knowledge Graph Explorer</h1>
          <p className="text-sm text-muted-foreground mt-1.5">Interactive visualization of assets, documents, and relationships</p>
        </div>
        <div className="flex gap-4 items-center">
          <div className="flex gap-2">
            <Badge variant="outline" className="text-blue-400 border-blue-400/40">{graphStats.nodes} Nodes</Badge>
            <Badge variant="outline" className="text-purple-400 border-purple-400/40">{graphStats.edges} Edges</Badge>
          </div>
          <Button 
            variant="outline" 
            size="sm" 
            onClick={() => setIsFullscreen(!isFullscreen)}
            className="flex items-center gap-2"
          >
            {isFullscreen ? <><Minimize className="h-4 w-4" /> Exit Fullscreen</> : <><Maximize className="h-4 w-4" /> Fullscreen</>}
          </Button>
        </div>
      </div>
      
      <div className="flex flex-1 gap-4 min-h-0">
        <Card className="flex-1 overflow-hidden relative">
          {loading && (
            <div className="absolute inset-0 flex items-center justify-center z-10 bg-background/80">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
              <span className="ml-3 text-muted-foreground">Loading knowledge graph...</span>
            </div>
          )}
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onNodeClick={onNodeClick}
            fitView
            className="bg-muted/20"
          >
            <Controls />
            <MiniMap nodeStrokeColor="#888" nodeColor="#3b82f6" maskColor="rgba(0,0,0,0.2)" />
            <Background color="#333" gap={16} />
          </ReactFlow>
        </Card>
        
        <Card className="w-72 flex flex-col">
          <CardHeader>
            <CardTitle>Graph Legend</CardTitle>
            <CardDescription>Node types in this graph</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 flex-1">
            {Object.entries(NODE_COLORS).map(([type, color]) => (
              <div key={type} className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-md border-2 flex items-center justify-center" style={{ borderColor: color, background: `${color}22` }}>
                  {type === 'asset' && <Settings className="h-4 w-4" style={{ color }} />}
                  {type === 'document' && <FileText className="h-4 w-4" style={{ color }} />}
                  {type === 'incident' && <Activity className="h-4 w-4" style={{ color }} />}
                  {type === 'person' && <User className="h-4 w-4" style={{ color }} />}
                  {type === 'maintenance' && <Activity className="h-4 w-4" style={{ color }} />}
                  {type === 'sensor' && <Activity className="h-4 w-4" style={{ color }} />}
                </div>
                <span className="text-sm font-medium capitalize">{type}</span>
              </div>
            ))}
            
            {selectedNode && (
              <div className="mt-4 pt-4 border-t border-border">
                <h4 className="text-sm font-semibold mb-2">Selected Node</h4>
                <p className="text-xs text-primary font-medium">{selectedNode.data.label}</p>
                <p className="text-xs text-sm text-muted-foreground mt-1.5">ID: {selectedNode.id}</p>
              </div>
            )}

            {!selectedNode && (
              <div className="mt-4 pt-4 border-t border-border">
                <h4 className="text-sm font-semibold mb-2">Node Details</h4>
                <p className="text-xs text-muted-foreground">Click a node in the graph to view its details and relationships.</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
