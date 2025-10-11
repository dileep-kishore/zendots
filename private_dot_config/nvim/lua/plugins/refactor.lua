return {
  {
    "ThePrimeagen/refactoring.nvim",
    event = "VeryLazy",
    dependencies = {
      "nvim-lua/plenary.nvim",
      "nvim-treesitter/nvim-treesitter",
    },
    keys = {
      {
        "<leader>re",
        ":Refactor extract ",
        mode = "x",
        desc = "Extract function",
      },
      {
        "<leader>rf",
        ":Refactor extract_to_file ",
        mode = "x",
        desc = "Extract function to file",
      },
      {
        "<leader>rv",
        ":Refactor extract_var ",
        mode = "x",
        desc = "Extract variable",
      },
    },
    config = function()
      require("refactoring").setup({})
    end,
  },
}
