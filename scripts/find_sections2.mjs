import fs from 'fs';
const pdfjsLib = await import('pdfjs-dist/legacy/build/pdf.mjs');
const data = new Uint8Array(fs.readFileSync('marked_report.pdf'));
const pdfDoc = await (pdfjsLib.getDocument({ data })).promise;

// Each PDF page begins with its page number as text (from @bottom-center counter)
// We identify each SECTION by scanning for the heading text on pages AFTER page 3 (TOC pages)
// The format on each page: "<page_num>  <heading text>  ..."

const SECTIONS = [
  '1. Abstract',
  '2. Introduction',
  '3. Project Innovations',
  '4. Problem Statement',
  '4.1 Problem Statement',
  '4.2 Objectives',
  '5. Existing System',
  '6. Proposed System',
  '7. System Architecture',
  '8. AI',
  '8.1 Data Ingestion',
  '8.2 Query Pre-Processing',
  '8.3 Hybrid Retrieval',
  '8.4 Post-Retrieval',
  '8.5 Generation',
  '9. Knowledge Graph',
  '10. Database Design',
  '11. Technology Stack',
  '12. System Workflow',
  '13. Implementation',
  '13.1 Backend Services',
  '13.2 Intent Classification',
  '13.3 Frontend Modules',
  '14. UI',
  '15. Deployment Architecture',
  '16. Data Flow',
  '17. Testing',
  '18. Advantages',
  '19. Conclusion',
  '20. References',
];

const found = {};

// Skip pages 1-3 (cover + TOC pages), start from page 4
for (let i = 4; i <= pdfDoc.numPages; i++) {
  const pg = await pdfDoc.getPage(i);
  const c = await pg.getTextContent();
  // Get raw items to find the first heading on the page
  const text = c.items.map(x => x.str).join(' ');
  
  for (const sec of SECTIONS) {
    if (!found[sec] && text.includes(sec)) {
      found[sec] = i;
    }
  }
}

console.log('=== EXACT PDF PAGE NUMBERS PER SECTION ===');
for (const sec of SECTIONS) {
  console.log(`  "${sec}" → ${found[sec] || 'NOT FOUND'}`);
}
