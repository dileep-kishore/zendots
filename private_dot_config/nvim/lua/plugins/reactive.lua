return {
  {
    "rasulomaroff/reactive.nvim",
    event = "VeryLazy",
    config = function()
      local palette = require("catppuccin.palettes").get_palette("mocha")
      local darken = require("catppuccin.utils.colors").darken
      require("reactive").setup({
        load = {
          "catppuccin-mocha-cursor",
          "catppuccin-mocha-cursorline",
        },
        configs = {
          ["catppuccin-mocha-cursorline"] = {
            modes = {
              n = {
                winhl = {
                  CursorLine = { bg = "None" },
                  CursorLineNr = { bg = "None" },
                },
              },
              i = {
                winhl = {
                  CursorLine = { bg = darken(palette.blue, 0.3) },
                  CursorLineNr = { bg = darken(palette.blue, 0.3) },
                },
              },
            },
          },
          ["catppuccin-mocha-cursor"] = {
            modes = {
              i = { hl = { ReactiveCursor = { bg = palette.blue } } },
              n = {
                hl = {
                  ReactiveCursor = { bg = palette.text },
                },
              },
            },
          },
        },
      })
    end,
  },
}
