const statAnimationTime = 1000.0;

class Carousel {
  constructor(element) {
    this.container = element.querySelector(".documents");
    this.outer = element;
    this.currentIndex = 0;
    this.setupListeners();
    this.updatePosition();
    window.addEventListener("resize", (event) => {
      this.updatePosition();
    });
  }

  setupListeners() {
    Array.from(this.container.children).forEach((child, index) => {
      child.addEventListener("click", (event) => {
        this.currentIndex = index;
        this.updatePosition();
      });
      var xDown = null;
      var yDown = null;
    });
    this.container.addEventListener("swiped-left", (event) => {
      this.currentIndex = this.currentIndex + 1;
      this.updatePosition();
    });
    this.container.addEventListener("swiped-right", (event) => {
      this.currentIndex = this.currentIndex - 1;
      this.updatePosition();
    });
    var xDelta = 0;
    var scrollLeftBefore = this.container.scrollLeft;
    this.container.addEventListener("touchstart", (event) => {
      scrollLeftBefore = this.container.scrollLeft;
      xDelta = event.touches[0].clientX;
    });
    this.container.addEventListener("touchmove", (event) => {
      xDelta = event.touches[0].clientX;
      this.container.scrollLeft = scrollLeftBefore - xDelta;
    });
    this.container.addEventListener("touchend", (event) => {
      this.container.scrollLeft = scrollLeftBefore;
      xDelta = 0;
      this.updatePosition();
    });
    this.container.addEventListener("touchcancel", (event) => {
      this.container.scrollLeft = scrollLeftBefore;
      xDelta = 0;
      this.updatePosition();
    });
    this.outer
      .querySelector(".carousel-shadow.left")
      .addEventListener("click", (event) => {
        event.preventDefault();
        this.currentIndex = this.currentIndex - 1;
        this.updatePosition();
      });
    this.outer
      .querySelector(".carousel-shadow.right")
      .addEventListener("click", (event) => {
        event.preventDefault();
        this.currentIndex = this.currentIndex + 1;
        this.updatePosition();
      });
  }

  updatePosition() {
    this.container.querySelectorAll(".carousel-dummy").forEach((child) => {
      this.container.removeChild(child);
    });
    this.container
      .querySelectorAll(".carousel-item.active")
      .forEach((child) => {
        child.classList.remove("active");
      });

    const childWidth = this.container.children[0].offsetWidth;
    const lastIndex = this.container.children.length - 1;
    if (this.currentIndex < 0) {
      this.currentIndex = lastIndex;
    }
    if (this.currentIndex > lastIndex) {
      this.currentIndex = 0;
    }
    var widthOffset = this.currentIndex;
    this.container.children[this.currentIndex].classList.add("active");
    if (this.currentIndex == 0) {
      const dummyLast = this.container.children[lastIndex].cloneNode(true);
      dummyLast.classList.add("carousel-dummy");
      dummyLast.addEventListener("click", (event) => {
        this.currentIndex = lastIndex;
        this.updatePosition();
      });
      this.container.prepend(dummyLast);
      widthOffset += 1;
    } else if (this.currentIndex == lastIndex) {
      const dummyFirst = this.container.children[0].cloneNode(true);
      dummyFirst.classList.add("carousel-dummy");
      dummyFirst.addEventListener("click", (event) => {
        this.currentIndex = 0;
        this.updatePosition();
      });
      this.container.append(dummyFirst);
    }
    const marginLeft = (window.innerWidth - childWidth) / 2.0;
    this.container.scrollLeft = childWidth * widthOffset - marginLeft;
  }
}

function animateStat(element) {
  const finalValue = parseInt(element.innerText);
  element.innerHTML = 0;
  const interval = window.setInterval((event) => {
    const currentValue = parseInt(element.innerText);
    if (currentValue < finalValue) {
      element.innerHTML = currentValue + 1;
    } else {
      window.clearInterval(interval);
    }
  }, statAnimationTime / finalValue);
}

const setupCarousels = () => {
  document.querySelectorAll(".carousel").forEach((container) => {
    new Carousel(container);
  });
};

const setupStats = () => {
  document.querySelectorAll(".stat .n").forEach((element) => {
    animateStat(element);
  });
};

const setupSocket = () => {
  const element = document.getElementById("theme-summary-container");
  if (element) {
    const roomId = element.dataset["queryTaskId"];
    if (roomId) {
      const socket = io();

      socket.on("connect", () => {
        socket.emit("join_room", { room_id: roomId });
      });

      socket.on("msg", (data) => {
        const element = document.getElementById("theme-summary-container");
        element.innerHTML = data.msg;
        setupDocumentLinkHighlight();
      });
    }
  }
};

const setupTyping = () => {
  if (document.querySelector(".type-it")) {
    new TypeIt(".type-it", { loop: true }).go();
  }
};

const setupDocumentLinkHighlight = () => {
  const container = document.getElementById("theme-summary-container");
  const urlRegex = /^(https:\/\/learn\.distributeddesign\.eu)?\/documents\//;
  if (container) {
    const links = container.querySelectorAll("a");
    links.forEach((link) => {
      const href = link.getAttribute("href");
      if (href && href.match(urlRegex)) {
        const doc_id = href.replace(urlRegex, "");
        link.addEventListener("mouseover", () => {
          const elems = document.querySelectorAll(`.document-${doc_id}`);
          elems.forEach((elem) => {
            elem.classList.add("focused");
          });
        });
        link.addEventListener("mouseout", () => {
          const elems = document.querySelectorAll(`.document-${doc_id}`);
          elems.forEach((elem) => {
            elem.classList.remove("focused");
          });
        });
      }
    });
  }
};

const setupFormClickHandler = () => {
  const form = document.querySelector(".query-form");
  if (form) {
    form.addEventListener("click", () => {
      form.querySelector('input[name="query"]').focus();
    });
  }
};

const setupSearchHint = () => {
  const hint = document.querySelector(".search-hint");
  if (hint) {
    hint.addEventListener("click", () => {
      input = document.querySelector(".query-form input[type='text']");
      if (input) {
        input.focus();
      }
    });
  }
};

const setupCookieBanner = () => {
  if (localStorage.getItem("cookie_consent") === null) {
    const banner = document.querySelector(".cookie-banner");
    banner.style.display = "flex";
    accept = banner.querySelector(".accept");
    accept.addEventListener("click", (event) => {
      event.preventDefault();
      localStorage.setItem("cookie_consent", "granted");
      gtag("consent", "update", {
        ad_user_data: "granted",
        ad_personalization: "granted",
        ad_storage: "granted",
        analytics_storage: "granted",
      });
      banner.style.display = "none";
    });
    reject = banner.querySelector(".reject");
    reject.addEventListener("click", (event) => {
      event.preventDefault();
      localStorage.setItem("cookie_consent", "refused");
      banner.style.display = "none";
    });
  }
};

document.addEventListener("DOMContentLoaded", (event) => {
  setupCarousels();
  setupStats();
  setupSocket();
  setupTyping();
  setupDocumentLinkHighlight();
  setupFormClickHandler();
  setupSearchHint();
  setupCookieBanner();
});
