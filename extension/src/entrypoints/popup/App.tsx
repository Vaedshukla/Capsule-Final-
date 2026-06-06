import { useState, useEffect } from 'react';

type Project = {
  id: string;
  name: string;
};

export default function App() {
  const [backendUrl, setBackendUrl] = useState('http://localhost:8000');
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>('');
  const [status, setStatus] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  
  const [isCreatingProject, setIsCreatingProject] = useState(false);
  const [newProjectName, setNewProjectName] = useState('');

  // 1. Load backend URL from storage first
  useEffect(() => {
    chrome.storage.sync.get(['backendUrl'], (result) => {
      if (result.backendUrl) {
        setBackendUrl(result.backendUrl);
      }
    });
  }, []);

  // 2. Fetch projects once backendUrl is known
  useEffect(() => {
    if (!backendUrl) return;
    fetchProjects();
  }, [backendUrl]);

  const fetchProjects = () => {
    fetch(`${backendUrl}/api/v1/projects/`)
      .then(res => res.json())
      .then((data: Project[]) => {
        setProjects(data);
        if (data.length > 0 && !selectedProjectId) {
          setSelectedProjectId(data[0].id);
        }
      })
      .catch(err => {
        console.error('Failed to fetch projects', err);
        setStatus('❌ Failed to fetch projects. Check your API settings in Options.');
      });
  };

  const handleCreateProject = async () => {
    if (!newProjectName.trim()) return;
    setLoading(true);
    setStatus('Creating project...');
    try {
      const res = await fetch(`${backendUrl}/api/v1/projects/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: newProjectName })
      });
      if (!res.ok) throw new Error('Failed to create project');
      const newProj = await res.json();
      setProjects([...projects, newProj]);
      setSelectedProjectId(newProj.id);
      setNewProjectName('');
      setIsCreatingProject(false);
      setStatus('✅ Project created!');
    } catch (e: any) {
      setStatus(`❌ Error: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleCapture = async () => {
    setLoading(true);
    setStatus('Capturing from active tab...');
    
    try {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      if (!tab.id) throw new Error('No active tab found.');

      // Send message to content script
      const response = await new Promise<any>((resolve) => {
        chrome.tabs.sendMessage(tab.id!, { type: 'CAPTURE_REQUEST' }, (res) => {
          resolve(res);
        });
      });

      if (!response || !response.success) {
        throw new Error(response?.error || 'Content script did not respond. Are you on a supported AI site?');
      }

      setStatus('Sending to Project Capsule backend...');

      // Dynamic payload from content script
      const payload = {
        source: response.data.source,
        project_hint: null,
        url: response.data.url,
        title: response.data.title,
        messages: response.data.messages
      };

      const ingestRes = await fetch(`${backendUrl}/api/v1/ingest/conversation?project_id=${selectedProjectId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!ingestRes.ok) {
        let errDetail = 'Unknown Error';
        try {
          const errJson = await ingestRes.json();
          errDetail = errJson.detail || errDetail;
        } catch (e) {
          errDetail = await ingestRes.text();
        }
        if (ingestRes.status === 409) {
          throw new Error(`Already Captured: ${errDetail}`);
        }
        throw new Error(`Backend error: ${errDetail}`);
      }

      setStatus('✅ Success! Conversation ingested.');
    } catch (err: any) {
      console.error(err);
      setStatus(`❌ Error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-80 p-4 font-sans bg-gray-50 text-gray-900 flex flex-col gap-4">
      <div className="flex justify-between items-center">
        <h1 className="text-xl font-bold text-gray-800">Project Capsule</h1>
        <button 
          onClick={() => chrome.runtime.openOptionsPage()}
          className="text-gray-500 hover:text-gray-800"
          title="Settings"
        >
          ⚙️
        </button>
      </div>
      
      <div>
        <div className="flex justify-between items-center mb-1">
          <label className="block text-sm font-medium text-gray-700">Project</label>
          <button 
            onClick={() => setIsCreatingProject(!isCreatingProject)}
            className="text-xs text-blue-600 hover:text-blue-800"
          >
            {isCreatingProject ? 'Cancel' : '+ New'}
          </button>
        </div>
        
        {isCreatingProject ? (
          <div className="flex gap-2">
            <input 
              type="text" 
              className="w-full border border-gray-300 rounded-md p-1"
              placeholder="Project Name"
              value={newProjectName}
              onChange={e => setNewProjectName(e.target.value)}
            />
            <button 
              onClick={handleCreateProject}
              disabled={loading || !newProjectName}
              className="bg-green-600 hover:bg-green-700 text-white px-2 py-1 rounded text-sm disabled:opacity-50"
            >
              Save
            </button>
          </div>
        ) : (
          <select 
            className="w-full border border-gray-300 rounded-md shadow-sm p-2 bg-white"
            value={selectedProjectId}
            onChange={(e) => setSelectedProjectId(e.target.value)}
          >
            {projects.map(p => (
              <option key={p.id} value={p.id}>{p.name}</option>
            ))}
          </select>
        )}
      </div>

      <button
        onClick={handleCapture}
        disabled={loading || projects.length === 0 || isCreatingProject}
        className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded disabled:opacity-50 transition-colors"
      >
        {loading ? 'Processing...' : 'Capture Conversation'}
      </button>

      {status && (
        <div className="p-2 text-sm rounded bg-gray-100 border border-gray-200 break-words">
          {status}
        </div>
      )}
    </div>
  );
}
