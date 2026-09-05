/**
 * Componenti per visualizzare immagini giocatori e loghi squadre
 */
import { useState, useEffect } from 'react';
import { playerImageUrl, teamLogoUrl } from '../../utils/playerMedia';
import './PlayerMedia.css';

/**
 * Avatar giocatore con fallback automatico
 * @param {number} playerId - ID del giocatore
 * @param {string} size - "small" (32px) o "medium" (72px)
 */
export function PlayerAvatar({ playerId, size = "small" }) {
  const [failed, setFailed] = useState(false);
  const url = playerImageUrl(playerId, size);

  // Reset failed state quando cambia l'URL
  useEffect(() => {
    setFailed(false);
  }, [url]);

  // Non mostrare nulla se non c'è URL o l'immagine è fallita
  if (!url || failed) {
    return null;
  }

  const box = size === "small" ? 32 : 72;

  return (
    <img
      className={`player-avatar${size === "small" ? "" : " player-avatar--lg"}`}
      src={url}
      alt=""
      width={box}
      height={box}
      loading="lazy"
      decoding="async"
      referrerPolicy="no-referrer"
      onError={() => setFailed(true)}
      style={{
        objectFit: 'contain',
        backgroundColor: 'transparent',
      }}
    />
  );
}

/**
 * Logo squadra con fallback automatico
 * @param {string} teamName - Nome della squadra
 * @param {number} size - Dimensione in pixel (default: 28)
 */
export function TeamLogo({ teamName, size = 28 }) {
  const [failed, setFailed] = useState(false);
  const url = teamLogoUrl(teamName);

  // Reset failed state quando cambia l'URL
  useEffect(() => {
    setFailed(false);
  }, [url]);

  // Non mostrare nulla se non c'è URL o l'immagine è fallita
  if (!url || failed) {
    return null;
  }

  return (
    <img
      className="team-logo"
      src={url}
      alt={teamName}
      width={size}
      height={size}
      loading="lazy"
      decoding="async"
      referrerPolicy="no-referrer"
      onError={() => setFailed(true)}
      style={{
        objectFit: 'contain',
      }}
    />
  );
}
