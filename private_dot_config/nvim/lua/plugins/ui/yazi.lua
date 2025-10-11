return {
  {
    "mikavilpas/yazi.nvim",
    event = "VeryLazy",
    dependencies = {
      "folke/snacks.nvim",
      "MagicDuck/grug-far.nvim",
    },
    keys = {
      {
        "-",
        "<cmd>Yazi<cr>",
        desc = "Open Yazi",
      },
      {
        "<leader>/",
        "<cmd>Yazi cwd<CR>",
        desc = "Open Yazi at cwd",
      },
    },
    init = function()
      vim.g.loaded_netrwPlugin = 1
    end,
    config = function()
      require("yazi").setup({
        open_for_directories = true,
        open_multiple_tabs = true,
        use_ya_for_events_reading = true,
        floating_window_scaling_factor = 0.8,
        highlight_groups = {
          hovered_buffer_background = { bg = "#363a4f" },
        },
        highlight_hovered_buffers_in_same_directory = false,
        yazi_floating_window_winblend = 0,
        yazi_floating_window_border = "rounded",
        keymaps = {
          show_help = "<C-/>",
          replace_in_directory = "<C-r>",
        },
        integrations = {
          grep_in_directory = "snacks.picker",
          grep_in_selected_files = "snacks.picker",
          bufdelete_implementation = "snacks-if-available",
          picker_add_copy_relative_path_action = "snacks.picker",
        },
      })
    end,
  },
}
