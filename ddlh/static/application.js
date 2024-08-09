const statAnimationTime = 1000.0;

class Carousel {
  constructor(element) {
    this.container = element;
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
    });
  }

  updatePosition() {
    this.container.querySelectorAll(".carousel-dummy").forEach((child) => {
      this.container.removeChild(child);
    });
    const childWidth = this.container.children[0].offsetWidth;
    const lastIndex = this.container.children.length - 1;
    var widthOffset = this.currentIndex;
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
  document.querySelectorAll(".carousel .documents").forEach((container) => {
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
    console.log(roomId);
    if (roomId) {
      const socket = io();

      socket.on("connect", () => {
        socket.emit("join_room", { room_id: roomId });
      });

      socket.on("msg", (data) => {
        const element = document.getElementById("theme-summary-container");
        element.innerHTML = data.msg;
      });
    }
  }
};

document.addEventListener("DOMContentLoaded", (event) => {
  setupCarousels();
  setupStats();
  setupSocket();
});
