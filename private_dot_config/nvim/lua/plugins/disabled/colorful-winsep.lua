return {
  {
    "nvim-zh/colorful-winsep.nvim",
    event = { "WinLeave" },
    config = function()
      require("colorful-winsep").setup({
        symbols = { "─", "│", "┌", "┐", "└", "┘" },
        animate = {
          enabled = "shift",
          shift = {
            delay = 1,
          },
        },
      })
    end,
  },
}
