import { useEffect } from 'react';

/**
 * Hook per mantenere attivo il backend con heartbeat periodici
 * Il backend si spegnerà automaticamente dopo 60s senza heartbeat (se avviato con --auto-shutdown)
 */
export function useBackendHeartbeat(intervalMs = 30000) {
  useEffect(() => {
    // Invia heartbeat iniziale
    sendHeartbeat();

    // Avvia heartbeat periodico
    const heartbeatInterval = setInterval(() => {
      sendHeartbeat();
    }, intervalMs);

    // Cleanup: ferma heartbeat quando componente viene smontato (pagina chiusa)
    return () => {
      clearInterval(heartbeatInterval);
      console.log('[Heartbeat] Stopped - backend will auto-shutdown in 60s if no other clients');
    };
  }, [intervalMs]);
}

function sendHeartbeat() {
  fetch('/api/heartbeat', { method: 'POST' })
    .then(res => res.json())
    .then(data => {
      // Heartbeat successful - silenzioso
    })
    .catch(err => {
      // Backend non raggiungibile - normale quando il backend non è avviato
      console.log('[Heartbeat] Backend not reachable');
    });
}
