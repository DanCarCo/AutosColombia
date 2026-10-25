export interface ClienteCrear {
  nombre: string;
  documento: string;
  telefono: string;
}
export type ClienteActualizar = Partial<ClienteCrear>;
export interface Cliente extends ClienteCrear {
  id: number;
}
export interface ClientesPagina {
  items: Cliente[];
  total: number;
  offset: number;
  limit: number;
}
