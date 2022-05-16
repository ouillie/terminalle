const { defaultTheme } = require('@vuepress/theme-default')

module.exports = {
  title: 'Terminalle',
  description: 'A fancy drop-down terminal emulateur.',
  base: '/terminalle/',
  theme: defaultTheme({
    repo: 'https://github.com/wm-noble/terminalle',
    docsDir: 'docs',
  }),
}
