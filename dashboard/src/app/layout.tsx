import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Vault — Distributed Storage Monitor',
  description: 'Real-time telemetry and management dashboard for Vault Distributed Object Storage',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="font-mono bg-vault-bg text-vault-text antialiased selection:bg-vault-purple selection:text-vault-bg">
        {children}
      </body>
    </html>
  );
}
