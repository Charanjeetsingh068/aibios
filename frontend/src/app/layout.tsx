import type { Metadata, Viewport } from 'next';
import '../styles/globals.css';
import QueryProvider from '../providers/QueryProvider';
import { AuthProvider } from '../contexts/AuthContext';

export const metadata: Metadata = {
  title: 'AI-BOS Enterprise Portal',
  description: 'AI Business Operating System Enterprise Administration Dashboard',
};

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const themeInitScript = `
    (function() {
      const savedTheme = localStorage.getItem('aibos-theme');
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      const theme = savedTheme || (prefersDark ? 'dark' : 'light');
      document.documentElement.setAttribute('data-theme', theme);
    })();
  `;

  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeInitScript }} />
      </head>
      <body>
        <AuthProvider>
          <QueryProvider>{children}</QueryProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
