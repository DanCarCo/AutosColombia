import { HttpErrorResponse } from '@angular/common/http';
import { Component, DestroyRef, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormBuilder, ReactiveFormsModule, ValidatorFn } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { AuthService } from '../services/auth.service';

const nonBlank: ValidatorFn = (control) =>
  typeof control.value === 'string' && control.value.trim() ? null : { required: true };

@Component({
  selector: 'app-login',
  imports: [ReactiveFormsModule, RouterLink],
  templateUrl: './login.html',
  styleUrls: ['./login.css', '../shared/gestion-tema.css'],
})
export class Login {
  private readonly auth = inject(AuthService);
  private readonly fb = inject(FormBuilder);
  private readonly destroyRef = inject(DestroyRef);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);
  readonly form = this.fb.group({
    usuario: this.fb.nonNullable.control('', nonBlank),
    password: this.fb.nonNullable.control('', nonBlank),
  });
  readonly saving = signal(false);
  readonly error = signal('');

  entrar(): void {
    if (this.saving()) return;
    this.form.markAllAsTouched();
    if (this.form.invalid) return;
    const { usuario, password } = this.form.getRawValue();
    this.saving.set(true);
    this.error.set('');
    this.auth
      .login({ usuario: usuario.trim(), password })
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: () => {
          this.saving.set(false);
          const volver = this.route.snapshot.queryParamMap.get('volver');
          this.router.navigateByUrl(volver || '/control-acceso');
        },
        error: (error: HttpErrorResponse) => {
          this.saving.set(false);
          this.error.set(this.mensaje(error));
        },
      });
  }

  private mensaje(error: HttpErrorResponse): string {
    if (error.status === 401) return 'Usuario o contraseña incorrectos.';
    if (error.status === 422) return 'Escribe tu usuario y tu contraseña.';
    return 'No se pudo conectar con el servicio. Comprueba la conexión e inténtalo de nuevo.';
  }
}
