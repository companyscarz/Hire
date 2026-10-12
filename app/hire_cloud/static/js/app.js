(() => {
  let deferredInstallPrompt = null;
  const installButton = document.getElementById("install-button");
  const installStatus = document.getElementById("install-status");
  const installInstructions = document.getElementById("install-instructions");

  const isStandalone = () =>
    window.matchMedia("(display-mode: standalone)").matches ||
    window.navigator.standalone === true;

  const setInstallStatus = (message) => {
    if (installStatus) installStatus.textContent = message;
  };

  if (isStandalone()) {
    if (installButton) {
      installButton.hidden = true;
      installButton.setAttribute("aria-hidden", "true");
    }
    setInstallStatus("You're using the installed app");
  }

  window.addEventListener("beforeinstallprompt", (event) => {
    event.preventDefault();
    deferredInstallPrompt = event;
    if (installButton && !isStandalone()) {
      installButton.hidden = false;
      installButton.disabled = false;
      installButton.textContent = "Install app";
    }
    setInstallStatus("Ready to install on this device");
  });

  if (installButton) {
    installButton.addEventListener("click", async () => {
      if (isStandalone()) {
        setInstallStatus("Hire Cloud is already installed on this device");
        installButton.hidden = true;
        return;
      }

      if (!deferredInstallPrompt) {
        const help = installButton.closest(".install-card")?.querySelector(".install-help");
        if (help) {
          help.open = true;
          help.scrollIntoView({ behavior: "smooth", block: "nearest" });
        }
        setInstallStatus("Use the instructions below for your browser");
        return;
      }

      installButton.disabled = true;
      try {
        deferredInstallPrompt.prompt();
        const choice = await deferredInstallPrompt.userChoice;
        if (choice?.outcome === "accepted") {
          setInstallStatus("Installation started");
        } else {
          setInstallStatus("Installation was cancelled. You can try again from your browser menu.");
        }
      } catch (_) {
        setInstallStatus("Use your browser menu to install Hire Cloud.");
      } finally {
        deferredInstallPrompt = null;
        installButton.disabled = false;
      }
    });
  }

  window.addEventListener("appinstalled", () => {
    deferredInstallPrompt = null;
    if (installButton) installButton.hidden = true;
    setInstallStatus("Hire Cloud was installed successfully");
  });

  if (installInstructions && /iPhone|iPad|iPod/i.test(navigator.userAgent)) {
    const paragraphs = installInstructions.querySelectorAll("p");
    paragraphs.forEach((paragraph) => {
      if (paragraph.textContent.includes("Android")) paragraph.hidden = true;
    });
  }

  if ("serviceWorker" in navigator && window.location.protocol === "https:") {
    window.addEventListener("load", async () => {
      try {
        const registration = await navigator.serviceWorker.register(
          "/service-worker.js",
          { updateViaCache: "none" }
        );
        await registration.update();
      } catch (_) {
        // The online app remains usable if offline caching cannot register.
      }
    });
  }
})();
