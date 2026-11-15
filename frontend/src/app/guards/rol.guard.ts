import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { Rol } from '../models/operador';
import { AuthService } from '../services/auth.service';

// RF-16: separa las pantallas por rol. Sin sesión redirige a /login; con un rol que no
// corresponde, a Inicio. El backend aplica el mismo control (403), este guard solo evita
// mostrar pantallas que la cuenta no podría usar.
export const rolGuard =
  (...roles: Rol[]): CanActivateFn =>
  (_route, state) => {
    const auth = inject(AuthService);
    const router = inject(Router);
    if (!auth.estaAutenticado()) {
      return router.createUrlTree(['/login'], { queryParams: { volver: state.url } });
    }
    const rol = auth.rol();
    return rol !== null && roles.includes(rol) ? true : router.createUrlTree(['/']);
  };
