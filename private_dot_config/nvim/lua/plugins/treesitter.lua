return {
  {
    "nvim-treesitter/nvim-treesitter",
    branch = "main",
    build = ":TSUpdate",
    event = "VeryLazy",
    dependencies = {
      { "nvim-treesitter/nvim-treesitter-textobjects", branch = "main" },
      "nvim-treesitter/nvim-treesitter-context",
      "windwp/nvim-ts-autotag",
    },
    config = function()
      local ts = require("nvim-treesitter")

      -- Install parsers (replaces ensure_installed = "all")
      -- Add/remove from this list as needed
      ts.install({
        "bash",
        "c",
        "cpp",
        "css",
        "dockerfile",
        "go",
        "html",
        "javascript",
        "json",
        "lua",
        "markdown",
        "markdown_inline",
        "python",
        "rust",
        "toml",
        "typescript",
        "tsx",
        "vim",
        "vimdoc",
        "yaml",
        -- NOTE: "ipkg" excluded (was in your ignore_install)
      })

      -- Enable highlighting per filetype (replaces highlight = { enable = true })
      vim.api.nvim_create_autocmd("FileType", {
        callback = function(ev)
          pcall(vim.treesitter.start, ev.buf)
        end,
      })

      -- incremental_selection is now a built-in Neovim feature via vim.treesitter
      -- These keymaps replicate your old incremental_selection config
      vim.keymap.set("n", "<CR>", function()
        vim.treesitter.select_node()
      end, { desc = "Init treesitter selection" })

      -- treesitter-context
      require("treesitter-context").setup({
        enable = true,
        max_lines = 0,
        mode = "topline",
        separator = "-",
      })

      -- nvim-ts-autotag
      require("nvim-ts-autotag").setup({
        opts = {
          enable_close = true,
          enable_rename = true,
          enable_close_on_slash = true,
        },
      })
    end,
  },

  -- Textobjects: split into its own spec, config on main branch uses direct API
  {
    "nvim-treesitter/nvim-treesitter-textobjects",
    branch = "main",
    dependencies = { { "nvim-treesitter/nvim-treesitter", branch = "main" } },
    config = function()
      require("nvim-treesitter-textobjects").setup({
        select = { lookahead = true },
        move = { set_jumps = true },
      })

      local select = require("nvim-treesitter-textobjects.select")
      local move = require("nvim-treesitter-textobjects.move")
      local swap = require("nvim-treesitter-textobjects.swap")

      -- SELECT keymaps
      local sel_maps = {
        { "af", "@function.outer" },
        { "if", "@function.inner" },
        { "ac", "@class.outer" },
        { "ic", "@class.inner" },
        { "al", "@loop.outer" },
        { "il", "@loop.inner" },
        { "as", "@conditional.outer" },
        { "is", "@conditional.inner" },
        -- neopyter cell objects
        { "aj", "@cell" },
        { "ij", "@cellcontent" },
      }
      for _, m in ipairs(sel_maps) do
        vim.keymap.set({ "x", "o" }, m[1], function()
          select.select_textobject(m[2], "textobjects")
        end, { desc = "Select " .. m[2] })
      end

      -- MOVE keymaps
      local next_start = {
        { "]f", "@function.outer" },
        { "]c", "@class.outer" },
        { "]l", "@loop.outer" },
        { "]s", "@conditional.outer" },
        { "]p", "@parameter.outer" },
        { "]j", "@cellseparator" },
      }
      local next_end = {
        { "]F", "@function.outer" },
        { "]C", "@class.outer" },
        { "]L", "@loop.outer" },
        { "]S", "@conditional.outer" },
        { "]P", "@parameter.outer" },
      }
      local prev_start = {
        { "[f", "@function.outer" },
        { "[c", "@class.outer" },
        { "[l", "@loop.outer" },
        { "[s", "@conditional.outer" },
        { "[p", "@parameter.outer" },
        { "[j", "@cellseparator" },
      }
      local prev_end = {
        { "[F", "@function.outer" },
        { "[C", "@class.outer" },
        { "[L", "@loop.outer" },
        { "[S", "@conditional.outer" },
        { "[P", "@parameter.outer" },
      }
      for _, m in ipairs(next_start) do
        vim.keymap.set({ "n", "x", "o" }, m[1], function()
          move.goto_next_start(m[2], "textobjects")
        end, { desc = "Next start " .. m[2] })
      end
      for _, m in ipairs(next_end) do
        vim.keymap.set({ "n", "x", "o" }, m[1], function()
          move.goto_next_end(m[2], "textobjects")
        end, { desc = "Next end " .. m[2] })
      end
      for _, m in ipairs(prev_start) do
        vim.keymap.set({ "n", "x", "o" }, m[1], function()
          move.goto_previous_start(m[2], "textobjects")
        end, { desc = "Prev start " .. m[2] })
      end
      for _, m in ipairs(prev_end) do
        vim.keymap.set({ "n", "x", "o" }, m[1], function()
          move.goto_previous_end(m[2], "textobjects")
        end, { desc = "Prev end " .. m[2] })
      end

      -- SWAP keymaps
      vim.keymap.set("n", "gpl", function()
        swap.swap_next("@parameter.inner")
      end, { desc = "Swap next parameter" })
      vim.keymap.set("n", "gph", function()
        swap.swap_previous("@parameter.inner")
      end, { desc = "Swap previous parameter" })

      -- Repeatable moves with ; and , (uncomment to enable)
      -- local ts_repeat = require("nvim-treesitter-textobjects.repeatable_move")
      -- vim.keymap.set({ "n", "x", "o" }, ";", ts_repeat.repeat_last_move_next)
      -- vim.keymap.set({ "n", "x", "o" }, ",", ts_repeat.repeat_last_move_previous)
    end,
  },
}
