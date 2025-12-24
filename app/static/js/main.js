/**
 * WorldInsights - Main JavaScript
 * Handles navigation, mobile menu, and interactions
 */

// Mobile Menu Toggle
document.addEventListener("DOMContentLoaded", function () {
  const mobileToggle = document.querySelector(".mobile-menu-toggle");
  const navLinks = document.querySelector(".nav-links");
  const body = document.body;

  if (mobileToggle) {
    mobileToggle.addEventListener("click", function () {
      navLinks.classList.toggle("active");
      body.classList.toggle("menu-open");

      // Animate hamburger icon
      const spans = mobileToggle.querySelectorAll("span");
      if (navLinks.classList.contains("active")) {
        spans[0].style.transform = "rotate(45deg) translateY(8px)";
        spans[1].style.opacity = "0";
        spans[2].style.transform = "rotate(-45deg) translateY(-8px)";
      } else {
        spans[0].style.transform = "";
        spans[1].style.opacity = "";
        spans[2].style.transform = "";
      }
    });

    // Close menu when clicking a link (but not the user dropdown toggle)
    navLinks.querySelectorAll(".nav-link").forEach((link) => {
      link.addEventListener("click", function (e) {
        // Don't close menu if clicking the user dropdown toggle
        if (!this.classList.contains("user-dropdown-toggle")) {
          navLinks.classList.remove("active");
          body.classList.remove("menu-open");
          const spans = mobileToggle.querySelectorAll("span");
          spans[0].style.transform = "";
          spans[1].style.opacity = "";
          spans[2].style.transform = "";
        }
      });
    });

    // Close mobile menu when clicking dropdown items (Profile/Logout)
    navLinks.querySelectorAll(".dropdown-item").forEach((item) => {
      item.addEventListener("click", function () {
        navLinks.classList.remove("active");
        body.classList.remove("menu-open");
        const spans = mobileToggle.querySelectorAll("span");
        spans[0].style.transform = "";
        spans[1].style.opacity = "";
        spans[2].style.transform = "";
      });
    });
  }

  // Navbar scroll effect
  const navbar = document.querySelector(".navbar");
  let lastScroll = 0;

  window.addEventListener("scroll", function () {
    const currentScroll = window.pageYOffset;

    if (currentScroll > 100) {
      navbar.style.background = "rgba(15, 23, 42, 0.95)";
      navbar.style.boxShadow = "0 4px 6px -1px rgba(0, 0, 0, 0.3)";
    } else {
      navbar.style.background = "rgba(15, 23, 42, 0.8)";
      navbar.style.boxShadow = "";
    }

    lastScroll = currentScroll;
  });

  // Smooth scroll for anchor links
  document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
    anchor.addEventListener("click", function (e) {
      e.preventDefault();
      const target = document.querySelector(this.getAttribute("href"));
      if (target) {
        target.scrollIntoView({
          behavior: "smooth",
          block: "start",
        });
      }
    });
  });

  // Add animation on scroll
  const observerOptions = {
    threshold: 0.1,
    rootMargin: "0px 0px -50px 0px",
  };

  const observer = new IntersectionObserver(function (entries) {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.style.opacity = "1";
        entry.target.style.transform = "translateY(0)";
      }
    });
  }, observerOptions);

  // Observe elements for animation
  document
    .querySelectorAll(".feature-card, .source-card, .use-case")
    .forEach((el) => {
      el.style.opacity = "0";
      el.style.transform = "translateY(20px)";
      el.style.transition = "opacity 0.6s ease, transform 0.6s ease";
      observer.observe(el);
    });

  // User Dropdown Menu
  const userDropdownBtn = document.getElementById("userDropdownBtn");
  const userDropdownMenu = document.getElementById("userDropdownMenu");

  if (userDropdownBtn && userDropdownMenu) {
    // Toggle dropdown on button click
    userDropdownBtn.addEventListener("click", function (e) {
      e.stopPropagation();
      userDropdownMenu.classList.toggle("show");
    });

    // Close dropdown when clicking outside
    document.addEventListener("click", function (e) {
      if (
        !userDropdownBtn.contains(e.target) &&
        !userDropdownMenu.contains(e.target)
      ) {
        userDropdownMenu.classList.remove("show");
      }
    });

    // Close dropdown on mobile menu close
    const mobileToggle = document.querySelector(".mobile-menu-toggle");
    if (mobileToggle) {
      mobileToggle.addEventListener("click", function () {
        userDropdownMenu.classList.remove("show");
      });
    }
  }
});

// Prevent body scroll when mobile menu is open
document.addEventListener("DOMContentLoaded", function () {
  const style = document.createElement("style");
  style.textContent = `
        body.menu-open {
            overflow: hidden;
        }
    `;
  document.head.appendChild(style);
});
