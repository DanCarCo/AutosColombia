import { Component, DestroyRef, inject, signal } from '@angular/core';
import { Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { AuthService } from './services/auth.service';

const FORMATO_FECHA = new Intl.DateTimeFormat('es-CO', {
  day: 'numeric',
  month: 'short',
  hour: '2-digit',
  minute: '2-digit',
  timeZone: 'America/Bogota',
});

@Component({
  selector: 'app-root',
  imports: [RouterLink, RouterLinkActive, RouterOutlet],
  templateUrl: './app.html',
  styleUrl: './app.css',
})
export class App {
  readonly auth = inject(AuthService);
  private readonly router = inject(Router);
  readonly fechaActual = signal(this.formatearFecha());

  constructor() {
    const intervalo = setInterval(() => this.fechaActual.set(this.formatearFecha()), 30000);
    inject(DestroyRef).onDestroy(() => clearInterval(intervalo));
  }

  private formatearFecha(): string {
    return `${FORMATO_FECHA.format(new Date())} · Colombia`;
  }

  iniciales(nombre: string): string {
    return nombre
      .trim()
      .split(/\s+/)
      .slice(0, 2)
      .map((parte) => parte[0]?.toUpperCase() ?? '')
      .join('');
  }

  cerrarSesion(): void {
    this.auth.logout();
    this.router.navigateByUrl('/login');
  }
}
