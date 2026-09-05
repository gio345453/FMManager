"""
Session Manager per auto-shutdown del backend quando nessun client è connesso
"""

import time
import threading
import sys
import os

class SessionManager:
    def __init__(self, timeout_seconds=60):
        """
        Args:
            timeout_seconds: Secondi senza heartbeat prima di shutdown (default 60)
        """
        self.timeout_seconds = timeout_seconds
        self.last_heartbeat = time.time()
        self.shutdown_enabled = False
        self.monitor_thread = None
        self.lock = threading.Lock()

    def start_monitoring(self):
        """Avvia il thread di monitoraggio"""
        if self.monitor_thread and self.monitor_thread.is_alive():
            return

        self.shutdown_enabled = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        print(f"[SessionManager] Monitoraggio avviato - auto-shutdown dopo {self.timeout_seconds}s di inattività")

    def stop_monitoring(self):
        """Ferma il monitoraggio"""
        self.shutdown_enabled = False
        print("[SessionManager] Monitoraggio fermato")

    def heartbeat(self):
        """Registra un heartbeat dal client"""
        with self.lock:
            self.last_heartbeat = time.time()

    def _monitor_loop(self):
        """Loop di monitoraggio (esegue in thread separato)"""
        while self.shutdown_enabled:
            time.sleep(5)  # Controlla ogni 5 secondi

            with self.lock:
                elapsed = time.time() - self.last_heartbeat

            if elapsed > self.timeout_seconds:
                print(f"\n[SessionManager] Nessun heartbeat da {elapsed:.0f}s - shutdown automatico...")
                self._shutdown()
                break

    def _shutdown(self):
        """Esegue lo shutdown del server"""
        print("[SessionManager] Chiusura server...")

        # Prova a killare processi su porte specifiche (opzionale)
        try:
            import psutil
            current_pid = os.getpid()
            current_process = psutil.Process(current_pid)

            # Uccidi processo corrente
            print(f"[SessionManager] Killing PID {current_pid}")
            current_process.terminate()

        except ImportError:
            print("[SessionManager] psutil non installato - shutdown semplice")
            pass
        except Exception as e:
            print(f"[SessionManager] Errore durante shutdown: {e}")

        # Exit forzato
        os._exit(0)


# Istanza globale
session_manager = SessionManager(timeout_seconds=60)
