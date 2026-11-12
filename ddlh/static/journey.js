// About page, "The Learning Hub journey": clicking a step's title opens its
// card and closes the others; clicking the open one closes it. The desktop
// and mobile graphs have their own copy of each step and are kept in sync,
// so the same step stays open when the layout changes.
(() => {
  const journey = document.querySelector(".about-journey");
  if (!journey) return;

  const steps = [...journey.querySelectorAll(".about-journey-step")];

  const open = (number) => {
    steps.forEach((step) => {
      const isOpen = step.dataset.step === number;
      step.classList.toggle("is-open", isOpen);
      step
        .querySelector(".about-journey-step-toggle")
        .setAttribute("aria-expanded", String(isOpen));
    });
  };

  journey.addEventListener("click", (event) => {
    const toggle = event.target.closest(".about-journey-step-toggle");
    if (!toggle) return;
    const step = toggle.closest(".about-journey-step");
    open(step.classList.contains("is-open") ? null : step.dataset.step);
  });
})();
