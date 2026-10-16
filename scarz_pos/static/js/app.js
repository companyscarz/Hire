document.addEventListener('DOMContentLoaded',()=>{
  const form=document.getElementById('checkout-form');
  if(!form)return;
  const inputs=[...form.querySelectorAll('.qty-input')];
  const output=document.getElementById('estimated-total');
  const currency=(document.querySelector('.total-box strong')?.textContent||'UGX').split(' ')[0];
  const update=()=>{
    let total=0;
    for(const input of inputs){
      const qty=Math.max(0,Math.min(Number.parseInt(input.value||'0',10)||0,Number.parseInt(input.max||'0',10)||0));
      input.value=String(qty);
      total+=qty*(Number.parseFloat(input.dataset.price)||0);
      const row=input.closest('tr');
      const remove=row?.querySelector('[data-remove-sale-item]');
      if(remove)remove.hidden=qty===0;
      if(row)row.classList.toggle('sale-item-selected',qty>0);
    }
    if(output)output.textContent=currency+' '+total.toLocaleString(undefined,{minimumFractionDigits:2,maximumFractionDigits:2});
  };
  inputs.forEach(input=>input.addEventListener('input',update));
  form.querySelectorAll('[data-remove-sale-item]').forEach(button=>button.addEventListener('click',()=>{
    const row=button.closest('tr');
    const input=row?.querySelector('.qty-input');
    if(!input)return;
    input.value='0';
    input.dispatchEvent(new Event('input',{bubbles:true}));
    const productName=row.querySelector('td strong')?.textContent?.trim()||'Item';
    const status=document.getElementById('product-search-status');
    if(status)status.textContent=productName+' removed from this sale. Other selected items are unchanged.';
    button.blur();
  }));
  update();
});
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
  // Freeze the page behind the camera dialog on mobile, preserving the exact scroll position.
  let scannerPageScrollY=0;
  let scannerPageLocked=false;
  let scannerBodyStyles=null;
  const lockPageForScanner=()=>{
    if(scannerPageLocked)return;
    scannerPageScrollY=window.scrollY||window.pageYOffset||0;
    scannerBodyStyles={position:document.body.style.position,top:document.body.style.top,left:document.body.style.left,right:document.body.style.right,width:document.body.style.width,overflow:document.body.style.overflow};
    document.body.style.position='fixed';
    document.body.style.top=`-${scannerPageScrollY}px`;
    document.body.style.left='0';
    document.body.style.right='0';
    document.body.style.width='100%';
    document.body.style.overflow='hidden';
    scannerPageLocked=true;
  };
  const unlockPageForScanner=()=>{
    if(!scannerPageLocked)return;
    const old=scannerBodyStyles||{};
    document.body.style.position=old.position||'';
    document.body.style.top=old.top||'';
    document.body.style.left=old.left||'';
    document.body.style.right=old.right||'';
    document.body.style.width=old.width||'';
    document.body.style.overflow=old.overflow||'';
    scannerPageLocked=false;
    scannerBodyStyles=null;
    window.scrollTo(0,scannerPageScrollY);
  };
  if(dialog)dialog.addEventListener('close',unlockPageForScanner);
  const cameraStatus=document.getElementById('barcode-camera-status');
  let stream=null, frame=0, scanning=false, zxingReader=null, nativeDetector=null, scanToken=0;
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
    const codeMatch=rows.find(item=>item.dataset.productBarcode===wanted||item.dataset.productSku===wanted);
    const exactNameMatches=rows.filter(item=>normalise(item.dataset.productName)===normalise(wanted));
    const row=codeMatch||(exactNameMatches.length===1?exactNameMatches[0]:null);
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
    scanToken++;
    if(frame)cancelAnimationFrame(frame);
    frame=0;
    if(zxingReader){try{zxingReader.stopContinuousDecode();}catch(_error){} zxingReader=null;}
    nativeDetector=null;
    if(stream){stream.getTracks().forEach(track=>track.stop());stream=null;}
    if(video){video.pause();video.srcObject=null;}
  };
  const showDialog=()=>{
    if(dialog&&!dialog.open){
      lockPageForScanner();
      dialog.showModal();
    }
  };
  const setCameraStatus=message=>{if(cameraStatus)cameraStatus.textContent=message;};
  const loadScript=src=>new Promise((resolve,reject)=>{
    const existing=document.querySelector('script[data-barcode-decoder]');
    if(existing){
      if(existing.dataset.loaded==='true'){resolve();return;}
      existing.addEventListener('load',()=>resolve(),{once:true});
      existing.addEventListener('error',()=>reject(new Error('Decoder library could not be loaded.')),{once:true});
      return;
    }
    const script=document.createElement('script');
    script.src=src;
    script.async=true;
    script.dataset.barcodeDecoder='true';
    script.onload=()=>{script.dataset.loaded='true';resolve();};
    script.onerror=()=>{script.remove();reject(new Error('Decoder library could not be loaded.'));};
    document.head.appendChild(script);
  });
  const deliverBarcode=(target,value)=>{
    if(!value)return;
    stopCamera();
    target.value=value;
    target.dispatchEvent(new Event('input',{bubbles:true}));
    target.dispatchEvent(new CustomEvent('barcode:detected',{bubbles:true,detail:{value}}));
    if(dialog?.open)dialog.close();
    if(target.id==='product-barcode')target.focus();
  };
  document.querySelectorAll('[data-scanner-close]').forEach(button=>button.addEventListener('click',()=>{
    stopCamera();
    if(dialog?.open)dialog.close();
  }));
  if(dialog)dialog.addEventListener('cancel',stopCamera);
  document.querySelectorAll('[data-barcode-scanner]').forEach(button=>button.addEventListener('click',async()=>{
    const target=document.getElementById(button.dataset.barcodeTarget);
    if(!target)return;
    if(!navigator.mediaDevices?.getUserMedia){
      showDialog();
      setCameraStatus('This page cannot access a camera. Use HTTPS or localhost, allow camera access in browser settings, or type the barcode / use a USB scanner.');
      return;
    }
    stopCamera();
    const thisScan=scanToken;
    showDialog();
    setCameraStatus('Requesting camera access…');
    try{
      stream=await navigator.mediaDevices.getUserMedia({video:{facingMode:{ideal:'environment'},width:{ideal:1280},height:{ideal:720}},audio:false});
      if(thisScan!==scanToken){stream.getTracks().forEach(track=>track.stop());return;}
      video.srcObject=stream;
      video.setAttribute('autoplay','');
      video.setAttribute('playsinline','');
      video.muted=true;
      await video.play();
      scanning=true;
      // Use ZXing for consistent desktop decoding, even when a partial native
      // BarcodeDetector implementation exists in the browser.
      const track=stream.getVideoTracks()[0];
      if(track?.applyConstraints){
        try{
          const capabilities=track.getCapabilities?.()||{};
          const advanced=[];
          if(capabilities.focusMode?.includes('continuous'))advanced.push({focusMode:'continuous'});
          if(advanced.length)await track.applyConstraints({advanced});
        }catch(_error){}
      }
      setCameraStatus('Camera is on. Preparing barcode detection…');
      const startNativeScanner=async()=>{
        if(!window.BarcodeDetector||typeof window.BarcodeDetector.getSupportedFormats!=='function')return false;
        try{
          const supported=await window.BarcodeDetector.getSupportedFormats();
          const wanted=['ean_13','ean_8','upc_a','upc_e','code_128','code_39','itf','codabar','qr_code'];
          const formats=wanted.filter(format=>supported.includes(format));
          if(!formats.length)return false;
          nativeDetector=new window.BarcodeDetector({formats});
          setCameraStatus('Camera is on. Hold the barcode inside the frame, keep it steady, and use good light…');
          const detect=async()=>{
            if(thisScan!==scanToken||!scanning||!nativeDetector)return;
            try{
              const results=await nativeDetector.detect(video);
              const match=results.find(item=>item.rawValue);
              if(match){deliverBarcode(target,match.rawValue);return;}
            }catch(_error){
              if(thisScan!==scanToken||!scanning)return;
              nativeDetector=null;
              setCameraStatus('Switching to compatibility barcode scanner…');
              await runZXingFallback(target,thisScan);
              return;
            }
            if(thisScan===scanToken&&scanning&&nativeDetector)window.setTimeout(detect,140);
          };
          detect();
          return true;
        }catch(_error){nativeDetector=null;return false;}
      };
      if(!(await startNativeScanner()))await runZXingFallback(target,thisScan);
    }catch(error){
      stopCamera();
      const name=error?.name||'';
      if(name==='NotAllowedError'||name==='PermissionDeniedError'){
        setCameraStatus('Camera permission was denied. Allow camera access for this site in Chrome settings, then try again.');
      }else if(name==='NotFoundError'||name==='DevicesNotFoundError'){
        setCameraStatus('No camera was found. Connect a webcam, or use a USB/Bluetooth barcode scanner or manual entry.');
      }else if(name==='NotReadableError'||name==='TrackStartError'){
        setCameraStatus('The camera is busy or blocked by another app. Close other camera apps and try again.');
      }else if(name==='NotSecureContext'){
        setCameraStatus('Camera access requires HTTPS or localhost. Open the secure site, then try again.');
      }else{
        setCameraStatus('Could not start the camera ('+name+'). Check Chrome site permissions and that another app is not using the camera, or enter the barcode manually.');
      }
    }
  }));
  async function runZXingFallback(target,thisScan){
    try{
      await loadScript('https://unpkg.com/@zxing/library@0.21.3/umd/index.min.js');
      if(thisScan!==scanToken||!scanning)return;
      if(!window.ZXing?.BrowserMultiFormatReader)throw new Error('Barcode decoder is unavailable.');
      const hints=new Map();
      const formats=[
        window.ZXing.BarcodeFormat.EAN_13,
        window.ZXing.BarcodeFormat.EAN_8,
        window.ZXing.BarcodeFormat.UPC_A,
        window.ZXing.BarcodeFormat.UPC_E,
        window.ZXing.BarcodeFormat.CODE_128,
        window.ZXing.BarcodeFormat.CODE_39,
        window.ZXing.BarcodeFormat.ITF,
        window.ZXing.BarcodeFormat.CODABAR
      ].filter(format=>format!==undefined);
      if(window.ZXing.DecodeHintType?.POSSIBLE_FORMATS&&formats.length){
        hints.set(window.ZXing.DecodeHintType.POSSIBLE_FORMATS,formats);
      }
      if(window.ZXing.DecodeHintType?.TRY_HARDER){
        hints.set(window.ZXing.DecodeHintType.TRY_HARDER,true);
      }
      const reader=new window.ZXing.BrowserMultiFormatReader(hints,250);
      zxingReader=reader;
      setCameraStatus('Camera is on. Enhanced barcode scanning is active. Center the barcode, keep it steady, and move it closer if needed…');
      reader.decodeFromVideoElementContinuously(video,(result,_error)=>{
        if(thisScan!==scanToken||!scanning)return;
        if(result?.getText)deliverBarcode(target,result.getText());
      }).catch(()=>{
        if(thisScan!==scanToken)return;
        stopCamera();
        setCameraStatus('The camera is on, but the decoder could not process the video. Try better lighting or enter the barcode manually.');
      });
    }catch(_error){
      if(thisScan!==scanToken)return;
      stopCamera();
      setCameraStatus('The camera opened, but the compatibility decoder could not load. Check your internet connection, then retry; manual entry and USB/Bluetooth scanners still work.');
    }
  }
  if(!window.BarcodeDetector){
    document.querySelectorAll('[data-scanner-help]').forEach(node=>node.textContent='Camera scanning uses a compatibility decoder when native browser support is missing. Allow camera access and keep the device online for the first decoder load. Manual entry and USB/Bluetooth scanners also work.');
  }
});


// Shared appearance preference and progressive-web-app installation.
document.addEventListener('DOMContentLoaded',()=>{
  const root=document.documentElement;
  const toggle=document.getElementById('theme-toggle');
  const meta=document.getElementById('theme-color-meta');
  const applyTheme=theme=>{
    const value=theme==='dark'?'dark':'light';
    root.dataset.theme=value;
    if(meta)meta.setAttribute('content',value==='dark'?'#070e19':'#0a1628');
    if(toggle){
      const next=value==='dark'?'light':'dark';
      toggle.setAttribute('aria-pressed',String(value==='dark'));
      toggle.setAttribute('aria-label','Switch to '+next+' theme');
      const label=toggle.querySelector('.theme-toggle-label');
      const icon=toggle.querySelector('.theme-toggle-icon');
      if(label)label.textContent=value==='dark'?'Light mode':'Dark mode';
      if(icon)icon.textContent=value==='dark'?'☀':'◐';
    }
  };
  applyTheme(root.dataset.theme||'light');
  toggle?.addEventListener('click',()=>{
    const next=root.dataset.theme==='dark'?'light':'dark';
    applyTheme(next);
    try{localStorage.setItem('hire-pos-theme',next);}catch(_error){}
  });
  const installButton=document.getElementById('install-app');
  let installPrompt=null;
  const standalone=()=>window.matchMedia('(display-mode: standalone)').matches||window.navigator.standalone===true;
  if(installButton){
    if(standalone())installButton.hidden=true;
    window.addEventListener('beforeinstallprompt',event=>{
      event.preventDefault();
      installPrompt=event;
      installButton.hidden=false;
    });
    window.addEventListener('appinstalled',()=>{
      installPrompt=null;
      installButton.hidden=true;
    });
    installButton.addEventListener('click',async()=>{
      if(!installPrompt){
        installButton.hidden=true;
        return;
      }
      installPrompt.prompt();
      try{await installPrompt.userChoice;}catch(_error){}
      installPrompt=null;
      installButton.hidden=true;
    });
  }
});
