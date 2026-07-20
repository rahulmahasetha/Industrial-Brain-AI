import fs from 'fs';

// Use pdfjs-dist to parse the PDF page by page and find markers
const pdfjsLib = await import('pdfjs-dist/legacy/build/pdf.mjs');

const data = new Uint8Array(fs.readFileSync('marked_report.pdf'));
const loadingTask = pdfjsLib.getDocument({ data });
const pdfDoc = await loadingTask.promise;

console.log(`Total pages: ${pdfDoc.numPages}`);

const MARKERS = [
  'TOC_MARKER', '§1_Abstract', '§2_Introduction', '§3_ProjectInnovations',
  '§4_ProblemStatement', '§4.1_ProblemStatement', '§4.2_Objectives',
  '§5_ExistingSystem', '§6_ProposedSystem', '§7_SystemArchitecture',
  '§8_AIRAGPipeline', '§8.1_DataIngestion', '§8.2_QueryPreProcessing',
  '§8.3_HybridRetrieval', '§8.4_PostRetrieval', '§8.5_Generation',
  '§9_KnowledgeGraph', '§10_DatabaseDesign', '§11_TechnologyStack',
  '§12_SystemWorkflow', '§13_Implementation', '§13.1_BackendServices',
  '§13.2_IntentRouting', '§13.3_FrontendModules', '§14_UIUX',
  '§15_Deployment', '§16_DataFlow', '§17_Testing', '§18_Advantages',
  '§19_Conclusion', '§20_References'
];

const found = {};

for (let i = 1; i <= pdfDoc.numPages; i++) {
  const page = await pdfDoc.getPage(i);
  const content = await page.getTextContent();
  const text = content.items.map(item => item.str).join('');
  
  for (const marker of MARKERS) {
    if (!found[marker] && text.includes(marker)) {
      found[marker] = i;
    }
  }
}

console.log('\n=== ACTUAL PDF PAGE NUMBERS ===');
for (const [marker, pg] of Object.entries(found)) {
  console.log(`  ${marker.padEnd(32)} → page ${pg}`);
}

// Also check which markers were NOT found
const notFound = MARKERS.filter(m => !found[m]);
if (notFound.length) {
  console.log('\nNOT FOUND:', notFound);
  
  // Try sampling page 1-5 text to debug
  for (let i = 1; i <= Math.min(5, pdfDoc.numPages); i++) {
    const page = await pdfDoc.getPage(i);
    const content = await page.getTextContent();
    const text = content.items.map(item => item.str).join(' ').substring(0, 200);
    console.log(`\nPage ${i} sample: ${text}`);
  }
}

fs.writeFileSync('page_numbers.json', JSON.stringify(found, null, 2));
