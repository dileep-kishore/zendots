return {
  {
    "max397574/better-escape.nvim",
    config = function()
      require("better_escape").setup({
        default_mappings = false,
        mappings = {
          c = { j = { k = "<Esc>" } },
          i = { j = { k = "<Esc>" } },
          s = { j = { k = "<Esc>" } },
          v = { j = { k = "<Esc>" } },
        },
      })
    end,
  },
}
