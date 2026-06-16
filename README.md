# WRO Pybricks Challenges

Sitio de tutoriales de robótica para Tomas, Gael y Juan Marcos — WRO 2025.

Construido con [Astro](https://astro.build) + Tailwind CSS. Desplegado en GitHub Pages.

## Estructura

```
src/pages/
  index.astro              ← página principal
  profe/index.astro        ← panel del profesor (con contraseña)
  challenges/
    00-setup.astro
    01-hola-hub.astro
    02-movimiento.astro
    03-sensor-color.astro
    04-sensor-ultrasonico.astro
    05-mision-wro.astro
```

## Desarrollo local

Necesitás Node.js 18+.

```bash
npm install
npm run dev
```

Abrí http://localhost:4321

## Deploy en GitHub Pages

### 1. Crear el repositorio

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/TU_USUARIO/wro-pybricks.git
git push -u origin main
```

### 2. Actualizar astro.config.mjs

Editá el archivo y reemplazá con tu usuario real:

```js
site: 'https://TU_USUARIO.github.io',
base: '/wro-pybricks',
```

### 3. Habilitar GitHub Pages

1. Ir a Settings → Pages en tu repositorio de GitHub
2. Source: **GitHub Actions**
3. El workflow `.github/workflows/deploy.yml` se activa automáticamente en cada push a `main`

La URL pública queda: `https://TU_USUARIO.github.io/wro-pybricks`

## Cambiar la contraseña del profesor

Editá `src/pages/profe/index.astro` y buscá esta línea:

```js
const PASSWORD = 'wro2025';
```

Cambiá `'wro2025'` por la contraseña que quieras.

> La contraseña está en el código fuente (es JavaScript del lado del cliente), así que no es segura para información sensible. Para el propósito de este sitio (control de acceso básico) funciona perfectamente.
