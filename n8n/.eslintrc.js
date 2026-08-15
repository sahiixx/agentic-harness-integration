module.exports = {
  root: true,
  parser: '@typescript-eslint/parser',
  plugins: ['eslint-plugin-n8n-nodes-base'],
  extends: ['plugin:n8n-nodes-base/recommended'],
  rules: {
    'n8n-nodes-base/cred-class-field-name-omit-oauth2': 'off',
  },
};
