import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Providers } from "@/components/providers";
import { Sidebar } from "@/components/sidebar";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Project Capsule Dashboard",
  description: "Next-gen memory capture and extraction.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="light">
      <body className={`${inter.className} bg-[#f9fafb] text-zinc-900 flex h-screen overflow-hidden p-2 antialiased`}>
        <Providers>
          <div className="flex w-full h-full rounded-2xl overflow-hidden bg-white shadow-[0_0_40px_-15px_rgba(0,0,0,0.05)] border border-zinc-200/60 ring-1 ring-black/[0.02]">
            <Sidebar />
            <main className="flex-1 overflow-y-auto bg-white relative border-l border-zinc-100">
              {children}
            </main>
          </div>
        </Providers>
      </body>
    </html>
  );
}
