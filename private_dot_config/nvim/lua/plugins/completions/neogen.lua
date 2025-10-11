return {
  {
    "danymat/neogen",
    event = "VeryLazy",
    config = function()
      require("neogen").setup({
        snippet_engine = "nvim",
        languages = {
          python = { template = { annotation_convention = "numpydoc" } },
          typescript = { template = { annotation_convention = "tsdoc" } },
          typescriptreact = { template = { annotation_convention = "tsdoc" } },
        },
      })
    end,
  },
}
