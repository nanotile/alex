import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { useAuth } from '@clerk/nextjs';
import Layout from '../components/Layout';
import { API_URL } from '../lib/config';
import { emitAnalysisCompleted, emitAnalysisFailed, emitAnalysisStarted } from '../lib/events';
import Head from 'next/head';

interface Agent {
  icon: string;
  name: string;
  role: string;
  description: string;
}

interface Job {
  id: string;
  created_at: string;
  status: string;
  job_type: string;
}

interface AnalysisProgress {
  stage: 'idle' | 'starting' | 'planner' | 'parallel' | 'completing' | 'complete' | 'error';
  message: string;
  activeAgents: string[];
  error?: string;
}

const agents: Agent[] = [
  {
    icon: '🎯',
    name: 'Financial Planner',
    role: 'Orchestrator',
    description: 'Coordinates your financial analysis',
  },
  {
    icon: '📊',
    name: 'Portfolio Analyst',
    role: 'Reporter',
    description: 'Analyzes your holdings and performance',
  },
  {
    icon: '📈',
    name: 'Chart Specialist',
    role: 'Charter',
    description: 'Visualizes your portfolio composition',
  },
  {
    icon: '🎯',
    name: 'Retirement Planner',
    role: 'Retirement',
    description: 'Projects your retirement readiness',
  }
];

export default function AdvisorTeam() {
  const router = useRouter();
  const { getToken } = useAuth();
  const [jobs, setJobs] = useState<Job[]>([]);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [currentJobId, setCurrentJobId] = useState<string | null>(null);
  const [progress, setProgress] = useState<AnalysisProgress>({
    stage: 'idle',
    message: '',
    activeAgents: []
  });
  const [pollInterval, setPollInterval] = useState<NodeJS.Timeout | null>(null);
  const [showTimeoutWarning, setShowTimeoutWarning] = useState(false);
  const [timeoutTimer, setTimeoutTimer] = useState<NodeJS.Timeout | null>(null);

  useEffect(() => {
    fetchJobs();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const checkJobStatusLocal = async (jobId: string) => {
      try {
        const token = await getToken();
        const response = await fetch(`${API_URL}/api/jobs/${jobId}`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });

        if (response.ok) {
          const job = await response.json();

          if (job.status === 'completed') {
            setProgress({
              stage: 'complete',
              message: 'Analysis complete!',
              activeAgents: []
            });

            if (pollInterval) {
              clearInterval(pollInterval);
              setPollInterval(null);
            }

            // Clear timeout warning
            if (timeoutTimer) {
              clearTimeout(timeoutTimer);
              setTimeoutTimer(null);
            }
            setShowTimeoutWarning(false);

            // Emit completion event so other components can refresh
            emitAnalysisCompleted(jobId);

            // Also refresh our own jobs list
            fetchJobs();

            setTimeout(() => {
              router.push(`/analysis?job_id=${jobId}`);
            }, 1500);
          } else if (job.status === 'failed') {
            setProgress({
              stage: 'error',
              message: 'Analysis failed',
              activeAgents: [],
              error: job.error || 'Analysis encountered an error'
            });

            if (pollInterval) {
              clearInterval(pollInterval);
              setPollInterval(null);
            }

            // Clear timeout warning
            if (timeoutTimer) {
              clearTimeout(timeoutTimer);
              setTimeoutTimer(null);
            }
            setShowTimeoutWarning(false);

            // Emit failure event
            emitAnalysisFailed(jobId, job.error);

            setIsAnalyzing(false);
            setCurrentJobId(null);
          }
        }
      } catch (error) {
        console.error('Error checking job status:', error);
      }
    };

    if (currentJobId && !pollInterval) {
      const interval = setInterval(() => {
        checkJobStatusLocal(currentJobId);
      }, 2000);
      setPollInterval(interval);
    }

    return () => {
      if (pollInterval) {
        clearInterval(pollInterval);
        setPollInterval(null);
      }
      if (timeoutTimer) {
        clearTimeout(timeoutTimer);
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentJobId, pollInterval, router, timeoutTimer]);

  const fetchJobs = async () => {
    try {
      const token = await getToken();
      const response = await fetch(`${API_URL}/api/jobs`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setJobs(data.jobs || []);
      }
    } catch (error) {
      console.error('Error fetching jobs:', error);
    }
  };

  const startAnalysis = async () => {
    setIsAnalyzing(true);
    setShowTimeoutWarning(false);
    // Show warning after 2 minutes
    const timer = setTimeout(() => setShowTimeoutWarning(true), 120000);
    setTimeoutTimer(timer);
    setProgress({
      stage: 'starting',
      message: 'Initializing analysis...',
      activeAgents: []
    });

    try {
      const token = await getToken();
      const response = await fetch(`${API_URL}/api/analyze`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          analysis_type: 'portfolio',
          options: {}
        })
      });

      if (response.ok) {
        const data = await response.json();
        setCurrentJobId(data.job_id);

        // Emit start event
        emitAnalysisStarted(data.job_id);

        setProgress({
          stage: 'planner',
          message: 'Financial Planner coordinating analysis...',
          activeAgents: ['Financial Planner']
        });

        setTimeout(() => {
          setProgress({
            stage: 'parallel',
            message: 'Agents working in parallel...',
            activeAgents: ['Portfolio Analyst', 'Chart Specialist', 'Retirement Planner']
          });
        }, 5000);
      } else {
        throw new Error('Failed to start analysis');
      }
    } catch (error) {
      console.error('Error starting analysis:', error);
      setProgress({
        stage: 'error',
        message: 'Failed to start analysis',
        activeAgents: [],
        error: error instanceof Error ? error.message : 'Unknown error'
      });
      // Clear timeout warning
      if (timeoutTimer) {
        clearTimeout(timeoutTimer);
        setTimeoutTimer(null);
      }
      setShowTimeoutWarning(false);
      setIsAnalyzing(false);
      setCurrentJobId(null);
    }
  };


  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'text-[#10B981]';
      case 'failed':
        return 'text-[#EF4444]';
      case 'running':
        return 'text-[#3B82F6]';
      default:
        return 'text-[#6B6B6B]';
    }
  };

  const isAgentActive = (agentName: string) => {
    return progress.activeAgents.includes(agentName);
  };

  return (
    <>
      <Head>
        <title>Advisor Team - Alex AI Financial Advisor</title>
      </Head>
      <Layout>
      <div className="dashboard-premium-wrapper">
        <div className="dashboard-premium">
          <div className="dashboard-content max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">

          {/* Header */}
          <div className="fade-in mb-10">
            <p className="stat-label mb-2">Your Team</p>
            <h1 className="font-display text-4xl md:text-5xl font-semibold text-[#FAFAFA] mb-2">
              AI Advisory Team
            </h1>
            <p className="text-[#6B6B6B]">
              Meet your team of specialized AI agents that work together to provide comprehensive financial analysis.
            </p>
          </div>

          {/* Agent Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-10 fade-in fade-in-delay-1">
            {agents.map((agent) => (
              <div
                key={agent.name}
                className={`card-premium p-6 relative overflow-hidden transition-all duration-300 ${
                  isAgentActive(agent.name) ? 'ring-2 ring-[#D4AF37] ring-opacity-60' : ''
                }`}
              >
                {isAgentActive(agent.name) && (
                  <div className="absolute inset-0 bg-gradient-to-br from-[rgba(212,175,55,0.15)] to-transparent animate-strong-pulse" />
                )}
                <div className="relative">
                  <div className={`text-5xl mb-4 ${isAgentActive(agent.name) ? 'animate-strong-pulse' : ''}`}>{agent.icon}</div>
                  <h3 className="text-xl font-semibold mb-1 text-[#D4AF37]">
                    {agent.name}
                  </h3>
                  <p className="text-sm text-[#6B6B6B] mb-3">{agent.role}</p>
                  <p className="text-[#A3A3A3] text-sm">{agent.description}</p>
                  {isAgentActive(agent.name) && (
                    <div className="mt-4 inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold text-[#0D0D0F] bg-[#D4AF37] animate-strong-pulse">
                      <span className="mr-2">●</span>
                      Active
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* Analysis Center */}
          <div className="card-premium p-8 fade-in fade-in-delay-2">
            <div className="flex items-center justify-between mb-6">
              <h2 className="font-display text-2xl text-[#FAFAFA]">Analysis Center</h2>
              <button
                onClick={startAnalysis}
                disabled={isAnalyzing}
                className="btn-premium"
              >
                {isAnalyzing ? 'Analysis in Progress...' : 'Start New Analysis'}
              </button>
            </div>

            {isAnalyzing && (
              <div className="mb-8 p-6 card-highlight rounded-xl">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-[#FAFAFA]">Analysis Progress</h3>
                  {progress.stage !== 'error' && progress.stage !== 'complete' && (
                    <div className="flex space-x-2">
                      <div className="w-3 h-3 bg-[#D4AF37] rounded-full animate-strong-pulse" />
                      <div className="w-3 h-3 bg-[#D4AF37] rounded-full animate-strong-pulse" style={{ animationDelay: '0.5s' }} />
                      <div className="w-3 h-3 bg-[#D4AF37] rounded-full animate-strong-pulse" style={{ animationDelay: '1s' }} />
                    </div>
                  )}
                </div>

                <p className={`text-sm mb-4 ${
                  progress.stage === 'error' ? 'text-[#EF4444]' : 'text-[#A3A3A3]'
                }`}>
                  {progress.message}
                </p>

                {showTimeoutWarning && progress.stage !== 'error' && progress.stage !== 'complete' && (
                  <div className="mb-4 p-3 bg-[rgba(212,175,55,0.08)] border border-[rgba(212,175,55,0.2)] rounded-lg">
                    <p className="text-sm text-[#D4AF37] font-medium">Taking longer than expected...</p>
                    <p className="text-xs text-[#A3A3A3] mt-1">Analysis typically completes within 2 minutes. The agents are still working. You can wait or try again later.</p>
                  </div>
                )}

                {progress.stage === 'error' && progress.error && (
                  <div className="mt-4 p-4 bg-[rgba(239,68,68,0.08)] border border-[rgba(239,68,68,0.2)] rounded-lg">
                    <p className="text-sm text-[#EF4444]">{progress.error}</p>
                    <button
                      onClick={() => {
                        setIsAnalyzing(false);
                        setCurrentJobId(null);
                        setProgress({ stage: 'idle', message: '', activeAgents: [] });
                      }}
                      className="mt-3 px-4 py-2 bg-[#EF4444] text-white rounded-lg hover:bg-[#DC2626] text-sm font-semibold transition-colors"
                    >
                      Try Again
                    </button>
                  </div>
                )}

                {progress.stage !== 'idle' && progress.stage !== 'error' && (
                  <div className="w-full bg-[#252529] rounded-full h-2">
                    <div
                      className="bg-gradient-to-r from-[#D4AF37] to-[#E8D48A] h-2 rounded-full transition-all duration-1000"
                      style={{
                        width: progress.stage === 'starting' ? '10%' :
                               progress.stage === 'planner' ? '30%' :
                               progress.stage === 'parallel' ? '70%' :
                               progress.stage === 'completing' ? '90%' :
                               '100%'
                      }}
                    />
                  </div>
                )}
              </div>
            )}

            {/* Previous Analyses */}
            <div>
              <div className="divider-gold mb-6" />
              <h3 className="stat-label mb-4">Previous Analyses</h3>
              {jobs.length === 0 ? (
                <p className="text-[#6B6B6B] italic">No previous analyses found. Start your first analysis above!</p>
              ) : (
                <div className="space-y-3">
                  {jobs.slice(0, 5).map((job) => (
                    <div
                      key={job.id}
                      className="flex items-center justify-between p-4 bg-[#1A1A1F] rounded-lg hover:bg-[#252529] transition-colors border border-[rgba(255,255,255,0.06)]"
                    >
                      <div className="flex-1">
                        <p className="text-sm font-medium text-[#FAFAFA]">
                          Analysis #{job.id.slice(0, 8)}
                        </p>
                        <p className="text-xs text-[#6B6B6B]">
                          {formatDate(job.created_at)}
                        </p>
                      </div>
                      <div className="flex items-center space-x-4">
                        <span className={`text-sm font-medium ${getStatusColor(job.status)}`}>
                          {job.status.charAt(0).toUpperCase() + job.status.slice(1)}
                        </span>
                        {job.status === 'completed' && (
                          <button
                            onClick={() => router.push(`/analysis?job_id=${job.id}`)}
                            className="btn-secondary text-sm py-2 px-4"
                          >
                            View
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          </div>
        </div>
      </div>
      </Layout>
    </>
  );
}
