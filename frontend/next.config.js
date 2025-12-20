/** @type {import('next').NextConfig} */
const nextConfig = {
  /* Basic Configuration */
  reactStrictMode: true,
  poweredByHeader: false,
  compress: true,

  /* TypeScript */
  typescript: {
    // Set to true to skip type checking during builds (not recommended for production)
    ignoreBuildErrors: false,
  },

  /* ESLint */
  eslint: {
    // Set to true to skip ESLint during builds (not recommended for production)
    ignoreDuringBuilds: false,
  },

  /* Environment Variables */
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
    NEXT_PUBLIC_APP_NAME: process.env.NEXT_PUBLIC_APP_NAME || 'WebScraper Platform',
    NEXT_PUBLIC_APP_VERSION: process.env.NEXT_PUBLIC_APP_VERSION || '1.0.0',
  },

  /* Images Configuration */
  images: {
    domains: ['localhost'],
    formats: ['image/avif', 'image/webp'],
    remotePatterns: [
      {
        protocol: 'https',
        hostname: '**',
      },
    ],
  },

  /* Headers */
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          {
            key: 'X-DNS-Prefetch-Control',
            value: 'on',
          },
          {
            key: 'Strict-Transport-Security',
            value: 'max-age=63072000; includeSubDomains; preload',
          },
          {
            key: 'X-Frame-Options',
            value: 'SAMEORIGIN',
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'X-XSS-Protection',
            value: '1; mode=block',
          },
          {
            key: 'Referrer-Policy',
            value: 'strict-origin-when-cross-origin',
          },
          {
            key: 'Permissions-Policy',
            value: 'camera=(), microphone=(), geolocation=()',
          },
        ],
      },
    ];
  },

  /* Redirects */
  async redirects() {
    return [
      {
        source: '/',
        destination: '/dashboard',
        permanent: false,
      },
    ];
  },

  /* Rewrites (for API proxying if needed) */
  async rewrites() {
    const apiBase = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    if (!apiBase) {
      throw new Error('NEXT_PUBLIC_API_URL is required for rewrites; set it in .env or .env.local');
    }
    return [
      {
        source: '/api/:path*',
        destination: `${apiBase}/api/:path*`,
      },
    ];
  },

  /* Webpack Configuration */
  webpack: (config, { isServer }) => {
    // Add any custom webpack configuration here
    if (!isServer) {
      config.resolve.fallback = {
        ...config.resolve.fallback,
        fs: false,
        net: false,
        tls: false,
      };
    }

    return config;
  },

  /* Experimental Features */
  experimental: {
    // Enable server actions if needed
    serverActions: {
      enabled: true,
    },
  },

  /* Output Configuration */
  output: 'standalone', // For Docker deployments
};

module.exports = nextConfig;
