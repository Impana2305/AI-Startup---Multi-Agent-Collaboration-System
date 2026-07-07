import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI Startup Boardroom — Executive AI Board Meeting",
  description:
    "Submit your startup idea and watch 9 AI executives evaluate it in a live board meeting with debate, conflict resolution, voting, and a comprehensive board report.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen antialiased">{children}</body>
    </html>
  );
}
