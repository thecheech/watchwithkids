/** 301 lowercase paths so /Friends.html resolves to /friends.html (Linux static hosting is case-sensitive). */
export default function middleware(request) {
  const url = new URL(request.url);
  const { pathname } = url;
  const lower = pathname.toLowerCase();
  if (pathname === lower) return;
  if (
    lower.endsWith(".html") ||
    lower.startsWith("/ep/") ||
    lower.startsWith("/guides/") ||
    lower.startsWith("/llms/")
  ) {
    url.pathname = lower;
    return Response.redirect(url, 301);
  }
}

export const config = {
  matcher: ["/((?!api/).*)"],
};
