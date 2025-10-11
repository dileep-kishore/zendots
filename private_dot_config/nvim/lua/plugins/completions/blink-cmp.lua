return {
  {
    "saghen/blink.compat",
    event = "VeryLazy",
  },
  {
    "saghen/blink.cmp",
    event = "VeryLazy",
    version = "1.*",
    dependencies = {
      "rafamadriz/friendly-snippets",
      "folke/lazydev.nvim",
      "SUSTech-data/neopyter",
      "echasnovski/mini.snippets",
      "Kaiser-Yang/blink-cmp-avante",
    },
    config = function()
      require("blink.cmp").setup({
        appearance = { nerd_font_variant = "normal" },
        snippets = { preset = "mini_snippets" },
        keymap = {
          preset = "enter",
          ["<Tab>"] = {},
          ["<S-Tab>"] = {},
          ["<C-p>"] = { "select_prev", "fallback_to_mappings" },
          ["<C-n>"] = { "select_next", "fallback_to_mappings" },
          ["<C-j>"] = { "snippet_forward", "fallback" },
          ["<C-k>"] = { "snippet_backward", "fallback" },
        },
        signature = {
          enabled = false,
          window = {
            show_documentation = true,
            border = {
              { "󰙎", "WarningMsg" },
              "─",
              "╮",
              "│",
              "╯",
              "─",
              "╰",
              "│",
            },
            winhighlight = "Normal:Pmenu,CursorLine:PmenuSel,Search:None",
          },
        },
        cmdline = {
          enabled = true,
          keymap = { preset = "inherit" },
          completion = {
            list = { selection = { preselect = false } },
            menu = { auto_show = true },
            ghost_text = { enabled = false },
          },
        },
        completion = {
          list = {
            selection = {
              preselect = false,
              auto_insert = false,
            },
          },
          menu = {
            border = {
              { "󱐋", "WarningMsg" },
              "─",
              "╮",
              "│",
              "╯",
              "─",
              "╰",
              "│",
            },
            winhighlight = "Normal:Pmenu,CursorLine:PmenuSel,Search:None",
            draw = {
              components = {
                -- customize the drawing of kind icons
                kind_icon = {
                  text = function(ctx)
                    -- default kind icon
                    local icon = ctx.kind_icon
                    -- if LSP source, check for color derived from documentation
                    if ctx.item.source_name == "LSP" then
                      local color_item =
                        require("nvim-highlight-colors").format(ctx.item.documentation, { kind = ctx.kind })
                      if color_item and color_item.abbr ~= "" then
                        icon = color_item.abbr
                      end
                    end
                    return icon .. ctx.icon_gap
                  end,
                  highlight = function(ctx)
                    -- default highlight group
                    local highlight = "BlinkCmpKind" .. ctx.kind
                    -- if LSP source, check for color derived from documentation
                    if ctx.item.source_name == "LSP" then
                      local color_item =
                        require("nvim-highlight-colors").format(ctx.item.documentation, { kind = ctx.kind })
                      if color_item and color_item.abbr_hl_group then
                        highlight = color_item.abbr_hl_group
                      end
                    end
                    return highlight
                  end,
                },
              },
            },
          },
          documentation = {
            auto_show = true,
            window = {
              border = {
                { "󰙎", "WarningMsg" },
                "─",
                "╮",
                "│",
                "╯",
                "─",
                "╰",
                "│",
              },
              winhighlight = "Normal:Pmenu,CursorLine:PmenuSel,Search:None",
            },
          },
          ghost_text = { enabled = false },
          accept = {
            auto_brackets = {
              enabled = true,
              semantic_token_resolution = { enabled = true },
            },
          },
        },
        sources = {
          default = {
            "avante",
            "lazydev",
            "neopyter",
            "lsp",
            "path",
            "snippets",
            "buffer",
          },
          providers = {
            snippets = {
              should_show_items = function(ctx)
                return ctx.trigger.initial_kind ~= "trigger_character"
              end,
            },
            lazydev = {
              name = "LazyDev",
              module = "lazydev.integrations.blink",
              score_offset = 100,
            },
            neopyter = {
              name = "Neopyter",
              module = "neopyter.blink",
            },
            avante = {
              module = "blink-cmp-avante",
              name = "Avante",
            },
          },
        },
      })
    end,
  },
}
