import eslintPlugin from '@eslint/js'
import nextPlugin from '@next/eslint-plugin-next'
import jsxA11yPlugin from 'eslint-plugin-jsx-a11y'
import reactPlugin from 'eslint-plugin-react'
import reactHooksPlugin from 'eslint-plugin-react-hooks'
import { defineConfig } from 'eslint/config'
import { configs as tseslintConfigs } from 'typescript-eslint'

// Global ignores configuration
const ignoresConfig = defineConfig([{
  name: 'project/ignores',
  ignores: [
    '.next/',
    'node_modules/',
    'public/',
    '.vscode/',
    'next-env.d.ts',
  ]
}])

// ESLint recommended rules for JavaScript/TypeScript
const eslintConfig = defineConfig([{
  name: 'project/javascript-recommended',
  files: ['**/*.{js,mjs,ts,tsx}'],
  ...eslintPlugin.configs.recommended,
}])

// TypeScript configuration
const typescriptConfig = defineConfig([
  {
    name: 'project/typescript-recommended',
    files: ['**/*.{ts,tsx}'],
    extends: [
      ...tseslintConfigs.recommended,
    ],
    languageOptions: {
      parserOptions: {
        ecmaFeatures: { jsx: true },
      },
    },
    rules: {
      // Allow unused vars with _ prefix
      '@typescript-eslint/no-unused-vars': ['warn', { 
        argsIgnorePattern: '^_',
        varsIgnorePattern: '^_'
      }],
      // Allow explicit any as warning
      '@typescript-eslint/no-explicit-any': 'warn',
    },
  },
  {
    name: 'project/javascript-disable-type-check',
    files: ['**/*.{js,mjs,cjs}'],
    ...tseslintConfigs.disableTypeChecked,
  }
])

// React and Next.js configuration
const reactConfig = defineConfig([{
  name: 'project/react-next',
  files: ['**/*.{jsx,tsx}'],
  plugins: {
    'react': reactPlugin,
    'react-hooks': reactHooksPlugin,
    'jsx-a11y': jsxA11yPlugin,
    '@next/next': nextPlugin,
  },
  rules: {
    // React recommended rules
    ...reactPlugin.configs.recommended.rules,
    ...reactPlugin.configs['jsx-runtime'].rules,
    // React Hooks rules
    ...reactHooksPlugin.configs['recommended-latest'].rules,
    // Accessibility rules
    ...jsxA11yPlugin.configs.recommended.rules,
    // Next.js rules
    ...nextPlugin.configs.recommended.rules,
    ...nextPlugin.configs['core-web-vitals'].rules,
    // Customizations
    'react/react-in-jsx-scope': 'off',
    'react/prop-types': 'off',
    'react-hooks/exhaustive-deps': 'warn',
    // Disable strict rules that need gradual migration
    'react-hooks/set-state-in-effect': 'off', // Common pattern in Next.js for client init
    'jsx-a11y/label-has-associated-control': 'warn',
    'jsx-a11y/click-events-have-key-events': 'warn',
    'jsx-a11y/no-noninteractive-element-interactions': 'warn',
    'jsx-a11y/no-static-element-interactions': 'warn',
  },
  settings: {
    react: { version: 'detect' },
  },
}])

// Custom project rules
const projectConfig = defineConfig([{
  name: 'project/custom-rules',
  files: ['**/*.{ts,tsx}'],
  rules: {
    'prefer-const': 'warn',
    // File size limits
    'max-lines': ['warn', { max: 300, skipBlankLines: true, skipComments: true }],
    'max-lines-per-function': ['warn', { max: 150, skipBlankLines: true, skipComments: true }],
  },
}])

export default defineConfig([
  ...ignoresConfig,
  ...eslintConfig,
  ...typescriptConfig,
  ...reactConfig,
  ...projectConfig,
])
