const mediumBreakpoint = 900;

const setupCarousels = () => {
  const n = window.screen.width < mediumBreakpoint ? 1 : 1;
  document.querySelectorAll(".carousel .documents").forEach((container) => {
    Array.from(container.children).forEach((child, index) => {
      if (index < n) {
        child.style.display = "flex";
      } else {
        child.style.display = "none";
      }
    });
  });
};

document.addEventListener("DOMContentLoaded", (event) => {
  setupCarousels();
});

window.addEventListener("resize", (event) => {
  setupCarousels();
});
