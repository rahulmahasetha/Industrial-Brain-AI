import * as lucide from "lucide-react";
const missing = ['ShieldCheck', 'AlertTriangle', 'FileText', 'Download', 'Play', 'ChevronDown', 'ChevronUp', 'BrainCircuit', 'Activity', 'BarChart3', 'Clock', 'Database', 'CheckCircle2', 'XCircle', 'Search', 'Settings', 'HelpCircle', 'Key', 'Users', 'BookOpen', 'AlertOctagon', 'TrendingDown', 'RefreshCcw', 'FileSignature', 'MessageSquare'].filter(icon => !lucide[icon]);
console.log("Missing icons:", missing);
