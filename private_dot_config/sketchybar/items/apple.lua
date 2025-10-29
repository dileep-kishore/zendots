local colors = require "colors"
local icons = require "icons"
local settings = require "settings"

local apple = sbar.add("item", {
    icon = {
        font = {
            size = 22.0,
        },
        string = icons.apple,
        padding_right = 8,
        padding_left = 8,
        highlight_color = settings.modes.service.color,
    },
    label = {
        drawing = false,
    },

    padding_left = 1,
    padding_right = 1,
    click_script = "$CONFIG_DIR/helpers/menus/bin/menus -s 0",
})

apple:subscribe("aerospace_enter_service_mode", function(_)
    sbar.animate("tanh", 10, function()
        apple:set {
            icon = {
                highlight = true,
                string = settings.modes.service.icon,
            },
        }
    end)
end)

apple:subscribe("aerospace_leave_service_mode", function(_)
    sbar.animate("tanh", 10, function()
        apple:set {
            icon = {
                highlight = false,
                string = settings.modes.main.icon,
            },
        }
    end)
end)

-- Padding to the right of the main button
sbar.add("item", {
    width = 7,
})
