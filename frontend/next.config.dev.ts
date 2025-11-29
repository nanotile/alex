import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  // NO output: 'export' - allow server-side rendering for development
  // Configure Turbopack root to fix lockfile warning
  turbopack: {
    root: '/home/kent_benson/AWS_projects/alex/frontend'
  }
};

export default nextConfig;
