/* =============================================================================
 * animations.js
 * Smooth scroll (Lenis) + scroll animations (GSAP, ScrollTrigger).
 * Text blocks fade up as a whole; nothing is split into lines or words.
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
 *      4.7 About ......... /about                   (.about-hero)
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

  if (!window.gsap || !window.ScrollTrigger) {
    root.classList.remove("has-anim");
    return;
  }

  gsap.registerPlugin(ScrollTrigger);

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
    if (title) fadeUp(title, { delay: 0.2 });

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

    // One trigger for the whole footer: it sits at the very end of the page,
    // so triggers on its lower parts may never reach their start position
    const groups = [
      [$$(".footer-partners h3", footer), { duration: 0.8 }],
      [$$(".footer-partners-logos > *", footer), { duration: 0.7, stagger: 0.03 }, "-=0.6"],
      [$$(".footer-credits-logos figure", footer), { autoAlpha: 0.6, stagger: 0.12 }, "-=0.5"],
      [$$(".footer-credits-text p", footer), { autoAlpha: 0.6 }, "-=0.7"],
      [$$(".footer-rights p", footer), { duration: 0.7 }, "-=0.6"],
    ].filter(([targets]) => targets.length);
    if (!groups.length) return;

    gsap.set(groups.flatMap(([targets]) => targets), { y: 30, autoAlpha: 0 });

    const tl = gsap.timeline({
      paused: true,
      defaults: { y: 0, autoAlpha: 1, duration: 0.9, ease },
    });
    groups.forEach(([targets, vars, position]) => tl.to(targets, vars, position));

    ScrollTrigger.create({
      trigger: footer,
      start: "top bottom-=80",
      once: true,
      onEnter: () => tl.play(),
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

    fadeUp($("h1", hero));

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

    // Intro banner
    const intro = $(".intro-banner-title");
    if (intro) fadeUp(intro, { scrollTrigger: onEnter(intro) });

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
        fadeUp(heading, { scrollTrigger: onEnter(title), delay: 0.1 });
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
      fadeUp($(".featured-carousel-heading", featured), {
        scrollTrigger: onEnter(featured),
      });

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

    // Theme page: editorial description as a whole
    fadeUp($(".theme-hero-description", hero), { delay: 0.6 });
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
      const description = $(".document-summary-description", summary);
      if (description)
        fadeUp(description, { scrollTrigger: onEnter(description) });
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
    animatePageHero("static");

    batchFadeUp($$("h2, p, li", content));
  };

  /* 4.7 About — hero, then each section on scroll-------------------------------- */

  const animateAboutPage = () => {
    const hero = animatePageHero("about");

    const image = $(".about-hero-image", hero);
    if (image) {
      show(image);
      fadeUp(image, { y: 40, duration: 1, delay: 0.3 });
    }

    // What is the Learning Hub?
    const whatIs = $(".about-what-is");
    if (whatIs) {
      const intro = $(".about-what-is-intro", whatIs);
      fadeUp($$(".about-what-is-title, .about-what-is-lead", intro), {
        stagger: 0.15,
        scrollTrigger: onEnter(intro),
      });
      fadeUp($(".about-what-is-text", intro), {
        delay: 0.2,
        scrollTrigger: onEnter(intro),
      });
      fadeUp($$(".about-what-is-profile", intro), {
        y: 15,
        duration: 0.6,
        stagger: 0.05,
        delay: 0.4,
        scrollTrigger: onEnter(intro),
      });

      const journeys = $(".about-what-is-journeys", whatIs);
      fadeUp($(".about-what-is-journeys-title", journeys), {
        scrollTrigger: onEnter(journeys),
      });
      fadeUp($$(".about-what-is-journeys-list li", journeys), {
        y: 20,
        duration: 0.7,
        stagger: 0.08,
        delay: 0.1,
        scrollTrigger: onEnter(journeys),
      });
    }

    // Evolving space banner
    const evolving = $(".about-evolving");
    if (evolving) {
      fadeUp($(".about-evolving-label", evolving), {
        y: 20,
        duration: 0.8,
        scrollTrigger: onEnter(evolving),
      });
      fadeUp($(".about-evolving-title", evolving), {
        delay: 0.1,
        scrollTrigger: onEnter(evolving),
      });
      const text = $(".about-evolving-text", evolving);
      fadeUp(text, { scrollTrigger: onEnter(text) });
    }

    // Learning methodology
    const methodology = $(".about-methodology");
    if (methodology) {
      const intro = $(".about-methodology-intro", methodology);
      fadeUp($$(".about-methodology-title, .about-methodology-lead", intro), {
        stagger: 0.15,
        scrollTrigger: onEnter(intro),
      });
      fadeUp($$(".about-methodology-aside p", intro), {
        stagger: 0.15,
        delay: 0.2,
        scrollTrigger: onEnter(intro),
      });

      const steps = $(".about-methodology-steps", methodology);
      fadeUp($$(".about-methodology-step > *", steps), {
        y: 20,
        duration: 0.7,
        stagger: 0.08,
        scrollTrigger: onEnter(steps),
      });

      const statement = $(".about-methodology-statement", methodology);
      fadeUp(statement, { scrollTrigger: onEnter(statement) });
    }

    // Adopt / Adapt / Apply
    const approach = $(".about-approach");
    if (approach) {
      const intro = $(".about-approach-intro", approach);
      fadeUp(intro.children, {
        stagger: 0.15,
        scrollTrigger: onEnter(intro),
      });

      const stages = $(".about-approach-stages", approach);
      fadeUp($$(".about-approach-stage", stages), {
        y: 60,
        stagger: 0.12,
        scrollTrigger: onEnter(stages),
      });
    }

    // Journey: the line draws itself as the page scrolls; each dot and
    // label appears when the line reaches it. There are two graphs, a
    // horizontal one (desktop, tablet) and a vertical one (mobile); CSS shows
    // one of them and matchMedia animates that one. Breakpoint matches the CSS.
    const journey = $(".about-journey");
    if (journey) {
      fadeUp($(".about-journey-title", journey), {
        scrollTrigger: onEnter(journey),
      });

      const graph = $(".about-journey-graph", journey);

      // `end`: where the graph's bottom edge is on screen when the line
      // finishes drawing
      const animateJourneyGraph = (svg, end) => {
        const line = svg && $(".about-journey-line", svg);
        if (!line) return;
        const length = line.getTotalLength();

        // Where each dot sits along the line, from 0 to 1
        const samples = 400;
        const progressAt = (x, y) => {
          let best = 0;
          let bestDistance = Infinity;
          for (let i = 0; i <= samples; i++) {
            const point = line.getPointAtLength((i / samples) * length);
            const distance = Math.hypot(point.x - x, point.y - y);
            if (distance < bestDistance) {
              bestDistance = distance;
              best = i / samples;
            }
          }
          return best;
        };

        // Labels are inside the SVG on desktop, HTML next to it on mobile
        const labels = svg.closest(".about-journey-mobile") || svg;
        const steps = $$(".about-journey-dot", svg).map((dot) => ({
          dot,
          label: $(`.about-journey-label[data-step="${dot.dataset.step}"]`, labels),
          at: progressAt(+dot.dataset.x, +dot.dataset.y),
        }));

        gsap.set(line, { strokeDasharray: length, strokeDashoffset: length });
        gsap.set(
          steps.map(({ dot }) => dot),
          { autoAlpha: 0, scale: 0, transformOrigin: "50% 50%" },
        );
        gsap.set(
          steps.map(({ label }) => label).filter(Boolean),
          { autoAlpha: 0, y: 16 },
        );

        const tl = gsap.timeline({
          defaults: { ease: "none" },
          scrollTrigger: {
            // Starts as the graph enters the bottom of the screen
            trigger: svg,
            start: "top 85%",
            end,
            scrub: 1,
            invalidateOnRefresh: true,
          },
        });

        tl.to(line, { strokeDashoffset: 0, duration: 1 }, 0);

        // Pan sideways when the graph is wider than the screen (tablet)
        tl.to(
          svg,
          {
            x: () =>
              Math.min(0, graph.clientWidth - svg.getBoundingClientRect().width),
            duration: 1,
          },
          0,
        );

        steps.forEach(({ dot, label, at }) => {
          tl.to(
            dot,
            { autoAlpha: 1, scale: 1, duration: 0.03, ease: "back.out(3)" },
            Math.max(0, at - 0.015),
          );
          if (label)
            tl.to(
              label,
              { autoAlpha: 1, y: 0, duration: 0.06, ease: "power2.out" },
              at,
            );
        });
      };

      gsap.matchMedia().add(
        { mobile: "(max-width: 767px)", desktop: "(min-width: 768px)" },
        ({ conditions }) =>
          conditions.mobile
            ? // Tall graph: done just above the middle of the screen
              animateJourneyGraph(
                $(".about-journey-svg-mobile", graph),
                "bottom 45%",
              )
            : // Done as soon as the whole graph is on screen
              animateJourneyGraph(
                $(".about-journey-svg-desktop", graph),
                "bottom 75%",
              ),
      );
    }

    // How does it work?
    const how = $(".about-how");
    if (how) {
      fadeUp($(".about-how-title", how), { scrollTrigger: onEnter(how) });

      const columns = $(".about-how-columns", how);
      fadeUp($$(".about-how-column", columns), {
        y: 40,
        stagger: 0.15,
        scrollTrigger: onEnter(columns),
      });
    }
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
    { selector: ".about-hero", animate: animateAboutPage },
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
