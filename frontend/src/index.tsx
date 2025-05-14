import React from 'react'
import ReactDOM from 'react-dom/client'

// Temporary App component until proper structure is in place
function App() {
  return (
    <React.StrictMode>
      <div>
        <h1>Welcome to Skyent</h1>
        <p>Frontend (React + TypeScript + Vite)</p>
      </div>
    </React.StrictMode>
  );
}

ReactDOM.createRoot(document.getElementById('root')!).render(<App />);
