import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import './App.css';
import './app-shell.css';
import './components/common/common.css';
import { AppProvider } from './context/AppContext';
import { useBackendHeartbeat } from './hooks/useBackendHeartbeat';
import AppShell from './components/layout/AppShell';

import Dashboard from './pages/Dashboard';
import Players from './pages/Players';
import PlayerDetail from './pages/PlayerDetail';
import Teams from './pages/Teams';
import TeamDetail from './pages/TeamDetail';
import Tiratori from './pages/Tiratori';
import Compare from './pages/Compare';
import Rosa from './pages/Rosa';
import SimulaStagione from './pages/SimulaStagione';
import Favorites from './pages/Favorites';
import Settings from './pages/Settings';
import GoalkeeperRotation from './pages/GoalkeeperRotation';
import SchieraFormazione from './pages/SchieraFormazione';
import Asta from './pages/Asta';

function App() {
  useBackendHeartbeat(30000);

  return (
    <AppProvider>
      <Router>
        <AppShell>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/players" element={<Players />} />
            <Route path="/players/:id" element={<PlayerDetail />} />
            <Route path="/teams" element={<Teams />} />
            <Route path="/teams/:name" element={<TeamDetail />} />
            <Route path="/tiratori" element={<Tiratori />} />
            <Route path="/compare" element={<Compare />} />
            <Route path="/rosa" element={<Rosa />} />
            <Route path="/simula-stagione" element={<SimulaStagione />} />
            <Route path="/favorites" element={<Favorites />} />
            <Route path="/goalkeeper-rotation" element={<GoalkeeperRotation />} />
            <Route path="/schiera-formazione" element={<SchieraFormazione />} />
            <Route path="/asta" element={<Asta />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </AppShell>
      </Router>
    </AppProvider>
  );
}

export default App;
