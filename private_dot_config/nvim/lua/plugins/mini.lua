return {
  {
    "echasnovski/mini.ai",
    config = function()
      require("mini.ai").setup({})
    end,
  },
  {
    "echasnovski/mini.animate",
    event = "VeryLazy",
    config = function()
      require("mini.animate").setup({
        cursor = { enable = false },
        scroll = { enable = false },
        resize = { enable = false },
        open = { enable = true },
        close = { enable = true },
      })
    end,
  },
  {
    "echasnovski/mini.basics",
    event = "VeryLazy",
    config = function()
      require("mini.basics").setup({
        options = { extra_ui = true },
        autocommands = {
          basic = true,
          relnum_in_visual_mode = false,
        },
      })
    end,
  },
  {
    "echasnovski/mini.icons",
    event = "VeryLazy",
    config = function()
      require("mini.icons").setup({
        style = "glpyh",
      })
    end,
  },
  {
    "echasnovski/mini.move",
    event = "VeryLazy",
    config = function()
      require("mini.move").setup({})
    end,
  },
  {
    "echasnovski/mini.operators",
    event = "VeryLazy",
    config = function()
      require("mini.operators").setup({
        exchange = { prefix = "ge" },
        sort = { prefix = "gS" },
      })
    end,
  },
  {
    "echasnovski/mini.surround",
    event = "VeryLazy",
    config = function()
      require("mini.surround").setup({
        respect_selection_type = true,
        search_method = "cover_or_nearest",
      })
    end,
  },
}
