return {
  {
    "chentoast/marks.nvim",
    event = "VeryLazy",
    keys = {
      {
        "<leader>xm",
        "<cmd>MarksListBuf<CR>",
        desc = "Quickfix marks (buffer)",
      },
      {
        "<leader>xM",
        "<cmd>MarksListAll<CR>",
        desc = "Quickfix marks (all)",
      },
    },
    opts = {
      default_mappings = true,
    },
  },
}
