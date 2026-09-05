/**
 * Format titolarità value for display
 * Backend returns value as percentage already (e.g., 90 = 90%)
 */
export function formatTitolarita(value) {
  if (value === null || value === undefined) return 'IND';
  // Value is already a percentage (90 = 90%), just format it
  return `${value.toFixed(0)}%`;
}

/**
 * Get role badge colors with support for all role variations
 * including C(T), C (T), D(E), D (E), etc.
 */
export function getRoleColors(role) {
  // Normalizza il ruolo rimuovendo spazi prima delle parentesi
  const normalizedRole = role ? role.replace(/\s+\(/g, '(').trim() : '';

  const colors = {
    'P': { bg: '#FFB000', text: '#0B0E14' },      // Yellow
    'D': { bg: '#22C55E', text: '#0B0E14' },      // Green
    'D(E)': { bg: '#22C55E', text: '#0B0E14' },   // Green (same as D)
    'C': { bg: '#3B82F6', text: '#F8FAFC' },      // Blue
    'C(T)': { bg: '#8B5CF6', text: '#F8FAFC' },   // Purple/Violet
    'C(E)': { bg: '#3B82F6', text: '#F8FAFC' },   // Blue (same as C)
    'A': { bg: '#EF4444', text: '#F8FAFC' },      // Red
  };

  return colors[normalizedRole] || { bg: '#1E293B', text: '#F8FAFC' };
}
