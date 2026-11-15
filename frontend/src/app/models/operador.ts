export const TURNOS = ['DIA', 'NOCHE'] as const;
export type Turno = (typeof TURNOS)[number];
export const ROLES = ['ADMINISTRADOR', 'OPERADOR'] as const;
export type Rol = (typeof ROLES)[number];
export interface OperadorCrear {
  nombre: string;
  telefono: string;
  usuario: string;
  password: string;
  turno: Turno;
  rol: Rol;
}
export type OperadorActualizar = Partial<OperadorCrear>;
export interface Operador {
  id: number;
  nombre: string;
  telefono: string;
  usuario: string;
  turno: Turno;
  rol: Rol;
}
export interface OperadoresPagina {
  items: Operador[];
  total: number;
  offset: number;
  limit: number;
}
