import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { Outfit } from 'next/font/google';
import "./globals.css";

const outfit = Outfit({
  subsets: ['latin'],
  weight: ['300', '400', '500', '600', '700'],
  variable: '--font-outfit',
});

export const metadata: Metadata = {
  title: "pharmamiku - Your AI Pharma Assistant",
  description: "pharmacy chatbot ui",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={outfit.className}
      >
        {children}
      </body>
    </html>
  );
}
