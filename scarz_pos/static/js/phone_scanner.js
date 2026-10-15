document.addEventListener('DOMContentLoaded', () => {
  const checkout = document.getElementById('checkout-form');
  const search = document.getElementById('product-search');
  if (!checkout || !search) return;
  const csrf = checkout.querySelector('input[name="csrf_token"]')?.value || '';
  const entry = search.closest('.barcode-entry');
  if (!entry) return;
  const button = document.createElement('button');
  button.type = 'button'; button.className = 'button secondary scan-button'; button.textContent = 'Connect phone';
  entry.appendChild(button);
  const dialog = document.createElement('dialog');
  dialog.className = 'scanner-dialog';
  dialog.innerHTML = '<div class="scanner-dialog-inner"><div class="panel-heading"><h2>Connect your phone</h2><button type="button" class="button secondary" data-close>Close</button></div><p class="muted">Scan this QR with your phone, or copy the link and open it on the phone. The pairing expires in 20 minutes.</p><div data-qr style="display:flex;justify-content:center;padding:1rem;min-height:180px"></div><label>Phone scanner link<input data-link readonly></label><button type="button" class="button secondary full" data-copy>Copy phone link</button><p class="muted" data-status aria-live="polite">Creating secure pairing…</p></div>';
  document.body.appendChild(dialog);
  const status = dialog.querySelector('[data-status]');
  const qr = dialog.querySelector('[data-qr]');
  const link = dialog.querySelector('[data-link]');
  let poller = null;
  const stopPolling = () => { if (poller) clearInterval(poller); poller = null; };
  dialog.querySelector('[data-close]').addEventListener('click', () => { stopPolling(); dialog.close(); });
  dialog.addEventListener('cancel', stopPolling);
  dialog.querySelector('[data-copy]').addEventListener('click', async () => {
    try { await navigator.clipboard.writeText(link.value); status.textContent = 'Link copied. Open it on your phone.'; }
    catch (_) { link.select(); status.textContent = 'Select and copy the link to your phone.'; }
  });
  button.addEventListener('click', async () => {
    stopPolling(); qr.textContent = ''; link.value = ''; status.textContent = 'Creating secure pairing…'; dialog.showModal();
    try {
      const response = await fetch('/scanner/pair', {method:'POST', headers:{'X-CSRFToken':csrf}});
      if (!response.ok) throw new Error('Could not create pairing. Refresh the page and sign in again.');
      const data = await response.json();
      const phoneUrl = window.location.origin + '/scanner/phone/' + encodeURIComponent(data.token);
      link.value = phoneUrl;
      try {
        await new Promise((resolve, reject) => {
          const script = document.createElement('script');
          script.src = 'https://cdnjs.cloudflare.com/ajax/libs/qrcodejs/1.0.0/qrcode.min.js';
          script.onload = resolve; script.onerror = () => reject(new Error('QR library unavailable'));
          document.head.appendChild(script);
        });
        new QRCode(qr, {text:phoneUrl,width:200,height:200});
      } catch (_) { qr.textContent = 'QR code unavailable. Copy the phone link below instead.'; }
      status.textContent = 'Waiting for a barcode from your phone… Keep checkout open.';
      let lastSequence = 0;
      poller = setInterval(async () => {
        if (!dialog.open) { stopPolling(); return; }
        try {
          const result = await fetch('/scanner/pair/' + encodeURIComponent(data.token) + '/next', {cache:'no-store'});
          if (!result.ok) { stopPolling(); status.textContent = 'Pairing expired. Close this dialog and connect again.'; return; }
          const payload = await result.json();
          if (payload.code && payload.sequence > lastSequence) {
            lastSequence = payload.sequence;
            search.value = payload.code;
            search.dispatchEvent(new Event('input', {bubbles:true}));
            search.dispatchEvent(new KeyboardEvent('keydown', {key:'Enter',bubbles:true,cancelable:true}));
            status.textContent = 'Received barcode ' + payload.code + '. Ready for the next scan.';
          }
        } catch (_) { status.textContent = 'Connection interrupted. Reconnecting…'; }
      }, 800);
    } catch (error) { status.textContent = error.message || 'Could not create pairing.'; }
  });
});
