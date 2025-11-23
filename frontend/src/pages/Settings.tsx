import { useEffect, useState } from 'react';

// Read current config from localStorage or env
function getInitialBaseUrl() {
  return (
    localStorage.getItem('apiBaseUrl') || (import.meta.env.VITE_API_BASE_URL as string) || ''
  );
}

function getInitialApiKey() {
  return (
    localStorage.getItem('apiKey') || (import.meta.env.VITE_INTERNAL_API_KEY as string) || ''
  );
}

export default function Settings() {
  const [baseUrl, setBaseUrl] = useState(getInitialBaseUrl());
  const [apiKey, setApiKey] = useState(getInitialApiKey());
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    setBaseUrl(getInitialBaseUrl());
    setApiKey(getInitialApiKey());
  }, []);

  const handleSave = () => {
    if (baseUrl) {
      localStorage.setItem('apiBaseUrl', baseUrl);
    } else {
      localStorage.removeItem('apiBaseUrl');
    }
    if (apiKey) {
      localStorage.setItem('apiKey', apiKey);
    } else {
      localStorage.removeItem('apiKey');
    }
    setSaved(true);
    // hide saved message after 2 seconds
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div className="space-y-6 max-w-xl">
      <h1 className="text-2xl font-bold text-neutral-900">Settings</h1>
      <p className="text-sm text-neutral-500">
        Configure how the frontend communicates with the backend. Changes here are saved
        locally in your browser and applied immediately to future requests.
      </p>
      <div className="bg-white p-6 rounded-lg shadow space-y-4">
        <div>
          <label className="block text-sm font-medium text-neutral-700 mb-1" htmlFor="base-url">
            API base URL
          </label>
          <input
            id="base-url"
            type="text"
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-brand focus:ring-brand text-sm"
            placeholder="http://127.0.0.1:8000"
            value={baseUrl}
            onChange={(e) => setBaseUrl(e.target.value)}
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-neutral-700 mb-1" htmlFor="api-key">
            Internal API key
          </label>
          <input
            id="api-key"
            type="text"
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-brand focus:ring-brand text-sm"
            placeholder="Not required unless backend enforces it"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
          />
        </div>
        <button
          onClick={handleSave}
          className="inline-flex items-center px-4 py-2 rounded-md text-sm font-medium text-white bg-brand hover:bg-brand-dark"
        >
          Save settings
        </button>
        {saved && (
          <div className="text-sm text-green-600 mt-2">Settings saved.</div>
        )}
      </div>
    </div>
  );
}