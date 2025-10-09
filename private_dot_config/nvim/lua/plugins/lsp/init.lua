require("lsps.diagnostic-signs")
local servers = require("lsps.servers")

return {
  {
    "neovim/nvim-lspconfig",
    dependencies = {
      "stevearc/conform.nvim",
      "Saghen/blink.cmp",
    },
    event = { "BufReadPre", "BufNewFile" },
    config = function()
      -- Set default configuration for all LSP servers
      vim.lsp.config("*", {
        capabilities = require("blink.cmp").get_lsp_capabilities({}, true),
        on_attach = function(_, bufnr)
          vim.api.nvim_buf_create_user_command(bufnr, "Format", function(_)
            require("conform").format({ async = true })
          end, { desc = "Format current buffer using conform" })
        end,
      })

      -- Configure and enable each LSP server
      for server_name, cfg in pairs(servers) do
        vim.lsp.config(server_name, cfg or {})
        vim.lsp.enable(server_name)
      end
    end,
  },
  {
    "folke/lazydev.nvim",
    cmd = "LazyDev",
    ft = "lua",
  },
  {
    "smjonas/inc-rename.nvim",
    event = "VeryLazy",
    opts = {
      show_message = true,
    },
  },
}
