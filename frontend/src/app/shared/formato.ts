// Formato de valores para las pantallas de pagos (RF-14, RF-19): pesos colombianos y hora de Bogotá.
const FORMATO_COP = new Intl.NumberFormat('es-CO', {
  style: 'currency',
  currency: 'COP',
  maximumFractionDigits: 0,
});

const FORMATO_FECHA_HORA = new Intl.DateTimeFormat('es-CO', {
  day: '2-digit',
  month: 'short',
  year: 'numeric',
  hour: '2-digit',
  minute: '2-digit',
  timeZone: 'America/Bogota',
});

const FORMATO_DIA = new Intl.DateTimeFormat('en-CA', {
  year: 'numeric',
  month: '2-digit',
  day: '2-digit',
  timeZone: 'America/Bogota',
});

export function formatoCop(valor: string | number): string {
  const numero = Number(valor);
  return Number.isFinite(numero) ? FORMATO_COP.format(numero) : String(valor);
}

export function fechaHoraBogota(iso: string): string {
  const fecha = new Date(iso);
  return Number.isNaN(fecha.getTime()) ? iso : FORMATO_FECHA_HORA.format(fecha);
}

// «AAAA-MM-DD» del instante dado, en la zona America/Bogota (para comparar con un <input type="date">).
export function diaBogota(iso: string): string {
  const fecha = new Date(iso);
  return Number.isNaN(fecha.getTime()) ? '' : FORMATO_DIA.format(fecha);
}
