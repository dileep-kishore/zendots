return {
  {
    "mason-org/mason.nvim",
    dependencies = {
      "mason-org/mason-lspconfig.nvim",
      "WhoIsSethDaniel/mason-tool-installer.nvim",
    },
    opts = {
      ui = {
        border = "rounded",
      },
    },
    config = function()
      require("mason").setup()
      require("mason-lspconfig").setup({
        automatic_enable = {
          "copilot_ls",
        },
        ensure_installed = {
          -- lsp
          "lua_ls",
          "basedpyright",
          "gopls",
          "astro",
          "bashls",
          "dockerls",
          "biome",
          "jsonls",
          "harper_ls",
          "texlab",
          "marksman",
          "julials",
          "ts_ls",
          "rust_analyzer",
          "svelte",
          "tailwindcss",
          "tinymist",
          "cssls",
          "html",
        },
      })
      require("mason-tool-installer").setup({
        ensure_installed = {
          "copilot-language-server",
          "ltex-ls-plus",
          -- formatters
          "stylua",
          "alejandra",
          "shfmt",
          "gofumpt",
          -- "rustfmt", -- NOTE: Recommended to install via rustup
          "ruff",
          "prettierd",
          "yamlfix",
          "typstyle",
          "kdlfmt",
          -- linters
          "rstcheck",
          "vale",
          "stylelint",
          "hadolint",
          "eslint_d",
          -- debuggers
          "debugpy",
        },
      })
    end,
  },
}
