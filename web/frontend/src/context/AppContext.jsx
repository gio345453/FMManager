import React, { createContext, useState, useEffect, useContext } from 'react';
import { playersApi, utilityApi, teamsApi } from '../api/client';

const AppContext = createContext();

export const useAppContext = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useAppContext must be used within AppProvider');
  }
  return context;
};

export const AppProvider = ({ children }) => {
  const [players, setPlayers] = useState([]);
  const [favorites, setFavorites] = useState([]);
  const [teams, setTeams] = useState([]);
  const [tags, setTags] = useState([]);
  const [statuses, setStatuses] = useState([]);
  const [settings, setSettings] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Pre-carica tutti i dati all'avvio
  useEffect(() => {
    loadInitialData();
  }, []);

  const loadInitialData = async () => {
    try {
      setLoading(true);

      // Prima carica le settings per ottenere il budget
      const settingsRes = await fetch('/api/settings');
      const settingsData = await settingsRes.json();
      setSettings(settingsData);

      const budget = settingsData.budget || 500;

      const [playersRes, favoritesRes, teamsRes, tagsRes, statusesRes] = await Promise.all([
        playersApi.getAll({ budget }),
        utilityApi.getFavorites(),
        teamsApi.getTeamsList(),
        utilityApi.getTags(),
        utilityApi.getStatuses(),
      ]);

      setPlayers(playersRes.data);
      setFavorites(favoritesRes.data);
      setTeams(teamsRes.data);
      setTags(tagsRes.data);
      setStatuses(statusesRes.data);
      setLoading(false);
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  };

  const refreshPlayers = async (filters = {}) => {
    try {
      const budget = settings?.budget || 500;
      const params = { budget, ...filters };
      const res = await playersApi.getAll(params);
      setPlayers(res.data);
    } catch (err) {
      setError(err.message);
    }
  };

  const reloadAfterSettingsChange = async () => {
    try {
      // Ricarica settings
      const settingsRes = await fetch('/api/settings');
      const settingsData = await settingsRes.json();
      setSettings(settingsData);

      // Ricarica giocatori con nuovo budget
      const budget = settingsData.budget || 500;
      const res = await playersApi.getAll({ budget });
      setPlayers(res.data);
    } catch (err) {
      setError(err.message);
    }
  };

  const toggleFavorite = async (playerId) => {
    try {
      await playersApi.toggleFavorite(playerId);

      // Aggiorna lista preferiti
      setFavorites(prevFavorites =>
        prevFavorites.includes(playerId)
          ? prevFavorites.filter(id => id !== playerId)
          : [...prevFavorites, playerId]
      );

      // Aggiorna stato is_favorite nei giocatori
      setPlayers(prevPlayers =>
        prevPlayers.map(p =>
          p.id === playerId ? { ...p, is_favorite: !p.is_favorite } : p
        )
      );
    } catch (err) {
      setError(err.message);
    }
  };

  const value = {
    players,
    favorites,
    teams,
    tags,
    statuses,
    settings,
    loading,
    error,
    refreshPlayers,
    reloadAfterSettingsChange,
    toggleFavorite,
    reloadData: loadInitialData,
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
};