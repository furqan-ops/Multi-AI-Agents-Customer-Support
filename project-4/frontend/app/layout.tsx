import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Customer Support & Booking Agent',
  description: 'AI-powered customer support and table reservation assistant',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <body className="bg-zinc-50 text-zinc-900 dark:bg-zinc-950 dark:text-zinc-100 antialiased selection:bg-zinc-700 selection:text-white">
        {children}
      </body>
    </html>
  )
}
