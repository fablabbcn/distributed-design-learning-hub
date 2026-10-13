// Smooth scroll (Lenis) + scroll animations (GSAP, ScrollTrigger, SplitText)

(() => {
  const root = document.documentElement;

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
  const mm = gsap.matchMedia();

  mm.add("(prefers-reduced-motion: no-preference)", () => {
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

    const onEnter = (trigger) => ({ trigger, start: "top 80%", once: true });

    // Hero: plays on load
    const hero = document.querySelector(".hero");
    if (hero) {
      gsap.set(hero.querySelectorAll(".hero-content, .hero-stats"), {
        autoAlpha: 1,
      });

      const h1 = hero.querySelector("h1");
      if (h1) {
        SplitText.create(h1, {
          type: "words,lines",
          mask: "lines",
          autoSplit: true,
          onSplit: (self) =>
            gsap.from(self.words, {
              yPercent: 110,
              duration: 1.1,
              stagger: 0.06,
              ease,
            }),
        });
      }

      gsap.from(hero.querySelectorAll(".hero-content h2, .hero-content p"), {
        y: 30,
        autoAlpha: 0,
        duration: 1,
        stagger: 0.15,
        delay: 0.4,
        ease,
      });

      const stats = hero.querySelectorAll(".hero-stat");
      gsap.from(stats, {
        y: 40,
        autoAlpha: 0,
        duration: 0.9,
        stagger: 0.12,
        delay: 0.7,
        ease,
      });

      // Count up the stat numbers
      hero.querySelectorAll(".hero-stat-value").forEach((el) => {
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
    }

    // Intro banner: line-by-line reveal
    const intro = document.querySelector(".intro-banner-title");
    if (intro)
      revealLines(intro, { scrollTrigger: onEnter(intro), stagger: 0.12 });

    // Numbered section titles (01, 02, 03)
    document
      .querySelectorAll(
        ".thematic-areas-title, .interest-search-title, .format-browser-title",
      )
      .forEach((title) => {
        const number = title.querySelector("[class$='-number']");
        const heading = title.querySelector("h2");
        if (number) {
          gsap.from(number, {
            y: 20,
            autoAlpha: 0,
            duration: 0.8,
            ease,
            scrollTrigger: onEnter(title),
          });
        }
        if (heading)
          revealLines(heading, { scrollTrigger: onEnter(title), delay: 0.1 });
      });

    // Thematic areas list
    const themes = document.querySelectorAll(".thematic-areas-item");
    if (themes.length) {
      gsap.from(themes, {
        y: 30,
        autoAlpha: 0,
        duration: 0.7,
        stagger: 0.05,
        ease,
        scrollTrigger: onEnter(".thematic-areas-list"),
      });
    }

    // Interest search
    const interest = document.querySelector(".interest-search-content");
    if (interest) {
      gsap.from(interest.children, {
        y: 40,
        autoAlpha: 0,
        duration: 0.9,
        stagger: 0.15,
        ease,
        scrollTrigger: onEnter(interest),
      });
    }

    // Format grid
    const formats = document.querySelectorAll(".format-browser-item");
    if (formats.length) {
      gsap.from(formats, {
        y: 60,
        autoAlpha: 0,
        duration: 0.9,
        stagger: 0.12,
        ease,
        scrollTrigger: onEnter(".format-browser-grid"),
      });
    }

    // Featured carousel
    const featured = document.querySelector(".featured-carousel");
    if (featured) {
      const heading = featured.querySelector(".featured-carousel-heading");
      if (heading) revealLines(heading, { scrollTrigger: onEnter(featured) });

      gsap.from(
        featured.querySelectorAll(
          ".featured-carousel-subheading, .featured-carousel-controls",
        ),
        {
          y: 20,
          autoAlpha: 0,
          duration: 0.8,
          stagger: 0.1,
          delay: 0.2,
          ease,
          scrollTrigger: onEnter(featured),
        },
      );

      const swiper = featured.querySelector(".featured-carousel-swiper");
      if (swiper) {
        gsap.from(swiper, {
          y: 60,
          autoAlpha: 0,
          duration: 1,
          ease,
          scrollTrigger: onEnter(swiper),
        });
      }
    }
  });

  // Reduced motion: just make sure nothing stays hidden
  mm.add("(prefers-reduced-motion: reduce)", () => {
    root.classList.remove("has-anim");
  });
})();
