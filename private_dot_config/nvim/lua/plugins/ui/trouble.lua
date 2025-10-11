return {
  {
    "folke/trouble.nvim",
    cmd = { "Trouble", "TroubleToggle" },
    keys = {
      {
        "<leader>xx",
        "<cmd>Trouble diagnostics toggle filter.buf=0 focus=true<CR>",
        desc = "Trouble diagnostics toggle (buffer)",
      },
      {
        "<leader>xX",
        "<cmd>Trouble diagnostics toggle focus=true<CR>",
        desc = "Trouble diagnostics toggle",
      },
      {
        "<leader>xl",
        "<cmd>Trouble lsp toggle focus=true win.position=bottom<cr>",
        desc = "Trouble LSP toggle",
      },
      { "<leader>xL", "<cmd>Trouble loclist<cr>", desc = "Trouble loclist" },
      {
        "<leader>xs",
        "<cmd>Trouble symbols toggle focus=true win.position=bottom<cr>",
        desc = "Trouble symbols toggle",
      },
      {
        "<leader>xq",
        "<cmd>Trouble qflist toggle<cr>",
        desc = "Trouble qflist toggle",
      },
      {
        "<leader>xt",
        "<cmd>Trouble todo toggle filter.buf=0 focus=true<cr>",
        desc = "Trouble todo toggle (buffer)",
      },
      {
        "<leader>xT",
        "<cmd>Trouble todo toggle focus=true<cr>",
        desc = "Trouble todo toggle",
      },
    },
    opts = {
      keys = {
        o = "jump",
        ["<cr>"] = "jump_close",
      },
    },
  },
}
