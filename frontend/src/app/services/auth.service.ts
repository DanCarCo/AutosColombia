import { HttpClient } from '@angular/common/http';
import { Injectable, computed, inject, signal } from '@angular/core';
import { tap, timeout } from 'rxjs';
import { LoginCrear, TokenRespuesta } from '../models/auth';
import { Operador } from '../models/operador';
import { API_BASE_URL } from './api.service';

const STORAGE_KEY = 'autos-colombia.sesion';

function leerSesionGuardada(): TokenRespuesta | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const data = JSON.parse(raw) as TokenRespuesta;
    return data?.access_token && data?.operador ? data : null;
  } catch {
    // Almacenamiento no disponible (privado, bloqueado, etc.): se inicia sin sesión.
    return null;
  }
}

// RF-16: inicio de sesión de operadores. El token se guarda en localStorage
// (por pestaña del navegador, no es un dato sensible de servidor) y viaja en
// cada solicitud mediante el interceptor de autenticación.
@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly http = inject(HttpClient);
  private readonly base = `${inject(API_BASE_URL)}/auth`;
  private readonly sesion = signal<TokenRespuesta | null>(leerSesionGuardada());
  readonly token = computed(() => this.sesion()?.access_token ?? null);
  readonly operador = computed<Operador | null>(() => this.sesion()?.operador ?? null);
  readonly estaAutenticado = computed(() => this.sesion() !== null);

  login(data: LoginCrear) {
    return this.http.post<TokenRespuesta>(`${this.base}/login`, data).pipe(
      timeout(15000),
      tap((respuesta) => {
        this.sesion.set(respuesta);
        try {
          localStorage.setItem(STORAGE_KEY, JSON.stringify(respuesta));
        } catch {
          // Sin almacenamiento persistente, la sesión sigue activa solo en memoria.
        }
      }),
    );
  }

  logout(): void {
    this.sesion.set(null);
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch {
      // Nada que limpiar si el almacenamiento no está disponible.
    }
  }
}
