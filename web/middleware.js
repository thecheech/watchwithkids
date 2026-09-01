/** 301 lowercase paths so /Friends and /Friends.html resolve to /friends (Linux static hosting is case-sensitive).
 * With cleanUrls enabled, Vercel strips .html first (Friends.html → Friends), so we need to catch both patterns. */
export default function middleware(request) {
  const url = new URL(request.url);
  const { pathname } = url;
  const lower = pathname.toLowerCase();
  if (pathname === lower) return;
  
  // Lowercase .html paths and extensionless show/episode/guide/llm paths
  // (cleanUrls converts /friends.html to /friends before this middleware runs)
  if (
    lower.endsWith(".html") ||
    lower.startsWith("/ep/") ||
    lower.startsWith("/guides/") ||
    lower.startsWith("/llms/") ||
    // Root-level show pages (extensionless after cleanUrls): /friends, /seinfeld, etc.
    // Only lowercase if path has uppercase letters and looks like a show page (no dots, no trailing slash for single segment)
    (pathname !== "/" && !pathname.includes(".") && !pathname.includes("/", 1))
  ) {
    url.pathname = lower;
    return Response.redirect(url, 301);
  }
}

export const config = {
  matcher: ["/((?!api/).*)"],
};
