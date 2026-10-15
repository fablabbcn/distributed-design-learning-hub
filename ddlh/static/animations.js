/* =============================================================================
 * animations.js
 * Smooth scroll (Lenis) + text & scroll animations (GSAP, ScrollTrigger,
 * SplitText).
 *
 * Contents
 *   1. Setup ............. plugins, Lenis smooth scroll
 *   2. Helpers ........... reusable animation building blocks
 *   3. Shared (all pages)  header, breadcrumbs, footer
 *   4. Pages
 *      4.1 Homepage ...... /                        (.hero)
 *      4.2 Theme / Query . /themes/<name>, /query   (.theme-hero)
 *      4.3 Format ........ /formats/<format>        (.format-hero)
 *      4.4 Tag ........... /tags/<tag>              (.tag-hero)
 *      4.5 Document ...... /documents/<id>          (.document-hero)
 *      4.6 About LLMs .... /about-our-use-of-llms   (.static-page-content)
 *   5. Shared sections ... resources list (theme, format and tag pages)
 *   6. Init .............. runs the animations for whatever is on the page
 *
 * Elements that are visible on load (header, heroes, breadcrumbs) are hidden
 * by the `.has-anim` inline style in layouts/main.j2 until this file reveals
 * them, to avoid a flash of unanimated content.
 * ========================================================================== */

(() => {
  const root = document.documentElement;

  /* ---------------------------------------------------------------------------
   * 1. Setup
   * ------------------------------------------------------------------------ */

  if (!window.gsap || !window.ScrollTrigger || !window.SplitText) {
    root.classList.remove("has-anim");
    return;
  }

  gsap.registerPlugin(ScrollTrigger, SplitText);

  // Lenis driven by GSAP's ticker so ScrollTrigger stays in sync
  if (window.Lenis) {
    const lenis = new Lenis({ anchors: true });
    lenis.on("scroll", ScrollTrigger.update);
    gsap.ticker.add((time) => lenis.raf(time * 1000));
    gsap.ticker.lagSmoothing(0);
    window.lenis = lenis;
  }

  const ease = "power3.out";

  /* ---------------------------------------------------------------------------
   * 2. Helpers
   * ------------------------------------------------------------------------ */

  const $ = (selector, scope = document) => scope.querySelector(selector);
  const $$ = (selector, scope = document) => [
    ...scope.querySelectorAll(selector),
  ];

  // ScrollTrigger config: play once when the element is 80% down the viewport
  const onEnter = (trigger) => ({ trigger, start: "top 80%", once: true });

  // Makes on-load elements visible again before animating them in
  const show = (targets) => gsap.set(targets, { autoAlpha: 1 });

  // Splits text into masked lines that slide up
  const revealLines = (el, vars = {}) =>
    SplitText.create(el, {
      type: "lines",
      mask: "lines",
      autoSplit: true,
      onSplit: (self) =>
        gsap.from(self.lines, {
          yPercent: 110,
          duration: 1,
          stagger: 0.08,
          ease,
          ...vars,
        }),
    });

  // Splits text into words that slide up inside masked lines (big titles)
  const revealWords = (el, vars = {}) =>
    SplitText.create(el, {
      type: "words,lines",
      mask: "lines",
      autoSplit: true,
      onSplit: (self) =>
        gsap.from(self.words, {
          yPercent: 110,
          duration: 1.1,
          stagger: 0.06,
          ease,
          ...vars,
        }),
    });

  // Simple fade + slide up, optionally staggered
  const fadeUp = (targets, vars = {}) => {
    if (!targets || (targets.length !== undefined && !targets.length)) return;
    return gsap.from(targets, {
      y: 30,
      autoAlpha: 0,
      duration: 0.9,
      stagger: 0.1,
      ease,
      ...vars,
    });
  };

  // Fades up long lists in batches as each item scrolls into view
  const batchFadeUp = (targets, vars = {}) => {
    if (!targets.length) return;
    gsap.set(targets, { y: 30, autoAlpha: 0 });
    ScrollTrigger.batch(targets, {
      start: "top 90%",
      once: true,
      onEnter: (batch) =>
        gsap.to(batch, {
          y: 0,
          autoAlpha: 1,
          duration: 0.8,
          stagger: 0.06,
          ease,
          overwrite: true,
          ...vars,
        }),
    });
  };

  // Hero shared by theme, format and tag pages: `.<name>-hero` with
  // `.<name>-hero-label` and `.<name>-hero-title` inside
  const animatePageHero = (name) => {
    const hero = $(`.${name}-hero`);
    if (!hero) return null;

    show($(`.${name}-hero-grid`, hero));

    const label = $(`.${name}-hero-label`, hero);
    const title = $(`.${name}-hero-title`, hero);

    if (label) fadeUp(label, { y: 20, duration: 0.8, delay: 0.1 });
    if (title) revealWords(title, { delay: 0.2 });

    return hero;
  };

  /* ---------------------------------------------------------------------------
   * 3. Shared (all pages)
   * ------------------------------------------------------------------------ */

  const animateHeader = () => {
    const header = $(".header-inner");
    if (!header) return;

    show(header);
    gsap.from([$(".header-logo", header), ...$$(".header-nav a", header)], {
      y: -20,
      autoAlpha: 0,
      duration: 0.8,
      stagger: 0.08,
      ease,
    });
  };

  const animateBreadcrumbs = () => {
    const breadcrumbs = $(".breadcrumbs-container");
    if (!breadcrumbs) return;

    show(breadcrumbs);
    fadeUp($$(".breadcrumbs li", breadcrumbs), {
      y: 0,
      x: -15,
      duration: 0.7,
      stagger: 0.08,
    });
  };

  const animateFooter = () => {
    const footer = $(".footer-inner");
    if (!footer) return;

    const heading = $(".footer-partners h3", footer);
    if (heading) revealLines(heading, { scrollTrigger: onEnter(footer) });

    fadeUp($$(".footer-partners-logos > *", footer), {
      duration: 0.7,
      stagger: 0.04,
      scrollTrigger: onEnter(footer),
    });

    const credits = $(".footer-credits", footer);
    if (credits) {
      fadeUp($$(".footer-credits-logos figure", credits), {
        stagger: 0.12,
        scrollTrigger: onEnter(credits),
      });
      const text = $(".footer-credits-text p", credits);
      if (text)
        revealLines(text, {
          stagger: 0.05,
          delay: 0.2,
          scrollTrigger: onEnter(credits),
        });
    }

    fadeUp($$(".footer-rights p", footer), {
      y: 15,
      duration: 0.7,
      scrollTrigger: onEnter($(".footer-rights", footer)),
    });
  };

  /* ---------------------------------------------------------------------------
   * 4. Pages
   * ------------------------------------------------------------------------ */

  /* 4.1 Homepage — hero, intro banner, numbered sections, carousel --------- */

  const animateHomepage = () => {
    // Hero: plays on load
    const hero = $(".hero");
    show($$(".hero-content, .hero-stats", hero));

    const h1 = $("h1", hero);
    if (h1) revealWords(h1);

    fadeUp($$(".hero-content h2, .hero-content p", hero), {
      stagger: 0.15,
      delay: 0.4,
    });

    fadeUp($$(".hero-stat", hero), {
      y: 40,
      stagger: 0.12,
      delay: 0.7,
    });

    // Count up the stat numbers
    $$(".hero-stat-value", hero).forEach((el) => {
      const target = parseInt(el.textContent, 10);
      if (Number.isNaN(target)) return;
      const counter = { value: 0 };
      gsap.to(counter, {
        value: target,
        duration: 1.8,
        delay: 0.7,
        ease: "power2.out",
        onUpdate: () => (el.textContent = Math.round(counter.value)),
      });
    });

    // Intro banner: line-by-line reveal
    const intro = $(".intro-banner-title");
    if (intro)
      revealLines(intro, { scrollTrigger: onEnter(intro), stagger: 0.12 });

    // Numbered section titles (01, 02, 03)
    $$(
      ".thematic-areas-title, .interest-search-title, .format-browser-title",
    ).forEach((title) => {
      const number = $("[class$='-number']", title);
      const heading = $("h2", title);
      if (number)
        fadeUp(number, {
          y: 20,
          duration: 0.8,
          scrollTrigger: onEnter(title),
        });
      if (heading)
        revealLines(heading, { scrollTrigger: onEnter(title), delay: 0.1 });
    });

    // Thematic areas list
    fadeUp($$(".thematic-areas-item"), {
      duration: 0.7,
      stagger: 0.05,
      scrollTrigger: onEnter(".thematic-areas-list"),
    });

    // Interest search
    const interest = $(".interest-search-content");
    if (interest)
      fadeUp(interest.children, {
        y: 40,
        stagger: 0.15,
        scrollTrigger: onEnter(interest),
      });

    // Format grid
    fadeUp($$(".format-browser-item"), {
      y: 60,
      stagger: 0.12,
      scrollTrigger: onEnter(".format-browser-grid"),
    });

    // Featured carousel
    const featured = $(".featured-carousel");
    if (featured) {
      const heading = $(".featured-carousel-heading", featured);
      if (heading) revealLines(heading, { scrollTrigger: onEnter(featured) });

      fadeUp(
        $$(
          ".featured-carousel-subheading, .featured-carousel-controls",
          featured,
        ),
        {
          y: 20,
          duration: 0.8,
          delay: 0.2,
          scrollTrigger: onEnter(featured),
        },
      );

      const swiper = $(".featured-carousel-swiper", featured);
      if (swiper)
        fadeUp(swiper, { y: 60, duration: 1, scrollTrigger: onEnter(swiper) });
    }
  };

  /* 4.2 Theme / Query — hero title, tags, description or live AI summary --- */

  const animateThemePage = () => {
    const hero = animatePageHero("theme");

    fadeUp($$(".theme-hero-tag", hero), {
      y: 15,
      duration: 0.6,
      stagger: 0.04,
      delay: 0.5,
    });

    const aiSummary = $(".theme-ai-summary", hero);
    if (aiSummary) {
      // Query page: the summary arrives later over Socket.IO
      // (see querySummary.js), so fade in its paragraphs when they land
      fadeUp(aiSummary.children, { stagger: 0.12, delay: 0.6 });
      new MutationObserver(() =>
        fadeUp(aiSummary.children, { y: 20, stagger: 0.15 }),
      ).observe(aiSummary, { childList: true });
      return;
    }

    // Theme page: editorial description, line by line
    $$(".theme-hero-description > *", hero).forEach((paragraph, i) =>
      revealLines(paragraph, { stagger: 0.05, delay: 0.6 + i * 0.15 }),
    );
  };

  /* 4.3 Format — hero title ------------------------------------------------ */

  const animateFormatPage = () => {
    animatePageHero("format");
  };

  /* 4.4 Tag — hero title --------------------------------------------------- */

  const animateTagPage = () => {
    animatePageHero("tag");
  };

  /* 4.5 Document — hero, summary, related resources ---------------------- */

  const animateDocumentPage = () => {
    const hero = animatePageHero("document");

    fadeUp($$(".document-hero-author, .document-hero-tag", hero), {
      y: 15,
      duration: 0.6,
      stagger: 0.04,
      delay: 0.5,
    });

    const image = $(".document-hero-image", hero);
    if (image) fadeUp(image, { y: 40, duration: 1, delay: 0.3 });

    const summary = $(".document-summary");
    if (summary) {
      fadeUp(
        $$(
          ".document-summary-themes > *, .document-summary-themes li",
          summary,
        ),
        {
          y: 20,
          duration: 0.7,
          stagger: 0.05,
          scrollTrigger: onEnter(summary),
        },
      );
      $$(".document-summary-description > *", summary).forEach((paragraph, i) =>
        revealLines(paragraph, {
          stagger: 0.04,
          delay: i * 0.1,
          scrollTrigger: onEnter(paragraph),
        }),
      );
      fadeUp($$(".document-summary-action", summary), {
        y: 15,
        scrollTrigger: onEnter($(".document-summary-actions", summary)),
      });
    }

    const related = $(".document-related");
    if (related) {
      fadeUp($(".document-related-label", related), {
        y: 20,
        scrollTrigger: onEnter(related),
      });
      batchFadeUp($$(".theme-resources-item", related));
    }
  };

  /* 4.6 About LLMs — title, then headings and paragraphs on scroll -------- */

  const animateStaticPage = () => {
    const content = $(".static-page-content");
    const title = $(".theme-tag-document-header h1");
    if (title) revealWords(title);

    $$("h2", content).forEach((heading) =>
      revealLines(heading, { scrollTrigger: onEnter(heading) }),
    );
    batchFadeUp($$("p, li", content));
  };

  /* ---------------------------------------------------------------------------
   * 5. Shared sections
   * ------------------------------------------------------------------------ */

  // Resources list + type filters (theme, format and tag pages)
  const animateResources = () => {
    const section = $(".theme-resources");
    if (!section) return;

    const filters = $(".theme-resources-filters", section);
    if (filters)
      fadeUp($$(".theme-resources-filters-header, li", filters), {
        y: 20,
        duration: 0.7,
        stagger: 0.05,
        scrollTrigger: onEnter(filters),
      });

    batchFadeUp($$(".theme-resources-item", section));

    // Filtering and opening resources changes the page height, so keep the
    // scroll triggers below the list in the right place
    const list = $(".theme-resources-list", section);
    if (list && window.ResizeObserver) {
      let frame;
      new ResizeObserver(() => {
        cancelAnimationFrame(frame);
        frame = requestAnimationFrame(() => ScrollTrigger.refresh());
      }).observe(list);
    }
  };

  /* ---------------------------------------------------------------------------
   * 6. Init
   * ------------------------------------------------------------------------ */

  // Each page is detected by an element only it renders
  const pages = [
    { selector: ".hero", animate: animateHomepage },
    { selector: ".theme-hero", animate: animateThemePage },
    { selector: ".format-hero", animate: animateFormatPage },
    { selector: ".tag-hero", animate: animateTagPage },
    { selector: ".document-hero", animate: animateDocumentPage },
    { selector: ".static-page-content", animate: animateStaticPage },
  ];

  const mm = gsap.matchMedia();

  mm.add("(prefers-reduced-motion: no-preference)", () => {
    animateHeader();
    animateBreadcrumbs();

    pages
      .filter(({ selector }) => $(selector))
      .forEach(({ animate }) => animate());

    animateResources();
    animateFooter();
  });

  // Reduced motion: just make sure nothing stays hidden
  mm.add("(prefers-reduced-motion: reduce)", () => {
    root.classList.remove("has-anim");
  });
})();
