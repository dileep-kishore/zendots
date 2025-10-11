return {
  {
    "SUSTech-data/neopyter",
    dependencies = {
      "nvim-lua/plenary.nvim",
      "nvim-treesitter/nvim-treesitter",
      "AbaoFromCUG/websocket.nvim",
    },
    keys = {
      {
        "<leader>jc",
        "<cmd>Neopyter execute notebook:run-cell<cr>",
        desc = "run selected",
      },
      {
        "<leader>ja",
        "<cmd>Neopyter execute notebook:run-all-above<cr>",
        desc = "run all above cell",
      },
      {
        "<leader>jr",
        "<cmd>Neopyter execute kernelmenu:restart<cr>",
        desc = "restart kernel",
      },
      {
        "<leader>jA",
        "<cmd>Neopyter execute notebook:restart-run-all<cr>",
        desc = "restart kernel and run all",
      },
    },
    opts = {
      mode = "direct",
      remote_address = "127.0.0.1:9001",
      file_pattern = { "*.ju.*" },
    },
  },
}
