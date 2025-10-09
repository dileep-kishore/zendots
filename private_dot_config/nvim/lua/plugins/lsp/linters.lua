return {
  {
    "mfussenegger/nvim-lint",
    event = "BufWritePost",
    config = function()
      local lint = require("lint")

      lint.linters_by_ft = {
        text = {},
        markdown = {},
        rst = { "rstcheck", "vale" },
        nix = { "nix" },
        json = { "biomejs" },
        css = { "stylelint" },
        scss = { "stylelint" },
        dockerfile = { "hadolint" },
        python = { "ruff" },
        javascript = { "biomejs" },
        typescript = { "biomejs" },
        javascriptreact = { "biomejs" },
        typescriptreact = { "biomejs" },
        svelte = { "eslint_d" },
      }

      -- Trigger linting on write
      vim.api.nvim_create_autocmd({ "BufWritePost" }, {
        callback = function()
          lint.try_lint()
        end,
      })
    end,
  },
}
