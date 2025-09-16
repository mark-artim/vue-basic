import js from '@eslint/js'
import pluginVue from 'eslint-plugin-vue'

export default [
  {
    name: 'app/files-to-lint',
    files: ['**/*.{js,mjs,jsx,vue}'],
  },

  {
    name: 'app/files-to-ignore',
    ignores: ['**/dist/**', '**/dist-ssr/**', '**/coverage/**'],
  },

  js.configs.recommended,
  ...pluginVue.configs['flat/recommended'],

  {
    languageOptions: {
      globals: {
        process: 'readonly',
        console: 'readonly',
        Buffer: 'readonly',
        __dirname: 'readonly',
        __filename: 'readonly',
        module: 'readonly',
        require: 'readonly',
        exports: 'readonly',
        global: 'readonly'
      },
      ecmaVersion: 2022,
      sourceType: 'module'
    },
    rules: {
      'vue/multi-word-component-names': 'off',
      'vue/valid-v-slot': 'warn',  // Downgrade from error to warning
      'no-unused-vars': ['error', { 
        argsIgnorePattern: '^_',   // Allow _unused parameters
        varsIgnorePattern: '^_'    // Allow _unused variables
      }],
      'no-case-declarations': 'error'
    },
  }
]
