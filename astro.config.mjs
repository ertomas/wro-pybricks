import { defineConfig } from 'astro/config';
import tailwind from '@astrojs/tailwind';

// ⚠️ Cambia estos valores antes de hacer deploy:
// site: tu URL de GitHub Pages (https://TU_USUARIO.github.io)
// base: el nombre del repositorio (/wro-pybricks)
const isProd = process.env.NODE_ENV === 'production';

export default defineConfig({
  site: 'https://ertomas.github.io',
  base: isProd ? '/wro-pybricks' : '/',
  integrations: [tailwind()],
});
