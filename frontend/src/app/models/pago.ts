export interface PagoCrear {
  vehiculo_id: number;
  // El periodo lo calcula el servidor (RF-14): no es un dato de entrada.
}
export interface Pago {
  id: number;
  vehiculo_id: number;
  operador_id: number;
  monto: string | number;
  periodo_inicio: string;
  periodo_fin: string;
  fecha_pago: string;
}
export interface PagosPagina {
  items: Pago[];
  total: number;
  offset: number;
  limit: number;
}
export interface MensualidadEstado {
  vehiculo_id: number;
  vigente: boolean;
  pago: Pago | null;
}
export interface ResumenReporte {
  celdas_totales: number;
  celdas_disponibles: number;
  clientes_registrados: number;
}
