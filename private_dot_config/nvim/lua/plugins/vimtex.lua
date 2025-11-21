return {
  {
    "lervag/vimtex",
    lazy = false,
    keys = {
      { "<leader>vc", "<cmd>VimtexCompile<cr>", desc = "Vimtex Compile" },
      { "<leader>vv", "<cmd>VimtexView<cr>", desc = "Vimtex View" },
    },
    init = function()
      vim.g.vimtex_view_method = "zathura"

      -- Compiler settings for custom output directory
      vim.g.vimtex_compiler_latexmk = {
        out_dir = "build",
        callback = 1,
        continuous = 1,
        executable = "latexmk",
        options = {
          "-verbose",
          "-file-line-error",
          "-synctex=1",
          "-interaction=nonstopmode",
          "-f",
        },
      }

      -- Quickfix settings
      vim.g.vimtex_quickfix_open_on_warning = 0
      vim.g.vimtex_quickfix_ignore_filters = {
        "Underfull",
        "Overfull",
        "LaTeX Warning: .\\+ float specifier changed to",
      }
      -- vim.g.vimtex_imaps_enabled = 0
      -- vim.g.vimtex_view_general_viewer = "okular"
      -- vim.g.vimtex_view_general_options = "--unique file:@pdf#src:@line@tex"
    end,
  },
}
