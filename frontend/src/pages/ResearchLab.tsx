import { useState, useEffect } from 'react';
import { useStartResearch, useResearchJob } from '@/hooks/useResearch';

export default function ResearchLab() {
  const [segment, setSegment] = useState('');
  const [maxCompanies, setMaxCompanies] = useState(10);
  const [jobId, setJobId] = useState<number | null>(null);
  const [logs, setLogs] = useState<{ time: Date; message: string }[]>([]);
  const startMutation = useStartResearch();
  const { data: job, refetch } = useResearchJob(jobId);

  // Poll job status every 5 seconds while running
  useEffect(() => {
    if (!jobId) return;
    const interval = setInterval(() => {
      refetch();
    }, 5000);
    return () => clearInterval(interval);
  }, [jobId, refetch]);

  useEffect(() => {
    if (!job) return;
    // Log job status changes. Use the id field from the response rather than
    // job_id (the backend serialises ``id`` as the key).
    const lastLog = logs[logs.length - 1];
    const statusMessage = `Job ${job.id} status: ${job.status}`;
    if (!lastLog || lastLog.message !== statusMessage) {
      setLogs((prev) => [...prev, { time: new Date(), message: statusMessage }]);
    }
    if (job.status !== 'running') {
      // job finished
      setLogs((prev) => [...prev, { time: new Date(), message: 'Research completed' }]);
    }
  }, [job]);

  const handleStart = async () => {
    try {
      setLogs([]);
      const res = await startMutation.mutateAsync({ segment, max_companies: maxCompanies });
      setJobId(res.id);
      setLogs([{ time: new Date(), message: `Started research for segment: ${segment}` }]);
    } catch (e) {
      setLogs([{ time: new Date(), message: (e as Error).message }]);
    }
  };

  return (
    <div className="space-y-6 max-w-3xl mx-auto">
      <h1 className="text-2xl font-bold text-neutral-900">Research Lab</h1>
      <p className="text-sm text-neutral-500">Define a market segment for the agent to explore and profile competitors.</p>
        <div className="bg-white p-6 rounded-lg shadow space-y-4">
        <div>
          <label className="block text-sm font-medium text-neutral-700 mb-1">Research objective / market segment</label>
          <input
            type="text"
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-brand focus:ring-brand text-sm"
            placeholder="e.g. learning management systems for universities in Europe"
            value={segment}
            onChange={(e) => setSegment(e.target.value)}
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-neutral-700 mb-1">Max companies</label>
          <input
            type="number"
            min={1}
            max={50}
            className="mt-1 block w-32 rounded-md border-gray-300 shadow-sm focus:border-brand focus:ring-brand text-sm"
            value={maxCompanies}
            onChange={(e) => setMaxCompanies(Number(e.target.value))}
          />
        </div>
        <button
          onClick={handleStart}
          disabled={!segment || startMutation.isLoading}
          className="inline-flex items-center px-4 py-2 rounded-md text-sm font-medium text-white bg-brand hover:bg-brand-dark disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {startMutation.isLoading ? 'Agent running…' : 'Start research'}
        </button>
      </div>
      {/* Agent status log */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-lg font-semibold mb-2 text-neutral-900">Agent Status</h2>
        <div className="max-h-64 overflow-y-auto space-y-1">
          {logs.map((log, idx) => (
            <div key={idx} className="text-sm text-neutral-700">
              <span className="text-xs text-neutral-400 mr-2">{log.time.toLocaleTimeString()}</span>
              {log.message}
            </div>
          ))}
          {logs.length === 0 && <div className="text-sm text-neutral-500">No activity yet.</div>}
        </div>
      </div>
      {/* Job companies list */}
      {job && job.companies.length > 0 && (
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-lg font-semibold mb-2 text-neutral-900">Discovered companies</h2>
          <table className="min-w-full divide-y divide-gray-200">
            <thead>
              <tr className="bg-gray-50 text-xs text-neutral-500 uppercase tracking-wider">
                <th className="px-4 py-2 text-left">Name</th>
                <th className="px-4 py-2 text-left">Status</th>
                <th className="px-4 py-2 text-left">Last updated</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {job.companies.map((c) => (
                <tr key={c.id}>
                  <td className="px-4 py-2 text-sm text-neutral-900">{c.name}</td>
                  <td className="px-4 py-2 text-sm text-neutral-700 capitalize">{c.status}</td>
                  <td className="px-4 py-2 text-sm text-neutral-700">
                    {c.last_updated ? new Date(c.last_updated).toLocaleString() : '–'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}