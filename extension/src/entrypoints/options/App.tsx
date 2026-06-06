import { useState, useEffect } from 'react';

export default function App() {
  const [backendUrl, setBackendUrl] = useState('http://localhost:8000');
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    chrome.storage.sync.get(['backendUrl'], (result) => {
      if (result.backendUrl) {
        setBackendUrl(result.backendUrl);
      }
    });
  }, []);

  const handleSave = () => {
    // Basic validation to strip trailing slash
    let finalUrl = backendUrl.trim();
    if (finalUrl.endsWith('/')) {
      finalUrl = finalUrl.slice(0, -1);
    }
    
    chrome.storage.sync.set({ backendUrl: finalUrl }, () => {
      setBackendUrl(finalUrl);
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    });
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8 bg-white p-8 rounded-xl shadow-md border border-gray-100">
        <div>
          <h2 className="text-center text-3xl font-extrabold text-gray-900">
            Project Capsule Settings
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Configure your connection to the Capsule Backend.
          </p>
        </div>
        <div className="mt-8 space-y-6">
          <div className="rounded-md shadow-sm -space-y-px">
            <div>
              <label htmlFor="backend-url" className="block text-sm font-medium text-gray-700">
                Backend API URL
              </label>
              <input
                id="backend-url"
                name="url"
                type="text"
                required
                className="mt-1 appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
                placeholder="http://localhost:8000"
                value={backendUrl}
                onChange={(e) => setBackendUrl(e.target.value)}
              />
              <p className="mt-1 text-xs text-gray-500">Do not include /api/v1 at the end.</p>
            </div>
          </div>

          <div>
            <button
              onClick={handleSave}
              className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              {saved ? 'Saved Successfully!' : 'Save Configuration'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
