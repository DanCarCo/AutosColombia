import { Operador } from './operador';

export interface LoginCrear {
  usuario: string;
  password: string;
}
export interface TokenRespuesta {
  access_token: string;
  token_type: string;
  expira_minutos: number;
  operador: Operador;
}
