return {
  {
    "MagicDuck/grug-far.nvim",
    cmd = { "GrugFar" },
    keys = {
      {
        "<leader>sr",
        "<cmd>GrugFar<CR>",
        desc = "GrugFar replace",
      },
    },
    config = function()
      require("grug-far").setup({})
    end,
  },
  {
    "cshuaimin/ssr.nvim",
    keys = {
      {
        "<leader>sR",
        '<cmd>lua require("ssr").open()<CR>',
        mode = { "n", "v", "x" },
        desc = "SSR (structured) replace",
      },
    },
    config = function()
      require("ssr").setup({})
    end,
  },
}
