document.addEventListener('DOMContentLoaded',()=>{const form=document.getElementById('checkout-form');if(!form)return;const inputs=[...form.querySelectorAll('.qty-input')];const output=document.getElementById('estimated-total');const currency=(document.querySelector('.total-box strong')?.textContent||'UGX').split(' ')[0];const update=()=>{let total=0;for(const input of inputs){const qty=Math.max(0,Math.min(Number.parseInt(input.value||'0',10)||0,Number.parseInt(input.max||'0',10)||0));input.value=String(qty);total+=qty*(Number.parseFloat(input.dataset.price)||0)}output.textContent=currency+' '+total.toLocaleString(undefined,{minimumFractionDigits:2,maximumFractionDigits:2})};inputs.forEach(input=>input.addEventListener('input',update));update()});
document.addEventListener('DOMContentLoaded',()=>{
  const money = value => new Intl.NumberFormat(undefined,{minimumFractionDigits:2,maximumFractionDigits:2}).format(Number(value)||0);
  document.querySelectorAll('.chart[data-chart]').forEach(node=>{
    let rows, series;
    try { rows=JSON.parse(node.dataset.chartData||'[]'); series=JSON.parse(node.dataset.chartSeries||'[]'); } catch(e) { node.textContent='Chart data could not be loaded.'; return; }
    if(!rows.length||!series.length){node.innerHTML='<div class="chart-empty">No data available for this period.</div>';return;}
    const esc=s=>String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
    if(node.dataset.chart==='bars'){
      const key=series[0].key, max=Math.max(1,...rows.map(r=>Number(r[key])||0));
      node.innerHTML=rows.map(row=>{const value=Math.max(0,Number(row[key])||0),pct=Math.min(100,value/max*100),shown=key==='quantity'?String(Math.round(value)):money(value);return '<div class="bar-chart-row"><span class="bar-chart-label" title="'+esc(row.label)+'">'+esc(row.label)+'</span><div class="bar-chart-track" aria-hidden="true"><div class="bar-chart-fill" style="width:'+pct+'%;background:'+esc(series[0].color||'#e8a020')+'"></div></div><strong class="bar-chart-value">'+shown+'</strong></div>';}).join('');
      return;
    }
    const width=760,height=260,left=62,right=18,top=18,bottom=42,plotW=width-left-right,plotH=height-top-bottom;
    const all=rows.flatMap(r=>series.map(s=>Number(r[s.key])||0)), max=Math.max(1,...all), min=Math.min(0,...all), span=Math.max(1,max-min);
    const x=i=>left+(rows.length<2?plotW/2:i*plotW/(rows.length-1)), y=v=>top+(max-v)*plotH/span;
    let svg='<svg viewBox="0 0 '+width+' '+height+'" role="img" aria-label="'+esc(node.getAttribute('aria-label')||node.dataset.chartTitle||'Chart')+'">';
    for(let i=0;i<=4;i++){const val=max-(max-min)*i/4, yy=y(val);svg+='<line class="chart-grid" x1="'+left+'" y1="'+yy+'" x2="'+(width-right)+'" y2="'+yy+'"/><text class="chart-axis" x="'+(left-8)+'" y="'+(yy+4)+'" text-anchor="end">'+esc(money(val))+'</text>';}
    const stride=Math.max(1,Math.ceil(rows.length/7));
    rows.forEach((r,i)=>{if(i%stride===0||i===rows.length-1){const label=String(r.label||'');svg+='<text class="chart-axis" x="'+x(i)+'" y="'+(height-12)+'" text-anchor="middle">'+esc(label.length>10?label.slice(5):label)+'</text>'; }});
    series.forEach(s=>{const pts=rows.map((r,i)=>x(i)+','+y(Number(r[s.key])||0)).join(' ');svg+='<polyline class="chart-line" stroke="'+esc(s.color||'#e8a020')+'" points="'+pts+'"/>';rows.forEach((r,i)=>{const v=Number(r[s.key])||0;svg+='<circle class="chart-point" cx="'+x(i)+'" cy="'+y(v)+'" r="3.5" fill="'+esc(s.color||'#e8a020')+'"><title>'+esc(r.label)+' · '+esc(s.label)+': '+esc(money(v))+'</title></circle>';});});
    svg+='</svg>';node.innerHTML=svg;
  });
});
