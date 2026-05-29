"use strict";

(function initPromptFeed() {
  const promptResults = document.querySelector("[data-prompt-results]");
  if (!promptResults) return;

  const promptTotalCount = document.getElementById("promptTotalCount");
  const sortSelect = document.querySelector("[data-prompt-sort]");
  const searchForms = Array.from(document.querySelectorAll("[data-prompt-search-form]"));
  const searchInputs = Array.from(document.querySelectorAll("[data-prompt-search-input]"));
  const categoryLinks = Array.from(document.querySelectorAll(".filter-section .cpill"));
  const resultsAnchor = document.getElementById("promptResults");
  const mobileMenu = document.getElementById("mobileMenu");
  const allowedSorts = new Set(["newest", "popular", "copied"]);
  const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const performanceMode = prefersReducedMotion || window.matchMedia("(max-width: 768px)").matches;

  let activeRequest = null;

  function normalizeSort(value) {
    const sortValue = (value || "newest").toLowerCase();
    return allowedSorts.has(sortValue) ? sortValue : "newest";
  }

  function readStateFromUrl() {
    const params = new URLSearchParams(window.location.search);
    return {
      search: (params.get("search") || "").trim(),
      category: (params.get("category") || "").trim(),
      sort: normalizeSort(params.get("sort")),
    };
  }

  function readCurrentSearch() {
    const firstInput = searchInputs[0];
    return (firstInput ? firstInput.value : "").trim();
  }

  function buildUrl(state) {
    const params = new URLSearchParams();
    if (state.search) params.set("search", state.search);
    if (state.category) params.set("category", state.category);
    if (state.sort && state.sort !== "newest") params.set("sort", state.sort);
    const queryString = params.toString();
    return `${window.location.pathname}${queryString ? `?${queryString}` : ""}`;
  }

  function syncControls(state) {
    searchInputs.forEach(input => {
      input.value = state.search;
    });

    if (sortSelect) {
      sortSelect.value = state.sort;
    }

    categoryLinks.forEach(link => {
      const linkUrl = new URL(link.href, window.location.origin);
      const linkCategory = (linkUrl.searchParams.get("category") || "").trim();
      const isActive = linkCategory === state.category;
      link.classList.toggle("active", isActive);
      if (isActive) {
        link.setAttribute("aria-current", "page");
      } else {
        link.removeAttribute("aria-current");
      }
    });
  }

  function setLoading(isLoading) {
    promptResults.classList.toggle("is-loading", isLoading);
    promptResults.setAttribute("aria-busy", String(isLoading));
  }

  async function fetchPromptFeed(state, options = {}) {
    const nextState = {
      search: (state.search || "").trim(),
      category: (state.category || "").trim(),
      sort: normalizeSort(state.sort),
    };
    currentState = nextState;

    const controller = new AbortController();
    if (activeRequest) {
      activeRequest.abort();
    }
    activeRequest = controller;

    const queryString = new URLSearchParams();
    if (nextState.search) queryString.set("search", nextState.search);
    if (nextState.category) queryString.set("category", nextState.category);
    if (nextState.sort !== "newest") queryString.set("sort", nextState.sort);

    setLoading(true);

    try {
      const response = await fetch(`/api/prompts${queryString.toString() ? `?${queryString.toString()}` : ""}`, {
        headers: {
          "Accept": "application/json",
          "X-Requested-With": "fetch",
        },
        signal: controller.signal,
      });

      if (!response.ok) {
        throw new Error(`Prompt feed request failed (${response.status})`);
      }

      const data = await response.json();
      if (controller.signal.aborted) return;

      promptResults.innerHTML = data.html;

      if (promptTotalCount) {
        promptTotalCount.textContent = String(data.prompt_count ?? 0);
      }

      syncControls(nextState);

      if (options.pushState !== false) {
        const nextUrl = buildUrl(nextState);
        if (options.replaceState) {
          window.history.replaceState({ promptFeed: nextState }, "", nextUrl);
        } else {
          window.history.pushState({ promptFeed: nextState }, "", nextUrl);
        }
      }

      if (options.scroll !== false && resultsAnchor) {
        requestAnimationFrame(() => {
          resultsAnchor.scrollIntoView({
            behavior: prefersReducedMotion ? "auto" : "smooth",
            block: "start",
          });
        });
      }
    } catch (error) {
      if (error.name !== "AbortError") {
        console.error(error);
      }
    } finally {
      if (activeRequest === controller) {
        activeRequest = null;
        setLoading(false);
      }
    }
  }

  let currentState = readStateFromUrl();
  syncControls(currentState);
  if (window.history.state && window.history.state.promptFeed) {
    currentState = window.history.state.promptFeed;
    syncControls(currentState);
  }

  searchForms.forEach(form => {
    form.addEventListener("submit", event => {
      event.preventDefault();
      const input = form.querySelector("[data-prompt-search-input]") || form.querySelector('input[name="search"]');
      const nextState = {
        search: (input ? input.value : readCurrentSearch()).trim(),
        category: currentState.category,
        sort: sortSelect ? sortSelect.value : currentState.sort,
      };
      fetchPromptFeed(nextState);
      if (mobileMenu) mobileMenu.classList.remove("open");
    });
  });

  if (sortSelect) {
    sortSelect.addEventListener("change", () => {
      fetchPromptFeed({
        search: readCurrentSearch(),
        category: currentState.category,
        sort: sortSelect.value,
      });
    });
  }

  categoryLinks.forEach(link => {
    link.addEventListener("click", event => {
      event.preventDefault();
      const linkUrl = new URL(link.href, window.location.origin);
      const linkCategory = (linkUrl.searchParams.get("category") || "").trim();
      const nextState = {
        search: linkCategory ? readCurrentSearch() : "",
        category: linkCategory,
        sort: linkCategory ? (sortSelect ? sortSelect.value : currentState.sort) : "newest",
      };
      fetchPromptFeed(nextState);
      if (mobileMenu) mobileMenu.classList.remove("open");
    });
  });

  window.addEventListener("popstate", () => {
    const nextState = readStateFromUrl();
    currentState = nextState;
    syncControls(nextState);
    fetchPromptFeed(nextState, { pushState: false, scroll: false, replaceState: false });
  });
})();
