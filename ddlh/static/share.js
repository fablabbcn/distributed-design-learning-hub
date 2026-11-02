// Share buttons: any `[data-share-url]` copies its URL and shows a toast
(() => {
  let toast;
  let hideTimer;

  const showToast = (message) => {
    if (!toast) {
      toast = document.createElement("div");
      toast.className = "share-toast";
      toast.setAttribute("role", "status");
      toast.setAttribute("aria-live", "polite");
      document.body.appendChild(toast);
    }
    toast.textContent = message;
    // Force a reflow so the transition replays on repeated clicks
    toast.classList.remove("is-visible");
    void toast.offsetWidth;
    toast.classList.add("is-visible");
    clearTimeout(hideTimer);
    hideTimer = setTimeout(() => toast.classList.remove("is-visible"), 2000);
  };

  document.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-share-url]");
    if (!button) return;
    try {
      await navigator.clipboard.writeText(button.dataset.shareUrl);
      showToast("Link copied to clipboard");
    } catch {
      showToast("Couldn't copy the link");
    }
  });
})();
