import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Static HTML export: `next build` emits a fully static site into `out/`.
  // Deployed to a private S3 bucket fronted by CloudFront (see deploy.config.yml).
  output: "export",

  // Emits `dashboard/index.html` instead of `dashboard.html`, which pairs with the
  // CloudFront viewer-request function that appends `index.html` to directory URIs.
  trailingSlash: true,

  // The Next.js image optimizer needs a server; there is none in a static export.
  images: { unoptimized: true },
};

export default nextConfig;
