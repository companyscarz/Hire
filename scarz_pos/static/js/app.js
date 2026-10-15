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

document.addEventListener('DOMContentLoaded',()=>{
  const search=document.getElementById('product-search');
  const rows=[...document.querySelectorAll('[data-product-row]')];
  const status=document.getElementById('product-search-status');
  const dialog=document.getElementById('barcode-camera-dialog');
  const video=document.getElementById('barcode-camera-video');
  const cameraStatus=document.getElementById('barcode-camera-status');
  let stream=null, frame=0, scanning=false;
  const normalise=value=>String(value||'').trim().toLocaleLowerCase();
  const filterRows=()=>{
    if(!search)return;
    const query=normalise(search.value);
    rows.forEach(row=>{
      const haystack=[row.dataset.productName,row.dataset.productSku,row.dataset.productBarcode].map(normalise);
      row.hidden=Boolean(query)&&!haystack.some(value=>value.includes(query));
    });
  };
  const updateSearchStatus=message=>{if(status)status.textContent=message;};
  const addExactMatch=code=>{
    if(!search)return false;
    const wanted=String(code||'').trim();
    if(!wanted)return false;
    const row=rows.find(item=>item.dataset.productBarcode===wanted||item.dataset.productSku===wanted);
    if(!row)return false;
    const qty=row.querySelector('.qty-input');
    const available=Number.parseInt(qty?.max||'0',10)||0;
    const current=Number.parseInt(qty?.value||'0',10)||0;
    if(!qty||available<1){updateSearchStatus('This item is out of stock. Check inventory before selling it.');return true;}
    if(current>=available){updateSearchStatus('Only '+available+' unit(s) are in stock for '+row.querySelector('td strong')?.textContent+'.');return true;}
    qty.value=String(current+1);
    qty.dispatchEvent(new Event('input',{bubbles:true}));
    updateSearchStatus('Added '+row.querySelector('td strong')?.textContent+' · quantity '+qty.value+'.');
    search.value='';
    filterRows();
    search.focus();
    return true;
  };
  if(search){
    search.addEventListener('input',filterRows);
    search.addEventListener('keydown',event=>{
      if(event.key!=='Enter')return;
      event.preventDefault();
      if(!addExactMatch(search.value))updateSearchStatus('No exact barcode or SKU match. Keep searching by name, or register the barcode on the Products page.');
    });
    search.addEventListener('barcode:detected',event=>{
      const code=event.detail?.value||search.value;
      if(!addExactMatch(code))updateSearchStatus('No product matches barcode '+code+'. Register the item on the Products page first.');
    });
  }
  const stopCamera=()=>{
    scanning=false;
    if(frame)cancelAnimationFrame(frame);
    frame=0;
    if(stream){stream.getTracks().forEach(track=>track.stop());stream=null;}
    if(video)video.srcObject=null;
  };
  document.querySelectorAll('[data-scanner-close]').forEach(button=>button.addEventListener('click',()=>{
    stopCamera();
    if(dialog?.open)dialog.close();
  }));
  if(dialog)dialog.addEventListener('cancel',stopCamera);
  document.querySelectorAll('[data-barcode-scanner]').forEach(button=>button.addEventListener('click',async()=>{
    const target=document.getElementById(button.dataset.barcodeTarget);
    if(!target)return;
    if(!window.BarcodeDetector){
      if(cameraStatus)cameraStatus.textContent='This browser does not provide native barcode detection. Type the barcode or use a USB/Bluetooth scanner; no extra library is installed.';
      if(dialog&&!dialog.open)dialog.showModal();
      return;
    }
    if(!navigator.mediaDevices?.getUserMedia){
      if(cameraStatus)cameraStatus.textContent='Camera access is unavailable in this browser or page context. Type the barcode or use a USB/Bluetooth scanner.';
      if(dialog&&!dialog.open)dialog.showModal();
      return;
    }
    if(dialog&&!dialog.open)dialog.showModal();
    if(cameraStatus)cameraStatus.textContent='Requesting camera access…';
    try{
      const availableFormats=await BarcodeDetector.getSupportedFormats();
      const formats=['ean_13','ean_8','upc_a','upc_e','code_128','code_39','itf','codabar'].filter(format=>availableFormats.includes(format));
      if(!formats.length){
        if(cameraStatus)cameraStatus.textContent='This browser cannot detect common retail barcodes. Type the barcode or use a USB/Bluetooth scanner.';
        return;
      }
      const detector=new BarcodeDetector({formats});
      stream=await navigator.mediaDevices.getUserMedia({video:{facingMode:{ideal:'environment'}},audio:false});
      video.srcObject=stream;
      await video.play();
      scanning=true;
      if(cameraStatus)cameraStatus.textContent='Hold the barcode steady inside the camera view.';
      const scanFrame=async()=>{
        if(!scanning)return;
        try{
          const codes=await detector.detect(video);
          const value=codes.find(code=>code.rawValue)?.rawValue;
          if(value){
            stopCamera();
            target.value=value;
            target.dispatchEvent(new Event('input',{bubbles:true}));
            target.dispatchEvent(new CustomEvent('barcode:detected',{bubbles:true,detail:{value}}));
            if(dialog?.open)dialog.close();
            if(target.id==='product-barcode')target.focus();
            return;
          }
        }catch(_error){
          stopCamera();
          if(cameraStatus)cameraStatus.textContent='The camera could not read this barcode. Try better lighting, type it manually, or use a hardware scanner.';
          return;
        }
        frame=requestAnimationFrame(scanFrame);
      };
      frame=requestAnimationFrame(scanFrame);
    }catch(_error){
      stopCamera();
      if(cameraStatus)cameraStatus.textContent='Camera permission or hardware is unavailable. Type the barcode or use a USB/Bluetooth scanner.';
    }
  }));
  if(!window.BarcodeDetector){
    document.querySelectorAll('[data-scanner-help]').forEach(node=>node.textContent='Camera scanning is not supported in this browser. Type the barcode or use a USB/Bluetooth scanner; product entry and sales search still work.');
  }
});
