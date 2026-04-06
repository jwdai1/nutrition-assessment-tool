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
          <a href="/patients" className="inline-block hover:opacity-80 transition-opacity">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg bg-white/20 flex items-center justify-center text-sm font-bold">
                N
              </div>
              <div>
                <h1 className="text-lg font-bold leading-tight">低栄養診断ツール</h1>
                <p className="text-xs text-blue-200">MNA-SF / GLIM Nutrition Assessment</p>
              </div>
            </div>
          </a>
        </header>
        <main className="max-w-6xl mx-auto px-4 py-6">{children}</main>
      </body>
    </html>
  );
}
