import type { Metadata } from "next";
import "./globals.css";
import Providers from "@/lib/providers";
import { Outfit, Inter, JetBrains_Mono } from "next/font/google";
import { cn } from "@/lib/utils";

const outfit = Outfit({
  subsets: ["latin"],
  variable: "--font-outfit",
});

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-jetbrains-mono",
});

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
    <html lang="en" className={cn(outfit.variable, inter.variable, jetbrainsMono.variable)}>
      <body className="antialiased font-inter">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
