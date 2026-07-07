import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import MainLayout from '@/components/layout/MainLayout';
import Dashboard from '@/pages/Dashboard';
import DocumentManagement from '@/pages/DocumentManagement';
import PageIndex from '@/pages/PageIndex';
import KnowledgeGraph from '@/pages/KnowledgeGraph';
import AICopilot from '@/pages/AICopilot';
import RootCauseAnalysis from '@/pages/RootCauseAnalysis';
import ComplianceCenter from '@/pages/ComplianceCenter';
import ExpertKnowledge from '@/pages/ExpertKnowledge';
import AssetIntelligence from '@/pages/AssetIntelligence';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<MainLayout />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="documents" element={<DocumentManagement />} />
          <Route path="page-index" element={<PageIndex />} />
          <Route path="graph" element={<KnowledgeGraph />} />
          <Route path="copilot" element={<AICopilot />} />
          <Route path="rca" element={<RootCauseAnalysis />} />
          <Route path="compliance" element={<ComplianceCenter />} />
          <Route path="expert" element={<ExpertKnowledge />} />
          <Route path="assets" element={<AssetIntelligence />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
