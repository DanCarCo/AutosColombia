import { Celda } from './celda';
import { Vehiculo } from './vehiculo';

// El operador que actúa se toma del token de sesión (RF-16); ya no viaja aquí.
export interface EntradaCrear {
  placa: string;
  celda_id: number;
}
export interface SalidaCrear {
  placa: string;
}
export interface CambiarCeldaCrear {
  placa: string;
  celda_id: number;
}
export interface Estancia {
  id: number;
  vehiculo_id: number;
  celda_id: number;
  entrada: string;
  salida: string | null;
  operador_entrada_id: number;
  operador_salida_id: number | null;
}
export interface EstadoVehiculo {
  vehiculo: Vehiculo;
  esta_dentro: boolean;
  estancia: (Estancia & { celda: Celda }) | null;
}
