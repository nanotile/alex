import Link from 'next/link';
import Head from 'next/head';

export default function Custom404() {
  return (
    <>
      <Head>
        <title>404 - Page Not Found | Alex AI Financial Advisor</title>
      </Head>
      <div className="dashboard-premium min-h-screen flex items-center justify-center px-4">
        <div className="text-center relative z-10">
          <h1 className="font-display text-7xl font-bold value-gold mb-4">404</h1>
          <h2 className="text-2xl font-semibold text-[#FAFAFA] mb-4">Page Not Found</h2>
          <p className="text-[#A3A3A3] mb-8">
            The page you&apos;re looking for doesn&apos;t exist or has been moved.
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
