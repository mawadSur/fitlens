/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    // Proxy API calls to FastAPI so the browser hits a single origin (no CORS surprises).
    const api = process.env.API_BASE || "http://localhost:8000";
    return [{ source: "/api/:path*", destination: `${api}/api/:path*` }];
  },
};
export default nextConfig;
