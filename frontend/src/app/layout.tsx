import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import "antd/dist/reset.css";
import { ConfigProvider, theme as antdTheme, App as AntApp } from "antd";
import '@ant-design/v5-patch-for-react-19';
import { AntdRegistry } from '@ant-design/nextjs-registry';

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "智能简历筛选系统",
  description: "AI 驱动的简历解析、筛选与对话系统",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${geistSans.variable} ${geistMono.variable} antialiased`}>
        <AntdRegistry>
          <ConfigProvider
            theme={{
              algorithm: antdTheme.defaultAlgorithm,
              token: {
                colorPrimary: "#1677ff",
                borderRadius: 6,
              },
            }}
          >
            <AntApp>
              {children}
            </AntApp>
          </ConfigProvider>
        </AntdRegistry>
      </body>
    </html>
  );
}
