import Link from 'next/link';
import Head from 'next/head';

export default function Custom500() {
  return (
    <>
      <Head>
        <title>500 - Server Error | Alex AI Financial Advisor</title>
      </Head>
      <div className="dashboard-premium min-h-screen flex items-center justify-center px-4">
        <div className="text-center relative z-10">
          <h1 className="font-display text-7xl font-bold text-[#EF4444] mb-4">500</h1>
          <h2 className="text-2xl font-semibold text-[#FAFAFA] mb-4">Internal Server Error</h2>
          <p className="text-[#A3A3A3] mb-8">
            Something went wrong on our end. Please try again later.
          </p>
          <Link href="/dashboard">
            <button className="btn-premium">
              Return to Dashboard
            </button>
          </Link>
        </div>
      </div>
    </>
  );
}
