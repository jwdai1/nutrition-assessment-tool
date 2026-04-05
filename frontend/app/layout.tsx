import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "低栄養診断ツール — MNA-SF / GLIM",
  description: "MNA-SFスクリーニングとGLIM基準による低栄養診断ツール",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ja">
      <body className={`${inter.className} bg-gray-50 min-h-screen`}>
        <header className="bg-[#1a56a4] text-white px-6 py-3">
          <h1 className="text-lg font-bold">低栄養診断ツール</h1>
          <p className="text-sm text-blue-200">MNA-SF / GLIM Nutrition Assessment</p>
        </header>
        <main className="max-w-6xl mx-auto px-4 py-6">{children}</main>
      </body>
    </html>
  );
}
