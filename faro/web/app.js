'use strict';
const $ = (id) => document.getElementById(id);
const esc = (value) => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const icon = (name) => `<svg aria-hidden="true"><use href="#i-${name}"/></svg>`;
const defang = (url) => String(url).replace(/^https:/i, 'hxxps:').replace(/^http:/i, 'hxxp:').replace(/\./g, '[.]');
const bytes = (size) => size < 1024 ? `${size} B` : size < 1048576 ? `${(size / 1024).toFixed(1)} KiB` : `${(size / 1048576).toFixed(1)} MiB`;
const riskLabels = {low:'Pocas señales',medium:'Revisión recomendada',high:'Precaución alta',unknown:'Riesgo no determinado'};
const colors = {low:'green',medium:'amber',high:'pink',unknown:'gray'};
const statusLabels = {complete:'Análisis completado',partial:'Análisis parcial',unsupported:'Contenido no evaluado'};
const severityLabels = {low:'Baja',medium:'Media',high:'Alta'};
const HISTORY_KEY = 'faro.history.v1';
const transport = window.faroTransport || {
  async analyze(path, body, headers) {
    const response = await fetch(path,{method:'POST',headers,body,signal:AbortSignal.timeout(25000)});
    const payload = await response.json();
    if(!response.ok) throw new Error(payload.error || 'No se pudo completar el análisis.');
    return payload;
  },
  async health() {
    const response = await fetch('/api/health',{signal:AbortSignal.timeout(5000)});
    if(!response.ok) throw new Error();
    const health = await response.json();
    return health.pdf_parser_available ? 'Motor local disponible' : 'PDF: dependencia pendiente';
  },
};
let report = null;
let history = [];
let busy = false;
let toastTimer;
try {
  const stored = JSON.parse(localStorage.getItem(HISTORY_KEY) || '[]');
  if (Array.isArray(stored)) history = stored.filter(x => x && typeof x.sha256 === 'string' && /^[a-f0-9]{64}$/.test(x.sha256) && Object.hasOwn(riskLabels,x.risk) && typeof x.name==='string' && Number.isFinite(x.score)).slice(0, 30);
} catch (_) { history = []; }

function toast(message) {
  $('toast').textContent = message;
  $('toast').hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { $('toast').hidden = true; }, 3500);
}

function navigate() {
  let page = location.hash.slice(1) || 'analizar';
  if (!['analizar','historial','metodologia','proyecto'].includes(page)) page = 'analizar';
  document.querySelectorAll('.page').forEach(el => { el.hidden = el.id !== `page-${page}`; });
  document.querySelectorAll('.nav-item').forEach(el => {
    const active = el.dataset.page === page;
    el.classList.toggle('active', active);
    active ? el.setAttribute('aria-current','page') : el.removeAttribute('aria-current');
  });
  $('breadcrumb').textContent = {analizar:'Analizar archivos',historial:'Historial',metodologia:'Cómo funciona',proyecto:'El proyecto'}[page];
  document.title = `Faro — ${$('breadcrumb').textContent}`;
  if (page === 'historial') renderHistory();
}
window.addEventListener('hashchange', navigate);

function renderHistory() {
  $('history-count').textContent = String(history.length);
  $('clear-history').disabled = history.length === 0;
  if (!history.length) {
    $('history-content').innerHTML = `<div class="empty-state">${icon('clock')}<h3>Un espacio que tú controlas</h3><p>Al terminar un análisis, activa “Guardar un resumen” para conservar aquí sus datos básicos. El historial está desactivado por defecto.</p></div>`;
    return;
  }
  $('history-content').innerHTML = `<div class="table-scroll"><table class="history-table"><thead><tr><th>Archivo</th><th>Resultado</th><th>Señales</th><th>Fecha</th></tr></thead><tbody>${history.map(r => `<tr><td>${esc(r.name)}<small>${esc(r.type)} · ${bytes(r.size)}</small></td><td><span class="badge ${colors[r.risk]}">${esc(riskLabels[r.risk])}</span><small>${esc(r.score)} puntos · ${esc(statusLabels[r.status] || 'Sin estado')}</small></td><td>${esc(r.count)}</td><td>${esc(new Date(r.date).toLocaleDateString('es-MX',{day:'numeric',month:'short',year:'numeric'}))}</td></tr>`).join('')}</tbody></table></div>`;
}
function writeHistory(next) {
  try {localStorage.setItem(HISTORY_KEY, JSON.stringify(next)); history = next; renderHistory(); return true;}
  catch (_) {toast('El navegador no permitió guardar el historial.'); return false;}
}
$('clear-history').addEventListener('click', () => {
  if (!window.confirm('¿Borrar todos los resúmenes guardados en este navegador?')) return;
  if (writeHistory([])) { if(report) $('remember').checked = false; toast('Historial borrado.'); }
});
$('remember').addEventListener('change', () => {
  if (!report) return;
  const without = history.filter(r => r.sha256 !== report.file.sha256);
  if (!$('remember').checked) {writeHistory(without); return;}
  const r = {name:report.file.name,sha256:report.file.sha256,size:report.file.size,type:report.file.type_label,score:report.score,risk:report.risk,status:report.status,count:report.signals.length,date:report.analyzed_at};
  if (!writeHistory([r,...without].slice(0,30))) $('remember').checked = false;
});

function reset() {
  if (busy) return;
  report = null;
  $('results').hidden = true;
  $('upload-area').hidden = false;
  $('error-box').hidden = true;
  $('file-input').value = '';
  window.scrollTo({top:0,behavior:'smooth'});
}
$('new-analysis').addEventListener('click', reset);
$('choose-file').addEventListener('click', () => $('file-input').click());
$('file-input').addEventListener('change', e => { if(e.target.files[0]) analyzeFile(e.target.files[0]); });
const drop = $('dropzone');
['dragenter','dragover'].forEach(type => drop.addEventListener(type,e => {e.preventDefault(); if(!busy) drop.classList.add('dragover');}));
['dragleave','drop'].forEach(type => drop.addEventListener(type,e => {e.preventDefault();drop.classList.remove('dragover');}));
drop.addEventListener('drop',e => {
  if(busy) return;
  if(e.dataTransfer.files.length !== 1) {showError('Selecciona un solo archivo por análisis.');return;}
  analyzeFile(e.dataTransfer.files[0]);
});
function showError(message) {
  $('error-box').textContent = message;
  $('error-box').hidden = false;
}
async function analyzeFile(file) {
  if (!file.size || file.size > 10*1024*1024) {showError('Selecciona un archivo no vacío de hasta 10 MiB.');return;}
  await runAnalysis('/api/analyze',file,{'X-Filename':encodeURIComponent(file.name),'Content-Type':'application/octet-stream'},file.name);
}
document.querySelectorAll('[data-demo]').forEach(button => button.addEventListener('click', () => runAnalysis('/api/demo',null,{'X-Demo':button.dataset.demo},button.dataset.demo)));

async function runAnalysis(path,body,headers,name) {
  if(busy) return;
  busy = true;
  $('error-box').hidden = true;
  $('upload-area').hidden = true;
  $('results').hidden = true;
  $('loading').hidden = false;
  $('loading-name').textContent = name;
  document.querySelectorAll('.demo-button,#choose-file').forEach(b=>{b.disabled=true;});
  try {
    report = await transport.analyze(path,body,headers);
    renderReport();
  } catch(err) {
    report = null;
    $('upload-area').hidden = false;
    showError(err.name==='TimeoutError' ? 'El motor no respondió a tiempo. El archivo no fue evaluado completamente.' : err instanceof TypeError ? 'No hay conexión con el motor local. Inicia Faro y vuelve a intentarlo.' : err.message);
  } finally {
    busy = false;
    $('loading').hidden = true;
    document.querySelectorAll('.demo-button,#choose-file').forEach(b=>{b.disabled=false;});
    $('file-input').value='';
  }
}

function renderReport() {
  const r=report, color=colors[r.risk];
  $('results').hidden = false;
  $('risk-score').textContent = String(r.score);
  $('risk-ring').className = `risk-ring ${r.risk}`;
  $('risk-badge').className=`badge ${color}`;
  $('risk-badge').textContent=riskLabels[r.risk];
  $('status-badge').textContent=statusLabels[r.status];
  const titles={low:r.signals.length?'Pocas señales, contexto necesario.':'Sin señales en lo que pudimos revisar.',medium:'Hay detalles que merecen una revisión.',high:'Toma una pausa antes de abrirlo.',unknown:'No tenemos información suficiente.'};
  const descriptions={low:'Confirma que esperabas este archivo y verifica al remitente. La ausencia de señales no garantiza su seguridad.',medium:'Revisa los hallazgos y confirma la legitimidad del archivo por un canal independiente antes de interactuar con él.',high:'La combinación de indicadores requiere especial atención. Evita ingresar credenciales y confirma el origen por otro medio.',unknown:'No se pudo evaluar todo el contenido. No interpretes la puntuación baja como una señal de seguridad.'};
  $('risk-title').textContent=titles[r.risk];
  $('risk-description').textContent=descriptions[r.risk];
  $('signal-count').textContent=String(r.signals.length);
  $('link-count').textContent=String(r.links.length);
  $('analysis-time').textContent=r.duration_ms<1000?`${r.duration_ms} ms`:`${(r.duration_ms/1000).toFixed(1)} s`;
  $('file-name').textContent=r.file.name;
  $('file-type').textContent=`${r.file.type_label} · ${bytes(r.file.size)} · ${new Date(r.analyzed_at).toLocaleString('es-MX')}`;
  $('file-hash').textContent=`${r.file.sha256.slice(0,12)}…${r.file.sha256.slice(-8)}`;
  $('file-hash').title=r.file.sha256;
  $('warnings').innerHTML=r.warnings.length?`<div class="note warning">${icon('alert')}<div><strong>Alcance limitado en este archivo</strong><ul>${r.warnings.map(w=>`<li>${esc(w)}</li>`).join('')}</ul></div></div>`:'';
  $('tab-signal-count').textContent=String(r.signals.length);
  $('tab-link-count').textContent=String(r.links.length);
  const signals=[...r.signals].sort((a,b)=>b.weight-a.weight);
  $('detail-signals').innerHTML=signals.length?signals.map(s=>`<article class="finding"><span class="file-icon ${colors[s.severity]}">${icon('alert')}</span><div class="finding-body"><div class="finding-header"><h3>${esc(s.title)}</h3><span class="badge ${colors[s.severity]}">${esc(severityLabels[s.severity])} · +${esc(s.weight)} puntos</span></div><p>${esc(s.explanation)}</p><div class="evidence">${s.evidence.map(e=>esc(defang(e))).join('<br>')}</div><div class="rule-id">Regla ${esc(s.id)}</div></div></article>`).join(''):`<div class="empty-state">${icon(r.status==='complete'?'check':'info')}<h3>${r.status==='complete'?'No se detectaron las señales evaluadas':'No se encontraron señales en el contenido revisado'}</h3><p>${r.status==='complete'?'Este resultado no garantiza que el archivo sea seguro. Faro solo revisa los indicadores descritos en su metodología.':'La revisión tiene limitaciones. Consulta los avisos antes de tomar una decisión.'}</p></div>`;
  $('detail-links').innerHTML=`<div class="note">${icon('lock')} Las direcciones se muestran desactivadas para evitar visitas accidentales. Faro no consultó su reputación ni descargó sus destinos.</div>`+(r.links.length?r.links.map(l=>`<div class="link-row">${icon('link')}<div><code>${esc(defang(l.url))}</code><p>Host real: ${esc(l.host.replace(/\./g,'[.]'))} · ${esc(l.source)}</p><div class="link-flags">${l.flags.map(f=>`<span class="badge amber">${esc(f)}</span>`).join('')||'<span class="badge neutral">Sin alertas de estructura</span>'}</div></div></div>`).join(''):`<div class="empty-state"><h3>No se extrajeron enlaces</h3><p>No incluye enlaces en imágenes, texto ofuscado o contenido que no pudo inspeccionarse.</p></div>`);
  const detailNames={pages:'Páginas',encrypted:'Cifrado',objects_checked:'Objetos revisados',forms:'Formularios',password_fields:'Campos de contraseña',characters:'Caracteres',xml_parts:'Partes XML',container_entries:'Entradas del contenedor'};
  const rows=[['Motor',`Faro ${r.engine_version}`],['Estado',statusLabels[r.status]],['Formato identificado',r.file.type_label],['Tamaño',bytes(r.file.size)],...Object.entries(r.details).map(([k,v])=>[detailNames[k]||k,typeof v==='boolean'?(v?'Sí':'No'):v])];
  $('detail-details').innerHTML=`<div class="detail-grid">${rows.map(([k,v])=>`<div class="detail-item"><span>${esc(k)}</span><strong>${esc(v)}</strong></div>`).join('')}</div><div class="full-hash"><strong>SHA-256</strong><br>${esc(r.file.sha256)}</div><h3>Limitaciones del análisis</h3><ul class="limits">${r.limitations.map(l=>`<li>${esc(l)}</li>`).join('')}</ul>`;
  $('remember').checked=history.some(h=>h.sha256===r.file.sha256);
  selectTab('signals');
}
function selectTab(tab) {
  document.querySelectorAll('.tab').forEach(b=>{const active=b.dataset.tab===tab;b.classList.toggle('active',active);b.setAttribute('aria-selected',String(active));b.tabIndex=active?0:-1;});
  document.querySelectorAll('.tab-content').forEach(p=>{p.hidden=p.id!==`detail-${tab}`;});
}
document.querySelectorAll('.tab').forEach((button,index,list)=>{
  button.addEventListener('click',()=>selectTab(button.dataset.tab));
  button.addEventListener('keydown',e=>{
    if(!['ArrowRight','ArrowLeft','Home','End'].includes(e.key))return;
    e.preventDefault();const next=e.key==='Home'?0:e.key==='End'?list.length-1:(index+(e.key==='ArrowRight'?1:list.length-1))%list.length;
    selectTab(list[next].dataset.tab);list[next].focus();
  });
});
$('export-json').addEventListener('click',()=>{
  if(!report)return;
  const url=URL.createObjectURL(new Blob([JSON.stringify(report,null,2)],{type:'application/json'}));
  const a=document.createElement('a');a.href=url;a.download=`faro-${report.file.sha256.slice(0,12)}.json`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
});
$('print-report').addEventListener('click',()=>{if(report)window.print();});
$('copy-hash').addEventListener('click',async()=>{
  if(!report)return;
  try{await navigator.clipboard.writeText(report.file.sha256);toast('Huella SHA-256 copiada.');}catch(_){toast('Copia la huella desde Detalles técnicos.');}
});
const ruleExamples=[['file.extension_mismatch','Extensión distinta al contenido',30],['html.password','Campo de contraseña',20],['html.credential_destination','Formulario de contraseña con destino de red',35],['html.link_mismatch','Texto del enlace distinto al destino',25],['pdf.javascript','JavaScript en el PDF',20],['pdf.launch','Acción Launch',45],['office.macros','Presencia de macros',30],['url.userinfo','Usuario incrustado en una URL',25],['text.urgency','Texto de urgencia',5]];
$('rules-list').innerHTML=ruleExamples.map(([id,title,points])=>`<div class="rule-line"><span>${esc(title)}<br><small>${esc(id)}</small></span><strong>+${points} puntos</strong></div>`).join('');
async function checkHealth(){
  try{$('connection').innerHTML=`<span class="status-light"></span>${esc(await transport.health())}`;}
  catch(_){$('connection').textContent='Motor no disponible';}
}
navigate();renderHistory();checkHealth();
