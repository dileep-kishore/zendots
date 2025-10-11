return {
  {
    "JoosepAlviste/nvim-ts-context-commentstring",
    event = "VeryLazy",
    config = function()
      require("ts_context_commentstring").setup({
        enable_autocmd = false,
      })
    end,
  },
  {
    "numToStr/Comment.nvim",
    event = "VeryLazy",
    dependencies = {
      "JoosepAlviste/nvim-ts-context-commentstring",
    },
    config = function()
      require("Comment").setup({
        sticky = true,
        mappings = { basic = true, extra = true },
        pre_hook = require("ts_context_commentstring.integrations.comment_nvim").create_pre_hook(),
      })
    end,
  },
}
