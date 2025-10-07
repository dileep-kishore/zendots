return {
  {
    "catppuccin/nvim",
    name = "catppuccin",
    lazy = false, -- Ensure it's loaded immediately
    priority = 1000, -- High priority to load before other plugins
    config = function()
      require("catppuccin").setup({
        flavour = "mocha", -- Set to mocha (other options: latte, frappe, macchiato)
        -- Add any other customizations here, e.g.:
        -- transparent_background = true,
      })
    end,
  },
}
