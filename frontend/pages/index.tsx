import { SignInButton, SignUpButton, SignedIn, SignedOut, UserButton } from "@clerk/nextjs";
import Link from "next/link";
import Head from "next/head";

export default function Home() {
  return (
    <>
      <Head>
        <title>Alex AI Financial Advisor - Intelligent Portfolio Management</title>
      </Head>

      <div className="dashboard-premium">
        {/* Navigation */}
        <nav className="px-8 py-6 border-b border-[rgba(212,175,55,0.1)] relative z-10">
          <div className="max-w-7xl mx-auto flex justify-between items-center">
            <div className="text-2xl font-bold text-[#FAFAFA]">
              Alex <span className="value-gold">AI Financial Advisor</span>
            </div>
            <div className="flex gap-4">
              <SignedOut>
                <SignInButton mode="modal">
                  <button className="btn-secondary px-6 py-2">
                    Sign In
                  </button>
                </SignInButton>
                <SignUpButton mode="modal">
                  <button className="btn-premium px-6 py-2">
                    Get Started
                  </button>
                </SignUpButton>
              </SignedOut>
              <SignedIn>
                <div className="flex items-center gap-4">
                  <Link href="/dashboard">
                    <button className="btn-premium px-6 py-2">
                      Go to Dashboard
                    </button>
                  </Link>
                  <UserButton afterSignOutUrl="/" />
                </div>
              </SignedIn>
            </div>
          </div>
        </nav>

        {/* Hero Section */}
        <section className="px-8 py-24 relative z-10">
          <div className="max-w-7xl mx-auto text-center">
            <h1 className="font-display text-5xl md:text-6xl font-semibold text-[#FAFAFA] mb-6">
              Your <span className="value-gold">AI-Powered</span> Financial Future
            </h1>
            <p className="text-xl text-[#A3A3A3] mb-10 max-w-3xl mx-auto">
              Experience the power of autonomous AI agents working together to analyze your portfolio,
              plan your retirement, and optimize your investments.
            </p>
            <div className="flex gap-6 justify-center flex-wrap">
              <SignedOut>
                <SignUpButton mode="modal">
                  <button className="btn-premium px-8 py-4 text-lg">
                    Start Your Analysis
                  </button>
                </SignUpButton>
              </SignedOut>
              <SignedIn>
                <Link href="/dashboard">
                  <button className="btn-premium px-8 py-4 text-lg">
                    Open Dashboard
                  </button>
                </Link>
              </SignedIn>
              <button className="btn-secondary px-8 py-4 text-lg">
                Watch Demo
              </button>
            </div>
          </div>
        </section>

        {/* Features Section */}
        <section className="px-8 py-20 relative z-10">
          <div className="max-w-7xl mx-auto">
            <h2 className="font-display text-3xl font-semibold text-center text-[#FAFAFA] mb-12">
              Meet Your <span className="value-gold">AI Advisory Team</span>
            </h2>
            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div className="card-premium text-center p-6">
                <div className="text-4xl mb-4">🎯</div>
                <h3 className="text-xl font-semibold text-[#D4AF37] mb-2">Financial Planner</h3>
                <p className="text-[#A3A3A3]">Coordinates your complete financial analysis with intelligent orchestration</p>
              </div>
              <div className="card-premium text-center p-6">
                <div className="text-4xl mb-4">📊</div>
                <h3 className="text-xl font-semibold text-[#D4AF37] mb-2">Portfolio Analyst</h3>
                <p className="text-[#A3A3A3]">Deep analysis of holdings, performance metrics, and risk assessment</p>
              </div>
              <div className="card-premium text-center p-6">
                <div className="text-4xl mb-4">📈</div>
                <h3 className="text-xl font-semibold text-[#D4AF37] mb-2">Chart Specialist</h3>
                <p className="text-[#A3A3A3]">Visualizes your portfolio composition with interactive charts</p>
              </div>
              <div className="card-premium text-center p-6">
                <div className="text-4xl mb-4">🏦</div>
                <h3 className="text-xl font-semibold text-[#D4AF37] mb-2">Retirement Planner</h3>
                <p className="text-[#A3A3A3]">Projects your retirement readiness with Monte Carlo simulations</p>
              </div>
            </div>
          </div>
        </section>

        {/* Benefits Section */}
        <section className="px-8 py-20 bg-[#1A1A1F] relative z-10">
          <div className="max-w-7xl mx-auto">
            <h2 className="font-display text-3xl font-semibold text-center text-[#FAFAFA] mb-12">
              Enterprise-Grade <span className="value-gold">AI Advisory</span>
            </h2>
            <div className="grid md:grid-cols-3 gap-8">
              <div className="card-premium p-8">
                <div className="text-[#D4AF37] text-3xl mb-4">⚡</div>
                <h3 className="text-xl font-semibold text-[#FAFAFA] mb-3">Real-Time Analysis</h3>
                <p className="text-[#A3A3A3]">Watch AI agents collaborate in parallel to analyze your complete financial picture</p>
              </div>
              <div className="card-premium p-8">
                <div className="text-[#D4AF37] text-3xl mb-4">🔒</div>
                <h3 className="text-xl font-semibold text-[#FAFAFA] mb-3">Bank-Level Security</h3>
                <p className="text-[#A3A3A3]">Your data is protected with enterprise security and row-level access controls</p>
              </div>
              <div className="card-premium p-8">
                <div className="text-[#D4AF37] text-3xl mb-4">📊</div>
                <h3 className="text-xl font-semibold text-[#FAFAFA] mb-3">Comprehensive Reports</h3>
                <p className="text-[#A3A3A3]">Detailed markdown reports with interactive charts and retirement projections</p>
              </div>
            </div>
          </div>
        </section>

        {/* CTA Section */}
        <section className="px-8 py-20 relative z-10">
          <div className="max-w-4xl mx-auto text-center">
            <h2 className="font-display text-3xl font-semibold text-[#FAFAFA] mb-6">
              Ready to Transform Your <span className="value-gold">Financial Future</span>?
            </h2>
            <p className="text-xl text-[#A3A3A3] mb-8">
              Join thousands of investors using AI to optimize their portfolios
            </p>
            <SignUpButton mode="modal">
              <button className="btn-premium px-10 py-4 text-lg">
                Get Started Free
              </button>
            </SignUpButton>
          </div>
        </section>

        {/* Footer */}
        <footer className="px-8 py-6 border-t border-[rgba(212,175,55,0.1)] text-[#6B6B6B] text-center text-sm relative z-10">
          <p>&copy; 2026 Alex AI Financial Advisor. All rights reserved.</p>
          <p className="mt-2">
            This AI-generated advice has not been vetted by a qualified financial advisor and should not be used for trading decisions.
            For informational purposes only.
          </p>
        </footer>
      </div>
    </>
  );
}
