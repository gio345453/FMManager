"""
Progress Tracker per simulazioni Monte Carlo
Versione semplice senza parallelismo
"""

class ProgressTracker:
    def __init__(self):
        self.reset()

    def reset(self):
        """Reset del progresso"""
        self.total_simulations = 0
        self.completed_simulations = 0
        self.message = ""
        self.is_running = False
        self.error = None
        self.progress = 0.0
        self.scenario_completed = {}

    def start(self, total_simulations, total_scenarios=3):
        """Avvia tracking"""
        self.reset()
        self.total_simulations = total_simulations
        self.total_scenarios = total_scenarios
        self.current_scenario = 0
        self.scenario_completed = {}
        self.progress = 0.0
        self.is_running = True
        self.message = "Inizializzazione..."

    def update(self, scenario, completed, total, progress):
        """
        Aggiorna progresso dalla queue inter-processo.

        Args:
            scenario: Scenario corrente (1-3)
            completed: Simulazioni completate in questo scenario
            total: Totale simulazioni globale
            progress: Progresso percentuale (0-100)
        """
        self.current_scenario = scenario
        self.total_simulations = total

        # Ogni scenario gira in parallelo: memorizziamo il massimo
        # completato osservato per ciascuno scenario e sommiamo i 3 valori.
        previous = self.scenario_completed.get(scenario, 0)
        self.scenario_completed[scenario] = max(previous, int(completed))

        self.completed_simulations = sum(self.scenario_completed.values())
        self.progress = (
            min(100.0, (self.completed_simulations / self.total_simulations) * 100.0)
            if self.total_simulations > 0 else 0.0
        )

        self.message = (
            f"Scenario {scenario}/{self.total_scenarios} in corso • "
            f"{self.completed_simulations}/{self.total_simulations} simulazioni"
        )

    def complete(self):
        """Marca come completato"""
        self.completed_simulations = self.total_simulations
        self.progress = 100.0
        self.is_running = False
        self.message = "Completato"

    def set_error(self, error_msg):
        """Imposta errore"""
        self.error = error_msg
        self.is_running = False

    def get_progress(self):
        """Ottieni il progresso globale aggregato dei 3 scenari."""
        return int(max(0.0, min(100.0, self.progress)))

    def get_status(self):
        """Ottieni status completo"""
        return {
            'progress': self.get_progress(),
            'completed': self.completed_simulations,
            'total': self.total_simulations,
            'message': self.message,
            'is_running': self.is_running,
            'error': self.error,
            'current_scenario': getattr(self, 'current_scenario', 0)
        }


# Istanza globale
progress_tracker = ProgressTracker()
