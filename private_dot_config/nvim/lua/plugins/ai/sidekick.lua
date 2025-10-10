return {
  {
    "folke/sidekick.nvim",
    opts = {
      nes = {
        enabled = true,
        debounce = 100,
      },
      cli = {
        mux = { backend = "tmux", enabled = true },
        tools = {
          opencode = {
            env = { OPENCODE_THEME = "catppuccin" },
          },
        },
      },
    },
    keys = {
      {
        "<tab>",
        function()
          if not require("sidekick").nes_jump_or_apply() then
            return "<Tab>"
          end
        end,
        mode = { "i", "n" },
        expr = true,
        desc = "Goto/Apply Next Edit Suggestion",
      },
      {
        "<Esc>",
        function()
          require("sidekick").clear()
        end,
        desc = "Clear NES",
        mode = { "n" },
      },
      {
        "<leader>ka",
        function()
          require("sidekick.cli").toggle()
        end,
        desc = "Sidekick Toggle CLI",
      },
      {
        "<leader>ks",
        function()
          require("sidekick.cli").select({ filter = { installed = true } })
        end,
        desc = "Select CLI",
      },
      {
        "<leader>kt",
        function()
          require("sidekick.cli").send({ msg = "{this}" })
        end,
        mode = { "x", "n" },
        desc = "Send This",
      },
      {
        "<leader>kf",
        function()
          require("sidekick.cli").send({ msg = "{file}" })
        end,
        desc = "Send File",
      },
      {
        "<leader>kv",
        function()
          require("sidekick.cli").send({ msg = "{selection}" })
        end,
        mode = { "x" },
        desc = "Send Visual Selection",
      },
      {
        "<leader>kp",
        function()
          require("sidekick.cli").prompt()
        end,
        mode = { "n", "x" },
        desc = "Sidekick Select Prompt",
      },
      {
        "<leader>kc",
        function()
          require("sidekick.cli").toggle({ name = "claude", focus = true })
        end,
        desc = "Sidekick Toggle Claude",
      },
    },
  },
}
