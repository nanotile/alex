import { useEffect, useState } from 'react';
import { useAuth } from '@clerk/nextjs';
import { API_URL } from '../lib/config';

interface AgentProgress {
  name: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  startTime?: string;
  endTime?: string;
  duration?: number;
  output?: string;
  error?: string;
}

interface AnalysisProgressTrackerProps {
  jobId: string;
  onComplete?: () => void;
  onError?: (error: string) => void;
}

interface JobStatus {
  job_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  job_type: string;
  created_at: string;
  updated_at: string;
  results?: any;
  error?: string;
  metadata?: {
    planner_output?: string;
    agents_invoked?: string[];
    agent_responses?: Record<string, any>;
  };
}

export default function AnalysisProgressTracker({
  jobId,
  onComplete,
  onError
}: AnalysisProgressTrackerProps) {
  const { getToken } = useAuth();
  const [jobStatus, setJobStatus] = useState<JobStatus | null>(null);
  const [agentProgress, setAgentProgress] = useState<Record<string, AgentProgress>>({
    planner: { name: 'Financial Planner (Orchestrator)', status: 'pending' },
    tagger: { name: 'Instrument Classifier', status: 'pending' },
    reporter: { name: 'Portfolio Analyst', status: 'pending' },
    charter: { name: 'Chart Specialist', status: 'pending' },
    retirement: { name: 'Retirement Planner', status: 'pending' },
  });
  const [pollCount, setPollCount] = useState(0);
  const [logs, setLogs] = useState<string[]>([]);
  const [startTime] = useState(Date.now());
  const [debugInfo, setDebugInfo] = useState({
    lastPollTime: '',
    pollInterval: 2000,
    totalPolls: 0,
    apiResponses: [] as any[],
  });

  const addLog = (message: string, type: 'info' | 'success' | 'error' | 'warning' = 'info') => {
    const timestamp = new Date().toLocaleTimeString();
    const prefix = type === 'error' ? '❌' : type === 'success' ? '✅' : type === 'warning' ? '⚠️' : 'ℹ️';
    setLogs(prev => [...prev, `[${timestamp}] ${prefix} ${message}`]);
  };

  useEffect(() => {
    addLog(`Starting progress tracking for job ${jobId}`, 'info');

    const pollJobStatus = async () => {
      try {
        const now = new Date().toLocaleTimeString();
        setDebugInfo(prev => ({
          ...prev,
          lastPollTime: now,
          totalPolls: prev.totalPolls + 1
        }));

        addLog(`Polling job status (poll #${pollCount + 1})`, 'info');

        const token = await getToken();
        if (!token) {
          addLog('No auth token available', 'error');
          return;
        }

        const response = await fetch(`${API_URL}/api/jobs/${jobId}`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });

        addLog(`API response: ${response.status} ${response.statusText}`,
          response.ok ? 'success' : 'error');

        if (!response.ok) {
          const errorText = await response.text();
          addLog(`API error: ${errorText}`, 'error');
          throw new Error(`Failed to fetch job status: ${response.status}`);
        }

        const job: JobStatus = await response.json();
        setJobStatus(job);

        // Store API response for debugging
        setDebugInfo(prev => ({
          ...prev,
          apiResponses: [...prev.apiResponses.slice(-4), {
            time: now,
            status: job.status,
            metadata: job.metadata
          }]
        }));

        addLog(`Job status: ${job.status}`, job.status === 'completed' ? 'success' : 'info');

        // Update agent progress based on job metadata
        const newProgress = { ...agentProgress };

        // Planner is always first
        if (job.status === 'processing' || job.status === 'completed' || job.status === 'failed') {
          newProgress.planner = {
            ...newProgress.planner,
            status: job.status === 'completed' ? 'completed' : 'running',
            output: job.metadata?.planner_output,
          };
        }

        // Check for agents that have been invoked
        if (job.metadata?.agents_invoked) {
          addLog(`Agents invoked: ${job.metadata.agents_invoked.join(', ')}`, 'info');

          job.metadata.agents_invoked.forEach((agentName: string) => {
            const agentKey = agentName.toLowerCase();
            if (newProgress[agentKey]) {
              newProgress[agentKey] = {
                ...newProgress[agentKey],
                status: 'running',
              };
            }
          });
        }

        // Check for completed agent responses
        if (job.metadata?.agent_responses) {
          Object.entries(job.metadata.agent_responses).forEach(([agentKey, response]: [string, any]) => {
            if (newProgress[agentKey]) {
              newProgress[agentKey] = {
                ...newProgress[agentKey],
                status: 'completed',
                output: typeof response === 'string' ? response : JSON.stringify(response).substring(0, 200),
              };
              addLog(`${newProgress[agentKey].name} completed`, 'success');
            }
          });
        }

        setAgentProgress(newProgress);

        // Handle job completion
        if (job.status === 'completed') {
          addLog('Analysis completed successfully! 🎉', 'success');
          Object.keys(newProgress).forEach(key => {
            if (newProgress[key].status !== 'completed') {
              newProgress[key].status = 'completed';
            }
          });
          setAgentProgress(newProgress);

          if (onComplete) {
            setTimeout(onComplete, 1500);
          }
          return; // Stop polling
        }

        // Handle job failure
        if (job.status === 'failed') {
          addLog(`Analysis failed: ${job.error || 'Unknown error'}`, 'error');
          Object.keys(newProgress).forEach(key => {
            if (newProgress[key].status === 'running') {
              newProgress[key].status = 'failed';
              newProgress[key].error = job.error;
            }
          });
          setAgentProgress(newProgress);

          if (onError) {
            onError(job.error || 'Analysis failed');
          }
          return; // Stop polling
        }

        setPollCount(prev => prev + 1);

      } catch (error) {
        console.error('Error polling job status:', error);
        addLog(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`, 'error');

        if (onError) {
          onError(error instanceof Error ? error.message : 'Unknown error');
        }
      }
    };

    // Initial poll
    pollJobStatus();

    // Set up polling interval
    const interval = setInterval(pollJobStatus, 2000);

    // Cleanup
    return () => clearInterval(interval);
  }, [jobId, pollCount]); // eslint-disable-line react-hooks/exhaustive-deps

  const getStatusIcon = (status: AgentProgress['status']) => {
    switch (status) {
      case 'pending': return '⏳';
      case 'running': return '🔄';
      case 'completed': return '✅';
      case 'failed': return '❌';
      default: return '❓';
    }
  };

  const getStatusColor = (status: AgentProgress['status']) => {
    switch (status) {
      case 'pending': return 'text-gray-500';
      case 'running': return 'text-blue-600 animate-pulse';
      case 'completed': return 'text-green-600';
      case 'failed': return 'text-red-600';
      default: return 'text-gray-500';
    }
  };

  const getElapsedTime = () => {
    const elapsed = Math.floor((Date.now() - startTime) / 1000);
    const minutes = Math.floor(elapsed / 60);
    const seconds = elapsed % 60;
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-dark">Analysis in Progress</h2>
          <p className="text-sm text-gray-500">Job ID: {jobId}</p>
        </div>
        <div className="text-right">
          <div className="text-3xl font-bold text-primary">{getElapsedTime()}</div>
          <div className="text-xs text-gray-500">Elapsed Time</div>
        </div>
      </div>

      {/* Overall Status */}
      <div className="bg-blue-50 border-2 border-blue-200 rounded-lg p-4">
        <div className="flex items-center gap-3">
          <div className="text-4xl">🤖</div>
          <div className="flex-1">
            <div className="text-lg font-semibold text-blue-900">
              Status: {jobStatus?.status || 'Initializing...'}
            </div>
            <div className="text-sm text-blue-700">
              {jobStatus?.status === 'processing' && 'AI agents are analyzing your portfolio...'}
              {jobStatus?.status === 'pending' && 'Queuing analysis request...'}
              {jobStatus?.status === 'completed' && 'Analysis completed successfully!'}
              {jobStatus?.status === 'failed' && 'Analysis encountered an error'}
            </div>
          </div>
          <div className="text-2xl">
            {jobStatus?.status === 'processing' && '🔄'}
            {jobStatus?.status === 'pending' && '⏳'}
            {jobStatus?.status === 'completed' && '✅'}
            {jobStatus?.status === 'failed' && '❌'}
          </div>
        </div>
      </div>

      {/* Agent Progress Cards */}
      <div className="space-y-3">
        <h3 className="text-lg font-semibold text-dark">Agent Activity</h3>
        {Object.entries(agentProgress).map(([key, agent]) => (
          <div
            key={key}
            className={`border-2 rounded-lg p-4 transition-all ${
              agent.status === 'running'
                ? 'border-blue-400 bg-blue-50 shadow-md'
                : agent.status === 'completed'
                ? 'border-green-300 bg-green-50'
                : agent.status === 'failed'
                ? 'border-red-300 bg-red-50'
                : 'border-gray-200 bg-gray-50'
            }`}
          >
            <div className="flex items-start gap-3">
              <div className="text-3xl">{getStatusIcon(agent.status)}</div>
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <h4 className="font-semibold text-dark">{agent.name}</h4>
                  <span className={`text-sm font-medium ${getStatusColor(agent.status)}`}>
                    {agent.status.toUpperCase()}
                  </span>
                </div>
                {agent.output && (
                  <p className="text-sm text-gray-600 mt-1 line-clamp-2">
                    {agent.output}
                  </p>
                )}
                {agent.error && (
                  <p className="text-sm text-red-600 mt-1">
                    Error: {agent.error}
                  </p>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Debug Information */}
      <details className="bg-gray-50 border border-gray-300 rounded-lg">
        <summary className="cursor-pointer p-3 font-semibold text-gray-700 hover:bg-gray-100">
          🔍 Debug Information (Click to expand)
        </summary>
        <div className="p-4 space-y-3 text-xs font-mono">
          <div>
            <strong>Last Poll:</strong> {debugInfo.lastPollTime || 'Not yet polled'}
          </div>
          <div>
            <strong>Total Polls:</strong> {debugInfo.totalPolls}
          </div>
          <div>
            <strong>Poll Interval:</strong> {debugInfo.pollInterval}ms (2 seconds)
          </div>

          {debugInfo.apiResponses.length > 0 && (
            <div>
              <strong>Recent API Responses:</strong>
              <div className="bg-white border border-gray-300 rounded p-2 mt-1 max-h-40 overflow-y-auto">
                {debugInfo.apiResponses.map((resp, idx) => (
                  <div key={idx} className="text-xs mb-2 pb-2 border-b border-gray-200 last:border-0">
                    <div><strong>{resp.time}:</strong> Status = {resp.status}</div>
                    {resp.metadata && (
                      <pre className="text-[10px] text-gray-600 mt-1 overflow-x-auto">
                        {JSON.stringify(resp.metadata, null, 2)}
                      </pre>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {jobStatus && (
            <div>
              <strong>Full Job Object:</strong>
              <pre className="bg-white border border-gray-300 rounded p-2 mt-1 overflow-x-auto text-[10px]">
                {JSON.stringify(jobStatus, null, 2)}
              </pre>
            </div>
          )}
        </div>
      </details>

      {/* Live Activity Log */}
      <details className="bg-gray-50 border border-gray-300 rounded-lg">
        <summary className="cursor-pointer p-3 font-semibold text-gray-700 hover:bg-gray-100">
          📋 Activity Log ({logs.length} events)
        </summary>
        <div className="p-4">
          <div className="bg-black text-green-400 rounded p-3 font-mono text-xs max-h-64 overflow-y-auto">
            {logs.map((log, idx) => (
              <div key={idx} className="mb-1">
                {log}
              </div>
            ))}
          </div>
        </div>
      </details>
    </div>
  );
}
