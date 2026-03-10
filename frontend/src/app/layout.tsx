import type { Metadata } from "next";
import { Plus_Jakarta_Sans } from "next/font/google";
import "./globals.css";
import "antd/dist/reset.css";
import { ConfigProvider, theme as antdTheme, App as AntApp } from "antd";
import '@ant-design/v5-patch-for-react-19';
import { AntdRegistry } from '@ant-design/nextjs-registry';

const plusJakarta = Plus_Jakarta_Sans({
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700"],
  variable: "--font-plus-jakarta",
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
    <html lang="zh-CN">
      <body className={`${plusJakarta.variable} ${plusJakarta.className} antialiased`}>
        <AntdRegistry>
          <ConfigProvider
            theme={{
              algorithm: antdTheme.defaultAlgorithm,
              token: {
                colorPrimary: "#0369A1",
                borderRadius: 8,
                fontFamily: "var(--font-plus-jakarta), system-ui, sans-serif",
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
