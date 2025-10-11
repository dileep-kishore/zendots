return {
  {
    "jedrzejboczar/possession.nvim",
    event = "VeryLazy",
    dependencies = {
      "nvim-lua/plenary.nvim",
    },
    config = function()
      require("possession").setup({
        autosave = { current = true },
        autoload = false,
        plugins = {
          delete_hidden_buffers = false,
        },
      })
    end,
  },
}
