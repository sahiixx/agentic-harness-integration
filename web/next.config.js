/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,

  async rewrites() {
    return [
      {
        source: '/api/harness/:path*',
        destination: `${process.env.HARNESS_API_URL || 'http://localhost:8000'}/:path*`,
      },
    ];
  },

  webpack: (config) => {
    config.resolve.alias = {
      ...config.resolve.alias,
      '@': require('path').resolve(__dirname),
    };
    return config;
  },
};

module.exports = nextConfig;
