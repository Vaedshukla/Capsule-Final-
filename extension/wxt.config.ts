import { defineConfig } from 'wxt';

export default defineConfig({
  srcDir: 'src',
  modules: ['@wxt-dev/module-react'],
  manifest: {
    name: 'Project Capsule',
    description: 'AI Workflow Memory & Context Continuity',
    permissions: ['activeTab', 'scripting', 'storage'],
    host_permissions: [
      '<all_urls>'
    ],
  },
});
