return {
  {
    "yetone/avante.nvim",
    event = "VeryLazy",
    version = false,
    build = vim.fn.has("win32") ~= 0 and "powershell -ExecutionPolicy Bypass -File Build.ps1 -BuildFromSource false"
      or "make",
    dependencies = {
      "nvim-lua/plenary.nvim",
      "MunifTanjim/nui.nvim",
      "zbirenbaum/copilot.lua",
      "folke/snacks.nvim",
    },
    opts = {
      -- NOTE: You can use claude code with ACP:
      -- provider = "claude-code",
      provider = "copilot",
      instructions_file = "CLAUDE.md",
      mode = "agentic",
      acp_providers = {
        ["claude-code"] = {
          command = "npx",
          args = { "@zed-industries/claude-code-acp" },
          env = {
            NODE_NO_WARNINGS = "1",
            ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY"),
          },
        },
      },
      providers = {
        copilot = { model = "gpt-5" },
        openai = { model = "gpt-5" },
        claude = { model = "claude-4.5" },
        ["copilot-o4-mini"] = {
          __inherited_from = "copilot",
          model = "o4-mini",
        },
        ["copilot-claude-sonnet-4"] = {
          __inherited_from = "copilot",
          model = "claude-sonnet-4",
        },
        ["copilot-gpt-5"] = {
          __inherited_from = "copilot",
          model = "gpt-5",
        },
        ["copilot-gemini-2.5-pro"] = {
          __inherited_from = "copilot",
          model = "gemini-2.5-pro",
        },
      },
      behavior = {
        auto_suggestions = false,
        enable_claude_text_editor_tool_mode = true,
        enable_cursor_planning_mode = true,
      },
      hints = { enabled = true },
      windows = { wrap = true },
    },
  },
}
