import { PHASE_DEVELOPMENT_SERVER } from "next/constants.js";

/** @type {import('next').NextConfig} */
const nextConfig = (phase) => {
  const isDev = phase === PHASE_DEVELOPMENT_SERVER;
  return {
    // Isolate dev artifacts from `next build` (.next) so concurrent/subsequent builds never break `next dev`
    distDir: isDev ? ".next-dev" : ".next",
    webpack: (config, { dev }) => {
      // Avoid Windows drive-letter case (D:\ vs d:\) PackFileCacheStrategy corruption in dev mode
      if (dev) {
        config.cache = { type: "memory" };
      }
      return config;
    },
  };
};

export default nextConfig;

