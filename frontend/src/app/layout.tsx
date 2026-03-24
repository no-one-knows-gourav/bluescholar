import type { Metadata } from "next";
import "./globals.css";
import Providers from "@/lib/providers";

export const metadata: Metadata = {
  title: "BlueScholar",
  description: "AI-Powered Academic Intelligence",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <Providers>
          <div className="app-shell">
            {children}
          </div>
        </Providers>
      </body>
    </html>
  );
}
