return {
  {
    "MeanderingProgrammer/render-markdown.nvim",
    ft = { "markdown", "Avante", "quarto" },
    dependencies = {
      "nvim-treesitter/nvim-treesitter",
      "nvim-tree/nvim-web-devicons",
    },
    config = function()
      require("render-markdown").setup({
        preset = "obsidian",
        render_modes = true,
        heading = {
          icons = {
            " ",
            " ",
            " ",
            " ",
            " ",
            " ",
          },
          position = "inline",
          width = "block",
          setext = false,
          min_width = 100,
          border = true,
          border_virtual = true,
        },
        completions = { blink = { enabled = true } },
        indent = { enabled = false },
        code = {
          width = "block",
          position = "left",
          right_pad = 5,
          border = "thick",
          min_width = 80,
        },
        bullet = {
          icons = { "◉", "●", "○", "◈", "◆", "◇" },
        },
        dash = { width = 100 },
        pipe_table = {
          preset = "round",
          alignment_indicator = "┅",
        },
        checkbox = {
          checked = { scope_highlight = "@markup.strikethrough" },
        },
        file_types = { "markdown", "Avante", "quarto" },
      })
    end,
  },
}
