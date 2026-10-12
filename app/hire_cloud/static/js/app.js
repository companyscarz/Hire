(() => {
  let deferredInstallPrompt = null;
  const installButton = document.getElementById("install-button");

  window.addEventListener("beforeinstallprompt", (event) => {
    event.preventDefault();
    deferredInstallPrompt = event;
    if (installButton) installButton.hidden = false;
  });

  if (installButton) {
    installButton.addEventListener("click", async () => {
      if (!deferredInstallPrompt) return;
      deferredInstallPrompt.prompt();
      await deferredInstallPrompt.userChoice;
      deferredInstallPrompt = null;
      installButton.hidden = true;
    });
  }

  if ("serviceWorker" in navigator && window.location.protocol === "https:") {
    window.addEventListener("load", async () => {
      try {
        const registration = await navigator.serviceWorker.register(
          "/service-worker.js",
          { updateViaCache: "none" }
        );
        // Ask the browser to check for a changed worker when the app is opened.
        await registration.update();
      } catch (_) {
        // The online app remains usable if offline caching cannot register.
      }
    });
  }
})();
