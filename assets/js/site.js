/* 全站脚本：主题三态切换、移动端菜单、BibTeX 复制。
   刻意保持无依赖、无动画——切换是瞬间完成的。
   注意：防闪烁的那段脚本内联在 <head>，不在这里。 */

(function () {
  "use strict";

  /* --- 主题：system → light → dark → system --------------------------- */

  var KEY = "pw-theme";
  var ORDER = ["system", "light", "dark"];
  var btn = document.querySelector(".theme-toggle");

  function apply(state) {
    if (state === "system") {
      document.documentElement.removeAttribute("data-theme");
    } else {
      document.documentElement.setAttribute("data-theme", state);
    }
    if (btn) {
      btn.setAttribute("data-state", state);
      btn.setAttribute(
        "aria-label",
        { system: "Theme: follow system", light: "Theme: light", dark: "Theme: dark" }[state]
      );
    }
  }

  var current = localStorage.getItem(KEY);
  if (ORDER.indexOf(current) === -1) current = "system";
  apply(current);

  if (btn) {
    btn.addEventListener("click", function () {
      current = ORDER[(ORDER.indexOf(current) + 1) % ORDER.length];
      if (current === "system") localStorage.removeItem(KEY);
      else localStorage.setItem(KEY, current);
      apply(current);
    });
  }

  /* --- 移动端菜单 ------------------------------------------------------ */

  var menuBtn = document.querySelector(".nav__menu");
  var links = document.querySelector(".nav__links");

  function setMenu(open) {
    if (!links || !menuBtn) return;
    links.hidden = !open;
    menuBtn.setAttribute("aria-expanded", String(open));
  }

  function isNarrow() {
    return window.matchMedia("(max-width: 40rem)").matches;
  }

  if (menuBtn && links) {
    if (isNarrow()) setMenu(false);
    menuBtn.addEventListener("click", function () {
      setMenu(links.hidden);
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && isNarrow()) setMenu(false);
    });
    window.addEventListener("resize", function () {
      if (!isNarrow()) links.hidden = false;
      else if (menuBtn.getAttribute("aria-expanded") !== "true") links.hidden = true;
    });
  }

  /* --- 复制 BibTeX ----------------------------------------------------- */

  document.addEventListener("click", function (e) {
    var b = e.target.closest(".copy-bib");
    if (!b) return;
    var pre = b.parentElement.querySelector("pre");
    if (!pre) return;
    var done = function () {
      var was = b.textContent;
      b.textContent = "copied";
      setTimeout(function () { b.textContent = was; }, 1400);
    };
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(pre.textContent).then(done, function () {});
    } else {
      var r = document.createRange();
      r.selectNodeContents(pre);
      var s = window.getSelection();
      s.removeAllRanges();
      s.addRange(r);
      try { document.execCommand("copy"); done(); } catch (err) {}
      s.removeAllRanges();
    }
  });
})();
