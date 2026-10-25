export const TURNOS = ['DIA', 'NOCHE'] as const;
export type Turno = (typeof TURNOS)[number];
export interface OperadorCrear {
  nombre: string;
  telefono: string;
  usuario: string;
  password: string;
  turno: Turno;
}
export type OperadorActualizar = Partial<OperadorCrear>;
export interface Operador {
  id: number;
  nombre: string;
  telefono: string;
  usuario: string;
  turno: Turno;
}
export interface OperadoresPagina {
  items: Operador[];
  total: number;
  offset: number;
  limit: number;
}
