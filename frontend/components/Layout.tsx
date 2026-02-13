import { useUser, UserButton, Protect } from "@clerk/nextjs";
import Link from "next/link";
import { useRouter } from "next/router";
import { ReactNode } from "react";
import PageTransition from "./PageTransition";

interface LayoutProps {
  children: ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  const { user } = useUser();
  const router = useRouter();

  // Helper to determine if a link is active
  const isActive = (path: string) => router.pathname === path;

  return (
    <Protect fallback={
      <div className="dashboard-premium min-h-screen flex items-center justify-center">
        <div className="text-center relative z-10">
          <p className="text-[#A3A3A3]">Redirecting to sign in...</p>
        </div>
      </div>
    }>
      <div className="min-h-screen bg-[#0D0D0F] flex flex-col">
        {/* Navigation */}
        <nav className="bg-[#0D0D0F] border-b border-[rgba(212,175,55,0.15)]">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center h-16">
              {/* Logo and Brand */}
              <div className="flex items-center gap-8">
                <Link href="/dashboard" className="flex items-center">
                  <h1 className="text-xl font-bold text-[#FAFAFA]">
                    Alex <span className="text-[#D4AF37]">AI Financial Advisor</span>
                  </h1>
                </Link>

                {/* Navigation Links */}
                <div className="hidden md:flex items-center gap-6">
                  <Link
                    href="/dashboard"
                    className={`text-sm font-medium transition-colors ${
                      isActive("/dashboard")
                        ? "text-[#D4AF37]"
                        : "text-[#A3A3A3] hover:text-[#D4AF37]"
                    }`}
                  >
                    Dashboard
                  </Link>
                  <Link
                    href="/accounts"
                    className={`text-sm font-medium transition-colors ${
                      isActive("/accounts")
                        ? "text-[#D4AF37]"
                        : "text-[#A3A3A3] hover:text-[#D4AF37]"
                    }`}
                  >
                    Accounts
                  </Link>
                  <Link
                    href="/advisor-team"
                    className={`text-sm font-medium transition-colors ${
                      isActive("/advisor-team")
                        ? "text-[#D4AF37]"
                        : "text-[#A3A3A3] hover:text-[#D4AF37]"
                    }`}
                  >
                    Advisor Team
                  </Link>
                  <Link
                    href="/analysis"
                    className={`text-sm font-medium transition-colors ${
                      isActive("/analysis")
                        ? "text-[#D4AF37]"
                        : "text-[#A3A3A3] hover:text-[#D4AF37]"
                    }`}
                  >
                    Analysis
                  </Link>
                </div>
              </div>

              {/* User Section */}
              <div className="flex items-center gap-4">
                <span className="hidden sm:inline text-sm text-[#A3A3A3]">
                  {user?.firstName || user?.emailAddresses[0]?.emailAddress}
                </span>
                <UserButton afterSignOutUrl="/" />
              </div>
            </div>

            {/* Mobile Navigation */}
            <div className="md:hidden flex items-center gap-4 pb-3">
              <Link
                href="/dashboard"
                className={`text-sm font-medium transition-colors ${
                  isActive("/dashboard")
                    ? "text-[#D4AF37]"
                    : "text-[#A3A3A3] hover:text-[#D4AF37]"
                }`}
              >
                Dashboard
              </Link>
              <Link
                href="/accounts"
                className={`text-sm font-medium transition-colors ${
                  isActive("/accounts")
                    ? "text-[#D4AF37]"
                    : "text-[#A3A3A3] hover:text-[#D4AF37]"
                }`}
              >
                Accounts
              </Link>
              <Link
                href="/advisor-team"
                className={`text-sm font-medium transition-colors ${
                  isActive("/advisor-team")
                    ? "text-[#D4AF37]"
                    : "text-[#A3A3A3] hover:text-[#D4AF37]"
                }`}
              >
                Advisor Team
              </Link>
              <Link
                href="/analysis"
                className={`text-sm font-medium transition-colors ${
                  isActive("/analysis")
                    ? "text-[#D4AF37]"
                    : "text-[#A3A3A3] hover:text-[#D4AF37]"
                }`}
              >
                Analysis
              </Link>
            </div>
          </div>
        </nav>

        {/* Main Content */}
        <main className="flex-1">
          <PageTransition>
            {children}
          </PageTransition>
        </main>

        {/* Footer */}
        <footer className="bg-[#0D0D0F] border-t border-[rgba(212,175,55,0.15)] mt-auto">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
            <div className="bg-[rgba(212,175,55,0.06)] border border-[rgba(212,175,55,0.15)] rounded-lg p-4">
              <p className="text-sm text-[#D4AF37] font-medium mb-2">
                Important Disclaimer
              </p>
              <p className="text-xs text-[#A3A3A3]">
                This AI-generated advice has not been vetted by a qualified financial advisor and should not be used for trading decisions.
                For informational purposes only. Always consult with a licensed financial professional before making investment decisions.
              </p>
            </div>
            <div className="mt-4 pt-4 border-t border-[rgba(255,255,255,0.06)]">
              <p className="text-xs text-[#6B6B6B] text-center">
                &copy; 2026 Alex AI Financial Advisor. Powered by AI agents and built with care.
              </p>
            </div>
          </div>
        </footer>
      </div>
    </Protect>
  );
}
