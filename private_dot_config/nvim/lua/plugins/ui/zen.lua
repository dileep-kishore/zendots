return {
  {
    "folke/zen-mode.nvim",
    keys = {
      {
        "<leader>zz",
        "<cmd>ZenMode<cr>",
        desc = "Zen mode",
      },
      {
        "<leader>zt",
        "<cmd>Twilight<cr>",
        desc = "Zen mode twilight",
      },
    },
    event = "VeryLazy",
    dependencies = {
      "folke/twilight.nvim",
    },
    config = function()
      require("zen-mode").setup({
        plugins = {
          twilight = { enabled = false },
        },
        window = { backdrop = 1 },
      })
    end,
  },
}
