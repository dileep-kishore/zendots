return {
  {
    "rcarriga/nvim-notify",
    lazy = false,
    config = function()
      require("notify").setup({
        level = "info",
        background_color = "#191724",
      })
    end,
  },
  {
    "folke/noice.nvim",
    event = "VeryLazy",
    dependencies = {
      "MunifTanjim/nui.nvim",
      "rcarriga/nvim-notify",
    },
    config = function()
      require("noice").setup({
        lsp = {
          progress = { enabled = true },
          hover = { enabled = true },
          signature = { enabled = true },
        },
        presets = {
          bottom_search = false,
          command_palette = true,
          long_message_to_split = false,
          lsp_doc_border = true,
          inc_rename = true,
        },
        notify = { enabled = true },
        messages = { enabled = true },
      })

      -- NOTE: Disable deprecation warnings for vim.tbl_islist
      local original_deprecate = vim.deprecate

      vim.deprecate = function(msg, ...)
        if msg:find("vim.tbl_islist") then
          return
        end
        original_deprecate(msg, ...)
      end
    end,
  },
}
