const { defaultTheme } = require('@vuepress/theme-default')

module.exports = {
  title: 'Terminalle',
  description: 'A fancy drop-down terminal emulateur.',
  base: '/terminalle/',
  theme: defaultTheme({
    repo: 'https://github.com/wm-noble/terminalle',
    docsDir: 'docs',
  }),

  plugins: [
    {
      name: 'clean-urls',
      extendsPage: (page) => {
        if (!page.frontmatter?.permalink) {
          const { path } = page
          if (path.endsWith('.html')) {
            page.path = path.slice(0, -5)
          } else if (path.endsWith('/')) {
            page.path = path.slice(0, -1)
          }
        }
      },
    },
  ],
}
