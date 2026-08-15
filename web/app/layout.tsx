import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'SAHIIX — Agentic Harness Bridge v6',
  description: 'Live console for the Agentic Harness Bridge — patterns, bridges, observability.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&family=Space+Mono:wght@400;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>
        <canvas id="fx" aria-hidden="true"></canvas>
        <div className="scroll-progress" id="scrollProgress" aria-hidden="true"></div>
        {children}
      </body>
    </html>
  );
}