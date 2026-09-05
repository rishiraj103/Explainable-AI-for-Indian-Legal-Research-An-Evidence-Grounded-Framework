// Parse the existing packet without rewriting its passages or punctuation.
export const labels = {
  '2008_1629': 'Clean success',
  '1980_105': 'Clean success · small eligible pool',
  '1980_133': 'Near-miss · rank 15',
  '1981_55': 'Retrieved, not selected · rank 28',
  '1985_40': 'Retrieved, not selected · rank 78',
  '1997_792': 'Authority-consistency failure',
  '2013_35': 'Expected authority absent at k=100',
};

export function loadCases(packet, evaluation, parity) {
  const cases = [];
  for (const match of packet.replace(/\r\n/g, '\n').matchAll(/^## Case `([^`]+)`\n([\s\S]*?)(?=^## |$(?![\s\S]))/gm)) {
    const id = match[1];
    if (!labels[id]) continue;
    const record = evaluation.per_case_records.find(row => row.query_case_id === id);
    const audit = parity.per_case.find(row => row.case_id === id);
    if (!record || !audit) throw new Error(`Missing frozen record for ${id}`);
    const displays = {};
    for (const block of match[2].matchAll(/^### (Structured, evidence-linked brief|Unstructured evidence presentation)\n([\s\S]*?)(?=^\*\*Response for Display)/gm)) {
      displays[block[1].startsWith('Structured') ? 'structured' : 'unstructured'] = block[2].trim();
    }
    const expected = record.citation_checks.map(check => check.chunk_id);
    for (const format of ['structured', 'unstructured']) {
      if (!displays[format]) throw new Error(`Missing ${format} display for ${id}`);
      const authorityLines = displays[format].split('\n').filter(line => line.startsWith('- '));
      const ids = authorityLines.map(line => /citation ID `([^`]+)`/.exec(line)?.[1]);
      if (JSON.stringify(ids) !== JSON.stringify(expected) ||
          JSON.stringify(ids) !== JSON.stringify(audit[`${format}_citation_ids`])) {
        throw new Error(`Citation ID mismatch for ${id}/${format}`);
      }
      record.citation_checks.forEach((check, i) => {
        const prefix = format === 'structured' ? `- ${check.evidence_id}: ` : '- ';
        if (!authorityLines[i].startsWith(`${prefix}${check.citation || 'No reporter citation'};`)) {
          throw new Error(`Reporter citation mismatch for ${id}/${format}`);
        }
      });
    }
    const passageIds = [...displays.structured.matchAll(/^E\d+ \(citation ID `([^`]+)`, verbatim\):$/gm)].map(m => m[1]);
    if (JSON.stringify(passageIds) !== JSON.stringify(expected)) throw new Error(`Passage ID mismatch for ${id}`);
    const passages = [...displays.structured.matchAll(/^> (.*(?:\n> .*)*)/gm)].map(m => m[1].replace(/\n> /g, '\n'));
    if (passages.length !== expected.length || passages.some(text => !displays.unstructured.includes(text))) {
      throw new Error(`Passage parity mismatch for ${id}`);
    }
    cases.push({id, label: labels[id], record, displays, passages, citationIds: expected});
  }
  if (cases.length !== Object.keys(labels).length) throw new Error('Incomplete seven-case packet');
  return cases;
}
