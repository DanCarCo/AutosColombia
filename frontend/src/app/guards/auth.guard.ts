import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from '../services/auth.service';

// RF-16: Control de acceso exige sesión iniciada; sin token, redirige a /login
// y recuerda a dónde volver.
export const authGuard: CanActivateFn = (_route, state) => {
  if (inject(AuthService).estaAutenticado()) return true;
  return inject(Router).createUrlTree(['/login'], { queryParams: { volver: state.url } });
};
