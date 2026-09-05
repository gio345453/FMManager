import axios from 'axios';

const API_BASE_URL = ' /api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const playersApi = {
  getAll: (params = {}) =>
    apiClient.get('/players', { params }),

  getById: (id, budget = 500) =>
    apiClient.get(`/players/${id}`, {
      params: { budget },
    }),

  compare: (ids, budget = 500) =>
    apiClient.get('/players/compare', {
      params: { ids, budget },
    }),

  recommend: (selectedIds = null, budget = 500, limit = 5) => {
    const params = {
      budget,
      limit,
    };

    if (selectedIds) {
      params.selected_ids = selectedIds;
    }

    return apiClient.get('/players/recommend', {
      params,
    });
  },

  toggleFavorite: (id) =>
    apiClient.post(`/players/${id}/favorite`),

  getNotes: (id) =>
    apiClient.get(`/players/${id}/notes`),

  updateNotes: (id, data) =>
    apiClient.put(`/players/${id}/notes`, data),
};

export const teamsApi = {
  getAll: () =>
    apiClient.get('/teams'),

  getByName: (name) =>
    apiClient.get(`/teams/${name}`),

  getDashboard: (name, includeRoster = false) =>
    apiClient.get(`/teams/${name}/dashboard`, {
      params: {
        include_roster: includeRoster,
      },
    }),

  getTeamsList: () =>
    apiClient.get('/teams/list'),

  getNeopromosse: () =>
    apiClient.get('/teams/neopromosse'),
};

export const optimizerApi = {
  buildRosa: (data) =>
    apiClient.post('/optimizer/build-rosa', data),
};

export const lineupApi = {
  getFormations: () =>
    apiClient.get('/lineup/formations'),

  recommend: (data) =>
    apiClient.post('/lineup/recommend', data),
};

export const utilityApi = {
  health: () =>
    apiClient.get('/health'),

  getFavorites: () =>
    apiClient.get('/favorites'),

  getTags: () =>
    apiClient.get('/tags'),

  getStatuses: () =>
    apiClient.get('/statuses'),
};

export const auctionApi = {
  getState: () =>
    apiClient.get('/auction/state'),

  initialize: (data) =>
    apiClient.post('/auction/initialize', data),

  getPlayers: () =>
    apiClient.get('/auction/players'),

  getTeams: () =>
    apiClient.get('/auction/teams'),

  start: () =>
    apiClient.post('/auction/start'),

  setPhase: (phase) =>
    apiClient.post('/auction/phase', {
      phase,
    }),

  open: (playerId) =>
    apiClient.post('/auction/open', {
      player_id: playerId,
    }),

  bid: (teamId, price) =>
    apiClient.post('/auction/bid', {
      team_id: teamId,
      price,
    }),

  assign: () =>
    apiClient.post('/auction/assign'),

  undo: () =>
    apiClient.post('/auction/undo'),

  redo: () =>
    apiClient.post('/auction/redo'),

  reset: () =>
    apiClient.post('/auction/reset'),

  advice: (
    playerId,
    teamId,
    currentPrice = null,
    signal = undefined
  ) =>
    apiClient.get('/auction/advice', {
      signal,
      params: {
        player_id: playerId,
        team_id: teamId,
        ...(currentPrice !== null &&
        currentPrice !== undefined
          ? {
              current_price: currentPrice,
            }
          : {}),
      },
    }),

  overview: (teamId) =>
    apiClient.get('/auction/overview', {
      params: {
        team_id: teamId,
      },
    }),

  getLeagueCalendar: () =>
    apiClient.get('/league-calendar'),

  /**
   * Carica il calendario lega personale.
   *
   * Il backend deve accettare multipart/form-data
   * sul relativo endpoint.
   */
  uploadLeagueCalendar: (file, signal = undefined) => {
    const formData = new FormData();
    formData.append('file', file);

    return apiClient.post('/league-calendar/upload', formData, {
      signal,
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },
};

export default apiClient;