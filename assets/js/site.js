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

/* --- 入场动效 ---------------------------------------------------------
   淡入 + 轻微上移，逐个错开。只处理带 .reveal 的块。
   用户开了「减少动效」就直接显示，不做任何过渡。 */

(function () {
  "use strict";

  var items = document.querySelectorAll(".reveal");
  if (!items.length) return;

  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (reduce || !("IntersectionObserver" in window)) {
    for (var i = 0; i < items.length; i++) items[i].classList.add("is-in");
    return;
  }

  var io = new IntersectionObserver(function (entries) {
    var shown = 0;
    entries.forEach(function (en) {
      if (!en.isIntersecting) return;
      // 同一屏里出现多个时错开一点，避免整片一起跳出来
      en.target.style.transitionDelay = (shown++ * 70) + "ms";
      en.target.classList.add("is-in");
      io.unobserve(en.target);
    });
  }, { rootMargin: "0px 0px -8% 0px", threshold: 0.05 });

  for (var j = 0; j < items.length; j++) io.observe(items[j]);

  // 兜底：IntersectionObserver 在页面处于后台标签、被隐藏容器包裹、
  // 或某些嵌入式浏览器里可能一直不触发。真出现那种情况时内容会永久不可见，
  // 这个代价太大，所以无条件在 1.5 秒后全部显示。
  setTimeout(function () {
    for (var k = 0; k < items.length; k++) {
      items[k].style.transitionDelay = "0ms";
      items[k].classList.add("is-in");
    }
  }, 1500);
})();
