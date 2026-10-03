// Content script — detects dashboard job pages only (localhost).
(() => {
  const match = location.pathname.match(/\/jobs\/([0-9a-f-]{36})/i);
  if (!match) return;
  const badge = document.createElement("div");
  badge.textContent = "Java Career AI · Open match tools in the page";
  badge.style.cssText =
    "position:fixed;bottom:16px;right:16px;z-index:99999;background:#0f172a;color:#2dd4bf;padding:10px 14px;border-radius:12px;font:12px/1.4 Segoe UI,sans-serif;border:1px solid #334155;";
  document.documentElement.appendChild(badge);
  setTimeout(() => badge.remove(), 4000);
})();
