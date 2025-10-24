return {
  {
    "NMAC427/guess-indent.nvim",
    event = "BufReadPre",
    config = function()
      require("guess-indent").setup({
        auto_cmd = true,
        override_editorconfig = false,
      })
    end,
  },
  {
    "windwp/nvim-autopairs",
    event = "InsertEnter",
    opts = { check_ts = true },
  },
  {
    "Wansmer/treesj",
    keys = {
      {
        "gs",
        '<cmd>lua require("treesj").toggle()<CR>',
        desc = "Toggle treesj",
      },
    },
    opts = { use_default_keymaps = false },
  },
  {
    "HakonHarnes/img-clip.nvim",
    event = "VeryLazy",
    keys = {
      {
        "<leader>P",
        "<cmd>PasteImage<cr>",
        desc = "Paste image from clipboard",
      },
    },
    opts = {
      default = {
        dir_path = "assets",
        relative_to_current_file = false,
        show_dir_path_in_prompt = true,
      },
    },
  },
  {
    "tpope/vim-repeat",
    event = "VeryLazy",
  },
  {
    "hedyhli/outline.nvim",
    cmd = { "Outline", "OutlineOpen" },
    keys = {
      {
        "go",
        "<cmd>Outline<CR>",
        desc = "Toggle Outline",
      },
    },
    dependencies = {
      "onsails/lspkind.nvim",
    },
    opts = {
      symbols = {
        icon_source = "lspkind",
        filter = {
          default = { "String", "Variable", exclude = true },
        },
      },
      keymaps = {
        goto_location = "e",
        peek_location = "<Cr>",
        fold = "h",
        unfold = "l",
        fold_toggle = "o",
      },
    },
  },
  {
    "christoomey/vim-tmux-navigator",
    event = "VeryLazy",
  },
  {
    "folke/todo-comments.nvim",
    event = "VeryLazy",
    dependencies = { "nvim-lua/plenary.nvim" },
    opts = {
      merge_keywords = true,
      gui_style = {
        bg = "BOLD",
        fg = "BOLD",
      },
      highlight = {
        before = "",
        after = "",
        keyword = "wide_fg",
      },
      keywords = {
        QUESTION = { icon = "" },
      },
    },
  },
  {
    "kevinhwang91/nvim-bqf",
    ft = "qf",
    opts = { auto_enable = true },
  },
  {
    "iamcco/markdown-preview.nvim",
    cmd = { "MarkdownPreviewToggle", "MarkdownPreview", "MarkdownPreviewStop" },
    ft = "markdown",
    build = "cd app && npm install",
  },
  {
    "laytan/cloak.nvim",
    event = "VeryLazy",
    opts = { enabled = true },
  },
  {
    "akinsho/git-conflict.nvim",
    event = "VeryLazy",
    version = "*",
    opts = {
      default_commands = true,
      default_mappings = true,
    },
  },
  {
    "chrisgrieser/nvim-early-retirement",
    event = "VeryLazy",
    opts = {},
  },
  {
    "Goose97/timber.nvim",
    event = "VeryLazy",
    keys = {
      {
        "gll",
        function()
          return require("timber.actions").insert_log({
            position = "below",
            operator = true,
          }) .. "_"
        end,
        desc = "Insert below log statements the current line",
        mode = "n",
        expr = true,
      },
      {
        "gls",
        function()
          require("timber.actions").insert_log({
            templates = { before = "default", after = "default" },
            position = "surround",
          })
        end,
        mode = "n",
        desc = "Insert surround log statements below the current line",
      },
    },
    opts = {},
  },
  {
    "declancm/maximize.nvim",
    event = "VeryLazy",
    keys = {
      {
        "<leader>wm",
        "<cmd>Maximize<CR>",
        desc = "Window maximize toggle",
      },
    },
    opts = {},
  },
  {
    "HiPhish/rainbow-delimiters.nvim",
  },
  {
    "karb94/neoscroll.nvim",
    opts = {},
  },
}
