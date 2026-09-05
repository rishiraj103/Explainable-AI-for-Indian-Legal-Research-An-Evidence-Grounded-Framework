import {loadCases} from './data.mjs';

const select = document.querySelector('#case');
const format = document.querySelector('#format');
const status = document.querySelector('#status');
const brief = document.querySelector('#brief');
const context = document.querySelector('#context');
function element(tag, text) {
  const node = document.createElement(tag);
  node.textContent = text;
  return node;
}

// Interpret only the packet's small, known Markdown vocabulary. All content
// is inserted as text nodes: source text can never become executable markup.
function render(text) {
  let list = null;
  for (const line of text.split('\n')) {
    if (!line) { list = null; continue; }
    if (line.startsWith('- ')) {
      if (!list) { list = document.createElement('ul'); brief.append(list); }
      list.append(element('li', line.slice(2)));
    } else {
      list = null;
      if (/^\*\*.*\*\*$/.test(line)) brief.append(element('h3', line.slice(2, -2)));
      else if (line.startsWith('> ')) brief.append(element('blockquote', line.slice(2)));
      else brief.append(element('p', line));
    }
  }
}

try {
  const paths = ['week13_review_packet.md', 'week11_temporal_prerank_evaluation.json', 'week13_rq3_ablation_parity.json'];
  const responses = await Promise.all(paths.map(async path => {
    const response = await fetch(`../artifacts/${path}`);
    if (!response.ok) throw new Error(`Cannot load ${path}: HTTP ${response.status}`);
    return path.endsWith('.json') ? response.json() : response.text();
  }));
  const cases = loadCases(...responses);
  for (const item of cases) {
    const option = element('option', `${item.id} · ${item.label}`);
    option.value = item.id;
    select.append(option);
  }
  function display() {
    const item = cases.find(row => row.id === select.value);
    brief.replaceChildren(element('h2', `${item.id} · ${format.selectedOptions[0].textContent}`));
    render(item.displays[format.value]);
    const r = item.record;
    context.replaceChildren(
      element('p', `Evaluation example: ${item.label}`),
      element('p', `Expected authority: ${r.expected_authority_selected ? 'retrieved and selected' : r.expected_authority_retrieved_at_100 ? 'retrieved within top 100, not selected' : 'absent from top 100'}. Displayed citation checks: ${r.citation_checks_passed}/${r.citation_check_count}.`),
    );
    if (!r.expected_authority_retrieved_at_100) context.append(element('p', 'Other evidence is still displayed. “Absent” refers to the answer-key authority, not an empty evidence set.'));
    status.textContent = `${cases.length} examples loaded · ${item.citationIds.length} citation IDs and reporter citations match the final evaluation · presentation parity verified`;
    brief.dataset.caseId = item.id;
    brief.dataset.format = format.value;
  }
  select.disabled = format.disabled = false;
  select.addEventListener('change', display);
  format.addEventListener('change', display);
  display();
} catch (error) {
  status.classList.add('error');
  status.textContent = `Demo unavailable: ${error.message}. Start the local server using demo/README.md.`;
}
