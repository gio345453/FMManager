/**
 * Utility per gestire immagini giocatori e loghi squadre
 * Usa il CDN pubblico di Fantacalcio.it
 */

const CDN = "https://content.fantacalcio.it/web";
const CAMPIONCINI_SET = "21"; // Aggiorna per stagione 2026-27 se necessario
const PLAYER_SIZES = { small: "small", medium: "medium", card: "card" };

export const MEDIA_STORAGE_KEY = "fanta-player-media";

/**
 * Genera URL per l'immagine di un giocatore
 * @param {number|string} playerId - ID del giocatore
 * @param {string} size - Dimensione: "small" (32px), "medium" (72px), "card" (grande)
 * @returns {string|null} URL dell'immagine o null
 */
export const playerImageUrl = (playerId, size = "small") => {
  if (playerId === null || playerId === undefined || playerId === "") {
    return null;
  }
  const cut = PLAYER_SIZES[size] || PLAYER_SIZES.small;
  return `${CDN}/campioncini/${CAMPIONCINI_SET}/${cut}/${encodeURIComponent(playerId)}.png`;
};

/**
 * Genera URL per il logo di una squadra
 * @param {string} teamName - Nome squadra (es. "Inter", "Milan")
 * @returns {string|null} URL del logo o null
 */
export const teamLogoUrl = (teamName) => {
  if (!teamName || teamName === "Unknown") {
    return null;
  }
  // Mappa nomi squadre -> ID per il CDN
  const teamIdMap = {
    "Atalanta": "atalanta",
    "Bologna": "bologna",
    "Cagliari": "cagliari",
    "Como": "como",
    "Empoli": "empoli",
    "Fiorentina": "fiorentina",
    "Frosinone": "frosinone",
    "Genoa": "genoa",
    "Inter": "inter",
    "Juventus": "juventus",
    "Lazio": "lazio",
    "Lecce": "lecce",
    "Milan": "milan",
    "Monza": "monza",
    "Napoli": "napoli",
    "Parma": "parma",
    "Roma": "roma",
    "Salernitana": "salernitana",
    "Sassuolo": "sassuolo",
    "Torino": "torino",
    "Udinese": "udinese",
    "Venezia": "venezia",
    "Verona": "verona",
  };

  const teamId = teamIdMap[teamName];
  return teamId ? `${CDN}/img/team/${encodeURIComponent(teamId)}.png` : null;
};

/**
 * Legge la preferenza utente per mostrare le immagini
 * @returns {boolean} true se l'utente vuole vedere le immagini
 */
export const readMediaPreference = () => {
  try {
    const value = localStorage.getItem(MEDIA_STORAGE_KEY);
    // Default: true (mostra immagini)
    return value === null ? true : value === "on";
  } catch {
    return true;
  }
};

/**
 * Salva la preferenza utente per mostrare le immagini
 * @param {boolean} enabled - true per mostrare, false per nascondere
 */
export const writeMediaPreference = (enabled) => {
  try {
    localStorage.setItem(MEDIA_STORAGE_KEY, enabled ? "on" : "off");
  } catch {
    // Ignore localStorage errors
  }
};
