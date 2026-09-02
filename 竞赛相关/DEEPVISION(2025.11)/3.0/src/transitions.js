/* DeepVision - Unified Page Transitions & Nav Enhancement
   Include after main scripts on all pages */

(function() {
    if (window.__DV_TRANSITIONS__) return;
    window.__DV_TRANSITIONS__ = true;

    // Page entry animation
    const entryClass = "dv-page-enter";
    document.addEventListener("DOMContentLoaded", () => {
        requestAnimationFrame(() => {
            document.body.classList.add(entryClass);
        });
    });

    // Smooth exit transitions on navigation clicks
    document.addEventListener("click", (e) => {
        const link = e.target.closest("a[href]");
        if (!link) return;
        const href = link.getAttribute("href");
        if (!href || href.startsWith("#") || href.startsWith("http") || href.startsWith("javascript")) return;
        if (link.getAttribute("target") === "_blank") return;
        if (link.hasAttribute("download")) return;

        e.preventDefault();
        document.body.classList.add("dv-page-exit");
        setTimeout(() => {
            window.location.href = href;
        }, 350);
    });

    // ESC key: go back to dashboard
    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape" && !document.querySelector(".dv-page-exit")) {
            const backBtn = document.querySelector('[data-back]');
            if (backBtn) {
                backBtn.click();
            }
        }
    });
})();