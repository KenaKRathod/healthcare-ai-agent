const THEME_KEY = "aurahealth-theme";

export function getStoredDarkMode() {
  const stored = localStorage.getItem(THEME_KEY);
  if (stored === "light") return false;
  if (stored === "dark") return true;
  return window.matchMedia("(prefers-color-scheme: dark)").matches;
}

export function applyDarkMode(isDark) {
  document.documentElement.classList.toggle("dark", isDark);
  localStorage.setItem(THEME_KEY, isDark ? "dark" : "light");
}
