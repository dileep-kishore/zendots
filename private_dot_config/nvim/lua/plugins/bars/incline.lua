return {
  {
    'b0o/incline.nvim',
    name = 'incline',
    event = 'VeryLazy',
    dependencies = {
        'nvim-tree/nvim-web-devicons',
        'cbochs/grapple.nvim',
        'folke/zen-mode.nvim',
    },
    config = function()
      local colors = require('catppuccin.palettes').get_palette 'mocha'
      local devicons = require 'nvim-web-devicons'
      local helpers = require 'incline.helpers'
      local darken = require('catppuccin.utils.colors').darken

      require('incline').setup {
        ignore = {
          floating_wins = false,
          wintypes = function(winid, wintype)
            local zen_view = package.loaded['zen-mode.view']
            if zen_view and zen_view.is_open() then
              return winid ~= zen_view.win
            end
            return wintype ~= ''
          end,
        },
        window = {
          padding = 0,
          -- padding_char = ' ',
          margin = { horizontal = 1, vertical = 0 },
        },
        render = function(props)
          local filename =
            vim.fn.fnamemodify(vim.api.nvim_buf_get_name(props.buf), ':t')
          if filename == '' then
            filename = '[No Name]'
          end

          local ft_icon, ft_color = devicons.get_icon_color(filename)

          local grapple_status = require('grapple').name_or_index() or ''
          local grapple_status_text
          if grapple_status ~= '' then
            grapple_status_text = ' 󰛢' .. grapple_status .. ' '
          else
            grapple_status_text = ' '
          end

          local modified = vim.bo[props.buf].modified

          local function get_git_diff()
            local icons = { removed = ' ', changed = ' ', added = ' ' }
            local signs = vim.b[props.buf].gitsigns_status_dict
            local labels = {}
            if signs == nil then
              return labels
            end
            for name, icon in pairs(icons) do
              if tonumber(signs[name]) and signs[name] > 0 then
                table.insert(
                  labels,
                  { icon .. signs[name] .. ' ', group = 'Diff' .. name }
                )
              end
            end
            if #labels > 0 then
              table.insert(labels, { '| ' })
            end
            return labels
          end

          local function get_diagnostic_label()
            local icons =
              { error = ' ', warn = ' ', info = ' ', hint = ' ' }
            local label = {}

            for severity, icon in pairs(icons) do
              local n = #vim.diagnostic.get(
                props.buf,
                { severity = vim.diagnostic.severity[string.upper(severity)] }
              )
              if n > 0 then
                table.insert(
                  label,
                  { icon .. n .. ' ', group = 'DiagnosticSign' .. severity }
                )
              end
            end
            if #label > 0 then
              table.insert(label, { '| ' })
            end
            return label
          end

          local inactive_modified = darken(colors.peach, 0.3)

          local res = {
            -- props.focused
            --     and {
            --       { get_diagnostic_label() },
            --       { get_git_diff() },
            --       guibg = colors.surface0,
            --     }
            --   or '',
            ft_icon
                and {
                  ' ',
                  ft_icon,
                  guifg = modified
                      and (props.focused and colors.peach or inactive_modified)
                    or props.focused and colors.blue
                    or colors.surface2,
                  -- guifg = props.focused and helpers.contrast_color(ft_color) or ft_color,
                  guibg = 'none',
                }
              or '',
            {
              ' ',
              filename,
              gui = 'italic,bold',
              guifg = modified
                  and (props.focused and colors.peach or inactive_modified)
                or props.focused and colors.blue
                or colors.surface2,
              guibg = 'none',
            },
            {
              props.focused and grapple_status_text or ' ',
              gui = 'bold',
              guifg = modified
                  and (props.focused and colors.peach or inactive_modified)
                or props.focused and colors.blue
                or colors.surface2,
              guibg = 'none',
            },
            guibg = colors.base,
          }
          -- table.insert(res, ' ')
          return res
        end,
      }
    end,
  }
}
