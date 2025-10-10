return {
  {
    "NeogitOrg/neogit",
    event = "VeryLazy",
    cmd = { "Neogit" },
    dependencies = {
      "nvim-lua/plenary.nvim",
      "sindrets/diffview.nvim",
      "folke/snacks.nvim",
    },
    keys = {
      { "<leader>gg", "<cmd>Neogit<cr>", desc = "Neogit" },
      { "<leader>gc", "<cmd>Neogit commit<cr>", desc = "Neogit commit" },
    },
    config = function()
      require("neogit").setup({
        graph_style = "kitty",
        process_spinner = true,
        signs = {
          -- { CLOSED, OPENED }
          hunk = { "", "" },
          item = { "▶", "▼" },
          section = { "▶", "▼" },
        },
        integrations = {
          diffview = true,
          snacks = true,
        },
      })
      vim.api.nvim_create_autocmd("User", {
        pattern = "NeogitStatusRefreshed",
        callback = function()
          vim.cmd("set autoread | checktime")
        end,
      })
    end,
  },
}
