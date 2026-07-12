import { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import { 
  Network, ZoomIn, ZoomOut, Maximize2, Search, Filter, Expand, Bot, 
  RefreshCw, Download, EyeOff, Calendar, BarChart3, 
  Copy, FileText, X, Info, LayoutGrid, Trash2
} from 'lucide-react';
import { apiClient } from '@/lib/api';
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '@/components/ui/card';
import { useNavigate } from 'react-router-dom';

function getGlowColor(hex: string, opacity: number = 0.5) {
  const cleanHex = hex.replace('#', '');
  if (cleanHex.length !== 6) return hex;
  const r = parseInt(cleanHex.substring(0, 2), 16);
  const g = parseInt(cleanHex.substring(2, 4), 16);
  const b = parseInt(cleanHex.substring(4, 6), 16);
  return `rgba(${r}, ${g}, ${b}, ${opacity})`;
}

export default function KnowledgeGraph() {
  const navigate = useNavigate();
  const [masterData, setMasterData] = useState<{ nodes: any[]; links: any[] }>({ nodes: [], links: [] });
  const [visibleNodeIds, setVisibleNodeIds] = useState<Set<string>>(new Set());
  const [hiddenNodeIds, setHiddenNodeIds] = useState<Set<string>>(new Set());
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const fgRef = useRef<any>(null);
  const [containerDimensions, setContainerDimensions] = useState({ width: 800, height: 600 });
  const containerRef = useRef<HTMLDivElement>(null);
  
  const [hoverNode, setHoverNode] = useState<any>(null);
  const [selectedNode, setSelectedNode] = useState<any>(null);
  const [hoverLink, setHoverLink] = useState<any>(null);
  const [selectedLink, setSelectedLink] = useState<any>(null);
  
  // Search & Filters
  const [searchQuery, setSearchQuery] = useState("");
  const [naturalLanguageQuery, setNaturalLanguageQuery] = useState("");
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [activeFilters, setActiveFilters] = useState<Set<string>>(new Set());
  const [activeRelationFilters, setActiveRelationFilters] = useState<Set<string>>(new Set());
  const [allTypes, setAllTypes] = useState<string[]>([]);
  const [allRelations, setAllRelations] = useState<string[]>([]);
  
  // Layout and view states
  const [layout, setLayout] = useState<'force' | 'circular' | 'hierarchical' | 'clustered' | 'timeline'>('force');
  const [sidebarTab, setSidebarTab] = useState<'details' | 'timeline' | 'analytics'>('details');
  const [evidenceMode, setEvidenceMode] = useState(false);
  const [contextMenu, setContextMenu] = useState<{ x: number; y: number; node: any } | null>(null);

  // Sidebar inline filters for selected node's connections
  const [sidebarSearch, setSidebarSearch] = useState("");
  const [sidebarDirection, setSidebarDirection] = useState<'all' | 'out' | 'in'>('all');
  const [sidebarType, setSidebarType] = useState<string>('all');

  // Reset sidebar inline filters when selected node changes
  useEffect(() => {
    setSidebarSearch("");
    setSidebarDirection("all");
    setSidebarType("all");
  }, [selectedNode]);

  // Handle outside click to close context menu
  useEffect(() => {
    const handleOutsideClick = () => setContextMenu(null);
    window.addEventListener('click', handleOutsideClick);
    return () => window.removeEventListener('click', handleOutsideClick);
  }, []);

  useEffect(() => {
    const updateDimensions = () => {
      if (containerRef.current) {
        setContainerDimensions({
          width: containerRef.current.clientWidth,
          height: containerRef.current.clientHeight
        });
      }
    };
    
    const resizeObserver = new ResizeObserver(() => {
      updateDimensions();
    });
    
    if (containerRef.current) {
      resizeObserver.observe(containerRef.current);
    }
    
    return () => {
      if (containerRef.current) {
        resizeObserver.unobserve(containerRef.current);
      }
      resizeObserver.disconnect();
    };
  }, []);

  useEffect(() => {
    const fetchGraphData = async () => {
      try {
        setLoading(true);
        const data = await apiClient.get('/knowledge-graph/?limit=1000');
        
        const formattedData = {
          nodes: data.nodes || [],
          links: (data.edges || []).map((e: any) => ({
            source: e.source,
            target: e.target,
            label: e.label,
            weight: e.weight || 1.0,
            color: '#475569'
          }))
        };
        
        setMasterData(formattedData as any);
        
        // Extract all unique node types
        const types = new Set<string>();
        formattedData.nodes.forEach((n: any) => {
          if (n.type) types.add(n.type.toLowerCase());
        });
        setAllTypes(Array.from(types).sort());

        // Extract all unique relationship types
        const relations = new Set<string>();
        formattedData.links.forEach((l: any) => {
          if (l.label) relations.add(l.label);
        });
        setAllRelations(Array.from(relations).sort());
        
        // Keep the initial cluster compact; expansion remains server-backed.
        const initialVisible = new Set<string>();
        formattedData.nodes.forEach((n: any) => {
          if (['asset', 'incident', 'maintenance', 'inspection', 'document', 'manual', 'sop', 'person', 'rca', 'qa', 'compliance', 'expert'].includes(n.type?.toLowerCase())) {
            initialVisible.add(n.id);
          }
        });
        
        if (initialVisible.size === 0) formattedData.nodes.forEach((n: any) => initialVisible.add(n.id));
        
        setVisibleNodeIds(initialVisible);
        setError(null);
      } catch (err) {
        console.error("Error fetching graph data:", err);
        setError("Failed to load knowledge graph data.");
      } finally {
        setLoading(false);
      }
    };

    fetchGraphData();
  }, []);

  // Compute rendered graph based on visibility, hidden filters, and toggles
  const renderData = useMemo(() => {
    const filteredNodes = masterData.nodes.filter((n: any) => {
      if (hiddenNodeIds.has(n.id)) return false;
      if (!visibleNodeIds.has(n.id)) return false;
      if (activeFilters.size > 0 && !activeFilters.has(n.type?.toLowerCase())) return false;
      return true;
    });

    const renderedNodeIds = new Set(filteredNodes.map((n: any) => n.id));

    const filteredLinks = masterData.links.filter((l: any) => {
      const sourceId = typeof l.source === 'object' ? l.source.id : l.source;
      const targetId = typeof l.target === 'object' ? l.target.id : l.target;
      
      const isVisible = renderedNodeIds.has(sourceId) && renderedNodeIds.has(targetId);
      if (!isVisible) return false;
      
      if (activeRelationFilters.size > 0 && !activeRelationFilters.has(l.label)) return false;
      return true;
    });

    return { nodes: filteredNodes, links: filteredLinks };
  }, [masterData, visibleNodeIds, activeFilters, activeRelationFilters, hiddenNodeIds]);

  // Handle layout transformations and node freezing
  useEffect(() => {
    const graph = fgRef.current;
    if (!graph) return;
    
    // Clear previous positions
    masterData.nodes.forEach((n: any) => {
      n.fx = undefined;
      n.fy = undefined;
    });
    
    if (layout === 'force') {
      if (graph.d3Force) {
        graph.d3Force('charge')?.strength(-150);
        graph.d3Force('link')?.distance(90);
        graph.d3Force('collide')?.radius((node: any) => node.type === 'asset' ? 22 : 14).strength(0.85);
        graph.d3ReheatSimulation?.();
      }
      return;
    }
    
    const nodes = renderData.nodes;
    const { width, height } = containerDimensions;
    
    if (layout === 'circular') {
      const N = nodes.length;
      const radius = Math.min(width, height) * 0.35;
      nodes.forEach((node: any, i: number) => {
        node.fx = radius * Math.cos(2 * Math.PI * i / N);
        node.fy = radius * Math.sin(2 * Math.PI * i / N);
      });
    } else if (layout === 'hierarchical') {
      const levels: Record<number, any[]> = {};
      nodes.forEach((node: any) => {
        let rank = 4;
        const type = node.type?.toLowerCase();
        if (type === 'asset') rank = 0;
        else if (['incident', 'maintenance', 'rca'].includes(type)) rank = 1;
        else if (['document', 'manual', 'sop', 'compliance'].includes(type)) rank = 2;
        else if (['technician', 'person', 'expert'].includes(type)) rank = 3;
        
        if (!levels[rank]) levels[rank] = [];
        levels[rank].push(node);
      });
      
      const ySpacing = height / (Object.keys(levels).length + 1);
      Object.entries(levels).forEach(([rankStr, levelNodes]) => {
        const rank = Number(rankStr);
        const y = -height/2.2 + (rank + 1) * ySpacing;
        const len = levelNodes.length;
        const xSpacing = width / (len + 1);
        levelNodes.forEach((node: any, i: number) => {
          node.fx = -width/2 + (i + 1) * xSpacing;
          node.fy = y;
        });
      });
    } else if (layout === 'clustered') {
      const types = Array.from(new Set(nodes.map((n: any) => n.type || 'unknown')));
      const N_types = types.length;
      const radius = Math.min(width, height) * 0.32;
      const centroids: Record<string, {x: number, y: number}> = {};
      types.forEach((type, i) => {
        centroids[type] = {
          x: radius * Math.cos(2 * Math.PI * i / N_types),
          y: radius * Math.sin(2 * Math.PI * i / N_types)
        };
      });
      
      nodes.forEach((node: any) => {
        const center = centroids[node.type || 'unknown'] || { x: 0, y: 0 };
        const angle = Math.random() * 2 * Math.PI;
        const offset = 15 + Math.random() * 30;
        node.fx = center.x + offset * Math.cos(angle);
        node.fy = center.y + offset * Math.sin(angle);
      });
    } else if (layout === 'timeline') {
      const getNumericDate = (n: any) => {
        if (n.metadata?.date_recorded) return new Date(n.metadata.date_recorded).getTime();
        if (n.metadata?.created_at) return new Date(n.metadata.created_at).getTime();
        if (n.metadata?.date) return new Date(n.metadata.date).getTime();
        return Date.now();
      };
      
      const sorted = [...nodes].sort((a, b) => getNumericDate(a) - getNumericDate(b));
      if (sorted.length > 0) {
        const tMin = getNumericDate(sorted[0]);
        const tMax = getNumericDate(sorted[sorted.length - 1]);
        const tRange = tMax - tMin || 1;
        
        nodes.forEach((node: any) => {
          const date = getNumericDate(node);
          node.fx = -width/2 + 80 + ((date - tMin) / tRange) * (width - 160);
          
          let typeIndex = 0;
          const type = node.type?.toLowerCase();
          if (type === 'asset') typeIndex = -1.5;
          else if (type === 'incident') typeIndex = -0.5;
          else if (type === 'maintenance') typeIndex = 0.5;
          else if (['document', 'manual', 'sop'].includes(type)) typeIndex = 1.5;
          
          node.fy = typeIndex * (height / 5.2);
        });
      }
    }
    
    if (graph.d3ReheatSimulation) {
      graph.d3ReheatSimulation();
    }
  }, [layout, renderData.nodes, masterData.nodes, containerDimensions]);

  // Highlight calculations for selections and hover
  const highlightedEntities = useMemo(() => {
    const highlightedNodes = new Set<string>();
    const highlightedLinks = new Set<string>();
    
    const activeNode = hoverNode || selectedNode;
    const activeLink = hoverLink || selectedLink;
    
    const getLinkId = (l: any) => {
      const s = typeof l.source === 'object' ? l.source.id : l.source;
      const t = typeof l.target === 'object' ? l.target.id : l.target;
      return `${s}|${t}|${l.label}`;
    };

    if (evidenceMode && selectedNode) {
      // Evidence Mode: Highlight only selected node and its direct cause/covers relationships
      highlightedNodes.add(selectedNode.id);
      renderData.links.forEach((l: any) => {
        const sId = typeof l.source === 'object' ? l.source.id : l.source;
        const tId = typeof l.target === 'object' ? l.target.id : l.target;
        if (sId === selectedNode.id || tId === selectedNode.id) {
          if (['caused_by', 'references', 'covers', 'reported_by'].includes(l.label)) {
            highlightedNodes.add(sId);
            highlightedNodes.add(tId);
            highlightedLinks.add(getLinkId(l));
          }
        }
      });
    } else if (activeNode) {
      highlightedNodes.add(activeNode.id);
      renderData.links.forEach((l: any) => {
        const sId = typeof l.source === 'object' ? l.source.id : l.source;
        const tId = typeof l.target === 'object' ? l.target.id : l.target;
        if (sId === activeNode.id || tId === activeNode.id) {
          highlightedNodes.add(sId);
          highlightedNodes.add(tId);
          highlightedLinks.add(getLinkId(l));
        }
      });
    } else if (activeLink) {
      const sId = typeof activeLink.source === 'object' ? activeLink.source.id : activeLink.source;
      const tId = typeof activeLink.target === 'object' ? activeLink.target.id : activeLink.target;
      highlightedNodes.add(sId);
      highlightedNodes.add(tId);
      highlightedLinks.add(getLinkId(activeLink));
    }
    
    const hasActiveFilter = !!(activeNode || activeLink || evidenceMode);
    
    return {
      nodes: highlightedNodes,
      links: highlightedLinks,
      hasActiveFilter,
      getLinkId
    };
  }, [renderData, hoverNode, selectedNode, hoverLink, selectedLink, evidenceMode]);

  const mergeGraph = useCallback((data: any, focusId?: string) => {
    setMasterData((current: any) => {
      const nodes = new Map(current.nodes.map((n: any) => [n.id, n]));
      (data.nodes || []).forEach((n: any) => nodes.set(n.id, n));
      const links = new Map(current.links.map((l: any) => [`${typeof l.source === 'object' ? l.source.id : l.source}|${typeof l.target === 'object' ? l.target.id : l.target}|${l.label}`, l]));
      (data.edges || []).forEach((e: any) => links.set(`${e.source}|${e.target}|${e.label}`, { ...e, color: '#475569' }));
      return { nodes: Array.from(nodes.values()), links: Array.from(links.values()) };
    });
    setVisibleNodeIds((current: Set<string>) => new Set([...current, ...(data.nodes || []).map((n: any) => n.id), ...(focusId ? [focusId] : [])]));
  }, []);

  const expandNeighbors = useCallback(async (nodeId: string) => {
    try {
      const data = await apiClient.get(`/knowledge-graph/neighbors/${encodeURIComponent(nodeId)}?limit=120`);
      mergeGraph(data, nodeId);
    } catch (err) {
      console.error('Unable to expand graph neighbors', err);
    }
  }, [mergeGraph]);

  const handleCollapseNode = useCallback((node: any) => {
    const connected = renderData.links.filter((l: any) => {
      const s = typeof l.source === 'object' ? l.source.id : l.source;
      const t = typeof l.target === 'object' ? l.target.id : l.target;
      return s === node.id || t === node.id;
    });
    
    const toCollapse = new Set<string>();
    connected.forEach((link: any) => {
      const s = typeof link.source === 'object' ? link.source.id : link.source;
      const t = typeof link.target === 'object' ? link.target.id : link.target;
      const targetId = s === node.id ? t : s;
      
      const neighborConnections = renderData.links.filter((l: any) => {
        const ns = typeof l.source === 'object' ? l.source.id : l.source;
        const nt = typeof l.target === 'object' ? l.target.id : l.target;
        return ns === targetId || nt === targetId;
      });
      
      if (neighborConnections.length <= 1) {
        toCollapse.add(targetId);
      }
    });
    
    setVisibleNodeIds(current => {
      const next = new Set(current);
      toCollapse.forEach(id => next.delete(id));
      return next;
    });
  }, [renderData]);

  const handleHideNode = useCallback((nodeId: string) => {
    setHiddenNodeIds(current => {
      const next = new Set(current);
      next.add(nodeId);
      return next;
    });
    setVisibleNodeIds(current => {
      const next = new Set(current);
      next.delete(nodeId);
      return next;
    });
  }, []);

  const getLinkColor = useCallback((link: any) => {
    const linkId = highlightedEntities.getLinkId(link);
    const isSelected = selectedLink && highlightedEntities.getLinkId(selectedLink) === linkId;
    const isHovered = hoverLink && highlightedEntities.getLinkId(hoverLink) === linkId;
    if (isSelected) return '#facc15';
    if (isHovered) return '#60a5fa';
    
    if (highlightedEntities.hasActiveFilter) {
      if (highlightedEntities.links.has(linkId)) {
        return '#818cf8';
      }
      return 'rgba(51, 65, 85, 0.05)'; // heavily faded edge
    }
    return '#334155';
  }, [highlightedEntities, selectedLink, hoverLink]);

  const getLinkWidth = useCallback((link: any) => {
    const linkId = highlightedEntities.getLinkId(link);
    const isSelected = selectedLink && highlightedEntities.getLinkId(selectedLink) === linkId;
    const isHovered = hoverLink && highlightedEntities.getLinkId(hoverLink) === linkId;
    if (isSelected) return 4;
    if (isHovered) return 2.5;
    
    if (highlightedEntities.hasActiveFilter) {
      return highlightedEntities.links.has(linkId) ? 2.2 : 0.4;
    }
    return 1;
  }, [highlightedEntities, selectedLink, hoverLink]);

  const getNodeColor = useCallback((node: any) => {
    const nodeId = typeof node === 'object' ? node.id : node;
    const nodeType = typeof node === 'object' ? node.type : 'unknown';
    const nodeLabel = typeof node === 'object' ? node.label : '';
    
    const isDimmed = highlightedEntities.hasActiveFilter && !highlightedEntities.nodes.has(nodeId);
    
    let baseColor = '#94a3b8';
    if (selectedNode && selectedNode.id === nodeId) {
      baseColor = '#facc15';
    } else if (hoverNode && hoverNode.id === nodeId) {
      baseColor = '#38bdf8';
    } else if (searchQuery && nodeLabel?.toLowerCase().includes(searchQuery.toLowerCase())) {
      baseColor = '#fbbf24';
    } else {
      switch (nodeType?.toLowerCase()) {
        case 'asset': baseColor = '#10b981'; break;
        case 'document': baseColor = '#6366f1'; break;
        case 'manual': baseColor = '#3b82f6'; break;
        case 'technician':
        case 'person': baseColor = '#f43f5e'; break;
        case 'incident': baseColor = '#ef4444'; break;
        case 'procedure': 
        case 'sop': baseColor = '#f59e0b'; break;
        case 'maintenance': baseColor = '#8b5cf6'; break;
        case 'inspection': baseColor = '#06b6d4'; break;
        case 'qa': baseColor = '#ec4899'; break;
        case 'rca': baseColor = '#fb7185'; break;
        case 'compliance': baseColor = '#14b8a6'; break;
        case 'expert': baseColor = '#d946ef'; break;
        default: baseColor = '#94a3b8';
      }
    }
    
    if (isDimmed) {
      return `${baseColor}22`; // dimmed
    }
    return baseColor;
  }, [highlightedEntities, selectedNode, hoverNode, searchQuery]);

  // View Controls
  const handleZoomIn = () => fgRef.current?.zoom(fgRef.current.zoom() * 1.5, 400);
  const handleZoomOut = () => fgRef.current?.zoom(fgRef.current.zoom() / 1.5, 400);
  const handleFitView = () => {
    fgRef.current?.zoomToFit(500);
  };
  const toggleFullscreen = () => setIsFullscreen(!isFullscreen);

  const handleResetGraph = () => {
    setSearchQuery("");
    setNaturalLanguageQuery("");
    setActiveFilters(new Set());
    setActiveRelationFilters(new Set());
    setHiddenNodeIds(new Set());
    setSelectedNode(null);
    setSelectedLink(null);
    setHoverNode(null);
    setHoverLink(null);
    setLayout('force');
    setEvidenceMode(false);
    
    const initialVisible = new Set<string>();
    masterData.nodes.forEach((n: any) => {
      if (['asset', 'incident', 'maintenance', 'inspection'].includes(n.type?.toLowerCase())) {
        initialVisible.add(n.id);
      }
    });
    if (initialVisible.size === 0) masterData.nodes.forEach((n: any) => initialVisible.add(n.id));
    setVisibleNodeIds(initialVisible);
    
    setTimeout(() => {
      fgRef.current?.zoomToFit(500);
    }, 150);
  };

  const handleExportPNG = () => {
    const canvas = fgRef.current?.canvas();
    if (canvas) {
      const dataURL = canvas.toDataURL("image/png");
      const link = document.createElement("a");
      link.download = "knowledge-graph-investigation.png";
      link.href = dataURL;
      link.click();
    }
  };

  const handleExportJSON = () => {
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(renderData, null, 2));
    const link = document.createElement("a");
    link.download = "knowledge-graph-data.json";
    link.href = dataStr;
    link.click();
  };

  const handleNodeClick = useCallback((node: any) => {
    setSelectedNode(node);
    setSelectedLink(null);
    if (fgRef.current) {
      fgRef.current.centerAt(node.x, node.y, 800);
      fgRef.current.zoom(2.5, 800);
    }
  }, []);

  const handleLinkClick = useCallback((link: any) => {
    setSelectedLink(link);
    setSelectedNode(null);
  }, []);

  // Text search submit
  const handleSearchSubmit = async (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && searchQuery) {
      try {
        const data = await apiClient.get(`/knowledge-graph/?q=${encodeURIComponent(searchQuery)}&limit=25`);
        mergeGraph(data);
        const match = data.nodes?.[0];
        if (match) {
          setSelectedNode(match);
          setSelectedLink(null);
          setTimeout(() => {
            const graphNode = fgRef.current?.graphData()?.nodes?.find((n: any) => n.id === match.id);
            if (graphNode) { 
              fgRef.current.centerAt(graphNode.x, graphNode.y, 800); 
              fgRef.current.zoom(2.8, 800); 
            }
          }, 80);
        }
      } catch (err) { 
        console.error('Graph search failed', err); 
      }
    }
  };

  // Natural Language Search Submit (e.g. "Show incidents related to FM101")
  const handleNLSearchSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!naturalLanguageQuery) return;
    
    // Parse target asset ID from user text
    const cleanQuery = naturalLanguageQuery.toLowerCase();
    const assetPatterns = masterData.nodes
      .filter(n => n.type?.toLowerCase() === 'asset')
      .map(n => n.id.toLowerCase());
      
    const matchedAssetId = assetPatterns.find(id => cleanQuery.includes(id));
    
    if (matchedAssetId) {
      const match = masterData.nodes.find(n => n.id.toLowerCase() === matchedAssetId);
      if (match) {
        handleNodeClick(match);
        await expandNeighbors(match.id);
        
        // Auto-filter to show Incidents and Maintenance logs related to this asset
        if (cleanQuery.includes('incident')) {
          setActiveFilters(new Set(['asset', 'incident']));
        } else if (cleanQuery.includes('maintenance')) {
          setActiveFilters(new Set(['asset', 'maintenance']));
        }
        
        setNaturalLanguageQuery("");
        return;
      }
    }

    // Default: Fallback to text query
    setSearchQuery(naturalLanguageQuery);
    const data = await apiClient.get(`/knowledge-graph/?q=${encodeURIComponent(naturalLanguageQuery)}&limit=25`);
    mergeGraph(data);
    setNaturalLanguageQuery("");
  };

  const toggleFilter = (type: string) => {
    const next = new Set(activeFilters);
    if (next.has(type)) next.delete(type);
    else next.add(type);
    setActiveFilters(next);
  };

  const toggleRelationFilter = (label: string) => {
    const next = new Set(activeRelationFilters);
    if (next.has(label)) next.delete(label);
    else next.add(label);
    setActiveRelationFilters(next);
  };

  // Pre-calculate selected node connected links for side panel
  const selectedNodeLinks = useMemo(() => {
    if (!selectedNode) return [];
    return renderData.links.filter((l: any) => {
      const s = typeof l.source === 'object' ? l.source.id : l.source;
      const t = typeof l.target === 'object' ? l.target.id : l.target;
      return s === selectedNode.id || t === selectedNode.id;
    });
  }, [selectedNode, renderData.links]);

  const sidebarAvailableTypes = useMemo(() => {
    if (!selectedNode) return [];
    const types = new Set<string>();
    selectedNodeLinks.forEach((link: any) => {
      const isSource = (typeof link.source === 'object' ? link.source.id : link.source) === selectedNode.id;
      const connectedNode = isSource ? link.target : link.source;
      const connectedNodeObj = typeof connectedNode === 'object' ? connectedNode : masterData.nodes.find(n => n.id === connectedNode);
      if (connectedNodeObj?.type) {
        types.add(connectedNodeObj.type.toLowerCase());
      }
    });
    return Array.from(types).sort();
  }, [selectedNode, selectedNodeLinks, masterData.nodes]);

  const filteredSidebarLinks = useMemo(() => {
    if (!selectedNode) return [];
    
    return selectedNodeLinks.filter((link: any) => {
      const isSource = (typeof link.source === 'object' ? link.source.id : link.source) === selectedNode.id;
      const connectedNode = isSource ? link.target : link.source;
      const connectedNodeObj = typeof connectedNode === 'object' ? connectedNode : masterData.nodes.find(n => n.id === connectedNode);
      
      const label = connectedNodeObj?.label || String(connectedNode);
      const type = connectedNodeObj?.type || 'unknown';
      
      if (sidebarSearch && !label.toLowerCase().includes(sidebarSearch.toLowerCase()) && !link.label.toLowerCase().includes(sidebarSearch.toLowerCase())) {
        return false;
      }
      
      if (sidebarDirection === 'out' && !isSource) return false;
      if (sidebarDirection === 'in' && isSource) return false;
      
      if (sidebarType !== 'all' && type.toLowerCase() !== sidebarType.toLowerCase()) return false;
      
      return true;
    });
  }, [selectedNode, selectedNodeLinks, masterData.nodes, sidebarSearch, sidebarDirection, sidebarType]);

  // Analytics Metrics
  const analyticsData = useMemo(() => {
    const nodes = renderData.nodes;
    const links = renderData.links;
    
    // Connected Components calculation (BFS)
    const adj: Record<string, string[]> = {};
    nodes.forEach(n => adj[n.id] = []);
    links.forEach(l => {
      const s = typeof l.source === 'object' ? l.source.id : l.source;
      const t = typeof l.target === 'object' ? l.target.id : l.target;
      if (adj[s]) adj[s].push(t);
      if (adj[t]) adj[t].push(s);
    });
    
    const visited = new Set<string>();
    let componentsCount = 0;
    nodes.forEach(n => {
      if (!visited.has(n.id)) {
        componentsCount++;
        const queue = [n.id];
        visited.add(n.id);
        while(queue.length > 0) {
          const curr = queue.shift()!;
          (adj[curr] || []).forEach(neigh => {
            if (!visited.has(neigh)) {
              visited.add(neigh);
              queue.push(neigh);
            }
          });
        }
      }
    });

    // Centrality calculations (Degree Centrality)
    const degrees: Record<string, number> = {};
    nodes.forEach(n => degrees[n.id] = 0);
    links.forEach(l => {
      const s = typeof l.source === 'object' ? l.source.id : l.source;
      const t = typeof l.target === 'object' ? l.target.id : l.target;
      if (degrees[s] !== undefined) degrees[s]++;
      if (degrees[t] !== undefined) degrees[t]++;
    });
    
    let maxNodeId = '';
    let maxDegree = 0;
    Object.entries(degrees).forEach(([id, deg]) => {
      if (deg > maxDegree) {
        maxDegree = deg;
        maxNodeId = id;
      }
    });
    const mostConnected = nodes.find(n => n.id === maxNodeId);
    
    // Density calculation: E / (V * (V-1) / 2) for undirected graph
    const V = nodes.length;
    const E = links.length;
    const density = V > 1 ? (2 * E) / (V * (V - 1)) : 0;

    // Distribution by Type
    const typeDistribution: Record<string, number> = {};
    nodes.forEach(n => {
      const t = n.type || 'Unknown';
      typeDistribution[t] = (typeDistribution[t] || 0) + 1;
    });

    return {
      totalNodes: V,
      totalEdges: E,
      componentsCount,
      mostConnected,
      maxDegree,
      density,
      typeDistribution
    };
  }, [renderData]);

  // Asset Event Timeline
  const assetTimelineEvents = useMemo(() => {
    if (!selectedNode || selectedNode.type?.toLowerCase() !== 'asset') return [];
    
    const events: any[] = [];
    selectedNodeLinks.forEach((link: any) => {
      const isSource = (typeof link.source === 'object' ? link.source.id : link.source) === selectedNode.id;
      const connectedNode = isSource ? link.target : link.source;
      const connectedNodeObj = typeof connectedNode === 'object' ? connectedNode : masterData.nodes.find(n => n.id === connectedNode);
      
      if (connectedNodeObj) {
        const type = connectedNodeObj.type?.toLowerCase();
        if (['incident', 'maintenance', 'inspection', 'rca', 'sop', 'manual'].includes(type)) {
          const date = connectedNodeObj.metadata?.date_recorded || 
                       connectedNodeObj.metadata?.created_at || 
                       connectedNodeObj.metadata?.date;
                       
          events.push({
            id: connectedNodeObj.id,
            label: connectedNodeObj.label,
            type: connectedNodeObj.type,
            date: date ? new Date(date) : null,
            dateString: date ? new Date(date).toLocaleDateString() : 'Unknown Date',
            description: connectedNodeObj.metadata?.observation || connectedNodeObj.metadata?.task_description || connectedNodeObj.metadata?.findings || 'No description available',
            color: getNodeColor(connectedNodeObj)
          });
        }
      }
    });
    
    // Sort chronologically (newest first)
    return events.sort((a, b) => {
      if (!a.date) return 1;
      if (!b.date) return -1;
      return b.date.getTime() - a.date.getTime();
    });
  }, [selectedNode, selectedNodeLinks, masterData.nodes, getNodeColor]);

  return (
    <div className={isFullscreen ? "fixed inset-0 z-50 flex flex-col p-6 gap-6 bg-slate-950 overflow-hidden text-white" : "flex-1 flex flex-col h-[calc(100vh-4rem)] p-6 gap-6 bg-slate-950 overflow-hidden text-white"}>
      {/* Top Header Section */}
      <div className="flex items-start justify-between flex-wrap gap-4 shrink-0">
        <div>
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
            <Network className="w-8 h-8 text-indigo-400" />
            Knowledge Graph Explorer
          </h1>
          <p className="text-slate-400 mt-1">Enterprise-grade digital twin neural network and relationship mapping.</p>
        </div>

        {/* Toolbar */}
        <div className="flex items-center gap-3 flex-wrap">
          <form onSubmit={handleNLSearchSubmit} className="flex items-center gap-2 bg-slate-900/80 backdrop-blur-md px-1.5 py-1 rounded-lg border border-slate-800 shadow-xl">
            <Bot className="w-4 h-4 text-indigo-400 ml-2 shrink-0" />
            <input 
              type="text" 
              placeholder="Ask Copilot (e.g. Incidents for FM101)..." 
              value={naturalLanguageQuery}
              onChange={(e) => setNaturalLanguageQuery(e.target.value)}
              className="bg-transparent text-xs rounded-md pl-1 pr-3 py-1 placeholder-slate-500 focus:outline-none w-52 focus:w-72 transition-all text-white border-0"
            />
            <button 
              type="submit" 
              className="bg-indigo-650 hover:bg-indigo-500 text-white rounded px-2.5 py-1 text-[10px] font-semibold transition-all shadow-md shrink-0"
            >
              Ask
            </button>
          </form>

          <div className="flex items-center gap-1.5 bg-slate-900/80 backdrop-blur-md p-1.5 rounded-lg border border-slate-800 shadow-xl">
            <div className="relative group">
              <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
              <input 
                type="text" 
                placeholder="Search nodes (Enter)..." 
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={handleSearchSubmit}
                className="bg-slate-950/60 border border-slate-800 text-xs rounded pl-8 pr-3 py-1 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 w-36 transition-all focus:w-48 text-white"
              />
            </div>
            
            <div className="w-px h-5 bg-slate-800 mx-1.5"></div>
            
            <button onClick={handleResetGraph} className="p-1.5 hover:bg-slate-800 rounded text-slate-400 hover:text-white transition-colors" title="Reset Graph">
              <RefreshCw className="w-3.5 h-3.5" />
            </button>
            <button onClick={handleZoomIn} className="p-1.5 hover:bg-slate-800 rounded text-slate-400 hover:text-white transition-colors" title="Zoom In">
              <ZoomIn className="w-3.5 h-3.5" />
            </button>
            <button onClick={handleZoomOut} className="p-1.5 hover:bg-slate-800 rounded text-slate-400 hover:text-white transition-colors" title="Zoom Out">
              <ZoomOut className="w-3.5 h-3.5" />
            </button>
            <button onClick={handleFitView} className="p-1.5 hover:bg-slate-800 rounded text-slate-400 hover:text-white transition-colors" title="Fit View">
              <Maximize2 className="w-3.5 h-3.5" />
            </button>
            <button onClick={toggleFullscreen} className={`p-1.5 rounded transition-colors ${isFullscreen ? 'bg-indigo-650 text-white' : 'hover:bg-slate-800 text-slate-400 hover:text-white'}`} title="Fullscreen">
              <Maximize2 className="w-3.5 h-3.5 rotate-45" />
            </button>
            
            <div className="w-px h-5 bg-slate-800 mx-1.5"></div>
            
            <button onClick={handleExportPNG} className="p-1.5 hover:bg-slate-800 rounded text-slate-400 hover:text-white transition-colors" title="Export PNG Image">
              <Download className="w-3.5 h-3.5" />
            </button>
            <button onClick={handleExportJSON} className="p-1.5 hover:bg-slate-800 rounded text-slate-400 hover:text-white transition-colors" title="Export JSON Data">
              <FileText className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>

      {/* Main Content Workspace Layout */}
      <div className="flex-1 flex gap-6 min-h-0 relative">
        
        {/* Left Control Sidebar */}
        <div className="w-64 flex-shrink-0 bg-slate-900/60 border border-slate-850 rounded-2xl p-4 flex flex-col gap-5 overflow-y-auto">
          {/* Layout Controls */}
          <div>
            <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2.5 flex items-center gap-1.5">
              <LayoutGrid className="w-3.5 h-3.5 text-indigo-400" />
              Graph Layout Models
            </h4>
            <div className="grid grid-cols-2 gap-1.5">
              {(['force', 'circular', 'hierarchical', 'clustered', 'timeline'] as const).map((l) => (
                <button
                  key={l}
                  onClick={() => setLayout(l)}
                  className={`px-2 py-1.5 text-[10px] rounded border font-semibold capitalize transition-all text-center ${
                    layout === l 
                      ? 'bg-indigo-650 border-indigo-500 text-white shadow-lg shadow-indigo-500/10' 
                      : 'bg-slate-950/40 border-slate-850 text-slate-400 hover:bg-slate-850 hover:text-slate-200'
                  }`}
                >
                  {l === 'force' ? 'Force Directed' : l}
                </button>
              ))}
            </div>
          </div>

          <div className="h-px bg-slate-850"></div>

          {/* Node Type Filters */}
          <div>
            <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2.5 flex items-center gap-1.5">
              <Filter className="w-3.5 h-3.5 text-indigo-400" />
              Entity Filters
            </h4>
            <div className="space-y-1.5 max-h-[160px] overflow-y-auto pr-1 custom-scrollbar">
              {allTypes.map(t => (
                <label 
                  key={t}
                  className="flex items-center gap-2 text-xs text-slate-300 hover:text-white cursor-pointer select-none py-0.5"
                >
                  <input
                    type="checkbox"
                    checked={activeFilters.size === 0 || activeFilters.has(t)}
                    onChange={() => toggleFilter(t)}
                    className="rounded border-slate-800 text-indigo-600 focus:ring-indigo-500 bg-slate-950 w-3.5 h-3.5"
                  />
                  <span className="capitalize">{t}</span>
                </label>
              ))}
            </div>
          </div>

          <div className="h-px bg-slate-850"></div>

          {/* Relationship Filter Toggles */}
          <div>
            <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2.5 flex items-center gap-1.5">
              <Network className="w-3.5 h-3.5 text-indigo-400" />
              Relation Filters
            </h4>
            <div className="space-y-1.5 max-h-[160px] overflow-y-auto pr-1 custom-scrollbar">
              {allRelations.map(rel => (
                <label 
                  key={rel}
                  className="flex items-center gap-2 text-xs text-slate-300 hover:text-white cursor-pointer select-none py-0.5"
                >
                  <input
                    type="checkbox"
                    checked={activeRelationFilters.size === 0 || activeRelationFilters.has(rel)}
                    onChange={() => toggleRelationFilter(rel)}
                    className="rounded border-slate-800 text-indigo-600 focus:ring-indigo-500 bg-slate-950 w-3.5 h-3.5"
                  />
                  <span className="font-mono text-[10px]">{rel}</span>
                </label>
              ))}
            </div>
          </div>

          <div className="h-px bg-slate-850"></div>

          {/* Evidence Mode Switch */}
          {selectedNode && (
            <div className="bg-slate-950/40 border border-slate-850 rounded-xl p-3 flex flex-col gap-2 shrink-0">
              <div className="flex items-center justify-between">
                <span className="text-[10px] uppercase font-bold tracking-wider text-slate-400">Evidence Mode</span>
                <button
                  onClick={() => setEvidenceMode(!evidenceMode)}
                  className={`w-8 h-4 rounded-full transition-all relative ${evidenceMode ? 'bg-indigo-600' : 'bg-slate-800'}`}
                >
                  <div className={`w-3.5 h-3.5 rounded-full bg-white absolute top-0.25 transition-all shadow ${evidenceMode ? 'right-0.25' : 'left-0.25'}`} />
                </button>
              </div>
              <p className="text-[9px] text-slate-500 leading-normal">
                Highlights only relationship nodes containing RAG evidence, fading out others.
              </p>
            </div>
          )}
        </div>

        {/* Central Canvas Visualizer */}
        <div 
          ref={containerRef}
          className="flex-1 bg-slate-950/40 border border-slate-850 rounded-2xl overflow-hidden shadow-2xl relative backdrop-blur-sm bg-[radial-gradient(ellipse_at_center,rgba(30,41,59,0.35),rgba(15,23,42,0.95))] after:content-[''] after:absolute after:inset-0 after:bg-[radial-gradient(rgba(99,102,241,0.035)_1px,transparent_0)] after:bg-[size:20px_20px] after:pointer-events-none"
        >
          {loading ? (
            <div className="absolute inset-0 flex flex-col items-center justify-center bg-slate-950/60 backdrop-blur-sm z-10">
              <div className="w-12 h-12 border-4 border-indigo-500/30 border-t-indigo-500 rounded-full animate-spin"></div>
              <p className="text-indigo-300 mt-4 font-medium animate-pulse">Initializing Neural Graph...</p>
            </div>
          ) : error ? (
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-6 max-w-md text-center">
                <p className="text-red-400 font-medium">{error}</p>
              </div>
            </div>
          ) : (
            <>
              <ForceGraph2D
                ref={fgRef}
                width={containerDimensions.width}
                height={containerDimensions.height}
                graphData={renderData}
                nodeLabel="label"
                nodeColor={getNodeColor}
                nodeRelSize={6}
                linkColor={getLinkColor}
                linkWidth={getLinkWidth}
                linkDirectionalArrowLength={3.5}
                linkDirectionalArrowRelPos={1}
                
                linkDirectionalParticles={(link: any) => {
                  const linkId = highlightedEntities.getLinkId(link);
                  if (selectedLink && highlightedEntities.getLinkId(selectedLink) === linkId) return 6;
                  if (hoverLink && highlightedEntities.getLinkId(hoverLink) === linkId) return 4;
                  return highlightedEntities.links.has(linkId) ? 3 : 0;
                }}
                linkDirectionalParticleWidth={(link: any) => {
                  const linkId = highlightedEntities.getLinkId(link);
                  return (selectedLink && highlightedEntities.getLinkId(selectedLink) === linkId) ? 3.5 : 2;
                }}
                linkDirectionalParticleSpeed={0.012}
                
                d3VelocityDecay={0.3}
                d3AlphaDecay={0.02}
                cooldownTicks={100}
                
                onNodeHover={setHoverNode}
                onNodeClick={handleNodeClick}
                onLinkHover={setHoverLink}
                onLinkClick={handleLinkClick}
                onNodeRightClick={(node, event) => {
                  event.preventDefault();
                  setContextMenu({
                    x: event.clientX,
                    y: event.clientY,
                    node
                  });
                }}
                backgroundColor="transparent"
                
                // Canvas Edge labels rendering
                linkCanvasObjectMode={() => "after"}
                linkCanvasObject={(link: any, ctx, globalScale) => {
                  const linkId = highlightedEntities.getLinkId(link);
                  const isLinkActive = highlightedEntities.links.has(linkId);
                  const isLinkSelected = selectedLink && highlightedEntities.getLinkId(selectedLink) === linkId;
                  const isLinkHovered = hoverLink && highlightedEntities.getLinkId(hoverLink) === linkId;
                  
                  const isDimmed = highlightedEntities.hasActiveFilter && !isLinkActive;
                  if (isDimmed) return;

                  const shouldShow = (globalScale >= 2.2) || isLinkSelected || isLinkHovered || isLinkActive;
                  if (!shouldShow) return;
                  
                  const start = link.source;
                  const end = link.target;
                  if (!start || !end || typeof start !== 'object' || typeof end !== 'object') return;
                  if (!Number.isFinite(start.x) || !Number.isFinite(start.y) || !Number.isFinite(end.x) || !Number.isFinite(end.y)) return;
                  
                  const textPos = {
                    x: start.x + (end.x - start.x) / 2,
                    y: start.y + (end.y - start.y) / 2
                  };
                  
                  const relLink = { x: end.x - start.x, y: end.y - start.y };
                  let textAngle = Math.atan2(relLink.y, relLink.x);
                  if (textAngle > Math.PI / 2) textAngle = -(Math.PI - textAngle);
                  if (textAngle < -Math.PI / 2) textAngle = -(-Math.PI - textAngle);
                  
                  const fontSize = 8.5 / globalScale;
                  ctx.font = `${isLinkSelected || isLinkHovered ? 'bold' : 'normal'} ${fontSize}px sans-serif`;
                  
                  ctx.save();
                  ctx.translate(textPos.x, textPos.y);
                  ctx.rotate(textAngle);
                  ctx.textAlign = 'center';
                  ctx.textBaseline = 'middle';
                  
                  const textWidth = ctx.measureText(link.label).width;
                  ctx.fillStyle = 'rgba(15, 23, 42, 0.75)';
                  ctx.fillRect(-textWidth / 2 - 2, -fontSize - 1, textWidth + 4, fontSize + 2);
                  
                  ctx.fillStyle = isLinkSelected || isLinkHovered ? '#facc15' : isLinkActive ? '#a5b4fc' : '#94a3b8';
                  ctx.fillText(link.label, 0, -fontSize / 2);
                  ctx.restore();
                }}

                // Render 3D glassmorphic spheres and dynamic labels
                nodeCanvasObjectMode={() => "replace"}
                nodeCanvasObject={(node: any, ctx, globalScale) => {
                  if (typeof node.x !== 'number' || typeof node.y !== 'number' || !Number.isFinite(node.x) || !Number.isFinite(node.y)) {
                    return; // Skip render if layout hasn't assigned valid coordinates yet
                  }

                  const label = node.label;
                  const fontSize = 10 / globalScale;
                  const isDimmed = highlightedEntities.hasActiveFilter && !highlightedEntities.nodes.has(node.id);
                  const isSelected = selectedNode && selectedNode.id === node.id;
                  const isHovered = hoverNode && hoverNode.id === node.id;
                  const isSearchMatch = searchQuery && label?.toLowerCase().includes(searchQuery.toLowerCase());
                  
                  const radius = node.type === 'asset' ? 10 : 8;
                  const baseColor = getNodeColor(node);
                  
                  // 1. Draw glowing outer halos
                  if (isSelected || isHovered) {
                    ctx.beginPath();
                    ctx.arc(node.x, node.y, radius + (isSelected ? 5.5 : 3.5), 0, 2 * Math.PI);
                    ctx.fillStyle = isSelected ? 'rgba(250, 204, 21, 0.12)' : 'rgba(56, 189, 248, 0.12)';
                    ctx.fill();
                    
                    ctx.beginPath();
                    ctx.arc(node.x, node.y, radius + (isSelected ? 3.5 : 2), 0, 2 * Math.PI);
                    ctx.strokeStyle = isSelected ? '#facc15' : '#38bdf8';
                    ctx.lineWidth = (isSelected ? 2 : 1.2) / globalScale;
                    ctx.stroke();
                  } else if (isSearchMatch) {
                    ctx.beginPath();
                    ctx.arc(node.x, node.y, radius + 3, 0, 2 * Math.PI);
                    ctx.strokeStyle = '#fbbf24';
                    ctx.lineWidth = 1.5 / globalScale;
                    ctx.stroke();
                  }

                  // 2. Draw node body with 3D-effect radial gradient
                  const gradient = ctx.createRadialGradient(
                    node.x - radius * 0.2,
                    node.y - radius * 0.2,
                    radius * 0.1,
                    node.x,
                    node.y,
                    radius
                  );
                  
                  let startColor = baseColor;
                  let endColor = baseColor;
                  if (isDimmed) {
                    startColor = getGlowColor(baseColor.substring(0, 7), 0.25);
                    endColor = getGlowColor(baseColor.substring(0, 7), 0.08);
                  } else {
                    startColor = getGlowColor(baseColor, 0.95);
                    endColor = getGlowColor(baseColor, 0.65);
                  }
                  
                  gradient.addColorStop(0, startColor);
                  gradient.addColorStop(1, endColor);
                  
                  ctx.beginPath();
                  ctx.arc(node.x, node.y, radius, 0, 2 * Math.PI);
                  ctx.fillStyle = gradient;
                  ctx.fill();
                  
                  // Soft outer rim stroke for depth
                  ctx.strokeStyle = isDimmed ? 'rgba(255, 255, 255, 0.03)' : 'rgba(255, 255, 255, 0.2)';
                  ctx.lineWidth = 0.8 / globalScale;
                  ctx.stroke();

                  // 3. Draw text label
                  const shouldShowLabel = !isDimmed && (
                    globalScale >= 2.2 || 
                    isHovered || 
                    isSelected ||
                    (highlightedEntities.hasActiveFilter && highlightedEntities.nodes.has(node.id))
                  );

                  if (shouldShowLabel && label) {
                    ctx.font = `${isSelected ? 'bold' : 'normal'} ${fontSize}px sans-serif`;
                    ctx.textAlign = 'center';
                    ctx.textBaseline = 'middle';
                    
                    const labelBgColor = isSearchMatch 
                      ? 'rgba(251, 191, 36, 0.95)' 
                      : isSelected 
                        ? 'rgba(79, 70, 229, 0.95)' 
                        : 'rgba(15, 23, 42, 0.85)';
                    
                    const textWidth = ctx.measureText(label).width;
                    const bckgDimensions = [textWidth, fontSize].map(n => n + fontSize * 0.3);
                    
                    ctx.fillStyle = labelBgColor;
                    ctx.fillRect(node.x - bckgDimensions[0] / 2, node.y + radius + 4, bckgDimensions[0], bckgDimensions[1]);
                    
                    ctx.fillStyle = isSearchMatch || isSelected ? '#ffffff' : 'rgba(241, 245, 249, 0.95)';
                    ctx.fillText(label, node.x, node.y + radius + 4 + (fontSize / 2));
                  }
                }}
              />

              {/* Floating Legend */}
              <div className="absolute bottom-4 left-4 bg-slate-900/90 backdrop-blur-md p-3.5 rounded-xl border border-slate-800 shadow-2xl max-w-[280px] z-10 text-[11px]">
                <h4 className="font-semibold text-slate-200 mb-2 flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-indigo-500 animate-pulse"></span>
                  Node Types Key
                </h4>
                <div className="grid grid-cols-2 gap-x-4 gap-y-1.5 text-slate-300 font-medium">
                  <div className="flex items-center gap-2">
                    <span className="w-2.5 h-2.5 rounded-full bg-[#10b981] shadow-sm"></span>
                    <span>Asset</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="w-2.5 h-2.5 rounded-full bg-[#6366f1] shadow-sm"></span>
                    <span>Document</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="w-2.5 h-2.5 rounded-full bg-[#3b82f6] shadow-sm"></span>
                    <span>Manual</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="w-2.5 h-2.5 rounded-full bg-[#f43f5e] shadow-sm"></span>
                    <span>Person</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="w-2.5 h-2.5 rounded-full bg-[#ef4444] shadow-sm"></span>
                    <span>Incident</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="w-2.5 h-2.5 rounded-full bg-[#f59e0b] shadow-sm"></span>
                    <span>SOP / Proc</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="w-2.5 h-2.5 rounded-full bg-[#8b5cf6] shadow-sm"></span>
                    <span>Maint.</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="w-2.5 h-2.5 rounded-full bg-[#06b6d4] shadow-sm"></span>
                    <span>Inspection</span>
                  </div>
                </div>
                <div className="mt-2.5 pt-2.5 border-t border-slate-800 text-[10px] text-slate-400 flex flex-col gap-1">
                  <div>💡 Left Click: Inspect Entity / Link</div>
                  <div>💡 Right Click: Context Commands</div>
                </div>
              </div>
            </>
          )}
        </div>

        {/* Right Tabbed Details Sidebar */}
        <Card className="w-[380px] flex-shrink-0 bg-slate-900/60 backdrop-blur-xl border-slate-850 shadow-2xl flex flex-col h-full overflow-hidden">
          <CardHeader className="pb-3 border-b border-slate-800 bg-slate-900/80 shrink-0">
            {selectedNode ? (
              <div className="flex items-start justify-between">
                <div className="min-w-0">
                  <span 
                    className="px-2 py-0.5 text-[9px] font-bold uppercase tracking-wider rounded-full mb-1.5 inline-block text-white"
                    style={{ backgroundColor: getNodeColor(selectedNode) }}
                  >
                    {selectedNode.type || 'Entity'}
                  </span>
                  <CardTitle className="text-lg font-bold text-white break-words pr-2 truncate">{selectedNode.label}</CardTitle>
                  <CardDescription className="text-slate-500 font-mono text-[10px] mt-0.5 truncate">{selectedNode.id}</CardDescription>
                </div>
                <button onClick={() => setSelectedNode(null)} className="text-slate-400 hover:text-white p-1 hover:bg-slate-800 rounded shrink-0">
                  <X className="w-4 h-4" />
                </button>
              </div>
            ) : selectedLink ? (
              <div className="flex items-start justify-between">
                <div>
                  <span className="px-2 py-0.5 text-[9px] font-bold uppercase tracking-wider text-indigo-300 bg-indigo-950 border border-indigo-900/40 rounded-full mb-1.5 inline-block">
                    Relationship
                  </span>
                  <CardTitle className="text-lg font-bold text-white break-words pr-2">{selectedLink.label}</CardTitle>
                  <CardDescription className="text-slate-500 text-[10px] mt-0.5">Connection details</CardDescription>
                </div>
                <button onClick={() => setSelectedLink(null)} className="text-slate-400 hover:text-white p-1 hover:bg-slate-800 rounded shrink-0">
                  <X className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <div>
                <CardTitle className="text-lg font-bold text-white">Investigation Panel</CardTitle>
                <CardDescription className="text-slate-500 text-[10px] mt-0.5">Select a node or edge to begin</CardDescription>
              </div>
            )}
            
            {/* Sidebar Navigation Tabs */}
            <div className="flex bg-slate-950/80 p-0.5 rounded border border-slate-850 mt-3 text-xs">
              <button 
                onClick={() => setSidebarTab('details')}
                className={`flex-1 py-1 rounded font-semibold transition-all ${sidebarTab === 'details' ? 'bg-indigo-650 text-white shadow-md' : 'text-slate-400 hover:text-slate-200'}`}
              >
                Details
              </button>
              <button 
                onClick={() => setSidebarTab('timeline')}
                className={`flex-1 py-1 rounded font-semibold transition-all flex items-center justify-center gap-1 ${sidebarTab === 'timeline' ? 'bg-indigo-650 text-white shadow-md' : 'text-slate-400 hover:text-slate-200'}`}
                disabled={!selectedNode || selectedNode.type?.toLowerCase() !== 'asset'}
                title={selectedNode?.type?.toLowerCase() !== 'asset' ? 'Select an Asset node to view chronological events' : ''}
              >
                <Calendar className="w-3 h-3" />
                Timeline
              </button>
              <button 
                onClick={() => setSidebarTab('analytics')}
                className={`flex-1 py-1 rounded font-semibold transition-all flex items-center justify-center gap-1 ${sidebarTab === 'analytics' ? 'bg-indigo-650 text-white shadow-md' : 'text-slate-400 hover:text-slate-200'}`}
              >
                <BarChart3 className="w-3.5 h-3.5" />
                Analytics
              </button>
            </div>
          </CardHeader>
          
          <CardContent className="pt-4 flex-1 overflow-y-auto min-h-0 flex flex-col gap-4">
            {sidebarTab === 'details' && selectedNode && (
              <>
                {/* Node Operations */}
                <div className="grid grid-cols-2 gap-2 shrink-0">
                  <button 
                    onClick={() => expandNeighbors(selectedNode.id)}
                    className="flex items-center justify-center gap-2 bg-slate-800 hover:bg-slate-750 text-slate-200 py-1.5 px-3 rounded text-xs font-semibold border border-slate-700/50 transition-colors"
                  >
                    <Expand className="w-3.5 h-3.5" />
                    Expand Neighbors
                  </button>
                  <button 
                    onClick={() => navigate(`/copilot?q=${encodeURIComponent('Show details and analyze asset ' + selectedNode.label)}`)}
                    className="flex items-center justify-center gap-2 bg-indigo-650 hover:bg-indigo-500 text-white py-1.5 px-3 rounded text-xs font-semibold transition-all shadow-md shadow-indigo-650/15"
                  >
                    <Bot className="w-3.5 h-3.5" />
                    Ask Copilot
                  </button>
                </div>

                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div className="bg-slate-950/40 border border-slate-850 rounded p-2 text-center">
                    <span className="text-slate-500 block text-[9px] uppercase font-bold tracking-wider">Connections</span>
                    <span className="text-white font-bold text-sm">{selectedNodeLinks.length} degree</span>
                  </div>
                  <div className="bg-slate-950/40 border border-slate-850 rounded p-2 text-center">
                    <span className="text-slate-500 block text-[9px] uppercase font-bold tracking-wider">Related Docs</span>
                    <span className="text-white font-bold text-sm">{selectedNode.metadata?.source_documents?.length || 0} docs</span>
                  </div>
                </div>

                {/* Node Metadata Section */}
                {selectedNode.metadata && Object.keys(selectedNode.metadata).filter(k => !['graph_managed', 'owner', 'source_documents'].includes(k)).length > 0 && (
                  <div className="bg-slate-950/30 border border-slate-850 rounded-xl p-3.5">
                    <h4 className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-2.5 flex items-center gap-1.5">
                      <Info className="w-3.5 h-3.5 text-indigo-400" />
                      Metadata Values
                    </h4>
                    <dl className="space-y-2 text-xs">
                      {Object.entries(selectedNode.metadata)
                        .filter(([key]) => !['graph_managed', 'owner', 'source_documents'].includes(key))
                        .slice(0, 10)
                        .map(([key, value]) => (
                          <div key={key} className="flex justify-between gap-3 border-b border-slate-900/50 pb-1.5">
                            <dt className="text-slate-500 capitalize font-medium shrink-0">{key.replace(/_/g, ' ')}</dt>
                            <dd className="text-slate-300 truncate font-mono text-right flex-1 select-all">{Array.isArray(value) ? value.join(', ') : String(value)}</dd>
                          </div>
                        ))}
                    </dl>
                  </div>
                )}

                {/* Connected Entities Table */}
                <div className="flex-1 flex flex-col min-h-0">
                  <div className="flex items-center justify-between mb-2.5 shrink-0">
                    <h4 className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Connected Entities</h4>
                    <span className="text-[10px] bg-slate-800 text-slate-300 px-1.5 py-0.5 rounded font-mono font-medium">
                      {filteredSidebarLinks.length} / {selectedNodeLinks.length}
                    </span>
                  </div>
                  
                  {selectedNodeLinks.length > 0 && (
                    <div className="flex flex-col gap-2 mb-3 shrink-0">
                      <div className="relative">
                        <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-500" />
                        <input 
                          type="text"
                          placeholder="Filter connections..."
                          value={sidebarSearch}
                          onChange={(e) => setSidebarSearch(e.target.value)}
                          className="w-full bg-slate-950/70 border border-slate-850 rounded pl-8 pr-2 py-1 text-xs text-white placeholder-slate-600 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                        />
                      </div>

                      <div className="flex gap-1.5 items-center justify-between">
                        <div className="flex bg-slate-950 p-0.5 rounded border border-slate-850 text-[9px] font-semibold">
                          {(['all', 'out', 'in'] as const).map((dir) => (
                            <button
                              key={dir}
                              onClick={() => setSidebarDirection(dir)}
                              className={`px-2 py-0.5 rounded capitalize transition-all ${sidebarDirection === dir ? 'bg-indigo-650 text-white shadow' : 'text-slate-400 hover:text-slate-200'}`}
                            >
                              {dir}
                            </button>
                          ))}
                        </div>

                        {sidebarAvailableTypes.length > 0 && (
                          <select
                            value={sidebarType}
                            onChange={(e) => setSidebarType(e.target.value)}
                            className="bg-slate-950 border border-slate-850 rounded px-2 py-0.5 text-[9px] text-slate-300 focus:outline-none focus:ring-1 focus:ring-indigo-500 max-w-[130px] font-semibold"
                          >
                            <option value="all">All Types</option>
                            {sidebarAvailableTypes.map(type => (
                              <option key={type} value={type} className="capitalize">{type}</option>
                            ))}
                          </select>
                        )}
                      </div>
                    </div>
                  )}
                  
                  <div className="flex-1 overflow-y-auto pr-1 custom-scrollbar">
                    {selectedNodeLinks.length === 0 ? (
                      <div className="text-xs text-slate-500 italic p-4 text-center border border-dashed border-slate-850 rounded-lg">
                        No active connections. Click neighbor expansion to explore.
                      </div>
                    ) : filteredSidebarLinks.length === 0 ? (
                      <div className="text-xs text-slate-500 italic p-4 text-center">
                        No matches found.
                      </div>
                    ) : (
                      <ul className="space-y-1.5 pb-2">
                        {filteredSidebarLinks.map((link: any, i: number) => {
                          const isSource = (typeof link.source === 'object' ? link.source.id : link.source) === selectedNode.id;
                          const connectedNode = isSource ? link.target : link.source;
                          const connectedNodeObj = typeof connectedNode === 'object' 
                            ? connectedNode 
                            : (masterData.nodes.find(n => n.id === connectedNode) || { id: connectedNode, label: connectedNode, type: 'unknown' });
                          
                          return (
                            <li 
                              key={i} 
                              onClick={() => handleNodeClick(connectedNodeObj)}
                              className="flex flex-col gap-1 text-[11px] bg-slate-950/40 hover:bg-slate-900 p-2 rounded border border-slate-900/60 hover:border-slate-800 transition-all cursor-pointer group"
                            >
                              <div className="flex items-center gap-2">
                                <span 
                                  className="w-1.5 h-1.5 rounded-full shrink-0" 
                                  style={{ backgroundColor: getNodeColor(connectedNodeObj) }}
                                ></span>
                                <span className="font-semibold text-slate-300 group-hover:text-indigo-400 truncate flex-1">
                                  {connectedNodeObj.label}
                                </span>
                                <span className="px-1 py-0.25 text-[8px] uppercase tracking-wider text-slate-500 bg-slate-950 rounded font-bold shrink-0">
                                  {connectedNodeObj.type || 'Unknown'}
                                </span>
                              </div>
                              
                              <div className="flex justify-between items-center ml-3.5 pl-2 border-l border-slate-900 group-hover:border-slate-800 transition-colors">
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    handleLinkClick(link);
                                  }}
                                  className="text-[9px] text-slate-500 hover:text-indigo-400 font-mono flex items-center gap-0.5 hover:bg-slate-950 px-1 py-0.5 rounded transition-colors"
                                  title="Inspect relationship details"
                                >
                                  {isSource ? (
                                    <span className="text-indigo-400 font-bold font-sans mr-0.5">→</span>
                                  ) : (
                                    <span className="text-emerald-400 font-bold font-sans mr-0.5">←</span>
                                  )}
                                  <span className="underline decoration-dotted">{link.label}</span>
                                </button>
                              </div>
                            </li>
                          );
                        })}
                      </ul>
                    )}
                  </div>
                </div>
              </>
            )}

            {sidebarTab === 'details' && selectedLink && (
              <>
                <div className="bg-slate-950/40 border border-slate-850 rounded-xl p-4 flex flex-col gap-4">
                  {/* Source Node details */}
                  <div 
                    onClick={() => {
                      const s = typeof selectedLink.source === 'object' ? selectedLink.source : masterData.nodes.find(n => n.id === selectedLink.source);
                      if (s) handleNodeClick(s);
                    }}
                    className="group cursor-pointer bg-slate-900/50 hover:bg-slate-850 p-2.5 rounded border border-slate-800 transition-all hover:scale-[1.01]"
                  >
                    <span className="text-[9px] text-slate-500 block mb-1 uppercase font-bold tracking-wider">Source Entity</span>
                    <div className="flex items-center gap-2">
                      <span 
                        className="w-2 h-2 rounded-full shrink-0" 
                        style={{ 
                          backgroundColor: getNodeColor(typeof selectedLink.source === 'object' ? selectedLink.source : { id: selectedLink.source, type: masterData.nodes.find(n => n.id === selectedLink.source)?.type }) 
                        }}
                      ></span>
                      <span className="text-xs font-bold text-white group-hover:text-indigo-400 truncate">
                        {typeof selectedLink.source === 'object' ? selectedLink.source.label : (masterData.nodes.find(n => n.id === selectedLink.source)?.label || selectedLink.source)}
                      </span>
                    </div>
                    <span className="text-[9px] text-indigo-400 block mt-1.5 font-semibold">Click to center source entity →</span>
                  </div>

                  <div className="flex flex-col items-center py-1">
                    <div className="bg-indigo-950/60 text-indigo-300 text-[10px] px-3 py-1 rounded-full font-mono font-bold border border-indigo-900/40">
                      {selectedLink.label}
                    </div>
                    <div className="w-0.5 h-4 bg-indigo-850 mt-1"></div>
                  </div>

                  {/* Target Node details */}
                  <div 
                    onClick={() => {
                      const t = typeof selectedLink.target === 'object' ? selectedLink.target : masterData.nodes.find(n => n.id === selectedLink.target);
                      if (t) handleNodeClick(t);
                    }}
                    className="group cursor-pointer bg-slate-900/50 hover:bg-slate-850 p-2.5 rounded border border-slate-800 transition-all hover:scale-[1.01]"
                  >
                    <span className="text-[9px] text-slate-500 block mb-1 uppercase font-bold tracking-wider">Target Entity</span>
                    <div className="flex items-center gap-2">
                      <span 
                        className="w-2 h-2 rounded-full shrink-0" 
                        style={{ 
                          backgroundColor: getNodeColor(typeof selectedLink.target === 'object' ? selectedLink.target : { id: selectedLink.target, type: masterData.nodes.find(n => n.id === selectedLink.target)?.type }) 
                        }}
                      ></span>
                      <span className="text-xs font-bold text-white group-hover:text-indigo-400 truncate">
                        {typeof selectedLink.target === 'object' ? selectedLink.target.label : (masterData.nodes.find(n => n.id === selectedLink.target)?.label || selectedLink.target)}
                      </span>
                    </div>
                    <span className="text-[9px] text-indigo-400 block mt-1.5 font-semibold">Click to center target entity →</span>
                  </div>
                </div>

                {/* Weight Centrality */}
                {selectedLink.weight !== undefined && (
                  <div className="bg-slate-950/30 border border-slate-850 rounded-xl p-4 flex flex-col gap-2">
                    <div className="flex justify-between items-center text-xs">
                      <span className="text-slate-400 font-semibold">Confidence Weight</span>
                      <span className="text-indigo-300 font-mono font-bold">{(selectedLink.weight * 100).toFixed(0)}%</span>
                    </div>
                    <div className="w-full bg-slate-850 rounded-full h-1.5 overflow-hidden border border-slate-800">
                      <div className="bg-indigo-650 h-full rounded-full transition-all" style={{ width: `${selectedLink.weight * 100}%` }}></div>
                    </div>
                    <p className="text-[10px] text-slate-500 mt-1 leading-normal italic">
                      This edge was parsed with {(selectedLink.weight * 100).toFixed(0)}% confidence score from raw source documentation.
                    </p>
                  </div>
                )}

                <div className="mt-auto shrink-0">
                  <button 
                    onClick={() => {
                      const sourceName = typeof selectedLink.source === 'object' ? selectedLink.source.label : (masterData.nodes.find(n => n.id === selectedLink.source)?.label || selectedLink.source);
                      const targetName = typeof selectedLink.target === 'object' ? selectedLink.target.label : (masterData.nodes.find(n => n.id === selectedLink.target)?.label || selectedLink.target);
                      navigate(`/copilot?q=${encodeURIComponent(`Explain the connection of type '${selectedLink.label}' between source '${sourceName}' and target '${targetName}'. What is the engineering context behind this relationship?`)}`);
                    }}
                    className="w-full flex items-center justify-center gap-2 bg-indigo-650 hover:bg-indigo-500 text-white py-2 px-4 rounded text-xs font-semibold transition-all shadow-md shadow-indigo-650/15"
                  >
                    <Bot className="w-3.5 h-3.5" />
                    Ask AI About This Connection
                  </button>
                </div>
              </>
            )}

            {/* Empty Details State */}
            {!selectedNode && !selectedLink && sidebarTab === 'details' && (
              <div className="flex-1 flex flex-col items-center justify-center text-slate-500 py-12 text-center text-xs">
                <Info className="w-10 h-10 text-slate-650 mb-3" />
                <p>Click any node or relationship link on the graph to inspect detailed attributes.</p>
              </div>
            )}

            {/* Timeline View Tab */}
            {sidebarTab === 'timeline' && selectedNode && (
              <div className="flex-1 flex flex-col min-h-0">
                <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3.5 flex items-center gap-1.5 shrink-0">
                  <Calendar className="w-3.5 h-3.5 text-indigo-400" />
                  Chronological Asset Events
                </h4>
                
                <div className="flex-1 overflow-y-auto pr-1 pl-2.5 relative border-l border-slate-800 custom-scrollbar">
                  {assetTimelineEvents.length === 0 ? (
                    <div className="text-xs text-slate-500 italic p-4 text-center">
                      No matching timeline events found for this asset.
                    </div>
                  ) : (
                    <div className="space-y-4 pb-4">
                      {assetTimelineEvents.map((evt, i) => (
                        <div key={i} className="relative group">
                          {/* Timeline bullet dot */}
                          <div 
                            className="absolute -left-[14.5px] top-1.5 w-2 h-2 rounded-full border border-slate-950 transition-all group-hover:scale-125"
                            style={{ backgroundColor: evt.color }}
                          />
                          
                          <div className="bg-slate-950/40 p-3 rounded border border-slate-900 hover:border-slate-800 transition-all hover:bg-slate-900/60">
                            <div className="flex items-center justify-between gap-2 mb-1.5">
                              <span className="text-[10px] font-bold font-mono text-indigo-400">{evt.dateString}</span>
                              <span 
                                className="px-1.5 py-0.25 rounded text-[8px] uppercase tracking-wider text-white font-bold"
                                style={{ backgroundColor: evt.color }}
                              >
                                {evt.type}
                              </span>
                            </div>
                            <h5 className="font-semibold text-xs text-slate-200 mb-1 group-hover:text-indigo-400 transition-colors">
                              {evt.label}
                            </h5>
                            <p className="text-[10px] text-slate-500 leading-normal line-clamp-3">
                              {evt.description}
                            </p>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Analytics Tab */}
            {sidebarTab === 'analytics' && (
              <div className="flex-1 flex flex-col gap-4 overflow-y-auto pr-1 custom-scrollbar pb-3">
                <div className="bg-slate-950/40 border border-slate-850 rounded-xl p-3.5 flex flex-col gap-3">
                  <h4 className="text-[10px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5 border-b border-slate-900 pb-1.5">
                    <BarChart3 className="w-3.5 h-3.5 text-indigo-400" />
                    Network Statistics
                  </h4>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div className="bg-slate-900/50 p-2 rounded border border-slate-850">
                      <span className="text-[9px] uppercase font-bold text-slate-500 block">Total Nodes</span>
                      <span className="text-white font-bold text-sm">{analyticsData.totalNodes}</span>
                    </div>
                    <div className="bg-slate-900/50 p-2 rounded border border-slate-850">
                      <span className="text-[9px] uppercase font-bold text-slate-500 block">Total Edges</span>
                      <span className="text-white font-bold text-sm">{analyticsData.totalEdges}</span>
                    </div>
                    <div className="bg-slate-900/50 p-2 rounded border border-slate-850">
                      <span className="text-[9px] uppercase font-bold text-slate-500 block">Components</span>
                      <span className="text-white font-bold text-sm">{analyticsData.componentsCount}</span>
                    </div>
                    <div className="bg-slate-900/50 p-2 rounded border border-slate-850">
                      <span className="text-[9px] uppercase font-bold text-slate-500 block">Density</span>
                      <span className="text-white font-bold text-sm font-mono">{analyticsData.density.toFixed(4)}</span>
                    </div>
                  </div>
                </div>

                {/* Centrality Info */}
                {analyticsData.mostConnected && (
                  <div className="bg-slate-950/40 border border-slate-850 rounded-xl p-3.5 flex flex-col gap-2">
                    <h4 className="text-[10px] font-bold text-slate-400 uppercase tracking-wider border-b border-slate-900 pb-1.5">
                      Centrality Central Node
                    </h4>
                    <div 
                      onClick={() => handleNodeClick(analyticsData.mostConnected)}
                      className="flex items-center gap-2 p-2 rounded bg-slate-900/50 hover:bg-slate-850 border border-slate-800/80 cursor-pointer group"
                    >
                      <span className="w-2 h-2 rounded-full shrink-0" style={{ backgroundColor: getNodeColor(analyticsData.mostConnected) }}></span>
                      <div className="min-w-0 flex-1">
                        <span className="text-xs font-bold text-slate-300 group-hover:text-indigo-400 truncate block">{analyticsData.mostConnected.label}</span>
                        <span className="text-[9px] text-slate-500 font-mono block uppercase">{analyticsData.mostConnected.type}</span>
                      </div>
                      <span className="text-[10px] font-mono font-bold text-slate-400 px-1.5 py-0.5 rounded bg-slate-950 shrink-0">
                        {analyticsData.maxDegree} deg
                      </span>
                    </div>
                  </div>
                )}

                {/* Node Type Distribution */}
                <div className="bg-slate-950/40 border border-slate-850 rounded-xl p-3.5 flex flex-col gap-2">
                  <h4 className="text-[10px] font-bold text-slate-400 uppercase tracking-wider border-b border-slate-900 pb-1.5">
                    Node Distribution
                  </h4>
                  <div className="space-y-2 text-xs mt-1">
                    {Object.entries(analyticsData.typeDistribution)
                      .sort((a, b) => b[1] - a[1])
                      .map(([type, count]) => {
                        const pct = analyticsData.totalNodes > 0 ? (count / analyticsData.totalNodes) * 100 : 0;
                        const sampleNode = masterData.nodes.find(n => n.type === type) || { type };
                        const color = getNodeColor(sampleNode);
                        return (
                          <div key={type} className="space-y-1">
                            <div className="flex justify-between items-center text-[10px]">
                              <span className="capitalize font-semibold text-slate-300">{type}</span>
                              <span className="font-mono text-slate-400">{count} ({pct.toFixed(0)}%)</span>
                            </div>
                            <div className="w-full bg-slate-950 h-1.5 rounded-full overflow-hidden border border-slate-900">
                              <div className="h-full rounded-full" style={{ width: `${pct}%`, backgroundColor: color }}></div>
                            </div>
                          </div>
                        );
                      })}
                  </div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Floating Node Context Menu */}
      {contextMenu && (
        <div 
          className="fixed z-50 bg-slate-900 border border-slate-800 rounded-lg shadow-2xl py-1 text-xs text-slate-200 min-w-[150px] overflow-hidden"
          style={{ left: contextMenu.x, top: contextMenu.y }}
        >
          <button 
            onClick={() => {
              expandNeighbors(contextMenu.node.id);
              setContextMenu(null);
            }}
            className="w-full text-left px-3 py-2 hover:bg-indigo-650 hover:text-white transition-colors flex items-center gap-2"
          >
            <Expand className="w-3.5 h-3.5" />
            Expand Neighbors
          </button>
          <button 
            onClick={() => {
              handleCollapseNode(contextMenu.node);
              setContextMenu(null);
            }}
            className="w-full text-left px-3 py-2 hover:bg-indigo-650 hover:text-white transition-colors flex items-center gap-2"
          >
            <EyeOff className="w-3.5 h-3.5" />
            Collapse Branch
          </button>
          <button 
            onClick={() => {
              handleNodeClick(contextMenu.node);
              setContextMenu(null);
            }}
            className="w-full text-left px-3 py-2 hover:bg-indigo-650 hover:text-white transition-colors flex items-center gap-2"
          >
            <Maximize2 className="w-3.5 h-3.5" />
            Focus View
          </button>
          <button 
            onClick={() => {
              handleHideNode(contextMenu.node.id);
              setContextMenu(null);
            }}
            className="w-full text-left px-3 py-2 hover:bg-red-700 hover:text-white transition-colors flex items-center gap-2 text-red-400"
          >
            <Trash2 className="w-3.5 h-3.5" />
            Hide Node
          </button>
          <div className="h-px bg-slate-800 my-1"></div>
          <button 
            onClick={() => {
              navigate(`/copilot?q=${encodeURIComponent('Analyze the entity ' + contextMenu.node.label)}`);
              setContextMenu(null);
            }}
            className="w-full text-left px-3 py-2 hover:bg-indigo-650 hover:text-white transition-colors flex items-center gap-2"
          >
            <Bot className="w-3.5 h-3.5" />
            Analyze with AI
          </button>
          <button 
            onClick={() => {
              navigator.clipboard.writeText(contextMenu.node.id);
              setContextMenu(null);
            }}
            className="w-full text-left px-3 py-2 hover:bg-indigo-650 hover:text-white transition-colors flex items-center gap-2"
          >
            <Copy className="w-3.5 h-3.5" />
            Copy Node ID
          </button>
        </div>
      )}
    </div>
  );
}
