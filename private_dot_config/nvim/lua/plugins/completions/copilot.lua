return {
  {
    "zbirenbaum/copilot.lua",
    dependencies = {
      "copilotlsp-nvim/copilot-lsp",
    },
    event = "InsertEnter",
    cmd = "Copilot",
    init = function()
      vim.g.copilot_nes_debounce = 500
    end,
    config = function()
      require("copilot").setup({
        panel = { enabled = false },
        copilot_model = "gpt-4o-copilot",
        suggestion = {
          enabled = true,
          auto_trigger = true,
          hide_during_completion = false,
          keymap = {
            accept = "<C-l>",
            accept_line = "<C-;>",
            accept_word = false,
            next = "<A-n>",
            prev = "<A-p>",
          },
        },
        filetypes = {
          gitrebase = true,
          ["grug-far"] = false,
          ["grug-far-history"] = false,
          ["grug-far-help"] = false,
          ["."] = false,
          [""] = false,
          ["chatgpt-input"] = false,
          oil = false,
          minifiles = false,
          markdown = true,
          yaml = true,
          gitcommit = true,
        },
      })
    end,
  },
}
